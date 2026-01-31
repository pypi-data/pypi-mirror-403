from typing import Annotated

from pydantic import Field, StringConstraints

from devopness.models import (
    NetworkRuleDirection,
    NetworkRuleDirectionPlain,
    NetworkRuleProtocol,
    NetworkRuleProtocolPlain,
    NetworkRuleUpdatePlain,
)

from ..models import ActionSummary, NetworkRuleSummary
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


class NetworkRuleService:
    @staticmethod
    async def tool_list_network_rules(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[NetworkRuleSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.network_rules.list_environment_network_rules(
            environment_id,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        network_rules = [
            NetworkRuleSummary.from_sdk_model(
                network_rule,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "network-rule",
                        network_rule.id,
                    )
                ),
            )
            for network_rule in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(rule.id),
                "Name": f"[{rule.name}]({rule.url_web_permalink})",
                "CIDR Block/IP Range": rule.cidr_block,
                "Port": str(rule.port),
                "Protocol": rule.protocol,
                "Direction": rule.direction,
                "Last action": render_action(rule.last_action),
            }
            for rule in network_rules
        ]

        return MCPResponse.ok(
            data=network_rules,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_choose_resource("network-rule"),
                get_instructions_next_action_suggestion("deploy", "network-rule"),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )

    @staticmethod
    async def tool_create_network_rule(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        rule_name: Annotated[
            str,
            StringConstraints(
                min_length=1,
                max_length=100,
            ),
            Field(
                min_length=3,
                max_length=60,
                description="The rule's name/description/reminder.",
            ),
        ],
        rule_direction: Annotated[
            str,
            NetworkRuleDirectionPlain,
            Field(
                description="Direction of network rule",
                examples=list(NetworkRuleDirectionPlain.__args__),
            ),
        ],
        rule_protocol: Annotated[
            str,
            NetworkRuleProtocolPlain,
            Field(
                examples=list(NetworkRuleProtocolPlain.__args__),
            ),
        ],
        rule_cidr_block: Annotated[
            str,
            Field(
                description="IP address range this rule applies for,"
                " defined using CIDR notation.",
                examples=["0.0.0.0/0", "192.168.1.0/24"],
            ),
        ],
        rule_port: Annotated[
            int,
            Field(
                description="Port range for the network rule",
                examples=[80, 443, 8080],
                gt=0,
                lt=65536,
            ),
        ],
    ) -> MCPResponse[NetworkRuleSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            rule_name=rule_name,
            rule_direction=rule_direction,
            rule_protocol=rule_protocol,
            rule_cidr_block=rule_cidr_block,
            rule_port=rule_port,
        )

        if not success:
            return error_response

        response = await ctx.devopness.network_rules.add_environment_network_rule(
            environment_id,
            {
                "name": rule_name,
                "direction": NetworkRuleDirection(rule_direction),
                "protocol": NetworkRuleProtocol(rule_protocol),
                "cidr_block": rule_cidr_block,
                "port": rule_port,
            },
        )

        network_rule = NetworkRuleSummary.from_sdk_model(
            response.data,
            ExtraData(
                url_web_permalink=get_web_link_to_environment_resource(
                    project_id,
                    environment_id,
                    "network-rule",
                    response.data.id,
                )
            ),
        )

        return MCPResponse.ok(
            network_rule,
            [
                get_instructions_format_resource_table(
                    [
                        ("ID", "{rule.id}"),
                        ("Name", "[{rule.name}]({rule.url_web_permalink})"),
                        ("CIDR Block/IP Range", "{rule.cidr_block}"),
                        ("Port", "{rule.port}"),
                        ("Protocol", "{rule.protocol}"),
                        ("Direction", "{rule.direction}"),
                    ],
                ),
                get_instructions_next_action_suggestion("deploy", "network-rule"),
            ],
        )

    @staticmethod
    async def tool_edit_network_rule(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        network_rule_id: int,
        rule_name: str,
        rule_direction: Annotated[str, NetworkRuleDirectionPlain],
        rule_protocol: Annotated[str, NetworkRuleProtocolPlain],
        rule_cidr_block: str,
    ) -> MCPResponse[NetworkRuleSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            network_rule_id=network_rule_id,
            rule_name=rule_name,
            rule_direction=rule_direction,
            rule_protocol=rule_protocol,
            rule_cidr_block=rule_cidr_block,
        )

        if not success:
            return error_response

        network_rule = (
            await ctx.devopness.network_rules.get_network_rule(network_rule_id)
        ).data

        payload: NetworkRuleUpdatePlain = {
            "id": network_rule_id,
            "name": rule_name or network_rule.name,
            "direction": NetworkRuleDirection(rule_direction),
            "protocol": NetworkRuleProtocol(rule_protocol),
            "cidr_block": rule_cidr_block,
        }

        await ctx.devopness.network_rules.update_network_rule(
            network_rule_id,
            payload,
        )

        updated_network_rule = (
            await ctx.devopness.network_rules.get_network_rule(network_rule_id)
        ).data

        return MCPResponse.ok(
            NetworkRuleSummary.from_sdk_model(
                updated_network_rule,
                ExtraData(
                    url_web_permalink=get_web_link_to_environment_resource(
                        project_id,
                        environment_id,
                        "network-rule",
                        updated_network_rule.id,
                    )
                ),
            ),
            [
                get_instructions_format_resource_table(
                    [
                        ("ID", "{rule.id}"),
                        ("Name", "[{rule.name}]({rule.url_web_permalink})"),
                        ("CIDR Block/IP Range", "{rule.cidr_block}"),
                        ("Port", "{rule.port}"),
                        ("Protocol", "{rule.protocol}"),
                        ("Direction", "{rule.direction}"),
                        ("Last action", "{rule.last_action}"),
                    ],
                ),
                "The network rule has been successfully updated.",
                get_instructions_next_action_suggestion("deploy", "network-rule"),
            ],
        )

    @staticmethod
    async def tool_delete_network_rule(
        ctx: ServerContext,
        project_id: int,
        environment_id: int,
        network_rule_id: int,
    ) -> MCPResponse[None]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            project_id=project_id,
            environment_id=environment_id,
            network_rule_id=network_rule_id,
        )

        if not success:
            return error_response

        await ctx.devopness.network_rules.delete_network_rule(network_rule_id)

        return MCPResponse.ok(
            None,
            ["Network rule has been successfully deleted."],
        )

    @staticmethod
    async def tool_deploy_network_rule(
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
