from pydantic import Field

from ..models import EnvironmentSummary
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, ExtraData, FormattedData, ServerContext
from ..utils import (
    get_instructions_choose_resource,
    get_instructions_format_table,
)


class EnvironmentService:
    @staticmethod
    async def tool_list_environments(
        ctx: ServerContext,
        project_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[EnvironmentSummary]]:
        """
        Rules:
        - BEFORE executing this tool, show to the user all the existing projects,
          so that the user can choose the project to be used, using the tool
          `devopness_list_projects`.
        - DO NOT execute this tool without first confirming with the user which
          project ID to use.
        - EVEN if a candidate project is found by name or ID, please confirm with
          the user which project should be used.
        - Do not use environment 'name or ID' as project 'name or ID'.
        """
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.environments.list_project_environments(
            project_id,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        environments = [
            EnvironmentSummary.from_sdk_model(
                environment,
                ExtraData(
                    url_web_permalink=f"https://app.devopness.com/projects/{project_id}/environments/{environment.id}",
                ),
            )
            for environment in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(environment.id),
                "Name": f"[{environment.name}]({environment.url_web_permalink})",
                "Description": environment.description or "-",
            }
            for environment in environments
        ]

        return MCPResponse.ok(
            data=environments,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("environment"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )
