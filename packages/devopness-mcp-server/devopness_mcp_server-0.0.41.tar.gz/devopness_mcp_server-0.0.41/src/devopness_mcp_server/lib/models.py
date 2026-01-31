"""
This module defines simplified data models tailored for use in the MCP Server.

These models are derived from the SDK models but include only the essential fields.
The purpose of this is to reduce the amount of data being sent to the LLM's,
which helps prevent unnecessary context noise and reduces the chances of hallucinations,
especially when working with large payloads.

By stripping down the models to their most relevant attributes, we ensure
leaner communication with the LLM and improve the quality and reliability
of its responses.
"""

import json
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Optional, cast

from devopness.base import DevopnessBaseModel
from devopness.models import (
    Action,
    ActionData,
    ActionRelation,
    ActionRelationShallow,
    ActionStatus,
    ActionStep,
    ActionTarget,
    ActionTargetCredentialData,
    ActionTargetNetworkData,
    ActionType,
    Application,
    ApplicationRelation,
    CredentialRelation,
    Daemon,
    DaemonRelation,
    EnvironmentRelation,
    Hook,
    HookRelation,
    HookSettings,
    HookTriggerWhen,
    HookType,
    Network,
    NetworkProvisionInputSettingsGcp,
    NetworkRelation,
    NetworkRule,
    NetworkRuleRelation,
    Pipeline,
    PipelineRelation,
    PipelineStepRunnerName,
    ProjectRelation,
    Server,
    ServerRelation,
    ServerStatus,
    Service,
    ServiceRelation,
    SshKey,
    SshKeyRelation,
    SslCertificate,
    SslCertificateRelation,
    Step,
    Variable,
    VariableRelation,
    VirtualHost,
    VirtualHostRelation,
)

from .types import TypeExtraData


def ensure_object(data: Any) -> Any:  # noqa: ANN401
    """
    Ensures that the given data is an object with attribute access.

    If the data is a JSON string, it parses it and recursively converts to SimpleNamespace.
    If the data is a dictionary, it recursively converts to SimpleNamespace.
    Otherwise, returns the data as-is.

    Args:
        data: The input data to convert

    Returns:
        The converted data with attribute access capability, or the original data
        if no conversion is needed
    """  # noqa: E501
    if isinstance(data, str):
        try:
            data = json.loads(data)

        except Exception:
            return data

    if isinstance(data, dict):
        return SimpleNamespace(**{k: ensure_object(v) for k, v in data.items()})

    if isinstance(data, list):
        return [ensure_object(item) for item in data]

    return data


class ProjectSummary(DevopnessBaseModel):
    id: int
    name: str
    url_web_permalink: str

    @classmethod
    def from_sdk_model(
        cls,
        data: ProjectRelation,
    ) -> "ProjectSummary":
        return cls(
            id=data.id,
            name=data.name,
            url_web_permalink=f"https://app.devopness.com/projects/{data.id}",
        )


class EnvironmentSummary(DevopnessBaseModel):
    id: int
    name: str
    description: Optional[str]
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: EnvironmentRelation,
        extra_data: TypeExtraData = None,
    ) -> "EnvironmentSummary":
        return cls(
            id=data.id,
            name=data.name,
            description=data.description,
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class ActionStepSummary(DevopnessBaseModel):
    id: int
    name: Optional[str]
    status: ActionStatus
    action_id: int
    action_target_id: int
    action_target_step_order: int

    @classmethod
    def from_sdk_model(
        cls,
        data: ActionStep,
    ) -> "ActionStepSummary | None":
        return cls(
            id=data.id,
            name=data.name,
            status=data.status,
            action_id=data.action_id,
            action_target_id=data.action_target_id,
            action_target_step_order=data.order,
        )


class ActionTargetSummary(DevopnessBaseModel):
    id: int
    target_id: int
    target_type: str
    target_name: Optional[str]
    steps: Optional[list[Optional[ActionStepSummary]]]
    steps_count: Optional[int]

    @classmethod
    def from_sdk_model(
        cls,
        data: ActionTarget,
    ) -> "ActionTargetSummary":
        return cls(
            id=data.id,
            target_id=data.resource_id,
            target_type=data.resource_type,
            target_name=(
                None
                if data.resource_data is None
                else data.resource_data.name
                if isinstance(
                    data.resource_data,
                    (ActionTargetCredentialData, ActionTargetNetworkData),
                )
                else data.resource_data.hostname
            ),
            steps=[
                ActionStepSummary.from_sdk_model(step)  #
                if step is not None
                else None
                for step in data.steps or []
            ],
            steps_count=data.total_steps,
        )


class ActionSummary(DevopnessBaseModel):
    id: int
    type: str
    status: ActionStatus
    status_reason_code: str
    data: Optional[ActionData]
    resource_id: Optional[int]
    resource_type: Optional[str]
    resource_name: Optional[str]
    resource_pipeline_id: Optional[int]
    targets: list[ActionTargetSummary]
    started_at: Optional[str] | Optional[datetime] = None
    completed_at: Optional[str] | Optional[datetime] = None
    created_by: Optional[str] = None
    environment_id: Optional[int]
    project_id: Optional[int]
    url_web_permalink: str

    @classmethod
    def from_sdk_model(
        cls,
        data: Action | ActionRelation | ActionRelationShallow,
    ) -> "ActionSummary":
        return cls(
            id=data.id,
            type=data.type_human_readable,
            status=data.status,
            status_reason_code=data.status_reason_human_readable,
            data=(
                data.action_data  # ActionRelation(Shallow) does not include action_data
                if isinstance(data, (Action))
                else None
            ),
            resource_id=(
                data.resource.id  # ActionRelationShallow does not include `resource`
                if isinstance(data, (Action, ActionRelation))
                else None
            ),
            resource_type=(
                data.resource.type
                # ActionRelationShallow does not include `resource`
                if isinstance(data, (Action, ActionRelation))
                else None
            ),
            resource_name=(
                getattr(data.resource.data, "name", None)
                # ActionRelationShallow does not include `resource`
                if isinstance(data, (Action, ActionRelation))
                else None
            ),
            resource_pipeline_id=(
                data.pipeline_id
                # ActionRelation(Shallow) does not include pipeline_id
                if isinstance(data, (Action))
                else None
            ),
            targets=[
                ActionTargetSummary.from_sdk_model(target)
                for target in data.targets or []
            ],
            started_at=data.started_at,
            completed_at=data.completed_at,
            created_by=(
                data.triggered_from.name if data.triggered_from is not None else None
            ),
            environment_id=(
                data.environment.id
                # ActionRelation(Shallow) does not include `environment`
                if isinstance(data, (Action)) and data.environment is not None
                else None
            ),
            project_id=(
                data.project.id
                # ActionRelation(Shallow) does not include `project`
                if isinstance(data, (Action)) and data.project is not None
                else None
            ),
            url_web_permalink=data.url_web_permalink,
        )


class PipelineStepSummary(DevopnessBaseModel):
    id: int
    name: Optional[str]
    command: str
    runner: PipelineStepRunnerName
    trigger_order: int
    is_auto_generated: bool
    url_web_permalink: Optional[str]

    @classmethod
    def from_sdk_model(
        cls,
        data: Step,
        extra_data: TypeExtraData = None,
    ) -> "PipelineStepSummary":
        return cls(
            id=data.id,
            name=data.name,
            command=data.command,
            runner=data.runner,
            trigger_order=data.trigger_order,
            is_auto_generated=data.is_auto_generated,
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class PipelineSummary(DevopnessBaseModel):
    id: int
    name: str
    operation: str
    steps: Optional[list[PipelineStepSummary]] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Pipeline | PipelineRelation,
        extra_data: TypeExtraData = None,
    ) -> "PipelineSummary":
        return cls(
            id=data.id,
            name=data.name,
            operation=data.operation,
            steps=[
                PipelineStepSummary.from_sdk_model(step)
                for step in getattr(data, "steps", [])
            ],
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class SSHKeySummary(DevopnessBaseModel):
    id: int
    name: str
    fingerprint: str
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: SshKey | SshKeyRelation,
        extra_data: TypeExtraData = None,
    ) -> "SSHKeySummary":
        return cls(
            id=data.id,
            name=data.name,
            fingerprint=data.fingerprint,
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class CredentialSummary(DevopnessBaseModel):
    id: int
    name: str
    provider: str
    provider_type: str
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: CredentialRelation,
        extra_data: TypeExtraData = None,
    ) -> "CredentialSummary":
        return cls(
            id=data.id,
            name=data.name,
            provider=data.provider.code_human_readable,
            provider_type=data.provider_type_human_readable,
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class ServiceSummary(DevopnessBaseModel):
    id: int
    name: str
    type: str
    version: str
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Service | ServiceRelation,
        extra_data: TypeExtraData = None,
    ) -> "ServiceSummary":
        return cls(
            id=data.id,
            name=data.name,
            type=data.type,
            version=cast(str, data.version),
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class ApplicationSummary(DevopnessBaseModel):
    id: int
    name: str
    repository: str
    programming_language: str
    programming_language_version: str
    programming_language_framework: str
    root_directory: Optional[str] = None
    install_dependencies_command: Optional[str] = None
    build_command: Optional[str] = None
    last_action: Optional[ActionSummary] = None
    live_deploy: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Application | ApplicationRelation,
        extra_data: TypeExtraData = None,
    ) -> "ApplicationSummary":
        return cls(
            id=data.id,
            name=data.name,
            repository=data.repository,
            programming_language=data.programming_language,
            programming_language_version=data.engine_version,
            programming_language_framework=data.framework,
            root_directory=data.root_directory,
            install_dependencies_command=data.install_dependencies_command,
            build_command=data.build_command,
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
            last_action=(
                ActionSummary.from_sdk_model(data.last_deployments.latest)
                if data.last_deployments is not None
                and data.last_deployments.latest is not None
                else None
            ),
            live_deploy=(
                ActionSummary.from_sdk_model(data.last_deployments.live)
                if data.last_deployments is not None
                and data.last_deployments.live is not None
                else None
            ),
        )


class ServerSummary(DevopnessBaseModel):
    id: int
    name: str
    status: ServerStatus
    ip_address: Optional[str] = None
    ssh_port: int
    provider_code: str
    provider_region: Optional[str] = None
    instance_type: Optional[str] = None
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Server | ServerRelation,
        extra_data: TypeExtraData = None,
    ) -> "ServerSummary":
        return cls(
            id=data.id,
            name=data.name,
            status=data.status,
            ip_address=data.ip_address,
            ssh_port=data.ssh_port,
            provider_code=data.provider_name,
            provider_region=(
                data.region
                if isinstance(data, ServerRelation)
                else getattr(
                    data.provision_input.settings,
                    "region",
                    None,
                )
            ),
            instance_type=extra_data.server_instance_type if extra_data else None,
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class DaemonSummary(DevopnessBaseModel):
    id: int
    name: str
    command: str
    run_as_user: str
    process_count: int
    working_directory: Optional[str]
    application_id: Optional[int] = None
    application_name: Optional[str] = None
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Daemon | DaemonRelation,
        extra_data: TypeExtraData = None,
    ) -> "DaemonSummary":
        return cls(
            id=data.id,
            name=data.name,
            command=data.command,
            run_as_user=data.run_as_user,
            process_count=data.process_count,
            working_directory=data.working_directory,
            application_id=data.application.id
            if data.application is not None
            else None,
            application_name=data.application.name
            if data.application is not None
            else None,
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class SSLCertificateSummary(DevopnessBaseModel):
    id: int
    name: str
    active: bool
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: SslCertificate | SslCertificateRelation,
        extra_data: TypeExtraData = None,
    ) -> "SSLCertificateSummary":
        return cls(
            id=data.id,
            name=data.name,
            active=data.active,
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class VirtualHostSummary(DevopnessBaseModel):
    id: int
    name: str
    root_directory: Optional[str]
    ssl_certificate_id: Optional[int] = None
    application_id: Optional[int] = None
    application_name: Optional[str] = None
    application_listen_address: Optional[str] = None
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: VirtualHost | VirtualHostRelation,
        extra_data: TypeExtraData = None,
    ) -> "VirtualHostSummary":
        return cls(
            id=data.id,
            name=data.name,
            ssl_certificate_id=data.ssl_certificate.id
            if data.ssl_certificate is not None
            else None,
            root_directory=data.root_directory or "",
            application_id=data.application.id
            if data.application is not None
            else None,
            application_name=data.application.name
            if data.application is not None
            else None,
            application_listen_address=data.application_listen_address,
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class VariableSummary(DevopnessBaseModel):
    id: int
    key: str
    value: str
    target: str
    is_secret: bool
    description: Optional[str]
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Variable | VariableRelation,
        extra_data: TypeExtraData = None,
    ) -> "VariableSummary":
        value = data.value or ""
        if extra_data and extra_data.application_hide_config_file_content:
            value = ""

        return cls(
            id=data.id,
            key=data.key,
            value=value,
            target=data.target,
            is_secret=data.hidden,
            description=data.description,
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class HookSummary(DevopnessBaseModel):
    id: str
    name: str
    type: HookType
    action_type: ActionType
    pipeline_id: Optional[int]
    url: Optional[str] = None
    target_url: Optional[str] = None
    requires_secret: bool
    verify_ssl: bool
    active: bool
    resource_id: int
    resource_type: str
    settings: Optional[HookSettings] = None
    trigger_when: Optional[HookTriggerWhen] = None
    secret: Optional[str] = None
    secret_algorithm: Optional[str] = None
    secret_header_name: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Hook | HookRelation,
    ) -> "HookSummary":
        data = ensure_object(data)

        return cls(
            id=data.id,
            name=data.name,
            type=data.type,
            action_type=data.action_type,
            pipeline_id=data.pipeline_id,
            url=getattr(data, "url", None),
            target_url=getattr(data, "target_url", None),
            requires_secret=data.requires_secret,
            verify_ssl=data.verify_ssl,
            active=data.active,
            resource_id=data.resource_id,
            resource_type=data.resource_type,
            settings=getattr(data, "settings", None),
            trigger_when=getattr(data, "trigger_when", None),
            secret=getattr(data, "secret", None),
            secret_algorithm=getattr(data, "secret_algorithm", None),
            secret_header_name=getattr(data, "secret_header_name", None),
        )


class NetworkRuleSummary(DevopnessBaseModel):
    id: int
    name: str
    cidr_block: str
    port: int
    protocol: str
    direction: str
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: NetworkRule | NetworkRuleRelation,
        extra_data: TypeExtraData = None,
    ) -> "NetworkRuleSummary":
        return cls(
            id=data.id,
            name=data.name,
            cidr_block=data.cidr_block,
            port=data.port,
            protocol=data.protocol,
            direction=data.direction,
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=extra_data.url_web_permalink if extra_data else None,
        )


class NetworkSummary(DevopnessBaseModel):
    id: int
    name: str
    provider_name: str
    provider_region: str
    cidr_block: Optional[str] = None
    last_action: Optional[ActionSummary] = None
    url_web_permalink: Optional[str] = None

    @classmethod
    def from_sdk_model(
        cls,
        data: Network | NetworkRelation,
        extra_data: TypeExtraData = None,
    ) -> "NetworkSummary":
        return cls(
            id=data.id,
            name=data.name,
            provider_name=data.provider_name_human_readable,
            provider_region=(
                data.provision_input.settings.region_human_readable
                or data.provision_input.settings.region
            ),
            cidr_block=(
                str(data.provision_input.settings.cidr_block)
                # NetworkProvisionInputSettingsGcp does not include `cidr_block`
                if not isinstance(
                    data.provision_input.settings,
                    NetworkProvisionInputSettingsGcp,
                )
                else None
            ),
            last_action=(
                ActionSummary.from_sdk_model(data.last_action)
                if data.last_action is not None
                else None
            ),
            url_web_permalink=(extra_data.url_web_permalink if extra_data else None),
        )
