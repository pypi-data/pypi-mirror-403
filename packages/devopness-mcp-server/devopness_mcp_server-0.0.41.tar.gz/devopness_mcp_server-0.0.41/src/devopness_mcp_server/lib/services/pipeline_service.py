from typing import Annotated

from pydantic import Field, StringConstraints

from ..models import PipelineStepSummary, PipelineSummary
from ..response import MCPResponse
from ..types import (
    MAX_RESOURCES_PER_PAGE,
    ExtraData,
    FormattedData,
    ResourceType,
    ServerContext,
)
from ..utils import (
    get_instructions_format_table,
    get_instructions_next_action_suggestion,
)


class PipelineService:
    @staticmethod
    async def tool_get_resource_pipelines(
        ctx: ServerContext,
        resource_id: int,
        resource_type: ResourceType,
        page: int = Field(
            default=1,
            gt=0,
        ),
    ) -> MCPResponse[list[PipelineSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            resource_id=resource_id,
            resource_type=resource_type,
            page=page,
        )

        if not success:
            return error_response

        response = await ctx.devopness.pipelines.list_pipelines_by_resource_type(
            resource_id,
            resource_type,
            page,
            per_page=MAX_RESOURCES_PER_PAGE,
        )

        pipelines = [
            PipelineSummary.from_sdk_model(
                pipeline,
                ExtraData(
                    url_web_permalink=(
                        "https://app.devopness.com/"
                        f"projects/{pipeline.project_id}/"
                        f"environments/{pipeline.environment_id}/"
                        f"{resource_type}s/{resource_id}/"
                        f"pipelines/{pipeline.id}"
                    )
                ),
            )
            for pipeline in response.data
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(pipeline.id),
                "Name": f"[{pipeline.name}]({pipeline.url_web_permalink})",
                "Operation": pipeline.operation,
            }
            for pipeline in pipelines
        ]

        return MCPResponse.ok(
            data=pipelines,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_next_action_suggestion("deploy", resource_type),
            ],
            next_page=(page + 1 if page < response.page_count else None),
        )

    @staticmethod
    async def tool_list_pipeline_steps(
        ctx: ServerContext,
        pipeline_id: int,
    ) -> MCPResponse[list[PipelineStepSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            pipeline_id=pipeline_id,
        )

        if not success:
            return error_response

        response = await ctx.devopness.pipelines.get_pipeline(pipeline_id)

        pipeline = response.data
        pipeline_steps = [
            PipelineStepSummary.from_sdk_model(
                step,
                ExtraData(
                    url_web_permalink=(
                        "https://app.devopness.com/"
                        f"projects/{pipeline.project_id}/"
                        f"environments/{pipeline.environment_id}/"
                        f"{pipeline.resource_type}s/{pipeline.resource_id}/"
                        f"pipelines/{step.pipeline_id}/"
                        f"steps/{step.id}"
                    )
                ),
            )
            for step in pipeline.steps
        ]

        formatted_data: list[FormattedData] = [
            {
                "ID": str(step.id),
                "Name": (
                    f"**{step.name}**"
                    if step.is_auto_generated
                    else f"[{step.name}]({step.url_web_permalink})"
                ),
                "Command": ("" if step.is_auto_generated else f"`{step.command}`"),
            }
            for step in pipeline_steps
        ]

        return MCPResponse.ok(
            data=pipeline_steps,
            formatted=formatted_data,
            instructions=[
                get_instructions_format_table(),
                get_instructions_next_action_suggestion(
                    "deploy",
                    response.data.resource_type.value,  # type: ignore[arg-type]
                ),
            ],
        )

    @staticmethod
    async def tool_create_pipeline_step(
        ctx: ServerContext,
        pipeline_id: int,
        name: Annotated[
            str,
            StringConstraints(
                min_length=4,
                max_length=60,
            ),
        ],
        command: Annotated[
            str,
            StringConstraints(
                min_length=10,
                max_length=300,
            ),
        ],
        trigger_after_step_id: int,
    ) -> MCPResponse[list[PipelineStepSummary]]:
        success, error_response = await ctx.confirm_params_if_supported_by_client(
            pipeline_id=pipeline_id,
            name=name,
            command=command,
            trigger_after_step_id=trigger_after_step_id,
        )

        if not success:
            return error_response

        pipeline_steps = await PipelineService.tool_list_pipeline_steps(
            ctx, pipeline_id
        )

        trigger_after_step = next(
            (
                step
                for step in pipeline_steps.data or []
                if step.id == trigger_after_step_id
            ),
            None,
        )

        if trigger_after_step is None:
            return MCPResponse.error(
                [
                    f"Pipeline step with id {trigger_after_step_id} not found.",
                    "You MUST list the pipeline steps and ask the user to choose"
                    " the step after which the new pipeline step will run.",
                ],
            )

        response = await ctx.devopness.pipelines.add_pipeline_step(
            pipeline_id,
            {
                "name": name,
                "command": command,
                "type": "pipeline-step",
                "runner": "custom",
                "run_as_user": "devopness",
            },
        )

        await ctx.devopness.pipelines.update_pipeline_step(
            pipeline_id,
            response.data.id,
            {
                "id": response.data.id,
                "command": response.data.command,
                "runner": response.data.runner,
                "trigger_after": trigger_after_step.trigger_order,
            },
        )

        pipeline_steps = await PipelineService.tool_list_pipeline_steps(
            ctx,
            pipeline_id,
        )

        return MCPResponse.ok(
            pipeline_steps.data,
            pipeline_steps.instructions,
        )
