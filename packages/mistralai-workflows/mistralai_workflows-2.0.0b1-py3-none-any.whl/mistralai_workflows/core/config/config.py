import os
from enum import StrEnum
from typing import Self

import structlog
from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mistralai_workflows.core.logging import Env, LogFormat, LoggerConfig, LogLevel, setup_logging
from mistralai_workflows.core.rate_limiting.rate_limit import RateLimit
from mistralai_workflows.core.storage.blob_storage_impl import StorageProvider

logger = structlog.getLogger(__name__)

env_file = ".env" if os.environ.get("PYTEST_VERSION") is None else ".env.test"


class CommonConfig(BaseSettings):
    app_name: str = "mistral-workflows"
    app_version: str = "0.0.0"
    env: Env = Env.DEV
    log_format: LogFormat = LogFormat.CONSOLE
    log_level: LogLevel = LogLevel.INFO
    enable_docs: bool = Field(default=True, validation_alias="ENABLE_DOCS")

    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4318"
    otel_sample_rate: float = 1.0
    otel_export_interval_ms: int = 30000
    otel_tail_sampling: bool = False
    otel_local: bool = False
    otel_inject_logs: bool = True

    redis_enabled: bool = False
    redis_connection_string: SecretStr = SecretStr("localhost:6379")
    redis_database: int = 0

    ca_bundle: str | None = Field(  # type: ignore[pydantic-alias]
        default=None,
        description="Path to the CA bundle file for TLS verification",
        validation_alias=AliasChoices("CA_BUNDLE", "CURL_CA_BUNDLE"),
    )

    mistral_api_key: SecretStr | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )


# Hardcoded reserved workflow names that conflict with API endpoints
# This CANNOT be overridden via environment variables for security reasons
RESERVED_WORKFLOW_NAMES: frozenset[str] = frozenset({"executions", "schedules", "definitions", "internal"})

RESERVED_UPDATE_NAMES: frozenset[str] = frozenset({"__submit_input"})

RESERVED_QUERY_NAMES: frozenset[str] = frozenset({"__get_pending_inputs"})

INTERNAL_ACTIVITY_PREFIX: str = "__internal__"


class TemporalConfig(BaseSettings):
    server_url: str = Field(
        default="localhost:7233",
    )
    namespace: str = Field(
        default="mistral-workflows",
    )
    api_key: SecretStr | None = Field(
        default=None,
    )
    namespace_retention_days: int = Field(
        default=30,
    )
    single_tenant_namespace: bool = Field(
        default=False,
        description="If True, the namespace matches the customer/workspace identifier.",
    )
    enforce_payload_encoding: bool = Field(
        default=False,
    )
    task_queue: str = Field(default="default")  # Allow override
    tls: bool = False
    external_server_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="TEMPORAL_",
        env_parse_none_str="null",
    )

    @model_validator(mode="after")
    def set_external_url(self) -> "Self":
        if not self.external_server_url:
            self.external_server_url = self.server_url
        return self


class BlobStorageConfig(BaseSettings):
    enabled: bool = False
    storage_provider: StorageProvider = StorageProvider.S3
    prefix: str | None = None

    # Azure settings
    container_name: str | None = None
    azure_connection_string: SecretStr | None = None

    # GCS settings
    bucket_id: str | None = None

    # S3 settings
    bucket_name: str | None = None
    region_name: str | None = None
    endpoint_url: str | None = None
    aws_access_key_id: SecretStr | None = None
    aws_secret_access_key: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )


class PayloadOffloadingConfig(BaseSettings):
    enabled: bool = False
    storage_config: BlobStorageConfig | None = None
    min_size_bytes: int = 1024 * 1024  # 1MB


class PayloadEncryptionMode(StrEnum):
    NONE = "none"
    FULL = "full"
    PARTIAL = "partial"


class PayloadEncryptionConfig(BaseSettings):
    mode: PayloadEncryptionMode = PayloadEncryptionMode.NONE

    # If both keys are provided, the main key will be used for encryption and both keys will be used for decryption
    # to support key rotation.
    main_key: SecretStr | None = None
    secondary_key: SecretStr | None = None


class AgentConfig(BaseSettings):
    llm_rate_limit: RateLimit | None = None
    mistral_client_server: str | None = None
    mistral_client_server_url: str | None = None
    mistral_client_url_params: dict[str, str] | None = None
    mistral_client_timeout_ms: int | None = None
    mistral_client_api_key: SecretStr | None = Field(  # type: ignore[pydantic-alias]
        default=None,
        description="API key for Mistral client",
        validation_alias=AliasChoices("MISTRAL_CLIENT_API_KEY", "MISTRAL_API_KEY"),
    )
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
        env_nested_delimiter="__",
    )


class WorkerVersioningConfig(BaseSettings):
    enabled: bool = Field(default=False)
    deployment_name: str | None = Field(
        default=None,
        validation_alias="DEPLOYMENT_NAME",
    )
    build_id: str | None = Field(
        default=None,
        validation_alias="BUILD_ID",
    )
    auto_register_as_current: bool | None = Field(
        default=None,
        validation_alias="WORKER_AUTO_REGISTER_AS_CURRENT",
    )

    @model_validator(mode="after")
    def configure_versioning(self) -> "WorkerVersioningConfig":
        """Infer worker versioning behaviour from environment and config values."""
        controller_deployment = os.environ.get("TEMPORAL_DEPLOYMENT_NAME")
        controller_build_id = os.environ.get("TEMPORAL_WORKER_BUILD_ID")
        is_managed_by_controller = bool(controller_deployment and controller_build_id)

        auto_register_override = self.auto_register_as_current

        if is_managed_by_controller:
            self.deployment_name = controller_deployment
            self.build_id = controller_build_id
            self.enabled = True
            if self.auto_register_as_current is None:
                self.auto_register_as_current = False
            logger.info(
                "Worker managed by Temporal Worker Controller",
                deployment_name=self.deployment_name,
                build_id=self.build_id,
                auto_register=self.auto_register_as_current,
            )
            return self

        # manual / local mode
        if self.deployment_name and self.build_id:
            self.enabled = True
            if auto_register_override is not None:
                self.auto_register_as_current = auto_register_override
            else:
                self.auto_register_as_current = True

            logger.info(
                "Worker in manual mode with versioning enabled",
                deployment_name=self.deployment_name,
                build_id=self.build_id,
                auto_register=self.auto_register_as_current,
            )
            return self

        if self.enabled:
            logger.warning(
                "Worker versioning enabled but deployment name or build ID missing; disabling versioning",
                deployment_name=self.deployment_name,
                build_id=self.build_id,
            )

        self.enabled = False
        self.auto_register_as_current = False
        return self

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )


class WorkerConfig(BaseSettings):
    retry_policy_max_attempts: int = 3
    retry_policy_backoff_coefficient: float = 2.0
    # - The workflow fails on any workflow-level error if set to True. Note: Workflow-level errors differ from
    # activity-level errors and typically result from bugs in the workflow code. By default, workflows do not fail
    #  on errors, enabling you to push code fixes without re-running workflows.
    # More information: https://community.temporal.io/t/workflow-retry-policy-seems-to-not-be-getting-respected/11203/2",
    dangerously_force_fail_workflow_on_error: bool = Field(
        default=False,
        description="☢️ DANGER ZONE ☢️",
        alias="DANGEROUSLY_FORCE_FAIL_WORKFLOW_ON_ERROR",
    )

    server_url: str = Field(  # type: ignore[pydantic-alias]
        default="https://api.mistral.ai",
        validation_alias=AliasChoices("SERVER_URL", "server_url"),
    )
    api_version: str = "v1"
    allow_override_namespace: bool = False
    enable_config_discovery: bool = True
    mistral_api_headers: dict[str, str] | None = None

    temporal_payload_offloading: PayloadOffloadingConfig = Field(default_factory=PayloadOffloadingConfig)
    temporal_payload_encryption: PayloadEncryptionConfig = Field(default_factory=PayloadEncryptionConfig)

    activity_attributes_offloading: PayloadOffloadingConfig = Field(default_factory=PayloadOffloadingConfig)

    agent: AgentConfig = Field(default_factory=AgentConfig)
    versioning: WorkerVersioningConfig = Field(default_factory=WorkerVersioningConfig)

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
        env_nested_delimiter="__",
    )


class SentryConfig(BaseSettings):
    dsn: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="SENTRY_",
        env_parse_none_str="null",
    )


class AppConfig(BaseSettings):
    common: CommonConfig = Field(default_factory=CommonConfig)
    worker: WorkerConfig = Field(default_factory=WorkerConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    blob_storage: BlobStorageConfig = Field(default_factory=BlobStorageConfig)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)

    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding="utf-8",
        extra="ignore",
        env_parse_none_str="null",
    )

    @property
    def otel_headers(self) -> str | None:
        """Generate OTEL headers with Mistral API key as bearer token if available."""
        if self.common.mistral_api_key and self.common.mistral_api_key.get_secret_value():
            return f"Authorization=Bearer {self.common.mistral_api_key.get_secret_value()}"
        return None

    @model_validator(mode="after")
    def inject_defaults(self) -> Self:
        has_temporal_key = self.temporal.api_key and self.temporal.api_key.get_secret_value()
        has_mistral_key = self.common.mistral_api_key and self.common.mistral_api_key.get_secret_value()
        if not has_temporal_key and has_mistral_key:
            self.temporal.api_key = self.common.mistral_api_key
        return self


def _get_or_load_config() -> AppConfig:
    """Read and initialize the application configuration."""
    # Load configuration from environment/file
    config = AppConfig()

    # Set OTEL_EXPORTER_OTLP_CERTIFICATE if CA_BUNDLE is set to enable TLS verification for OpenTelemetry
    if config.common.ca_bundle is not None:
        os.environ["OTEL_EXPORTER_OTLP_CERTIFICATE"] = config.common.ca_bundle

    # Set OTEL_EXPORTER_OTLP_HEADERS if Mistral API key is available
    if config.otel_headers is not None:
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = config.otel_headers

    # Set up structured logging with OpenTelemetry trace injection if enabled
    if not structlog.is_configured():
        setup_logging(
            log_level=config.common.log_level,
            log_format=config.common.log_format,
            app_version=config.common.app_version,
            inject_otel_trace=config.common.otel_enabled and config.common.otel_inject_logs,
            extra_config=[
                # noisy
                LoggerConfig(
                    name="httpx",
                    level=LogLevel.WARNING,
                ),
                LoggerConfig(
                    name="asyncio",
                    level=LogLevel.WARNING,
                ),
            ],
        )

    logger.info("Configuration loaded", config=config.model_dump())
    return config


config = _get_or_load_config()
