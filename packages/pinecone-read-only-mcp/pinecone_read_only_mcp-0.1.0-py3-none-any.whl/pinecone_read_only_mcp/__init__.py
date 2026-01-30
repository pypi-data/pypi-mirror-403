"""
Pinecone Read-Only MCP Server Package.

A Model Context Protocol server for semantic search over Pinecone vector
databases using hybrid search with reranking and automatic namespace discovery.
"""

from .server import main

__all__ = ["main"]
