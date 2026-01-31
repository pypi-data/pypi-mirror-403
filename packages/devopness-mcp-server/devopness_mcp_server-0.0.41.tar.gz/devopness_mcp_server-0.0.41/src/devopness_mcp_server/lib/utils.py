"""
Utility functions for generating formatted strings and instructions related to
MCP Server.

These helpers produce consistent textual patterns, URLs, and instructions
for various resource types such as applications, servers, environments, etc.,
to be used primarily in communication with LLMs.

All functions ensure consistent, clear, and user-friendly communication patterns
when interacting with resources in the Devopness MCP server ecosystem.
"""

import os
from datetime import datetime

from devopness.models import ActionRelation, ActionStatus, ServerStatus
from devopness_mcp_server.lib.models import ActionSummary

from .types import ResourceType


def get_web_link_to_environment_resource(
    project_id: int,
    environment_id: int,
    resource_type: ResourceType,
    resource_id: int,
) -> str:
    """
    Constructs a URL linking to a specific resource within a project environment.
    """
    return (
        os.environ.get("DEVOPNESS_APP_URL", "https://app.devopness.com")
        + f"/projects/{project_id}"
        + f"/environments/{environment_id}"
        + f"/{resource_type}s/{resource_id}"
    )


def get_web_link_to_url_slug(
    url_slug: str,
) -> str:
    """
    Constructs a full URL from a given URL slug.
    """
    return (
        os.environ.get("DEVOPNESS_APP_URL", "https://app.devopness.com")
        + f"/@{url_slug}"
        + "/projects"
    )


def get_instructions_format_resource_list() -> str:
    """
    Instructions for formatting a resource list as a markdown table.
    """
    return (
        "You MUST present a resource list using the data in '.formatted' field.\n"
        "Present the data as a markdown table.\n"
        "Each .key in the 'formatted' field represents a column name,\n"
        "and each .value represents the corresponding cell value.\n"
        "Present the data as a markdown table with appropriate columns.\n"
        "Ensure the formatting is consistent. Do not add or remove columns.\n"
    )


def get_instructions_format_resource_details() -> str:
    """
    Instructions for formatting resource details as a markdown table.
    """
    return (
        "You MUST present the resource details using the data in '.formatted' field.\n"
        "Present the data as a markdown table with two columns: 'Field' and 'Value'.\n"
        "Ensure the formatting is consistent. Do not add or remove rows.\n"
    )


def get_instructions_format_resource(
    resource_type: ResourceType,
    pattern: list[str],
) -> str:
    return (
        f"You MUST present the {resource_type} using the exact format shown below:\n"
        f"{' '.join(pattern)}\n"
        "Make sure the formatting is consistent and follows the structure."
    )


def get_instructions_format_resource_table(
    column_and_value_templates: list[tuple[str, str]],
) -> str:
    table = "Field | Value\n"

    for column, value in column_and_value_templates:
        table += f"{column} | {value}\n"
    table += "\n"

    return f"""You MUST present a table in the below format:
    {table}
    """


def get_instructions_format_list(
    header: str,
    extra_instructions: list[str] | None = None,
) -> list[str]:
    return [
        "You MUST present a bullet list in the below format:",
        header,
        *(extra_instructions or []),
        "Make sure each item follows this structure and "
        "that the formatting is consistent. Do not modify "
        "the order of the list items. Do not add or remove "
        "any items. Include all the required items in the list.",
    ]


def get_instructions_format_table(
    column_and_value_templates: list[tuple[str, str]] | None = None,
) -> str:
    if not column_and_value_templates:
        return (
            "You MUST present a table using the data in '.formatted' field.\n"
            "Each .key in the 'formatted' field represents a column name,\n"
            "and each .value represents the corresponding cell value.\n"
            "Present the data as a markdown table with appropriate columns.\n"
            "Ensure the formatting is consistent. Do not add or remove columns.\n"
        )

    table = ""

    for column, _ in column_and_value_templates:
        table += f"{column} |"
    table += "\n"

    for _, value in column_and_value_templates:
        table += f"- {value} |"
    table += "\n"

    return f"""You MUST present a table in the below format:
    {table}
    """


def get_instructions_next_action_suggestion(
    action: str,
    resource_type: ResourceType,
) -> str:
    return (
        f"You MUST clearly instruct the user to {action} the {resource_type} next.\n"
        f"Use imperative language and avoid ambiguity."
    )


def get_instructions_how_to_monitor_action(
    action_url_web_permalink: str,
) -> str:
    return (
        "You MUST instruct the user to visit the following link to view the"
        f" real-time progress: {action_url_web_permalink}\n"
        "Make it clear that the page contains status tracking and logs."
        "Always display the action link as a clickable link and its URL as its text."
    )


def get_instructions_choose_resource(
    resource_type: ResourceType,
) -> list[str]:
    return [
        f"IF the list contains multiple {resource_type}s. "
        "You MUST show the following message to the user:",
        f"Please enter the ID or name of the {resource_type} you want to work with, "
        f"or type `next page` if your {resource_type} isn't listed here.",
        #
        f"IF the list contains only one {resource_type}. "
        "You MUST show the following message to the user:",
        "Found one " + resource_type + " with ID {resource_id}. "
        "I will use it to achieve our goal.",
    ]


def render_server_status(
    status: ServerStatus,
) -> str:
    """
    Returns a formatted string representing the server status with an emoji.
    """
    emoji = ""

    match status:
        case "running":
            emoji = "🟢"
        case "stopped":
            emoji = "🟠"
        case "failed":
            emoji = "🔴"
        case _:
            emoji = "🟡"

    return f"{emoji} {status.capitalize()}"


def render_action_status(
    status: ActionStatus,
    include_text: bool = True,
    include_emoji: bool = True,
    capitalize_text: bool = True,
) -> str:
    """
    Returns a formatted string representing the action status with an emoji.
    """
    emoji = ""

    match status:
        case "completed":
            emoji = "🟢"
        case "failed":
            emoji = "🔴"
        case "skipped":
            emoji = "⚪"
        case _:
            emoji = "🟠"

    parts = []

    if include_emoji:
        parts.append(emoji)

    if include_text:
        parts.append(status.capitalize() if capitalize_text else status)

    return " ".join(parts)


def render_action(
    action: ActionSummary | ActionRelation | None,
    include_type: bool = True,
) -> str:
    """
    Returns a formatted string representing the action with status and duration.
    """
    if action is None:
        return "-"

    return "[{}]({}){}{}".format(
        # icon + status
        render_action_status(action.status),
        # link
        action.url_web_permalink,
        # duration
        ""
        if action.completed_at is None
        else " in {}".format(
            render_duration_in_human_readable_form(
                action.started_at,
                action.completed_at,
            ),
        ),
        f" ({action.type})" if include_type else "",
    )


def render_timestamp_in_human_readable_form(
    timestamp: datetime | str | None,
) -> str:
    """
    Returns a formatted string representing the timestamp in human-readable form.
    """
    if timestamp is None:
        return "-"

    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return "-"

    return timestamp.strftime("%Y-%m-%d %H:%M")


def render_duration_in_human_readable_form(
    start_timestamp: datetime | str | None,
    end_timestamp: datetime | str | None,
) -> str:
    """
    Returns a formatted string representing the duration in human-readable form.
    """
    if not start_timestamp or not end_timestamp:
        return "-"

    if isinstance(start_timestamp, str):
        try:
            start_timestamp = datetime.fromisoformat(
                start_timestamp.replace("Z", "+00:00")
            )
        except ValueError:
            return "-"

    if isinstance(end_timestamp, str):
        try:
            end_timestamp = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))
        except ValueError:
            return "-"

    duration = end_timestamp - start_timestamp
    total_seconds = int(duration.total_seconds())

    if total_seconds < 0:
        return "-"

    if total_seconds < 60:
        return f"{total_seconds} s"

    if total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        if seconds == 0:
            return f"{minutes} m"

        return f"{minutes} m {seconds} s"

    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    parts = [f"{hours} h"]
    if minutes > 0:
        parts.append(f"{minutes} m")
    if seconds > 0:
        parts.append(f"{seconds} s")

    return " ".join(parts)
