from typing import Annotated

from pydantic import Field

from ..models import ActionSummary, SSHKeySummary
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, FormattedData, ServerContext
from ..utils import (
    get_instructions_choose_resource,
    get_instructions_format_resource_table,
    get_instructions_format_table,
    get_instructions_how_to_monitor_action,
    get_instructions_next_action_suggestion,
    render_action,
)


class SSHKeyService:
    @staticmethod
    async def tool_create_ssh_key(
        ctx: ServerContext,
        environment_id: int,
        name: str,
        public_key: str,
    ) -> MCPResponse[SSHKeySummary]:
        """
        Rules:
        - If the user does not provide a public key, you MUST ask them to provide one.
        - You MUST offer to find the public key for the user.
        - You MUST offer to generate a new ssh key pair for the user.
        """
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            environment_id=environment_id,
            name=name,
            public_key=public_key,
        )

        if not success:
            return error_response

        response = await ctx.devopness.ssh_keys.add_environment_ssh_key(
            environment_id,
            {
                "name": name,
                "public_key": public_key,
            },
        )

        ssh_key = SSHKeySummary.from_sdk_model(response.data)

        return MCPResponse.ok(
            ssh_key,
            [
                get_instructions_format_resource_table(
                    [
                        (
                            "ID",
                            "{ssh_key.id}",
                        ),
                        (
                            "Name",
                            "[{ssh_key.name}]({ssh_key.url_web_permalink})",
                        ),
                    ]
                ),
                get_instructions_next_action_suggestion("deploy", "ssh-key"),
            ],
        )

    @staticmethod
    async def tool_deploy_ssh_key(
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
                "Show the user the command to remote connect"
                "the server(s) using the SSH Key.",
            ],
        )

    @staticmethod
    async def tool_list_ssh_keys(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[SSHKeySummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.ssh_keys.list_environment_ssh_keys(
            environment_id,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        ssh_keys: list[SSHKeySummary] = [
            SSHKeySummary.from_sdk_model(item) for item in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(ssh_key.id),
                "Name": f"[{ssh_key.name}]({ssh_key.url_web_permalink})",
                "Last action": render_action(ssh_key.last_action),
            }
            for ssh_key in ssh_keys
        ]

        return MCPResponse.ok(
            data=ssh_keys,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("ssh-key"),
                get_instructions_next_action_suggestion("deploy", "ssh-key"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )
