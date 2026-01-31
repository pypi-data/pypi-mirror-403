"""
This module defines a generic response model (`MCPResponse`) used to communicate
between the MCP Server and LLM-based clients.

The response encapsulates:
- A status indicator ("ok", "warning", or "error")
- A next page number for paginated responses
- A generic payload (`data`) that can be any serializable type
- An optional list of instructions for guiding LLM behavior

To simplify response creation, the class provides classmethods
that return pre-structured response objects based on the context.

Example usage:
    MCPResponse.ok(data={"message": "All good"})
    MCPResponse.warning(instructions=["Ask the user to verify the server name."])
    MCPResponse.error(instructions=["Inform the user the operation failed."])
"""

from typing import Any, Generic, Literal, Self, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

type FormattedData = dict[str, str]


class MCPResponse(BaseModel, Generic[T]):
    """
    Represents a response from the Devopness MCP Server.

    Args:
        status (Literal["ok", "warning", "error"]): The status of the response.
        next_page (int | None): The next page number for paginated responses.
        instructions (list[Any]): Instructions to be sent to LLM.
        formatted (FormattedData | list[FormattedData] | None): Formatted data to
                                                                be sent to LLM.
        data (T | None): The data to be sent as the response.
    """

    status: Literal["ok", "warning", "error"]
    next_page: int | None = None
    instructions: list[Any]
    formatted: FormattedData | list[FormattedData] | None = None
    data: T | None = None

    @classmethod
    def ok(
        cls,
        data: T | None = None,
        instructions: list[Any] | None = None,
        formatted: FormattedData | list[FormattedData] | None = None,
        next_page: int | None = None,
    ) -> Self:
        """
        Create an MCP response with a status of "ok".

        Args:
            data (T | None): The data to be sent as the response.
            instructions (list[Any] | None): Instructions to be sent to LLM.
            formatted (FormattedData | list[FormattedData] | None): Formatted data to
                                                                    be sent to LLM.
            next_page (int | None): The next page number for paginated responses.

        Returns:
            Self: The created MCP response.
        """
        return cls(
            data=data,
            status="ok",
            instructions=instructions or [],
            formatted=formatted or [],
            next_page=next_page,
        )

    @classmethod
    def warning(cls, instructions: list[Any]) -> Self:
        """
        Create an MCP response with a status of "warning".

        Args:
            instructions (list[Any]): Instructions to be sent to LLM.

        Returns:
            Self: The created MCP response.
        """
        return cls(
            status="warning",
            instructions=instructions,
        )

    @classmethod
    def error(cls, instructions: list[Any] | None = None) -> Self:
        """
        Create an MCP response with a status of "error".

        Args:
            instructions (list[Any] | None): Instructions to be sent to LLM.

        Returns:
            Self: The created MCP response.
        """
        return cls(
            status="error",
            instructions=instructions or [],
        )
