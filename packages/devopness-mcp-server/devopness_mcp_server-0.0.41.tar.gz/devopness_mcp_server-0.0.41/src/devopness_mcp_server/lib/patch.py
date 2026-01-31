"""
CONTEXT:
- ANY changes here require extensive testing across ALL MCP functionality
- FastMCP version updates can break this without warning
- All patches here are monkey-patching internal FastMCP APIs (inherently fragile)

WHY THIS FILE EXISTS:
1. FastMCP doesn't support custom dependency injection natively
2. Our tools need access to OAuth configuration, API clients, and environment variables
3. Without these patches, our entire authentication and API integration system breaks
4. We patch internal FastMCP modules that aren't part of their public API

WHAT THIS FILE DOES:
- Replaces FastMCP's context injection system with our custom ServerContext
- Implements complete OAuth 2.0 flow endpoints (RFC 8414, RFC 9728, etc.)
- Provides bearer token authentication middleware
- Enables tools to access devopness_api, server config, and auth systems

FUTURE PLANS:
- HIGH PRIORITY: Migrate OAuth to FastMCP's native RemoteOAuthProvider (https://gofastmcp.com/servers/auth/remote-oauth)
- Monitor FastMCP roadmap for native custom context support
- Replace context injection patches when FastMCP adds proper dependency injection

VERSION MANAGEMENT:
- pyproject.toml must pin FastMCP to specific versions (no caret ranges)
- Test ALL functionality when updating any FastMCP-related dependencies
"""

import base64
from functools import wraps
from typing import Any, Awaitable, Callable, Literal, Optional, cast

import fastmcp.server.dependencies
import fastmcp.tools.tool
import httpx
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
from mcp.server.auth.provider import TokenVerifier as TokenVerifierProtocol
from mcp.server.auth.routes import cors_middleware
from pydantic import AnyUrl, BaseModel, ValidationError
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from starlette.routing import Route

from .token_verifier import create_introspection_verifier
from .types import Server, ServerContext

__all__ = [
    "patch_oauth_middleware_and_routes",
    "patch_server_context_injection",
]

# Default client name for OAuth registrations
DEFAULT_CLIENT_NAME = "Devopness MCP Server"


def patch_server_context_injection(server: Server) -> None:
    """⚠️  CRITICAL PATCH: FastMCP Context Injection Override

    🚨 MAINTENANCE WARNING: This is a FRAGILE monkey patch! 🚨

    🔥 TODO - CHECK FASTMCP OFFICIAL CONTEXT EXTENSION:
    Investigate if FastMCP now provides official ways to extend FastMCP.Server.Context
    with custom dependencies. Our needs are documented in:
    - types.py::Server - Custom server fields (env, devopness, logger)
    - types.py::ServerContext - Custom context wrapper with server access

    If FastMCP has added proper dependency injection or context extension APIs,
    replace this entire monkey patch with the official mechanism.

    WHY THIS PATCH IS NECESSARY (LEGACY):
    - FastMCP's default context system doesn't support custom dependency injection
    - Our MCP tools REQUIRE access to:
      * Devopness API client instances
      * Server environment variables and settings

    WHAT THIS PATCH DOES:
    - Monkey patches fastmcp.tools.tool.get_context()
    - Monkey patches fastmcp.server.dependencies.get_context()
    - Replaces FastMCP's default context with our ServerContext wrapper
    - Enables ALL our tools to access server.env, server.devopness, etc.

    FRAGILITY RISKS:
    - FastMCP may change these internal APIs at ANY time (even in PATCH releases)
    - The get_context() functions are NOT part of FastMCP's public API
    - Type hints may break if FastMCP changes internal module structure
    - This patch MUST be applied before any tools are registered

    BREAKING SCENARIOS:
    - FastMCP renames or moves get_context functions
    - FastMCP changes context object structure or inheritance
    - FastMCP adds their own custom context support (conflicts with ours)
    - FastMCP removes or refactors the modules we're patching

    TESTING REQUIREMENTS:
    - Test MCP tools after any FastMCP-related dependency changes
    - Verify OAuth flow still works end-to-end
    - Check that tools can access server.env variables
    - Ensure API calls to Devopness still authenticate properly

    Args:
        server: Our custom Server instance with OAuth and API configuration

    Raises:
        AttributeError: If FastMCP's internal APIs have changed

    Note:
        This function MUST be called before registering any tools that use get_context()
    """
    original_get_context = fastmcp.tools.tool.get_context  # type: ignore[attr-defined]

    @wraps(original_get_context)
    def enhanced_get_context() -> ServerContext:
        """
        Enhanced context provider that returns custom ServerContext.

        Returns:
            ServerContext: Custom context with OAuth-enabled server instance
        """
        original_context = original_get_context()
        return ServerContext(original_context)

    # ⚠️  FRAGILE MONKEY PATCHING: These lines directly modify FastMCP's internal modules
    # If FastMCP moves, renames, or removes these functions, this will break silently
    # The type: ignore comments are necessary because we're accessing private APIs
    fastmcp.tools.tool.get_context = enhanced_get_context  # type: ignore[attr-defined]
    fastmcp.server.dependencies.get_context = enhanced_get_context

    server.logger.info("Custom ServerContext injection patch applied")


def patch_oauth_middleware_and_routes(server: Server) -> None:
    """⚠️  CRITICAL PATCH: Complete OAuth 2.0 Implementation Override

    🚨 MAINTENANCE WARNING: This completely replaces FastMCP's auth system! 🚨

    🔥 TODO - MIGRATION TO FASTMCP NATIVE OAUTH:
    FastMCP now has official OAuth support! See: https://gofastmcp.com/servers/auth/remote-oauth

    MIGRATION PLAN:
    1. Evaluate FastMCP's RemoteOAuthProvider to see if it meets our needs
    2. Check if we can extend/customize it for Devopness OAuth server integration
    3. Test compatibility with our current OAuth flow (PKCE, client registration, etc.)
    4. If compatible, replace this entire patch with FastMCP's native implementation

    BENEFITS OF MIGRATION:
    - Remove this fragile monkey patching completely
    - Use FastMCP's maintained and tested OAuth implementation
    - Reduce our maintenance burden significantly
    - Follow FastMCP's official patterns and best practices

    WHY THIS MASSIVE PATCH EXISTS (LEGACY):
    - FastMCP's OAuth support was incomplete/insufficient when we built this
    - We need full RFC-compliant OAuth 2.0 with PKCE support
    - Bearer token authentication must work with our API architecture

    WHAT THIS PATCH IMPLEMENTS:
    1. Complete OAuth 2.0 Authorization Server Metadata (RFC 8414)
    2. OAuth 2.0 Protected Resource Metadata (RFC 9728)
    3. Dynamic Client Registration (RFC 7591)
    4. Authorization Code Flow with PKCE (RFC 6749 + RFC 7636)
    5. Bearer Token Authentication Middleware
    6. Token Introspection for validation
    7. CORS support for web-based OAuth flows

    ENDPOINTS CREATED:
    - /.well-known/oauth-authorization-server (server metadata)
    - /.well-known/oauth-protected-resource (resource metadata)
    - /register (dynamic client registration)
    - /authorize (authorization code flow start)
    - /token (token exchange endpoint)

    FRAGILITY RISKS:
    - Changes to FastMCP's middleware system could break our patches
    - Starlette/FastAPI dependencies could introduce breaking changes

    Args:
        server: Server instance with OAuth configuration in server.env

    Side Effects:
        - Completely replaces server.auth with custom token verifier
        - Adds multiple OAuth endpoints to the application
        - Installs authentication middleware

    Note:
        This must be called during server initialization before starting FastMCP
    """
    server.logger.info("Applying OAuth middleware and routes patch...")

    # ⚠️  CRITICAL: Custom token verifier with embedded route definitions
    token_verifier = create_introspection_verifier(
        endpoint=server.env.DEVOPNESS_MCP_AUTH_SERVER_INTROSPECTION_URL,
        server_url=server.env.DEVOPNESS_MCP_SERVER_URL,
        # 🚨 HACK: Embedding route definitions in token verifier constructor
        # This is fragile - changes to create_introspection_verifier() can break this
        get_routes_handler=lambda mcp_path: [
            # OAuth Discovery Endpoints (RFC 8414, RFC 9728)
            Route(
                path="/.well-known/oauth-protected-resource",
                endpoint=cors_middleware(
                    create_route_handler(handle_protected_resource_metadata, server),
                    ["GET", "OPTIONS"],
                ),
                methods=["GET", "OPTIONS"],
            ),
            Route(
                path="/.well-known/oauth-authorization-server",
                endpoint=cors_middleware(
                    create_route_handler(handle_authorization_server_metadata, server),
                    ["GET", "OPTIONS"],
                ),
                methods=["GET", "OPTIONS"],
            ),
            # OAuth Flow Endpoints
            Route(
                path="/register",
                endpoint=cors_middleware(
                    create_route_handler(handle_client_registration, server),
                    ["POST", "OPTIONS"],
                ),
                methods=["POST", "OPTIONS"],
            ),
            Route(
                path="/authorize",
                endpoint=create_route_handler(handle_authorization_request, server),
                methods=["GET"],
            ),
            Route(
                path="/token",
                endpoint=cors_middleware(
                    create_route_handler(handle_token_request, server),
                    ["POST"],
                ),
                methods=["POST"],
            ),
        ],
        # Patch middleware to use Bearer token authentication
        get_middleware_handler=lambda: [
            Middleware(
                AuthenticationMiddleware,
                backend=BearerAuthBackend(cast(TokenVerifierProtocol, token_verifier)),
            ),
            Middleware(AuthContextMiddleware),
        ],
    )

    # ⚠️  DANGEROUS CAST: Completely replacing FastMCP's auth system
    # We're casting our token verifier to Any because it doesn't match FastMCP's type
    # This breaks type safety but is necessary for our OAuth integration
    server.auth = cast(Any, token_verifier)

    server.logger.info("OAuth middleware and routes patch applied successfully")


def create_route_handler(
    handler: Callable[[Server, Request], Awaitable[Response]],
    server: Server,
) -> Callable[[Request], Awaitable[Response]]:
    """
    Create a route handler with server context injection.

    Args:
        handler: The actual route handler function
        server: Server instance to inject into handler

    Returns:
        Wrapped handler function that accepts only Request
    """

    async def route_wrapper(request: Request) -> Response:
        return await handler(server, request)

    return route_wrapper


async def handle_protected_resource_metadata(  # noqa: RUF029
    server: Server,
    request: Request,
) -> JSONResponse | PlainTextResponse:
    """
    Handle OAuth protected resource metadata discovery (RFC 9728).

    This endpoint provides metadata about the protected resource to help
    clients understand authorization requirements and server capabilities.

    Args:
        server: Server instance with configuration
        request: HTTP request object

    Returns:
        JSON response with protected resource metadata or CORS preflight response
    """
    if request.method == "OPTIONS":
        return create_cors_preflight_response(["GET", "OPTIONS"])

    metadata = {
        "resource": server.env.DEVOPNESS_MCP_SERVER_URL,
        "authorization_servers": [server.env.DEVOPNESS_MCP_SERVER_URL],
    }

    return JSONResponse(metadata)


async def handle_authorization_server_metadata(  # noqa: RUF029
    server: Server,
    request: Request,
) -> JSONResponse | PlainTextResponse:
    """
    Handle OAuth authorization server metadata discovery (RFC 8414).

    This endpoint provides OAuth server configuration and capabilities
    to enable automatic client configuration and flow discovery.

    Args:
        server: Server instance with OAuth configuration
        request: HTTP request object

    Returns:
        JSON response with authorization server metadata or CORS preflight response
    """
    if request.method == "OPTIONS":
        return create_cors_preflight_response(["GET", "OPTIONS"])

    metadata = {
        "issuer": server.env.DEVOPNESS_MCP_SERVER_URL,
        "registration_endpoint": server.env.DEVOPNESS_MCP_SERVER_REGISTER_URL,
        "authorization_endpoint": server.env.DEVOPNESS_MCP_SERVER_AUTHORIZE_URL,
        "token_endpoint": server.env.DEVOPNESS_MCP_SERVER_TOKEN_URL,
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
    }

    return JSONResponse(metadata)


async def handle_client_registration(
    server: Server,
    request: Request,
) -> JSONResponse | PlainTextResponse:
    """
    Handle OAuth client registration requests (RFC 7591).

    ⚠️  EXTERNAL DEPENDENCY WARNING:
    This function makes HTTP calls to the Devopness OAuth server.
    Changes to the external API can break this without any code changes here.

    FAILURE MODES:
    - External OAuth server downtime/unreachable
    - API schema changes at server.env.DEVOPNESS_MCP_AUTH_SERVER_REGISTER_URL
    - Network connectivity issues
    - Authentication failures at the external server

    Proxies client registration requests to the external OAuth server
    and returns the registered client information.

    Args:
        server: Server instance with OAuth configuration
        request: HTTP request with client registration data

    Returns:
        JSON response with registered client data or CORS preflight response

    Raises:
        HTTPException: If registration fails at the OAuth server
    """
    if request.method == "OPTIONS":
        return create_cors_preflight_response(["POST", "OPTIONS"])

    class ClientRegistration(BaseModel):
        # OAuth 2.0 Dynamic Client Registration Protocol
        # https://datatracker.ietf.org/doc/html/rfc7591#section-2
        client_name: str
        token_endpoint_auth_method: Literal["none", "client_secret_post"]
        redirect_uris: list[AnyUrl]

    try:
        registration_data = await request.json()

        validated = ClientRegistration.model_validate(registration_data)

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=dict(
                error="invalid_client_metadata",
                error_description=(
                    "The value of one of the client metadata fields is invalid and the"
                    "server has rejected this request.  Note that an authorization"
                    "server MAY choose to substitute a valid value for any requested"
                    "parameter of a client's metadata."
                ),
                exception=str(e),
            ),
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                server.env.DEVOPNESS_MCP_AUTH_SERVER_REGISTER_URL,
                json=validated.model_dump(mode="json"),
            )
            response.raise_for_status()

        client_data = response.json()
        return JSONResponse(client_data)

    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=dict(
                error="invalid_client_metadata",
                error_description=(
                    "The value of one of the client metadata fields is invalid and the"
                    "server has rejected this request.  Note that an authorization"
                    "server MAY choose to substitute a valid value for any requested"
                    "parameter of a client's metadata."
                ),
                exception=str(e),
            ),
        )


async def handle_authorization_request(  # noqa: RUF029
    server: Server,
    request: Request,
) -> RedirectResponse | JSONResponse:
    """
    Handle OAuth authorization requests (RFC 6749 Section 4.1.1).

    Redirects authorization requests to the external OAuth server with
    proper parameter encoding and state management.

    Args:
        server: Server instance with OAuth configuration
        request: HTTP request with authorization parameters

    Returns:
        Redirect response to OAuth authorization server
    """

    class AuthorizationRequest(BaseModel):
        # The OAuth 2.0 Authorization Framework
        # https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.1
        response_type: Literal["code"]
        client_id: str
        redirect_uri: Optional[AnyUrl]
        scope: Optional[str] = None
        state: Optional[str] = None

        # Proof Key for Code Exchange by OAuth Public Clients
        # https://datatracker.ietf.org/doc/html/rfc7636#section-4.3
        code_challenge: str
        code_challenge_method: Literal["plain", "S256"] = "plain"

        # Devopness OAuth Flow
        client_name: str = DEFAULT_CLIENT_NAME

    query_params = dict(request.query_params)

    try:
        validated = AuthorizationRequest.model_validate(query_params)

    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content=dict(
                error="invalid_request",
                error_description=(
                    "The request is missing a required parameter, includes an "
                    "invalid parameter value, includes a parameter more than "
                    "once, or is otherwise malformed."
                ),
                exception=str(e),
            ),
        )

    # Encode query parameters for safe transmission
    json_bytes = validated.model_dump_json(exclude_none=True).encode("utf-8")
    encoded_params = base64.b64encode(json_bytes).decode("utf-8")

    authorization_url = (
        f"{server.env.DEVOPNESS_MCP_AUTH_SERVER_AUTHORIZE_URL}?next={encoded_params}"
    )

    return RedirectResponse(url=authorization_url)


async def handle_token_request(
    server: Server,
    request: Request,
) -> Response:
    """
    Handle OAuth token requests (RFC 6749 Section 4.1.3).

    ⚠️  CRITICAL EXTERNAL DEPENDENCY:
    This is the core of our OAuth flow - it exchanges auth codes for access tokens.
    Any failure here breaks ALL authenticated MCP operations.

    HIGH-RISK DEPENDENCIES:
    - server.env.DEVOPNESS_MCP_AUTH_SERVER_TOKEN_URL must be stable
    - External server's token endpoint API must not change
    - Network reliability is critical for user experience

    MONITORING REQUIRED:
    - Track success/failure rates of token exchanges
    - Monitor external server response times
    - Alert on authentication failures

    Proxies token exchange requests to the external OAuth server
    and returns the access token response.

    Args:
        server: Server instance with OAuth configuration
        request: HTTP request with token exchange data

    Returns:
        Token response from OAuth server

    Raises:
        HTTPException: If token exchange fails at the OAuth server
    """

    class TokenRequest(BaseModel):
        # The OAuth 2.0 Authorization Framework
        # https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.3
        grant_type: Literal["authorization_code"]
        code: str
        redirect_uri: AnyUrl
        client_id: str
        resource: str = server.env.DEVOPNESS_MCP_SERVER_URL

        # Proof Key for Code Exchange by OAuth Public Clients
        # https://datatracker.ietf.org/doc/html/rfc7636#section-4.5
        code_verifier: str

    form_data = dict(await request.form())

    try:
        validated = TokenRequest.model_validate(form_data)

    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content=dict(
                error="invalid_request",
                error_description=(
                    "The request is missing a required parameter, includes an "
                    "invalid parameter value, includes a parameter more than "
                    "once, or is otherwise malformed."
                ),
                exception=str(e),
            ),
        )

    response = None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                server.env.DEVOPNESS_MCP_AUTH_SERVER_TOKEN_URL,
                json=validated.model_dump(mode="json"),
            )

            response.raise_for_status()

        return Response(
            content=response.content,
            media_type=response.headers.get("content-type", "application/json"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=response.status_code if response else 400,
            detail=(
                response.content.decode("utf-8")
                if response is not None  #
                else str(e)
            ),
        ) from None


def create_cors_preflight_response(allowed_methods: list[str]) -> PlainTextResponse:
    """
    Create a CORS preflight response for OAuth endpoints.

    Args:
        allowed_methods: List of HTTP methods allowed for the endpoint

    Returns:
        CORS preflight response with appropriate headers
    """
    return PlainTextResponse(
        "",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": ", ".join(allowed_methods),
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Max-Age": "86400",  # 24 hours
        },
    )
