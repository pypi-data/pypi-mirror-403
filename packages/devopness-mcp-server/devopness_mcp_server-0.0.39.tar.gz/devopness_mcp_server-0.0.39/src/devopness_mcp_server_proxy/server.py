from fastmcp.client.transports import StreamableHttpTransport

from devopness_mcp_server_proxy.lib.middlewares.initialize_middleware import (
    InitializeMiddleware,
)
from devopness_mcp_server_proxy.lib.proxy import (
    ProxyClientFactory,
    ProxyServer,
)


async def proxy_run(
    mcp_url: str,
    devopness_token: str,
) -> None:
    """
    Configure and run the Devopness MCP Server Proxy.

    Args:
        mcp_url (str): The URL of the MCP server to proxy to.
        devopness_token (str): The Devopness Token for authentication.
    """

    transport = StreamableHttpTransport(
        url=mcp_url,
        auth=devopness_token,
    )

    client_factory = ProxyClientFactory(transport)

    proxy = ProxyServer(
        name="Devopness MCP Server",
        client_factory=client_factory,
    )

    proxy.add_middleware(InitializeMiddleware(client_factory))

    await proxy.run_async(
        transport="stdio",
        show_banner=False,
        log_level="info",
    )
