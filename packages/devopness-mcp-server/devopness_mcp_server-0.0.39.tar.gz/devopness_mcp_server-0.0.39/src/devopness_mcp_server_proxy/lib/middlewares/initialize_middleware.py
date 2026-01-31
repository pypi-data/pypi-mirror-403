from typing import override

import mcp.types as mt
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from devopness_mcp_server_proxy.lib.proxy import (
    ProxyClientFactory,
)


class InitializeMiddleware(Middleware):
    """Intercept MCP initialize request and initialize the proxy client."""

    def __init__(self, client_factory: ProxyClientFactory) -> None:
        super().__init__()

        self._client_factory = client_factory

    @override
    async def on_initialize(
        self,
        context: MiddlewareContext[mt.InitializeRequest],
        call_next: CallNext[mt.InitializeRequest, mt.InitializeResult | None],
    ) -> mt.InitializeResult | None:
        try:
            self._client_factory.set_init_params(context.message)

            client = await self._client_factory.get_client()
            await client._connect()

            return await call_next(context)

        except Exception:
            raise
