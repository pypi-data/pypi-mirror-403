import os
from base64 import b64encode
from typing import cast, override

import mcp.types as mt
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult

from ..devopness_api import DevopnessCredentials, ensure_authenticated
from ..types import MCP_TRANSPORT_PROTOCOL, ServerContext


class AuthMiddleware(Middleware):
    @override
    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        ctx = cast(ServerContext, context.fastmcp_context)
        credentials = get_credentials(context)
        ensure_authenticated(ctx, credentials)

        return await call_next(context)


def get_credentials(
    ctx: MiddlewareContext[mt.CallToolRequestParams],
) -> DevopnessCredentials:
    transport = cast(
        MCP_TRANSPORT_PROTOCOL,
        ctx.fastmcp_context.fastmcp.env.DEVOPNESS_MCP_SERVER_TRANSPORT,  # type: ignore[union-attr]
    )

    if transport == "stdio":
        return credentials_stdio()

    if transport == "streamable-http":
        return credentials_http_stream()

    raise ValueError(f"Unknown transport: {transport}")


def credentials_stdio() -> DevopnessCredentials:
    api_token = os.environ.get("DEVOPNESS_PERSONAL_ACCESS_TOKEN")

    if api_token:
        return credentials_stdio_api_token(api_token)

    raise RuntimeError(
        "ERROR: Devopness Credentials."
        "\nThe environment variable DEVOPNESS_PERSONAL_ACCESS_TOKEN must be set."
    )


def credentials_stdio_api_token(
    api_token: str,
) -> DevopnessCredentials:
    return DevopnessCredentials(
        type="api_token",
        data=b64encode(api_token.encode()).decode("utf-8"),
    )


def credentials_http_stream() -> DevopnessCredentials:
    request_headers: dict[str, str] = get_http_headers()

    # FastMCP `get_http_headers` returns all headers as lowercase
    oauth_token = request_headers.get("authorization")

    if oauth_token:
        return credentials_http_stream_oauth_token(oauth_token)

    raise RuntimeError(
        "ERROR: Devopness Credentials.\nThe header Authorization Bearer must be set."
    )


def credentials_http_stream_oauth_token(oauth_token: str) -> DevopnessCredentials:
    return DevopnessCredentials(
        type="oauth_token",
        data=b64encode(oauth_token.replace("Bearer ", "").encode()).decode("utf-8"),
    )
