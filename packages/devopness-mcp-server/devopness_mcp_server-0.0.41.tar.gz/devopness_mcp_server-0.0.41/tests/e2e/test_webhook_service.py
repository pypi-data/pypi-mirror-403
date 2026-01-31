from typing import cast

from devopness_mcp_server.lib.models import HookSummary
from devopness_mcp_server.lib.response import MCPResponse
from tests.devopness_test_session import DevopnessTestSession


class TestWebhookService(DevopnessTestSession):
    async def test_tool_create_webhook(self) -> None:
        async with self.client as client:
            await client.ping()

            # Prepare the environment
            project = await self.create_project()
            environment = await self.create_environment(project.id)

            credential = await self.create_credential(environment.id)
            application = await self.create_application(
                environment.id,
                credential.id,
            )

            application_pipelines = await self.list_pipelines_of_resource(
                application.id,
                "application",
            )

            # get the "deploy" pipeline
            pipeline = next(p for p in application_pipelines if p.operation == "deploy")

            hook_settings = {
                "name": "e2e-webhook",
                "active": True,
                "requires_secret": False,
            }

            result = await client.call_tool(
                "devopness_create_webhook",
                {
                    "pipeline_id": pipeline.id,
                    "hook_type": "incoming",
                    "hook_settings": hook_settings,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, HookSummary)
            self.assertEqual(response.status, "ok")

            hook = cast(HookSummary, response.data)
            self.assertEqual(hook.name, hook_settings["name"])
            self.assertEqual(hook.active, hook_settings["active"])
            self.assertEqual(hook.requires_secret, hook_settings["requires_secret"])

    async def test_tool_list_webhook_of_application(self) -> None:
        async with self.client as client:
            await client.ping()

            # Prepare the environment
            project = await self.create_project()
            environment = await self.create_environment(project.id)

            credential = await self.create_credential(environment.id)
            application = await self.create_application(
                environment.id,
                credential.id,
            )

            application_pipelines = await self.list_pipelines_of_resource(
                application.id,
                "application",
            )

            # get the "deploy" pipeline
            pipeline = next(p for p in application_pipelines if p.operation == "deploy")

            # create webhook for this application
            webhook = await self.create_webhook(
                pipeline.id,
                "incoming",
                {
                    "name": "e2e-webhook",
                    "active": True,
                    "requires_secret": False,
                },
            )

            result = await client.call_tool(
                "devopness_list_webhook_of_application",
                {
                    "application_id": application.id,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, list[HookSummary])
            self.assertEqual(response.status, "ok")

            hooks = cast(list[HookSummary], response.data)
            self.assertEqual(len(hooks), 1)
            self.assertEqual(hooks[0].id, webhook.id)
            self.assertEqual(hooks[0].name, webhook.name)

    async def test_tool_list_webhook_of_pipeline(self) -> None:
        async with self.client as client:
            await client.ping()

            # Prepare the environment
            project = await self.create_project()
            environment = await self.create_environment(project.id)

            credential = await self.create_credential(environment.id)
            application = await self.create_application(
                environment.id,
                credential.id,
            )

            application_pipelines = await self.list_pipelines_of_resource(
                application.id,
                "application",
            )

            # get the "deploy" pipeline
            pipeline = next(p for p in application_pipelines if p.operation == "deploy")

            # create webhook for this pipeline
            webhook = await self.create_webhook(
                pipeline.id,
                "incoming",
                {
                    "name": "e2e-webhook",
                    "active": True,
                    "requires_secret": False,
                },
            )

            result = await client.call_tool(
                "devopness_list_webhook_of_pipeline",
                {
                    "pipeline_id": pipeline.id,
                },
            )

            self.assertIsNotNone(result)

            response = self.cast_to_mcp_response(result, list[HookSummary])
            self.assertEqual(response.status, "ok")

            hooks = cast(list[HookSummary], response.data)
            self.assertEqual(len(hooks), 1)
            self.assertEqual(hooks[0].id, webhook.id)
            self.assertEqual(hooks[0].name, webhook.name)

    async def test_tool_delete_webhook(self) -> None:
        async with self.client as client:
            await client.ping()

            # Prepare the environment
            project = await self.create_project()
            environment = await self.create_environment(project.id)

            credential = await self.create_credential(environment.id)
            application = await self.create_application(
                environment.id,
                credential.id,
            )

            application_pipelines = await self.list_pipelines_of_resource(
                application.id,
                "application",
            )

            # get the "deploy" pipeline
            pipeline = next(p for p in application_pipelines if p.operation == "deploy")

            # create webhook for this pipeline
            webhook = await self.create_webhook(
                pipeline.id,
                "incoming",
                {
                    "name": "e2e-webhook",
                    "active": True,
                    "requires_secret": False,
                },
            )

            result = await client.call_tool(
                "devopness_delete_webhook",
                {
                    "hook_id": webhook.id,
                    "hook_type": "incoming",
                },
            )

            self.assertIsNotNone(result)

            response: MCPResponse[None] = self.cast_to_mcp_response(result, None)
            self.assertEqual(response.status, "ok")
