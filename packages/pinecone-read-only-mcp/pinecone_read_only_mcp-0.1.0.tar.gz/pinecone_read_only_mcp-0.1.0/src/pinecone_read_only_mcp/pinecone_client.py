"""
Pinecone client for hybrid search retrieval.

Optimized Pinecone query class that performs hybrid search (dense + sparse)
with reranking. Designed for high performance with connection pooling and
lazy initialization.
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from pinecone import Pinecone

logger = logging.getLogger(__name__)


class PineconeClient:
    """
    Optimized Pinecone client for hybrid search retrieval.

    Features:
    - Lazy initialization of Pinecone client and indexes
    - Connection reuse for better performance
    - Hybrid search (dense + sparse) with reranking
    - Configurable via environment variables or constructor parameters
    """

    def __init__(
        self,
        api_key: str | None = None,
        index_name: str | None = None,
        rerank_model: str | None = None,
        top_k: int | None = None,
    ):
        """
        Initialize the Pinecone client.

        Args:
            api_key: Pinecone API key (falls back to PINECONE_API_KEY env var)
            index_name: Pinecone index name (default: "rag-hybrid")
            rerank_model: Reranking model name (default: "bge-reranker-v2-m3")
            top_k: Default number of results to return (default: 10)
        """
        # Load environment variables
        load_dotenv()

        self.api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "rag-hybrid")
        self.rerank_model = rerank_model or os.getenv(
            "PINECONE_RERANK_MODEL", "bge-reranker-v2-m3"
        )
        self.default_top_k = top_k or int(os.getenv("PINECONE_TOP_K", "10"))

        # Lazy initialization
        self._pc: Pinecone | None = None
        self._dense_index: Any = None
        self._sparse_index: Any = None
        self._initialized = False

    def _ensure_client(self) -> Pinecone:
        """Ensure Pinecone client is initialized."""
        if self._pc is None:
            if not self.api_key:
                raise ValueError(
                    "Pinecone API key is required. Set PINECONE_API_KEY environment "
                    "variable or pass api_key parameter."
                )
            self._pc = Pinecone(api_key=self.api_key)
            logger.debug("Pinecone client initialized")
        return self._pc

    def _ensure_indexes(self) -> tuple[Any, Any]:
        """Ensure Pinecone indexes are initialized and return them."""
        if self._initialized:
            return self._dense_index, self._sparse_index

        pc = self._ensure_client()
        dense_name = self.index_name
        sparse_name = f"{self.index_name}-sparse"

        self._dense_index = pc.Index(dense_name)
        self._sparse_index = pc.Index(sparse_name)
        self._initialized = True

        logger.info(f"Connected to indexes: {dense_name} and {sparse_name}")
        return self._dense_index, self._sparse_index

    def list_namespaces(self) -> list[str]:
        """
        List all available namespaces in the Pinecone index.

        Fetches the list of namespaces from both dense and sparse indexes
        and returns the union of available namespaces.

        Returns:
            List of namespace names available in the index
        """
        try:
            dense_index, sparse_index = self._ensure_indexes()

            # Get stats from both indexes to discover namespaces
            namespaces = set()

            # Try to get namespaces from dense index stats
            try:
                dense_stats = dense_index.describe_index_stats()
                if hasattr(dense_stats, "namespaces") and dense_stats.namespaces:
                    namespaces.update(dense_stats.namespaces.keys())
            except Exception as e:
                logger.debug(f"Could not get namespaces from dense index: {e}")

            # Try to get namespaces from sparse index stats
            try:
                sparse_stats = sparse_index.describe_index_stats()
                if hasattr(sparse_stats, "namespaces") and sparse_stats.namespaces:
                    namespaces.update(sparse_stats.namespaces.keys())
            except Exception as e:
                logger.debug(f"Could not get namespaces from sparse index: {e}")

            return sorted(namespaces)
        except Exception as e:
            logger.error(f"Error listing namespaces: {e}")
            return []

    def _search_index(
        self,
        index: Any,
        query: str,
        top_k: int,
        namespace: str | None = None,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search a Pinecone index using text query.

        Args:
            index: Pinecone index to search
            query: Search query text
            top_k: Number of results to return
            namespace: Optional namespace to search within
            metadata_filter: Optional metadata filter

        Returns:
            List of search hits
        """
        try:
            query_dict: dict[str, Any] = {
                "top_k": top_k,
                "inputs": {"text": query},
            }

            if metadata_filter is not None:
                query_dict["filter"] = metadata_filter

            result = index.search(
                namespace=namespace,
                query=query_dict,
            )
            return result.get("result", {}).get("hits", [])
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []

    def _merge_results(
        self, dense_hits: list[dict[str, Any]], sparse_hits: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Merge and deduplicate results from dense and sparse searches.

        Uses the higher score when duplicates are found.
        """
        deduped: dict[str, dict[str, Any]] = {}

        for hit in dense_hits + sparse_hits:
            hit_id = hit.get("_id", "")
            hit_score = hit.get("_score", 0.0)

            if hit_id in deduped and deduped[hit_id].get("_score", 0.0) >= hit_score:
                continue

            hit_metadata = {}
            content = ""
            for key, metadata in hit.get("fields", {}).items():
                if key == "chunk_text":
                    content = metadata
                else:
                    hit_metadata[key] = metadata

            deduped[hit_id] = {
                "_id": hit_id,
                "_score": hit_score,
                "chunk_text": content,
                "metadata": hit_metadata,
            }

        return sorted(
            deduped.values(), key=lambda x: x.get("_score", 0.0), reverse=True
        )

    def _rerank_results(
        self, query: str, results: list[dict[str, Any]], top_n: int
    ) -> list[dict[str, Any]]:
        """
        Rerank results using Pinecone's reranking model.

        Args:
            query: Original query text
            results: Merged search results
            top_n: Number of results to return after reranking

        Returns:
            Reranked results as list of dicts
        """
        if not results:
            return []

        pc = self._ensure_client()

        try:
            rerank_result = pc.inference.rerank(
                model=self.rerank_model,
                query=query,
                documents=results,
                rank_fields=["chunk_text"],
                top_n=top_n,
                return_documents=True,
                parameters={"truncate": "END"},
            )

            reranked = []
            for item in rerank_result.data:
                document = item.get("document", {})
                reranked.append(
                    {
                        "id": document.get("_id", ""),
                        "content": document.get("chunk_text", ""),
                        "score": float(item.get("score", 0.0)),
                        "metadata": document.get("metadata", {}),
                        "reranked": True,
                    }
                )
            return reranked

        except Exception as e:
            logger.error(f"Error reranking results: {e}")
            # Fall back to returning unreranked results
            return [
                {
                    "id": result.get("_id", ""),
                    "content": result.get("chunk_text", ""),
                    "score": result.get("_score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "reranked": False,
                }
                for result in results[:top_n]
            ]

    def query(
        self,
        query: str,
        top_k: int | None = None,
        namespace: str = "mailing",
        metadata_filter: dict[str, Any] | None = None,
        use_reranking: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Query Pinecone indexes using hybrid search with optional reranking.

        Performs parallel searches on dense and sparse indexes, merges results,
        and optionally reranks using the configured reranking model.

        Args:
            query: Search query text
            top_k: Number of results to return (default: configured default_top_k)
            namespace: Pinecone namespace to search (default: "mailing")
            metadata_filter: Optional metadata filter for the search
            use_reranking: Whether to use reranking (default: True)

        Returns:
            List of document dicts with id, content, score, metadata, and reranked flag

        Raises:
            ValueError: If the query is empty or namespace is invalid
            RuntimeError: If Pinecone indexes cannot be initialized
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        top_k = top_k or self.default_top_k
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if top_k > 100:
            top_k = 100  # Cap at 100 for performance

        # Ensure indexes are ready
        dense_index, sparse_index = self._ensure_indexes()

        # Perform hybrid search
        dense_hits = self._search_index(
            dense_index, query, top_k, namespace, metadata_filter
        )
        sparse_hits = self._search_index(
            sparse_index, query, top_k, namespace, metadata_filter
        )

        # Merge results
        merged_results = self._merge_results(dense_hits, sparse_hits)

        # Optionally rerank
        if use_reranking:
            documents = self._rerank_results(query, merged_results, top_n=top_k)
        else:
            documents = [
                {
                    "id": result.get("_id", ""),
                    "content": result.get("chunk_text", ""),
                    "score": result.get("_score", 0.0),
                    "metadata": result.get("metadata", {}),
                    "reranked": False,
                }
                for result in merged_results[:top_k]
            ]

        logger.info(
            f"Retrieved {len(documents)} documents from hybrid search "
            f"(dense: {len(dense_hits)}, sparse: {len(sparse_hits)})"
        )

        return documents
