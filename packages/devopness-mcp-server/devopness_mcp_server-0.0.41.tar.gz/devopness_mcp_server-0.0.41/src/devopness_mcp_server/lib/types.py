"""
This module defines types and constants used to manage data visibility
when interacting with Large Language Models (LLMs) in the MCP Server.
"""

import weakref
from logging import Logger
from typing import Any, Literal, Optional, Tuple, cast

from fastmcp import Context, FastMCP
from fastmcp.server.elicitation import (
    AcceptedElicitation,
    CancelledElicitation,
    DeclinedElicitation,
)

from devopness import DevopnessClientAsync
from devopness.base.base_model import DevopnessBaseModel

from .environment import EnvironmentVariables
from .response import MCPResponse

MCP_TRANSPORT_PROTOCOL = Literal[
    "stdio",
    "streamable-http",
]


MAX_RESOURCES_PER_PAGE = 5
"""
The Large Language Models (LLMs) can start hallucinating during resource listing
if the volume of data is 'large', which is easily achieved when listing an
environment resource such as an application or server.

To avoid the hallucinations that can lead to errors and harm to the user of the
MCP Server, we set the maximum number of resources per page for listing.

If the resource that the user is looking for is not on the first page,
the LLM is able to list the <page + 1> until it finds the user's resource.
"""

ResourceType = Literal[
    "application",
    "credential",
    "daemon",
    "environment",
    "network",
    "network-rule",
    "project",
    "server",
    "service",
    "ssh-key",
    "ssl-certificate",
    "virtual-host",
]


class ExtraData(DevopnessBaseModel):
    url_web_permalink: Optional[str] = None
    application_hide_config_file_content: bool = False
    server_instance_type: Optional[str] = None


type TypeExtraData = Optional[ExtraData]

type FormattedData = dict[str, str]


# TODO: Replace custom Server class with official FastMCP dependency injection
# mechanism once available. Current approach extends FastMCP[Any] to add
# Devopness-specific fields (env, devopness, logger) but should use
# proper DI pattern to avoid library patching.
class Server(FastMCP[Any]):
    """
    Custom Devopness MCP Server model extending the base FastMCP.

    This class adds additional fields required by Devopness-specific tools,
    such as access to environment variables via the `env` property.
    """

    env: EnvironmentVariables
    devopness: DevopnessClientAsync
    logger: Logger


# TODO: Use official FastMCP Context extension API when available.
# Current implementation uses weakref and attribute mirroring to inject
# custom Server instance into Context, but should leverage proper
# context extension mechanism to avoid manual attribute management.
class ServerContext(Context):
    """
    Custom context wrapper for FastMCP, injecting the custom `Server` class.

    This overrides the default `fastmcp` attribute from the base `Context` class,
    casting it to the custom `Server` model to allow tool access to extended fields
    (e.g., `fastmcp.env`).
    """

    server: Server
    devopness: DevopnessClientAsync

    def __init__(self, ctx: Context) -> None:
        # Inject the custom `Server` and `Devopness`
        self.server = cast(Server, ctx.fastmcp)
        self.devopness = self.server.devopness

        # Mirror the base `Context` attributes
        self._fastmcp = weakref.ref(ctx.fastmcp)
        self._tokens = ctx._tokens
        self._notification_queue = ctx._notification_queue

    async def confirm_params_if_supported_by_client(
        self,
        **params: Any,  # noqa: ANN401
    ) -> Tuple[bool, MCPResponse[Any]]:
        """
        Confirm parameters with the user if the client supports elicitation.
        See:
            https://modelcontextprotocol.io/docs/learn/client-concepts#elicitation.

        This method:
        - Checks if the client's capabilities include elicitation.
        - Prompts the user to confirm parameters if supported.
        - Automatically assumes confirmation when elicitation is not supported.

        Returns:
            Tuple[bool, MCPResponse[Any]]: (confirmed, response)
            - confirmed=True  → Parameters confirmed.
            - confirmed=False → Operation cancelled or declined.
        """

        if not self._client_supports_elicitation():
            return True, MCPResponse.ok()

        params_list = self._format_params_for_confirmation(**params)

        response = await self.elicit(
            "Please confirm the following parameters before proceeding:\n"
            + "\n".join(f"- {key}: {value}" for key, value in params_list),
            None,
        )

        match response:
            case AcceptedElicitation():
                return True, MCPResponse.ok()
            case CancelledElicitation():
                return False, MCPResponse.error(
                    [
                        "Operation was cancelled by the user.",
                    ]
                )
            case DeclinedElicitation():
                return False, MCPResponse.error(
                    [
                        "Operation was declined by the user.",
                    ]
                )

    def _client_supports_elicitation(self) -> bool:
        """
        Checks if the connected MCP client supports parameter elicitation.
        """
        # Client has no elicitation capability
        if self.session._client_params.capabilities.elicitation is None:  # type: ignore[union-attr]
            return False

        # TODO: Remove this hardcoded check once Cursor fixes their capabilities
        #       definition. As of 2025-09, Cursor v1.6.35 reports support for
        #       elicitation, but triggering an elicitation request from the server
        #       causes the UI to hang. To prevent this, we temporarily skip
        #       elicitation for Cursor.
        # INFO: Related discussions:
        #       - https://forum.cursor.com/t/mcp-elicitation-support-immediate-need/116516/4
        #       - https://forum.cursor.com/t/mcp-elicitation-with-http-oauth-hangs-with-request-timed-out-error/133735/4
        if "cursor" in self.session._client_params.clientInfo.name.lower():  # type: ignore[union-attr]  # noqa: SIM103
            return False

        return True

    def _format_params_for_confirmation(self, **params: Any) -> list[tuple[str, str]]:  # noqa: ANN401
        """
        Converts Python parameter names and values into a human-readable list
        for user confirmation.

        Example:
            environment_id -> Environment Id
            None           -> not provided
            True           -> yes
        """
        formatted = []

        for key, value in params.items():
            # convert python param name to human readable name
            # (e.g., "environment_id" to "Environment Id")
            name = key.replace("_", " ").title()

            # convert bool to yes/no
            if isinstance(value, bool):
                display_value = "yes" if value else "no"

            # convert None to 'not provided'
            elif value is None:
                display_value = "not provided"

            # convert empty string to 'empty string'
            elif isinstance(value, str) and not value.strip():
                display_value = "empty string"

            # convert list to comma-separated string
            # (e.g., [1, 2, 3] to "1, 2, 3")
            elif isinstance(value, list):
                display_value = ", ".join(str(v) for v in value)

            # fallback to str conversion
            else:
                display_value = str(value)

            formatted.append((name, display_value))

        return formatted
