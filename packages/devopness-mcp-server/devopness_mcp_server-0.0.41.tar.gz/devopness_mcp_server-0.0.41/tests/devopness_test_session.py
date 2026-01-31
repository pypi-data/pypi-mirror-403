import datetime
import os
import random
import string
import unittest
from base64 import b64encode
from typing import (
    Any,
    Optional,
    Type,
    TypeVar,
    cast,
    get_args,
    get_origin,
    override,
)

import dotenv
from fastmcp import Client
from fastmcp.client.client import CallToolResult

from devopness.core.response import DevopnessResponse
from devopness.models import (
    Action,
    Application,
    Credential,
    Environment,
    Hook,
    HookPipelineCreatePlain,
    HookTypeParamPlain,
    NetworkRule,
    PipelineRelation,
    Project,
    Server,
)
from devopness_mcp_server.lib.devopness_api import (
    DevopnessCredentials,
    ensure_authenticated,
)
from devopness_mcp_server.lib.environment import EnvironmentVariables
from devopness_mcp_server.lib.models import (
    ensure_object,
)
from devopness_mcp_server.lib.response import MCPResponse
from devopness_mcp_server.lib.types import ResourceType, ServerContext
from devopness_mcp_server.server import MCPServer

T = TypeVar("T")


class DevopnessTestSession(unittest.IsolatedAsyncioTestCase):
    _created_resources: dict[ResourceType, list[int]]

    @override
    async def asyncSetUp(self) -> None:
        """
        Setup the Devopness MCP Server and Client for testing.

        Ensure that the Devopness Client is authenticated before running tests.
        """
        self._created_resources = {}
        for resource_type in get_args(ResourceType):
            self._created_resources[resource_type] = []

        dotenv.load_dotenv(override=True, dotenv_path=".env.e2e")

        self.env = EnvironmentVariables()
        self.env.DEVOPNESS_API_URL = os.environ.get("DEVOPNESS_API_URL", "")
        self.env.DEVOPNESS_MCP_SERVER_TRANSPORT = os.environ.get(
            "DEVOPNESS_MCP_SERVER_TRANSPORT", ""
        )

        self.server = MCPServer(self.env)
        self.client = Client(self.server)

        # Ensure the Devopness Client is authenticated
        personal_access_token = os.environ.get("DEVOPNESS_PERSONAL_ACCESS_TOKEN", "")

        ensure_authenticated(
            # The context is not used in the current implementation
            cast(ServerContext, {}),
            DevopnessCredentials(
                type="oauth_token",
                data=b64encode(personal_access_token.encode()).decode("utf-8"),
            ),
        )

    @override
    async def asyncTearDown(self) -> None:
        """
        Cleanup created resources in a configured order.
        """
        resources_by_priority: list[ResourceType] = [
            "application",
            "credential",
            "network-rule",
        ]

        for resource_type in resources_by_priority:
            for resource_id in self._created_resources[resource_type]:
                try:
                    if resource_type == "application":
                        await self.server.devopness.applications.delete_application(
                            resource_id,
                        )

                        self.server.logger.info(
                            f"Deleted application {resource_id}",
                        )

                    elif resource_type == "credential":
                        await self.server.devopness.credentials.delete_credential(
                            resource_id,
                        )

                        self.server.logger.info(
                            f"Deleted credential {resource_id}",
                        )

                    elif resource_type == "network-rule":
                        await self.server.devopness.network_rules.delete_network_rule(
                            resource_id,
                        )

                        self.server.logger.info(
                            f"Deleted network rule {resource_id}",
                        )

                except Exception:
                    self.server.logger.error(
                        f"Failed to delete {resource_type} {resource_id}"
                    )

    # Utility Methods #

    def random_name(self, size: int = 8, prefix: str = "") -> str:
        """
        Generate a random name with the given size and prefix.
        """
        return prefix + "".join(
            random.choice(string.ascii_lowercase)  # noqa: S311
            for i in range(size)
        )

    def cast_to_mcp_response(
        self,
        call_tool_result: CallToolResult,
        response_type: Type[T] | None = None,
    ) -> MCPResponse[T]:
        """
        Convert a CallToolResult from FastMCP Client to a MCPResponse.

        Args:
            call_tool_result (CallToolResult): The result from calling an MCP
            tool, containing structured content that will be used to
            create the MCPResponse.

            response_type (Type[T] | None, optional): The target type for data field.
                Can be either:
                - A model class (e.g., Application, Environment) for single objects
                - A List type (e.g., list[Application]) for collections
                If None, the data field will remain untyped. Defaults to None.

        Returns:
            MCPResponse[T]: An MCPResponse instance with the data field cast to the
            specified type T. If response_type is None, T will be Any.

        Examples:
            >>> # Cast to a single model
            >>> result = await client.call_tool("get_application", {...})
            >>> response = self.cast_to_mcp_response(result, Application)
            >>> app: Application = response.data

            >>> # Cast to a list of models
            >>> result = await client.call_tool("list_applications", {...})
            >>> response = self.cast_to_mcp_response(result, list[Application])
            >>> apps: list[Application] = response.data

            >>> # No type casting
            >>> result = await client.call_tool("delete_application", {...})
            >>> response = self.cast_to_mcp_response(result)
            >>> [None] = response.data
        """
        content: Any = call_tool_result.structured_content

        response: MCPResponse[T] = MCPResponse(**content)

        if response_type is not None:
            type_origin = get_origin(response_type)

            # Handle list[Model]
            if type_origin is list:
                type_args = get_args(response_type)

                if len(type_args) != 1:
                    raise ValueError(
                        "Only lists with a single type argument are supported. But got:"
                        f" {type_args}"
                    )

                model_cls: Any = type_args[0]

                list_data: Any = [model_cls(**item) for item in response.data]  # type: ignore[union-attr]

                response.data = cast(T, list_data)

            # Handle Model
            else:
                model_data: Any = response_type(**response.data)  # type: ignore[arg-type]

                response.data = cast(T, model_data)

        return response

    async def get_resource_by_id(
        self,
        resource_id: int,
        resource_type: ResourceType,
        resource_class: Type[T],
    ) -> T:
        """
        This method retrieves a resource from the Devopness API
        and casts it to the specified type.
        """
        endpoint_parts = [
            "/",
            resource_type + "s/",
            str(resource_id),
        ]

        endpoint: str = "".join(endpoint_parts)

        response = await self.server.devopness.projects._get(endpoint)

        resource: DevopnessResponse[T] = await DevopnessResponse.from_async(
            response,
            resource_class,
        )

        return resource.data

    async def list_resource_by_type(
        self,
        parent_resource_id: int,
        parent_resource_type: ResourceType,
        resource_type: ResourceType,
        resource_class: Type[T],
    ) -> list[T]:
        """
        This method retrieves a list of resources from the Devopness API
        and casts them to the specified type.
        """
        endpoint_parts = [
            "/",
            parent_resource_type + "s/",
            str(parent_resource_id),
            "/",
            resource_type + "s",
        ]

        endpoint: str = "".join(endpoint_parts)

        response = await self.server.devopness.projects._get(endpoint)

        resources: DevopnessResponse[list[T]] = await DevopnessResponse.from_async(
            response,
            list[resource_class],  # type: ignore[valid-type]
        )

        return resources.data

    async def create_fake_server(
        self,
        project_id: int,
    ) -> Server:
        """
        This method creates a "fake server" in the Devopness API.
        The server is "fake" in that it does not exist in any cloud provider.
        """
        endpoint_parts = [
            "/",
            "dev-tests/",
            "fake-server/",
            str(project_id) + "/",
            self.random_name(prefix="mcp-fake-server-"),
        ]

        endpoint: str = "".join(endpoint_parts)

        response = await self.server.devopness.projects._post(endpoint)

        server: DevopnessResponse[Server] = await DevopnessResponse.from_async(
            response,
            Server,
        )

        return server.data

    # SDK Methods #

    async def create_project(
        self,
    ) -> Project:
        """
        This method creates a project in the Devopness API.
        """
        project_name = self.random_name(prefix=f"MCP-E2E-{datetime.datetime.now()}-")

        response = await self.server.devopness.projects.add_project(
            {
                "name": project_name,
            }
        )

        return response.data

    async def create_environment(
        self,
        project_id: int,
    ) -> Environment:
        """
        This method creates an environment in the Devopness API.
        """
        environment_name = self.random_name(
            prefix=f"MCP-E2E-ENV-{datetime.datetime.now()}-",
        )

        response = await self.server.devopness.environments.add_project_environment(
            project_id,
            {
                "name": environment_name,
                "type": "development",
            },
        )

        return response.data

    async def create_credential(
        self,
        environment_id: int,
    ) -> Credential:
        """
        This method creates a credential in the Devopness API.

        TODO: this method should accept the 'provider' as parameter
        and create the credential accordingly.
        """

        credential_name = self.random_name(
            prefix=f"MCP-E2E-CRED-{datetime.datetime.now()}-",
        )

        # Currently, we do not support creating credentials for source
        # providers programmatically.
        #
        # User interaction through a browser is required to access
        # the provider's site and confirm access to their account.
        #
        # TODO: Remove this workaround once we support creating source
        # credentials via access tokens, similar to cloud providers.

        # pylint: disable=protected-access
        api_response = await self.server.devopness.credentials._post(
            f"/dev-tests/fake-credentials/{environment_id}",
            {
                "source": {
                    "name": credential_name,
                    "provider_code": "github",
                    "access_token": os.environ.get("GITHUB_ACCESS_TOKEN", ""),
                }
            },
        )

        credential = Credential.from_dict((api_response.json())[0])

        self._created_resources["credential"].append(credential.id)

        return credential

    async def create_application(
        self,
        environment_id: int,
        source_credential_id: int,
    ) -> Application:
        """
        This method creates an application in the Devopness API.
        """
        response = await self.server.devopness.applications.add_environment_application(
            environment_id,
            {
                "name": self.random_name(prefix="e2e-"),
                "credential_id": source_credential_id,
                "repository": "devopness/devopness",
                "root_directory": "/",
                "programming_language": "html",
                "engine_version": "none",
                "framework": "none",
                "default_branch": "main",
            },
        )

        application = response.data

        self._created_resources["application"].append(application.id)

        return application

    async def create_webhook(
        self,
        pipeline_id: int,
        hook_type: HookTypeParamPlain,
        hook_settings: HookPipelineCreatePlain,
    ) -> Hook:
        """
        This method creates a webhook in the Devopness API.
        """
        response = await self.server.devopness.hooks.add_pipeline_hook(
            hook_type,
            pipeline_id,
            hook_settings,
        )

        # TODO: fix the "Hook Type" in Devopness SDK.
        #       Currently, pydantic fails to parse the response, and return a
        #       plain string.
        #       We use `ensure_object` as a workaround to convert the string
        #       into a "OpaqueObject".
        #       ERROR:
        #         trigger_when: Input should be a valid dictionary or instance of
        #                       HookTriggerWhen.
        return cast(Hook, ensure_object(response.data))

    async def create_network_rule(
        self,
        environment_id: int,
    ) -> NetworkRule:
        """
        This method creates a network rule in the Devopness API.
        """
        response = (
            await self.server.devopness.network_rules.add_environment_network_rule(
                environment_id,
                {
                    "name": self.random_name(prefix="mcp-e2e-"),
                    "direction": "inbound",
                    "protocol": "tcp",
                    "cidr_block": "0.0.0.0/0",
                    "port": 9000,
                },
            )
        )

        network_rule = response.data

        self._created_resources["network-rule"].append(network_rule.id)

        return network_rule

    async def list_pipelines_of_resource(
        self,
        resource_id: int,
        resource_type: ResourceType,
    ) -> list[PipelineRelation]:
        """
        This method lists the pipelines of a resource in the Devopness API.
        """
        response = (
            await self.server.devopness.pipelines.list_pipelines_by_resource_type(
                resource_id,
                resource_type,
            )
        )

        return response.data

    # Actions Triggers #

    async def trigger_credential_get_status(
        self,
        credential_id: int,
    ) -> Action:
        """
        This method triggers a credential get status action in the Devopness API.
        """
        response = await self.server.devopness.credentials.get_status_credential(
            credential_id
        )

        action_id = cast(int, response.action_id)

        action_response = await self.server.devopness.actions.get_action(action_id)

        return action_response.data

    async def trigger_pipeline(
        self,
        pipeline_id: int,
        servers: Optional[list[int]] = None,
    ) -> Action:
        """
        This method triggers a pipeline action in the Devopness API.
        """
        response = await self.server.devopness.actions.add_pipeline_action(
            pipeline_id,
            {
                "servers": servers or [],
            },
        )

        action_id = cast(int, response.action_id)

        action_response = await self.server.devopness.actions.get_action(action_id)

        return action_response.data


__all__ = ["DevopnessTestSession"]
