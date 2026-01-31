# ruff: noqa: ANN401

import contextlib
from typing import Any, Self, override

import httpx
from fastmcp import Client
from fastmcp.client.transports import ClientTransport
from fastmcp.exceptions import NotFoundError
from fastmcp.server.proxy import ClientFactoryT, FastMCPProxy
from fastmcp.server.proxy import ProxyClient as _ProxyClient
from fastmcp.server.proxy import ProxyToolManager as _ProxyToolManager
from fastmcp.tools import Tool
from mcp import McpError
from mcp.types import Implementation as ClientInfo
from mcp.types import InitializeRequest, JSONRPCError, JSONRPCMessage


class ProxyToolManager(_ProxyToolManager):
    """
    Proxy tool manager that caches the tools after the first retrieval.
    """

    def __init__(
        self,
        client_factory: ClientFactoryT,
        **kwargs: Any,
    ) -> None:
        super().__init__(client_factory, **kwargs)

        self._cached_tools: dict[str, Tool] | None = None

    @override
    async def get_tool(self, key: str) -> Tool:
        """
        Return the tool from cached tools.
        """
        if self._cached_tools is None:
            self._cached_tools = await self.get_tools()

        if key in self._cached_tools:
            return self._cached_tools[key]

        raise NotFoundError(f"Tool {key!r} not found")

    @override
    async def get_tools(self) -> dict[str, Tool]:
        """Return list tools."""
        self._cached_tools = await super(ProxyToolManager, self).get_tools()

        return self._cached_tools


class ProxyServer(FastMCPProxy):
    def __init__(
        self,
        *,
        client_factory: ClientFactoryT,
        **kwargs: Any,
    ) -> None:
        super().__init__(client_factory=client_factory, **kwargs)

        self._tool_manager = ProxyToolManager(
            client_factory=self.client_factory,
            transformations=self._tool_manager.transformations,
        )


class ProxyClient(_ProxyClient):
    """
    Proxy client that retries connection on RuntimeError and
    raises McpError on JSON-RPC errors.
    """

    def __init__(
        self,
        transport: ClientTransport,
        max_connect_retry: int = 3,
        **kwargs: Any,
    ) -> None:
        super().__init__(transport, **kwargs)

        self._max_connect_retry = max_connect_retry

    @override
    async def _connect(
        self,
        retry: int = 0,
    ) -> Self:
        try:
            result = await super(ProxyClient, self)._connect()

            return result  # noqa: RET504

        except httpx.HTTPStatusError as http_error:
            response = http_error.response

            try:
                body = await response.aread()
                jsonrpc_msg = JSONRPCMessage.model_validate_json(body).root

            except Exception:
                raise http_error from http_error

            # If the response is a JSON-RPC error, we want to raise it as an McpError
            if isinstance(jsonrpc_msg, JSONRPCError):
                raise McpError(error=jsonrpc_msg.error) from http_error

            raise http_error

        except RuntimeError as e:
            if isinstance(e.__cause__, McpError):
                raise e.__cause__ from e

            if retry > self._max_connect_retry:
                raise e

            with contextlib.suppress(httpx.TimeoutException):
                await self._disconnect(force=True)

            return await self._connect(retry + 1)

    async def __aexit__(
        self,
        _exc_type: Any,
        _exc_val: Any,
        _exc_tb: Any,
    ) -> None:
        """
        The Devopness MCP Server Proxy is a proxy from stdio to streamble-http.

        We want the client to remain connected until the stdio connection is closed.

        https://modelcontextprotocol.io/specification/2024-11-05/basic/transports#stdio

            1. close stdin
            2. terminate subprocess
        """


class ProxyClientFactory:
    """Client factory that returns a connected client."""

    def __init__(self, transport: ClientTransport) -> None:
        """Initialize a client factory with transport."""
        self._transport = transport
        self._client: ProxyClient | None = None
        self._initialize_request: InitializeRequest | None = None

    def set_init_params(self, initialize_request: InitializeRequest) -> None:
        """Set client init parameters."""
        self._initialize_request = initialize_request

    async def get_client(self) -> Client:
        """Get client."""
        if self._client is None:
            self._client = ProxyClient(
                self._transport,
                client_info=ClientInfo(
                    name="Devopness MCP Server Proxy",
                    version="0.1.0",
                ),
                elicitation_handler=self._handle_elicitation,
            )

        return self._client

    async def __call__(self) -> Client:
        """Implement the callable factory interface."""
        return await self.get_client()

    async def disconnect(self) -> None:
        """Disconnect all the clients (no throw)."""
        try:
            if self._client:
                await self._client._disconnect(force=True)

        except Exception:  # noqa: S110
            pass

    async def _handle_elicitation(
        self,
        message: Any,
        response_type: Any,
        params: Any,
        context: Any,
    ) -> dict[str, Any]:
        """
        Elicitation handler that always accepts the elicitation without user input.
        """
        return {}
