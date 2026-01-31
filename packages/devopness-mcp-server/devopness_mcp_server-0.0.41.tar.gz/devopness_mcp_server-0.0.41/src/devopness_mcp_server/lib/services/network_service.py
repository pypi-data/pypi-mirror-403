from pydantic import Field

from devopness.models import Network, NetworkProvisionInputSettingsGcp

from ..models import NetworkSummary
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, ExtraData, FormattedData, ServerContext
from ..utils import (
    get_instructions_choose_resource,
    get_instructions_format_resource_details,
    get_instructions_format_resource_list,
    get_instructions_next_action_suggestion,
    get_web_link_to_environment_resource,
    get_web_link_to_url_slug,
    render_action,
    render_timestamp_in_human_readable_form,
)


class NetworkService:
    @staticmethod
    async def tool_list_networks(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[NetworkSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.networks.list_environment_networks(
            environment_id,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        networks = [
            NetworkSummary.from_sdk_model(
                network,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "network",
                        network.id,
                    )
                ),
            )
            for network in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(network.id),
                "Name": f"[{network.name}]({network.url_web_permalink})",
                "Provider": network.provider_name,
                "Region": network.provider_region,
                "CIDR Block": network.cidr_block or "-",
                "Last Action": render_action(network.last_action),
            }
            for network in networks
        ]

        return MCPResponse.ok(
            data=networks,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_resource_list(),
                get_instructions_choose_resource("network"),
                get_instructions_next_action_suggestion("deploy", "network"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )

    @staticmethod
    async def tool_get_network(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        network_id: int,
    ) -> MCPResponse[Network]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            network_id=network_id,
        )

        if not success:
            return error_response

        response = await ctx.devopness.networks.get_network(
            network_id,
        )

        network = response.data

        formatted_data: FormattedData = {
            "ID": str(network.id),
            "Name": "[{}]({})".format(
                network.name,
                get_web_link_to_environment_resource(
                    project_id,
                    environment_id,
                    "network",
                    network.id,
                ),
            ),
            "Provider": network.provider_name,
            "Region": (
                network.provision_input.settings.region_human_readable
                or network.provision_input.settings.region
            ),
            "CIDR Block": (
                str(network.provision_input.settings.cidr_block)
                # NetworkProvisionInputSettingsGcp does not include `cidr_block`
                if not isinstance(
                    network.provision_input.settings,
                    NetworkProvisionInputSettingsGcp,
                )
                else "-"
            ),
            "Credential": (
                "-"
                if network.credential is None
                else "[{}]({})".format(
                    network.credential.name,
                    get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "credential",
                        network.credential.id,
                    ),
                )
            ),
            "Last Action": render_action(network.last_action),
            "Created At": render_timestamp_in_human_readable_form(network.created_at),
            "Updated At": render_timestamp_in_human_readable_form(network.updated_at),
            "Created By": "[{}]({})".format(
                network.created_by_user.url_slug,
                get_web_link_to_url_slug(network.created_by_user.url_slug),
            ),
        }

        return MCPResponse.ok(
            data=network,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_resource_details(),
                get_instructions_next_action_suggestion("deploy", "network"),
            ],
        )
