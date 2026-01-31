from pydantic import Field

from ..models import ProjectSummary
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, FormattedData, ServerContext
from ..utils import (
    get_instructions_choose_resource,
    get_instructions_format_table,
)


class ProjectService:
    @staticmethod
    async def tool_list_projects(
        ctx: ServerContext,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[ProjectSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.projects.list_projects(
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        projects = [ProjectSummary.from_sdk_model(project) for project in response.data]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(project.id),
                "Name": f"[{project.name}]({project.url_web_permalink})",
            }
            for project in projects
        ]

        return MCPResponse.ok(
            data=projects,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("project"),
                "EVEN if a candidate project is found by name or ID, please confirm"
                " with the user the project to be used.",
                "Do not use environment 'name or ID' as project 'name or ID'.",
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )
