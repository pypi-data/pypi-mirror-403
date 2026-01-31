from typing import Annotated

from pydantic import Field

from ..models import ActionSummary, SSLCertificateSummary
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


class SSLCertificateService:
    @staticmethod
    async def tool_list_ssl_certificates(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[SSLCertificateSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            page=page,
        )

        if not success:
            return error_response

        response = (
            await ctx.devopness.ssl_certificates.list_environment_ssl_certificates(
                environment_id,
                page,
                per_page=MAX_RESOURCES_PER_PAGE,
            )
        )

        ssl_certificates = [
            SSLCertificateSummary.from_sdk_model(
                ssl_certificate,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "ssl-certificate",
                        ssl_certificate.id,
                    ),
                ),
            )
            for ssl_certificate in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(ssl_certificate.id),
                "Name": f"[{ssl_certificate.name}]({ssl_certificate.url_web_permalink})",  # noqa: E501
                "Active": "🔒 Yes" if ssl_certificate.active else "🔓 No",
                "Last action": render_action(ssl_certificate.last_action),
            }
            for ssl_certificate in ssl_certificates
        ]

        return MCPResponse.ok(
            data=ssl_certificates,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("ssl-certificate"),
                get_instructions_next_action_suggestion("deploy", "ssl-certificate"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )

    @staticmethod
    async def tool_create_ssl_certificate(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        virtual_host_id: int,
    ) -> MCPResponse[SSLCertificateSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            virtual_host_id=virtual_host_id,
        )

        if not success:
            return error_response

        response = await ctx.devopness.ssl_certificates.add_environment_ssl_certificate(
            environment_id,
            {
                "virtual_host_id": virtual_host_id,
                "issuer": "lets-encrypt",
            },
        )

        ssl_certificate = SSLCertificateSummary.from_sdk_model(
            response.data,
            ExtraData(
                url_web_permalink=get_web_link_to_environment_resource(
                    project_id,
                    environment_id,
                    "ssl-certificate",
                    response.data.id,
                ),
            ),
        )

        return MCPResponse.ok(
            ssl_certificate,
            [
                get_instructions_format_resource_table(
                    [
                        (
                            "ID",
                            "{ssl_certificate.id}",
                        ),
                        (
                            "Name",
                            "[{ssl_certificate.name}]({ssl_certificate.url_web_permalink})",
                        ),
                        (
                            "Active",
                            "IF {ssl_certificate.active} THEN `🔒 Yes` ELSE `🔓 No`",
                        ),
                    ]
                ),
                get_instructions_next_action_suggestion("deploy", "ssl-certificate"),
            ],
        )

    @staticmethod
    async def tool_deploy_ssl_certificate(
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
                "Show to the user how to access the domain using the URL 'https://{ssl_certificate.name}'",
            ],
        )
