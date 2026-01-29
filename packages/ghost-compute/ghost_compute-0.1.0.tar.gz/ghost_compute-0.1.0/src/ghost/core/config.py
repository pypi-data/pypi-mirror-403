"""
Configuration management for Ghost Compute.

This module handles loading, validating, and providing access to Ghost configuration
from multiple sources: YAML files, environment variables, and programmatic settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ghost.core.models import Platform, Strategy
from ghost.core.exceptions import ConfigurationError


class PredictConfig(BaseModel):
    """Configuration for the Predict strategy."""

    enabled: bool = True
    lookahead_minutes: int = Field(default=60, ge=5, le=1440)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    min_historical_data_days: int = Field(default=7, ge=1)
    model_retrain_hours: int = Field(default=24, ge=1)
    warm_instances_per_pattern: int = Field(default=2, ge=1, le=10)


class HibernateConfig(BaseModel):
    """Configuration for the Hibernate strategy."""

    enabled: bool = True
    idle_timeout_minutes: int = Field(default=10, ge=1, le=120)
    storage_backend: str = Field(default="s3", pattern="^(s3|gcs|adls|local)$")
    storage_bucket: Optional[str] = None
    storage_prefix: str = "ghost-hibernate/"
    compression_enabled: bool = True
    encryption_enabled: bool = True
    max_state_size_gb: float = Field(default=100.0, ge=1.0)
    state_retention_days: int = Field(default=7, ge=1, le=90)


class SpotConfig(BaseModel):
    """Configuration for the Spot strategy."""

    enabled: bool = True
    max_spot_percentage: int = Field(default=80, ge=0, le=100)
    fallback_to_ondemand: bool = True
    interruption_buffer_seconds: int = Field(default=120, ge=30, le=600)
    diversification_enabled: bool = True
    max_instance_types: int = Field(default=5, ge=1, le=20)
    checkpoint_frequency_minutes: int = Field(default=5, ge=1, le=30)

    # Price constraints
    max_spot_price_percent_of_ondemand: int = Field(default=70, ge=10, le=100)

    @field_validator("max_spot_percentage")
    @classmethod
    def validate_spot_percentage(cls, v: int) -> int:
        if v > 0 and v < 20:
            raise ValueError("max_spot_percentage should be either 0 (disabled) or >= 20")
        return v


class PoolConfig(BaseModel):
    """Configuration for the Pool strategy."""

    enabled: bool = True
    cross_team_sharing: bool = True
    max_idle_instances: int = Field(default=10, ge=0, le=100)
    idle_instance_timeout_minutes: int = Field(default=60, ge=5, le=480)
    prewarmed_instance_types: list[str] = Field(default_factory=list)
    instance_refresh_hours: int = Field(default=24, ge=1, le=168)


class InsightConfig(BaseModel):
    """Configuration for the Insight strategy."""

    enabled: bool = True
    cost_alerts_enabled: bool = True
    alert_threshold_usd: float = Field(default=1000.0, ge=0)
    alert_threshold_percent_increase: float = Field(default=20.0, ge=0, le=100)
    daily_report_enabled: bool = True
    weekly_report_enabled: bool = True
    report_recipients: list[str] = Field(default_factory=list)
    anomaly_detection_enabled: bool = True
    recommendation_auto_apply: bool = False


class StrategiesConfig(BaseModel):
    """Combined configuration for all strategies."""

    predict: PredictConfig = Field(default_factory=PredictConfig)
    hibernate: HibernateConfig = Field(default_factory=HibernateConfig)
    spot: SpotConfig = Field(default_factory=SpotConfig)
    pool: PoolConfig = Field(default_factory=PoolConfig)
    insight: InsightConfig = Field(default_factory=InsightConfig)

    def get_enabled_strategies(self) -> list[Strategy]:
        """Return list of enabled strategies."""
        enabled = []
        if self.predict.enabled:
            enabled.append(Strategy.PREDICT)
        if self.hibernate.enabled:
            enabled.append(Strategy.HIBERNATE)
        if self.spot.enabled:
            enabled.append(Strategy.SPOT)
        if self.pool.enabled:
            enabled.append(Strategy.POOL)
        if self.insight.enabled:
            enabled.append(Strategy.INSIGHT)
        return enabled


class ExclusionRule(BaseModel):
    """Rule for excluding clusters from Ghost management."""

    cluster_name: Optional[str] = Field(
        None,
        description="Glob pattern for cluster names to exclude"
    )
    cluster_id: Optional[str] = Field(
        None,
        description="Specific cluster ID to exclude"
    )
    tag: Optional[str] = Field(
        None,
        description="Tag key or key=value to match for exclusion"
    )

    @field_validator("cluster_name", "cluster_id", "tag")
    @classmethod
    def at_least_one_required(cls, v: Optional[str], info: Any) -> Optional[str]:
        return v


class GhostConfig(BaseSettings):
    """
    Main Ghost configuration.

    Configuration can be loaded from:
    1. YAML file (ghost.yaml)
    2. Environment variables (GHOST_*)
    3. Programmatic settings

    Priority: programmatic > environment > file
    """

    model_config = SettingsConfigDict(
        env_prefix="GHOST_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    # Platform settings
    platform: Platform = Platform.DATABRICKS
    workspace_url: Optional[str] = None
    workspace_id: Optional[str] = None

    # Authentication
    api_key: Optional[str] = Field(None, description="Ghost API key for cloud features")
    credentials_path: Path = Field(
        default=Path.home() / ".ghost" / "credentials.json",
        description="Path to platform credentials"
    )

    # Strategies
    strategies: StrategiesConfig = Field(default_factory=StrategiesConfig)

    # Exclusions
    exclusions: list[ExclusionRule] = Field(default_factory=list)

    # Operational settings
    dry_run: bool = Field(
        default=False,
        description="If true, don't make any changes, just report what would happen"
    )
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    metrics_enabled: bool = True
    metrics_port: int = Field(default=9090, ge=1024, le=65535)

    # Advanced settings
    api_timeout_seconds: int = Field(default=30, ge=5, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    concurrent_operations: int = Field(default=5, ge=1, le=20)

    # Platform-specific configuration
    platform_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific settings (region, project_id, subscription_id, etc.)"
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "GhostConfig":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {path}",
                suggestion=f"Create a configuration file at {path} or specify a different path"
            )

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in configuration file: {e}",
                suggestion="Check the YAML syntax in your configuration file"
            )

        return cls(**data)

    @classmethod
    def discover(cls) -> "GhostConfig":
        """
        Discover and load configuration from standard locations.

        Searches in order:
        1. ./ghost.yaml
        2. ~/.ghost/config.yaml
        3. /etc/ghost/config.yaml
        4. Environment variables only
        """
        search_paths = [
            Path.cwd() / "ghost.yaml",
            Path.home() / ".ghost" / "config.yaml",
            Path("/etc/ghost/config.yaml"),
        ]

        for path in search_paths:
            if path.exists():
                return cls.from_yaml(path)

        # No config file found, use defaults + environment
        return cls()

    def is_cluster_excluded(self, cluster_id: str, cluster_name: str, tags: dict[str, str]) -> bool:
        """Check if a cluster matches any exclusion rules."""
        import fnmatch

        for rule in self.exclusions:
            if rule.cluster_id and rule.cluster_id == cluster_id:
                return True

            if rule.cluster_name and fnmatch.fnmatch(cluster_name, rule.cluster_name):
                return True

            if rule.tag:
                if "=" in rule.tag:
                    key, value = rule.tag.split("=", 1)
                    if tags.get(key) == value:
                        return True
                else:
                    if rule.tag in tags:
                        return True

        return False

    def validate_for_platform(self) -> None:
        """Validate configuration is complete for the specified platform."""
        if self.platform == Platform.DATABRICKS:
            if not self.workspace_url:
                raise ConfigurationError(
                    "workspace_url is required for Databricks",
                    config_key="workspace_url",
                    suggestion="Set GHOST_WORKSPACE_URL or add workspace_url to ghost.yaml"
                )

        elif self.platform == Platform.EMR:
            # EMR uses AWS credentials from profile/environment
            region = self.platform_config.get("region")
            if not region:
                import os
                if not os.environ.get("AWS_DEFAULT_REGION"):
                    raise ConfigurationError(
                        "AWS region is required for EMR",
                        config_key="platform_config.region",
                        suggestion="Set region in platform_config or AWS_DEFAULT_REGION environment variable"
                    )

        elif self.platform == Platform.SYNAPSE:
            subscription_id = self.platform_config.get("subscription_id")
            if not subscription_id:
                import os
                if not os.environ.get("AZURE_SUBSCRIPTION_ID"):
                    raise ConfigurationError(
                        "Azure subscription_id is required for Synapse",
                        config_key="platform_config.subscription_id",
                        suggestion="Set subscription_id in platform_config or AZURE_SUBSCRIPTION_ID environment variable"
                    )

        elif self.platform == Platform.DATAPROC:
            project_id = self.platform_config.get("project_id")
            if not project_id:
                import os
                if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
                    raise ConfigurationError(
                        "GCP project_id is required for Dataproc",
                        config_key="platform_config.project_id",
                        suggestion="Set project_id in platform_config or GOOGLE_CLOUD_PROJECT environment variable"
                    )

        # Check for credentials file (optional - some platforms use environment auth)
        if self.credentials_path.exists():
            pass  # Credentials file exists, good
        elif self.platform == Platform.DATABRICKS:
            # Databricks requires explicit credentials
            raise ConfigurationError(
                f"Credentials file not found: {self.credentials_path}",
                config_key="credentials_path",
                suggestion="Run 'ghost connect databricks' to set up platform credentials"
            )


def get_config() -> GhostConfig:
    """
    Get the current Ghost configuration.

    This is the recommended way to access configuration throughout the codebase.
    """
    return GhostConfig.discover()
