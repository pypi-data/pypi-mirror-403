from pydantic import Field

from ..models import CredentialSummary
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, ExtraData, FormattedData, ServerContext
from ..utils import (
    get_instructions_choose_resource,
    get_instructions_format_table,
    get_web_link_to_environment_resource,
)


class CredentialService:
    @staticmethod
    async def tool_list_credentials(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[CredentialSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.credentials.list_environment_credentials(
            environment_id,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        credentials = [
            CredentialSummary.from_sdk_model(
                credential,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "credential",
                        credential.id,
                    ),
                ),
            )
            for credential in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(credential.id),
                "Name": f"[{credential.name}]({credential.url_web_permalink})",
                "Provider": credential.provider,
                "Provider Type": credential.provider_type,
            }
            for credential in credentials
        ]

        return MCPResponse.ok(
            data=credentials,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("credential"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )
