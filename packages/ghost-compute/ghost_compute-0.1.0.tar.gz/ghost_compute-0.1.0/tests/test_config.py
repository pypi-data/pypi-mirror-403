"""
Tests for Ghost configuration.
"""

import pytest
import tempfile
from pathlib import Path

from ghost.core.config import (
    GhostConfig,
    PredictConfig,
    HibernateConfig,
    SpotConfig,
    PoolConfig,
    InsightConfig,
    StrategiesConfig,
    ExclusionRule,
)
from ghost.core.models import Platform, Strategy
from ghost.core.exceptions import ConfigurationError


class TestPredictConfig:
    def test_defaults(self):
        config = PredictConfig()
        assert config.enabled is True
        assert config.lookahead_minutes == 60
        assert config.confidence_threshold == 0.8

    def test_custom_values(self):
        config = PredictConfig(
            enabled=False,
            lookahead_minutes=120,
            confidence_threshold=0.9,
        )
        assert config.enabled is False
        assert config.lookahead_minutes == 120


class TestHibernateConfig:
    def test_defaults(self):
        config = HibernateConfig()
        assert config.enabled is True
        assert config.idle_timeout_minutes == 10
        assert config.storage_backend == "s3"

    def test_storage_backend_validation(self):
        # Valid backends
        for backend in ["s3", "gcs", "adls", "local"]:
            config = HibernateConfig(storage_backend=backend)
            assert config.storage_backend == backend


class TestSpotConfig:
    def test_defaults(self):
        config = SpotConfig()
        assert config.enabled is True
        assert config.max_spot_percentage == 80
        assert config.fallback_to_ondemand is True

    def test_spot_percentage_validation(self):
        # 0 is valid (disabled)
        config = SpotConfig(max_spot_percentage=0)
        assert config.max_spot_percentage == 0

        # 20+ is valid
        config = SpotConfig(max_spot_percentage=50)
        assert config.max_spot_percentage == 50


class TestStrategiesConfig:
    def test_get_enabled_strategies(self):
        config = StrategiesConfig()
        enabled = config.get_enabled_strategies()

        # All enabled by default
        assert Strategy.PREDICT in enabled
        assert Strategy.HIBERNATE in enabled
        assert Strategy.SPOT in enabled
        assert Strategy.POOL in enabled
        assert Strategy.INSIGHT in enabled

    def test_get_enabled_strategies_partial(self):
        config = StrategiesConfig(
            predict=PredictConfig(enabled=False),
            hibernate=HibernateConfig(enabled=True),
            spot=SpotConfig(enabled=False),
        )
        enabled = config.get_enabled_strategies()

        assert Strategy.PREDICT not in enabled
        assert Strategy.HIBERNATE in enabled
        assert Strategy.SPOT not in enabled


class TestGhostConfig:
    def test_defaults(self):
        config = GhostConfig()
        assert config.platform == Platform.DATABRICKS
        assert config.dry_run is False
        assert config.log_level == "INFO"

    def test_from_yaml(self):
        yaml_content = """
platform: emr
workspace_url: https://example.com
dry_run: true
strategies:
  predict:
    enabled: true
    lookahead_minutes: 90
  hibernate:
    enabled: false
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            config = GhostConfig.from_yaml(f.name)

            assert config.platform == Platform.EMR
            assert config.workspace_url == "https://example.com"
            assert config.dry_run is True
            assert config.strategies.predict.enabled is True
            assert config.strategies.predict.lookahead_minutes == 90
            assert config.strategies.hibernate.enabled is False

    def test_from_yaml_file_not_found(self):
        with pytest.raises(ConfigurationError):
            GhostConfig.from_yaml("/nonexistent/path.yaml")

    def test_is_cluster_excluded_by_id(self):
        config = GhostConfig(
            exclusions=[ExclusionRule(cluster_id="cluster-123")]
        )

        assert config.is_cluster_excluded("cluster-123", "test", {}) is True
        assert config.is_cluster_excluded("cluster-456", "test", {}) is False

    def test_is_cluster_excluded_by_name_pattern(self):
        config = GhostConfig(
            exclusions=[ExclusionRule(cluster_name="production-*")]
        )

        assert config.is_cluster_excluded("c1", "production-main", {}) is True
        assert config.is_cluster_excluded("c2", "production-backup", {}) is True
        assert config.is_cluster_excluded("c3", "dev-main", {}) is False

    def test_is_cluster_excluded_by_tag(self):
        config = GhostConfig(
            exclusions=[ExclusionRule(tag="ghost:exclude")]
        )

        assert config.is_cluster_excluded("c1", "test", {"ghost:exclude": "true"}) is True
        assert config.is_cluster_excluded("c2", "test", {"other": "tag"}) is False

    def test_is_cluster_excluded_by_tag_value(self):
        config = GhostConfig(
            exclusions=[ExclusionRule(tag="env=production")]
        )

        assert config.is_cluster_excluded("c1", "test", {"env": "production"}) is True
        assert config.is_cluster_excluded("c2", "test", {"env": "dev"}) is False
