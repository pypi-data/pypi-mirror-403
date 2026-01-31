"""
Simple MCP Client Example

This module demonstrates how to connect to the Devopness MCP server using the
FastMCP client with a Personal Access Token (PAT) for authentication.

It loads environment variables from `.env` and `.env.e2e`, configures a remote
MCP server using the `streamable-http` transport, and performs basic operations:
- Establishing a connection
- Pinging the server
- Listing available tools
- Fetching the authenticated user's profile

This script is intended as a minimal reference implementation for local
development and end-to-end testing.
"""

import asyncio
import os

import dotenv
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig, RemoteMCPServer

dotenv.load_dotenv(override=True, dotenv_path=".env")
dotenv.load_dotenv(override=True, dotenv_path=".env.e2e")

mcp_server_url = os.environ.get("DEVOPNESS_MCP_SERVER_URL", "http://localhost")

transport = MCPConfig(
    mcpServers={
        "devopness_mcp_server": RemoteMCPServer(
            url=f"{mcp_server_url}/mcp/",
            transport="streamable-http",
            headers={
                "Authorization": "Bearer "
                + os.environ.get(
                    "DEVOPNESS_PERSONAL_ACCESS_TOKEN",
                    "invalid_token",
                ),
            },
        ),
    }
)

client = Client(transport)


async def main() -> None:
    async with client:
        await client.ping()

        tools = await client.list_tools()

        print("Available tools:")
        for tool in tools:
            print(tool.name)

        me = await client.call_tool("devopness_get_user_profile", {})
        print(f"\nUser profile: {me}")


if __name__ == "__main__":
    asyncio.run(main())
