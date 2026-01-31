from typing import cast

from devopness_mcp_server.lib.models import ActionSummary
from tests.devopness_test_session import DevopnessTestSession


class TestActionService(DevopnessTestSession):
    async def test_list_actions_of_resource(self) -> None:
        async with self.client as client:
            await client.ping()

            project = await self.create_project()
            environment = await self.create_environment(project.id)

            credential = await self.create_credential(environment.id)
            action = await self.trigger_credential_get_status(credential.id)

            result = await client.call_tool(
                "devopness_list_actions_of_resource",
                {
                    "resource_type": "credential",
                    "resource_id": credential.id,
                    "page": 1,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, list[ActionSummary])
            self.assertEqual(response.status, "ok")

            actions = cast(list[ActionSummary], response.data)
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].id, action.id)
