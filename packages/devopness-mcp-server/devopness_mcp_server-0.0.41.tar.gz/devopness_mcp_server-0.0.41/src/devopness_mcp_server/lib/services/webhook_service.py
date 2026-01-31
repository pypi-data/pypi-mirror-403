from pydantic import Field

from devopness.models import HookPipelineCreate, HookTypeParamPlain
from devopness_mcp_server.lib.utils import (
    get_instructions_format_table,
    get_instructions_next_action_suggestion,
)

from ..models import HookSummary, ensure_object
from ..response import MCPResponse
from ..types import MAX_RESOURCES_PER_PAGE, FormattedData, ServerContext


class WebHookService:
    @staticmethod
    async def tool_create_webhook(
        ctx: ServerContext,
        pipeline_id: int,
        hook_type: HookTypeParamPlain,
        hook_settings: HookPipelineCreate,
    ) -> MCPResponse[HookSummary]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            pipeline_id=pipeline_id,
            hook_type=hook_type,
            hook_settings=hook_settings,
        )

        if not success:
            return error_response

        response = await ctx.devopness.hooks.add_pipeline_hook(
            hook_type,
            pipeline_id,
            hook_settings,
        )

        hook_summary = HookSummary.from_sdk_model(ensure_object(response.data))
        instructions = [
            get_instructions_format_table(
                [
                    ("ID", "{hook.id}"),
                    ("Name", "{hook.name}"),
                    ("Type", "{hook.type}"),
                    ("Action Type", "{hook.action_type}"),
                    ("URL", "{hook.url}"),
                    ("Active", "{hook.active}"),
                    ("Requires Secret", "{hook.requires_secret}"),
                ]
            ),
            get_instructions_next_action_suggestion("list", "webhook"),  # type: ignore[arg-type]
        ]
        return MCPResponse.ok(hook_summary, instructions=instructions)

    @staticmethod
    async def tool_list_webhook_of_application(
        ctx: ServerContext,
        application_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[HookSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            application_id=application_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.hooks.list_application_hooks(
            application_id,
            page=page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        hooks = [
            HookSummary.from_sdk_model(hook) for hook in ensure_object(response.data)
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": hook.id,
                "Name": hook.name,
                "Type": hook.type,
                "Operation": str(hook.action_type).replace("_", " ").title(),
                "URL": hook.url or "-",
                "Active": "🟢 Yes" if hook.active else "🔴 No",
                "Requires secret": "🔒 Yes" if hook.requires_secret else "🔓 No",
            }
            for hook in hooks
        ]

        instructions = [
            get_instructions_format_table(),
            get_instructions_next_action_suggestion("create", "webhook"),  # type: ignore[arg-type]
        ]

        return MCPResponse.ok(
            data=hooks,
            formatted=formatted_data,
            instructions=instructions,
            next_page=None,
        )

    @staticmethod
    async def tool_list_webhook_of_pipeline(
        ctx: ServerContext,
        pipeline_id: int,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[HookSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            pipeline_id=pipeline_id,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.hooks.list_pipeline_hooks(
            pipeline_id,
            page=page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        hooks = [
            HookSummary.from_sdk_model(hook) for hook in ensure_object(response.data)
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": hook.id,
                "Name": hook.name,
                "Type": hook.type,
                "Operation": str(hook.action_type).replace("_", " ").title(),
                "URL": hook.url or "-",
                "Active": "🟢 Yes" if hook.active else "🔴 No",
                "Requires secret": "🔒 Yes" if hook.requires_secret else "🔓 No",
            }
            for hook in hooks
        ]

        instructions = [
            get_instructions_format_table(),
            get_instructions_next_action_suggestion("create", "webhook"),  # type: ignore[arg-type]
        ]

        return MCPResponse.ok(
            data=hooks,
            formatted=formatted_data,
            instructions=instructions,
            next_page=None,
        )

    @staticmethod
    async def tool_delete_webhook(
        ctx: ServerContext,
        hook_id: str,
        hook_type: HookTypeParamPlain,
    ) -> MCPResponse[None]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            hook_id=hook_id,
        )

        if not success:
            return error_response

        await ctx.devopness.hooks.delete_hook(
            hook_id,
            hook_type,
        )

        return MCPResponse.ok()
