from typing import cast

from devopness.core.api_error import DevopnessApiError
from devopness.models import EnvironmentRelation, NetworkRule
from devopness_mcp_server.lib.models import ActionSummary, NetworkRuleSummary
from devopness_mcp_server.lib.response import MCPResponse
from tests.devopness_test_session import DevopnessTestSession


class TestNetworkRuleService(DevopnessTestSession):
    async def test_create_network_rule(self) -> None:
        async with self.client as client:
            await client.ping()

            project = await self.create_project()
            environment = await self.create_environment(project.id)

            network_rule_name = "Redis Access"
            network_rule_direction = "inbound"
            network_rule_protocol = "tcp"
            network_rule_cidr_block = "0.0.0.0/0"
            network_rule_port = 6379

            result = await client.call_tool(
                "devopness_create_network_rule",
                {
                    "project_id": project.id,
                    "environment_id": environment.id,
                    "rule_name": network_rule_name,
                    "rule_direction": network_rule_direction,
                    "rule_protocol": network_rule_protocol,
                    "rule_cidr_block": network_rule_cidr_block,
                    "rule_port": network_rule_port,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, NetworkRuleSummary)
            self.assertEqual(response.status, "ok")

            network_rule = cast(NetworkRuleSummary, response.data)
            self.assertEqual(network_rule.name, network_rule_name)
            self.assertEqual(network_rule.direction, network_rule_direction)
            self.assertEqual(network_rule.protocol, network_rule_protocol)
            self.assertEqual(network_rule.cidr_block, network_rule_cidr_block)
            self.assertEqual(network_rule.port, network_rule_port)

    async def test_list_network_rules(self) -> None:
        async with self.client as client:
            await client.ping()

            project = await self.create_project()
            environment = await self.create_environment(project.id)

            network_rule = await self.create_network_rule(environment.id)

            result = await client.call_tool(
                "devopness_list_network_rules",
                {
                    "project_id": project.id,
                    "environment_id": environment.id,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, list[NetworkRuleSummary])
            self.assertEqual(response.status, "ok")

            network_rules = cast(list[NetworkRuleSummary], response.data)
            self.assertEqual(len(network_rules), 1)
            self.assertEqual(network_rules[0].id, network_rule.id)

    async def test_delete_network_rule(self) -> None:
        async with self.client as client:
            await client.ping()

            project = await self.create_project()
            environment = await self.create_environment(project.id)

            network_rule = await self.create_network_rule(environment.id)

            result = await client.call_tool(
                "devopness_delete_network_rule",
                {
                    "project_id": project.id,
                    "environment_id": environment.id,
                    "network_rule_id": network_rule.id,
                },
            )

            self.assertIsNotNone(result)

            response: MCPResponse[None] = self.cast_to_mcp_response(result)
            self.assertEqual(response.status, "ok")

            # Verify deletion
            try:
                await self.get_resource_by_id(
                    network_rule.id,
                    "network-rule",
                    NetworkRule,
                )

                self.fail(f"Network Rule with ID {network_rule.id} was not deleted.")

            except DevopnessApiError as e:
                self.assertEqual(e.status_code, 404)
                self.assertIn("Client error '404 Not Found'", e.message)

    async def test_edit_network_rule(self) -> None:
        async with self.client as client:
            await client.ping()

            project = await self.create_project()
            environment = await self.create_environment(project.id)

            network_rule = await self.create_network_rule(environment.id)

            new_rule_name = "New Rule Name"
            new_rule_direction = "outbound"
            new_rule_protocol = "udp"
            new_rule_cidr_block = "10.0.0.0/8"

            result = await client.call_tool(
                "devopness_edit_network_rule",
                {
                    "project_id": project.id,
                    "environment_id": environment.id,
                    "network_rule_id": network_rule.id,
                    "rule_name": new_rule_name,
                    "rule_direction": new_rule_direction,
                    "rule_protocol": new_rule_protocol,
                    "rule_cidr_block": new_rule_cidr_block,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, NetworkRuleSummary)
            self.assertEqual(response.status, "ok")

            updated_network_rule = cast(NetworkRuleSummary, response.data)
            self.assertEqual(updated_network_rule.id, network_rule.id)
            self.assertEqual(updated_network_rule.name, new_rule_name)
            self.assertEqual(updated_network_rule.direction, new_rule_direction)
            self.assertEqual(updated_network_rule.protocol, new_rule_protocol)
            self.assertEqual(updated_network_rule.cidr_block, new_rule_cidr_block)

            # Verify the update via retrieval
            retrieved_network_rule = await self.get_resource_by_id(
                network_rule.id,
                "network-rule",
                NetworkRule,
            )

            self.assertEqual(retrieved_network_rule.name, new_rule_name)
            self.assertEqual(retrieved_network_rule.direction, new_rule_direction)
            self.assertEqual(retrieved_network_rule.protocol, new_rule_protocol)
            self.assertEqual(retrieved_network_rule.cidr_block, new_rule_cidr_block)

    async def test_deploy_network_rule(self) -> None:
        async with self.client as client:
            await client.ping()

            project = await self.create_project()
            environment = (
                await self.list_resource_by_type(
                    project.id,
                    "project",
                    "environment",
                    EnvironmentRelation,
                )
            ).pop()

            server = await self.create_fake_server(project.id)

            network_rule = await self.create_network_rule(environment.id)

            pipelines = await self.list_pipelines_of_resource(
                network_rule.id,
                "network-rule",
            )

            deploy_pipeline = next(p for p in pipelines if p.operation == "deploy")

            result = await client.call_tool(
                "devopness_deploy_network_rule",
                {
                    "pipeline_id": deploy_pipeline.id,
                    "server_ids": [server.id],
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, ActionSummary)
            self.assertEqual(response.status, "ok")

            action = cast(ActionSummary, response.data)
            self.assertEqual(action.type, "Deploy")
            self.assertEqual(action.resource_id, network_rule.id)
            self.assertEqual(action.resource_type, "network-rule")
