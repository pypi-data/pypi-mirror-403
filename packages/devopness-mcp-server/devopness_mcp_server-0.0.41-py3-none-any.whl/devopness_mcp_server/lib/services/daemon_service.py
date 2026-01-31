from typing import Annotated, Optional

from pydantic import Field

from ..models import ActionSummary, DaemonSummary
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, ExtraData, FormattedData, ServerContext
from ..utils import (
    get_instructions_choose_resource,
    get_instructions_format_resource_table,
    get_instructions_format_table,
    get_instructions_how_to_monitor_action,
    get_instructions_next_action_suggestion,
    get_web_link_to_environment_resource,
    render_action,
)


class DaemonService:
    @staticmethod
    async def tool_list_daemons(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[DaemonSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.daemons.list_environment_daemons(
            environment_id,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        daemons = [
            DaemonSummary.from_sdk_model(
                daemon,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "daemon",
                        daemon.id,
                    ),
                ),
            )
            for daemon in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(daemon.id),
                "Name": f"[{daemon.name}]({daemon.url_web_permalink})",
                "Command": daemon.command,
                "Run as user": daemon.run_as_user,
                "Application": daemon.application_name or "-",
                "Working directory": (
                    f"~/{daemon.application_name}/current/{daemon.working_directory}"
                    if daemon.application_name
                    else daemon.working_directory or "-"
                ),
                "Last action": render_action(daemon.last_action),
            }
            for daemon in daemons
        ]

        return MCPResponse.ok(
            data=daemons,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("daemon"),
                get_instructions_next_action_suggestion("deploy", "daemon"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )

    @staticmethod
    async def tool_create_daemon(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        name: str,
        command: str,
        working_directory: Annotated[
            str,
            Field(
                examples=[
                    "IF application is set: 'relative/path/in/app/directory'"
                    " or EMPTY STRING",
                    "IF application is not set: '/absolute/path'",
                ],
            ),
        ],
        process_count: int = 1,
        run_as_user: str = "devopness",
        application_id: Optional[int] = None,
    ) -> MCPResponse[DaemonSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            name=name,
            command=command,
            working_directory=working_directory,
            process_count=process_count,
            run_as_user=run_as_user,
            application_id=application_id,
        )

        if not success:
            return error_response

        response = await ctx.devopness.daemons.add_environment_daemon(
            environment_id,
            {
                "name": name,
                "command": command,
                "run_as_user": run_as_user,
                "process_count": process_count,
                "working_directory": working_directory,
                "application_id": application_id,
            },
        )

        daemon = DaemonSummary.from_sdk_model(
            response.data,
            ExtraData(
                url_web_permalink=get_web_link_to_environment_resource(
                    project_id,
                    environment_id,
                    "daemon",
                    response.data.id,
                ),
            ),
        )

        return MCPResponse.ok(
            daemon,
            [
                get_instructions_format_resource_table(
                    [
                        (
                            "ID",
                            "{daemon.id}",
                        ),
                        (
                            "Name",
                            "[{daemon.name}]({daemon.url_web_permalink})",
                        ),
                        (
                            "Command",
                            "{daemon.command}",
                        ),
                        (
                            "Run as user",
                            "{daemon.run_as_user}",
                        ),
                        (
                            "Application",
                            "{daemon.application_name} OR `-`",
                        ),
                        (
                            "Working directory",
                            "IF {daemon.application_name} "
                            "THEN `~/{daemon.application_name}/current/{daemon.working_directory}`"  # noqa: E501
                            "ELSE `{daemon.working_directory}`",
                        ),
                        (
                            "Process count",
                            "{daemon.process_count}",
                        ),
                    ]
                ),
                get_instructions_next_action_suggestion("deploy", "daemon"),
            ],
        )

    @staticmethod
    async def tool_deploy_daemon(
        ctx: ServerContext,
        pipeline_id: int,
        server_ids: Annotated[
            list[int],
            Field(
                min_length=1,
                description="List of Server IDs to which the action will be targeted.",
            ),
        ],
    ) -> MCPResponse[ActionSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            pipeline_id=pipeline_id,
            server_ids=server_ids,
        )

        if not success:
            return error_response

        response = await ctx.devopness.actions.add_pipeline_action(
            pipeline_id,
            {
                "servers": server_ids,
            },
        )

        action = ActionSummary.from_sdk_model(response.data)

        return MCPResponse.ok(
            action,
            [
                get_instructions_how_to_monitor_action(action.url_web_permalink),
            ],
        )

    @staticmethod
    async def tool_edit_daemon(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        daemon_id: int,
        name: str,
        command: str,
        working_directory: Annotated[
            str,
            Field(
                examples=[
                    "IF application is set: 'relative/path/in/app/directory'"
                    " or EMPTY STRING",
                    "IF application is not set: '/absolute/path'",
                ],
            ),
        ],
        process_count: int = 1,
        run_as_user: str = "devopness",
        application_id: Optional[int] = None,
    ) -> MCPResponse[DaemonSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            daemon_id=daemon_id,
            name=name,
            command=command,
            working_directory=working_directory,
            process_count=process_count,
            run_as_user=run_as_user,
            application_id=application_id,
        )

        if not success:
            return error_response

        await ctx.devopness.daemons.update_daemon(
            daemon_id,
            {
                "id": daemon_id,
                "name": name,
                "command": command,
                "run_as_user": run_as_user,
                "process_count": process_count,
                "working_directory": working_directory,
                "application_id": application_id,
            },
        )

        daemon = (await ctx.devopness.daemons.get_daemon(daemon_id)).data

        return MCPResponse.ok(
            DaemonSummary.from_sdk_model(
                daemon,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "daemon",
                        daemon_id,
                    ),
                ),
            ),
            [
                get_instructions_format_resource_table(
                    [
                        (
                            "ID",
                            "{daemon.id}",
                        ),
                        (
                            "Name",
                            "[{daemon.name}]({daemon.url_web_permalink})",
                        ),
                        (
                            "Command",
                            "{daemon.command}",
                        ),
                        (
                            "Run as user",
                            "{daemon.run_as_user}",
                        ),
                        (
                            "Application",
                            "{daemon.application_name} OR `-`",
                        ),
                        (
                            "Working directory",
                            "IF {daemon.application_name} "
                            "THEN `~/{daemon.application_name}/current/{daemon.working_directory}`"  # noqa: E501
                            "ELSE `{daemon.working_directory}`",
                        ),
                        (
                            "Process count",
                            "{daemon.process_count}",
                        ),
                    ]
                ),
                get_instructions_next_action_suggestion("deploy", "daemon"),
            ],
        )
