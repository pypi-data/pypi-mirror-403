#!/usr/bin/env python
"""
Simple test client for the Pinecone Read-Only MCP Server.

Usage:
    python test_client.py

Requires PINECONE_API_KEY environment variable to be set.
"""

import asyncio
import os
import sys

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    # Check for API key
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY environment variable is required")
        sys.exit(1)

    # Start the server as a subprocess
    server_params = StdioServerParameters(
        command="pinecone-read-only-mcp",
        args=["--api-key", api_key],
    )

    print("Connecting to Pinecone Read-Only MCP Server...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected!\n")

            # List available tools
            print("=== Available Tools ===")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:80]}...")
            print()

            # Test list_namespaces
            print("=== Testing list_namespaces ===")
            result = await session.call_tool("list_namespaces", {})
            print(result.content[0].text)
            print()

            # Get first available namespace
            import json

            namespaces_result = json.loads(result.content[0].text)
            if (
                namespaces_result["status"] == "success"
                and namespaces_result["namespaces"]
            ):
                test_namespace = namespaces_result["namespaces"][0]

                # Test query with first available namespace
                print(f"=== Testing query (using namespace: {test_namespace}) ===")
                result = await session.call_tool(
                    "query",
                    {
                        "query_text": "test query",
                        "namespace": test_namespace,
                        "top_k": 5,
                        "use_reranking": True,
                    },
                )
                print(result.content[0].text)
            else:
                print("No namespaces available for testing query")


if __name__ == "__main__":
    asyncio.run(main())
