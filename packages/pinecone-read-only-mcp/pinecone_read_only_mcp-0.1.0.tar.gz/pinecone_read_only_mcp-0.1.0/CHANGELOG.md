# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-26

### Added
- Initial release of Pinecone Read-Only MCP
- `list_namespaces` tool to dynamically discover available namespaces in Pinecone indexes
- `query` tool for hybrid semantic search with reranking
- Configurable Pinecone connection via environment variables or CLI
- Support for both stdio and SSE transport mechanisms
- Hybrid search combining dense and sparse embeddings
- Optional semantic reranking using BGE reranker model
- Input validation and error handling for production use
- Automatic namespace discovery from Pinecone index stats
