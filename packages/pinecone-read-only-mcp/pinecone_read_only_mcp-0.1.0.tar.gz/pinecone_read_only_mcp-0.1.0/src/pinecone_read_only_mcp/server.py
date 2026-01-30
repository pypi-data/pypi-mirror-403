"""
Pinecone Read-Only MCP Server.

This module implements a Model Context Protocol (MCP) server that provides
semantic search capabilities over Pinecone vector databases using hybrid
search (dense + sparse) with reranking.
"""

import json
import logging
import os
import sys
from typing import Annotated

import click
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .pinecone_client import PineconeClient

# Environment variable for log level
LOG_LEVEL = os.environ.get("PINECONE_READ_ONLY_MCP_LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Global Pinecone client (initialized lazily)
_pinecone_client: PineconeClient | None = None


def get_pinecone_client() -> PineconeClient:
    """Get or create the global Pinecone client."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client


def set_pinecone_client(client: PineconeClient) -> None:
    """Set the global Pinecone client (for configuration via CLI)."""
    global _pinecone_client
    _pinecone_client = client


# Create FastMCP server
mcp = FastMCP(
    "Pinecone Read-Only MCP",
    instructions=(
        "A semantic search server that provides hybrid search capabilities "
        "over Pinecone vector indexes with automatic namespace discovery."
    ),
)


@mcp.tool()
def list_namespaces() -> str:
    """
    List all available namespaces in the Pinecone index.

    Discovers and returns a list of namespace names that can be queried.
    Namespaces are logical partitions within the Pinecone index that
    separate different data collections.
    """
    try:
        client = get_pinecone_client()
        namespaces = client.list_namespaces()
        return json.dumps(
            {
                "status": "success",
                "namespaces": namespaces,
                "count": len(namespaces),
            },
            indent=2,
        )
    except Exception as e:
        logger.error(f"Error listing namespaces: {e}")
        return json.dumps(
            {
                "status": "error",
                "message": str(e)
                if LOG_LEVEL == "DEBUG"
                else "Failed to list namespaces",
            }
        )


@mcp.tool()
def query(
    query_text: Annotated[
        str, Field(description="Search query text. Be specific for better results.")
    ],
    namespace: Annotated[
        str,
        Field(
            description=(
                "Namespace to search within. Use list_namespaces tool to "
                "discover available namespaces in the index."
            ),
        ),
    ],
    top_k: Annotated[
        int,
        Field(
            description="Number of results to return (1-100). Default: 10",
            default=10,
            ge=1,
            le=100,
        ),
    ] = 10,
    use_reranking: Annotated[
        bool,
        Field(
            description=(
                "Whether to use semantic reranking for better relevance. "
                "Slower but more accurate. Default: true"
            ),
            default=True,
        ),
    ] = True,
) -> str:
    """
    Search the Pinecone vector database using hybrid semantic search.

    Performs a hybrid search combining dense and sparse embeddings for
    better recall, with optional reranking for improved precision.
    Returns documents with relevance scores and metadata.

    Supports natural language queries and returns the most relevant
    documents based on semantic similarity.
    """
    try:
        # Validate query
        if not query_text or not query_text.strip():
            return json.dumps(
                {
                    "status": "error",
                    "message": "Query text cannot be empty",
                }
            )

        client = get_pinecone_client()
        results = client.query(
            query=query_text.strip(),
            top_k=top_k,
            namespace=namespace,
            use_reranking=use_reranking,
        )

        # Format results for output
        formatted_results = []
        for doc in results:
            metadata = doc.get("metadata", {})
            formatted_results.append(
                {
                    "paper_number": (
                        metadata.get("document_number")
                        or metadata.get("filename", "").replace(".md", "").upper()
                        or None
                    ),
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "url": metadata.get("url", ""),
                    # Truncate for readability
                    "content": doc.get("content", "")[:2000],
                    "score": round(doc.get("score", 0.0), 4),
                    "reranked": doc.get("reranked", False),
                }
            )

        return json.dumps(
            {
                "status": "success",
                "query": query_text,
                "namespace": namespace,
                "result_count": len(formatted_results),
                "results": formatted_results,
            },
            indent=2,
            ensure_ascii=False,
        )

    except ValueError as e:
        logger.warning(f"Validation error in query: {e}")
        return json.dumps(
            {
                "status": "error",
                "message": str(e),
            }
        )
    except Exception as e:
        logger.error(f"Error executing query: {e}", exc_info=True)
        return json.dumps(
            {
                "status": "error",
                "message": str(e)
                if LOG_LEVEL == "DEBUG"
                else "An error occurred while processing your query",
            }
        )


@click.command()
@click.option(
    "--api-key",
    envvar="PINECONE_API_KEY",
    help="Pinecone API key (can also be set via PINECONE_API_KEY env var)",
)
@click.option(
    "--index-name",
    default="rag-hybrid",
    envvar="PINECONE_INDEX_NAME",
    help="Pinecone index name (default: rag-hybrid)",
)
@click.option(
    "--rerank-model",
    default="bge-reranker-v2-m3",
    envvar="PINECONE_RERANK_MODEL",
    help="Reranking model name (default: bge-reranker-v2-m3)",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type (default: stdio)",
)
@click.option(
    "--port",
    default=8000,
    help="Port for SSE transport (default: 8000)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Logging level (default: INFO)",
)
def main(
    api_key: str | None,
    index_name: str,
    rerank_model: str,
    transport: str,
    port: int,
    log_level: str,
) -> int:
    """
    Run the Pinecone Read-Only MCP server.

    Provides semantic search over Pinecone vector indexes using hybrid
    search with automatic namespace discovery.
    """
    # Configure logging
    logging.getLogger().setLevel(log_level)

    # Validate API key
    if not api_key:
        logger.error(
            "Pinecone API key is required. Set PINECONE_API_KEY environment "
            "variable or use --api-key option."
        )
        return 1

    # Initialize Pinecone client with configuration
    client = PineconeClient(
        api_key=api_key,
        index_name=index_name,
        rerank_model=rerank_model,
    )
    set_pinecone_client(client)

    logger.info(f"Starting Pinecone Read-Only MCP server with {transport} transport")
    logger.info(f"Using Pinecone index: {index_name}")

    try:
        if transport == "sse":
            mcp.run(transport="sse", port=port)
        else:
            mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
