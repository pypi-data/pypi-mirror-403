"""
Tests for platform integrations.

These tests verify that platform integrations are properly structured
and can be instantiated. Full integration tests require actual cloud
credentials and are marked for skip unless explicitly enabled.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone

from ghost.core.models import Platform, Strategy, ClusterStatus, ClusterState
from ghost.core.config import GhostConfig
from ghost.core.exceptions import PlatformError


class TestEMRIntegration:
    """Tests for AWS EMR integration."""

    def test_emr_platform_property(self):
        """Test that EMR integration returns correct platform."""
        from ghost.integrations.emr import EMRIntegration

        config = GhostConfig(
            platform=Platform.EMR,
            platform_config={"region": "us-east-1"},
        )
        integration = EMRIntegration(config)
        assert integration.platform == Platform.EMR

    def test_emr_pricing_data_exists(self):
        """Test that EMR pricing data is defined."""
        from ghost.integrations.emr import EMR_INSTANCE_PRICING

        assert "m5.xlarge" in EMR_INSTANCE_PRICING
        assert "r5.xlarge" in EMR_INSTANCE_PRICING
        assert "i3.xlarge" in EMR_INSTANCE_PRICING

        # Verify pricing structure
        m5_pricing = EMR_INSTANCE_PRICING["m5.xlarge"]
        assert "on_demand" in m5_pricing
        assert "spot" in m5_pricing
        assert "emr" in m5_pricing
        assert m5_pricing["on_demand"] > 0
        assert m5_pricing["emr"] > 0
        assert m5_pricing["spot"] < m5_pricing["on_demand"]  # Spot should be cheaper

    def test_emr_exclusion_management(self):
        """Test EMR cluster exclusion management."""
        from ghost.integrations.emr import EMRIntegration

        config = GhostConfig(
            platform=Platform.EMR,
            platform_config={"region": "us-east-1"},
        )
        integration = EMRIntegration(config)

        cluster_id = "j-ABC123DEF456"
        integration.add_exclusion(cluster_id)
        assert cluster_id in integration._exclusions

        integration.remove_exclusion(cluster_id)
        assert cluster_id not in integration._exclusions

    def test_emr_strategy_state_tracking(self):
        """Test EMR strategy state tracking."""
        from ghost.integrations.emr import EMRIntegration

        config = GhostConfig(
            platform=Platform.EMR,
            platform_config={"region": "us-east-1"},
        )
        integration = EMRIntegration(config)

        # Verify initial state
        assert integration._prediction_engine_running is False
        assert integration._hibernation_manager_running is False
        assert integration._spot_orchestrator_running is False


class TestSynapseIntegration:
    """Tests for Azure Synapse integration."""

    def test_synapse_platform_property(self):
        """Test that Synapse integration returns correct platform."""
        from ghost.integrations.synapse import SynapseIntegration

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub-id"},
        )
        integration = SynapseIntegration(config)
        assert integration.platform == Platform.SYNAPSE

    def test_synapse_pricing_data_exists(self):
        """Test that Synapse pricing data is defined."""
        from ghost.integrations.synapse import SYNAPSE_SPARK_PRICING

        assert "Small" in SYNAPSE_SPARK_PRICING
        assert "Medium" in SYNAPSE_SPARK_PRICING
        assert "Large" in SYNAPSE_SPARK_PRICING
        assert "XLarge" in SYNAPSE_SPARK_PRICING
        assert "XXLarge" in SYNAPSE_SPARK_PRICING

        # Verify pricing structure
        medium_pricing = SYNAPSE_SPARK_PRICING["Medium"]
        assert "node_cost_per_hour" in medium_pricing
        assert "vcores" in medium_pricing
        assert "memory_gb" in medium_pricing
        assert medium_pricing["node_cost_per_hour"] > 0

        # Verify larger sizes cost more
        assert SYNAPSE_SPARK_PRICING["Large"]["node_cost_per_hour"] > SYNAPSE_SPARK_PRICING["Medium"]["node_cost_per_hour"]
        assert SYNAPSE_SPARK_PRICING["XLarge"]["node_cost_per_hour"] > SYNAPSE_SPARK_PRICING["Large"]["node_cost_per_hour"]

    def test_synapse_status_conversion(self):
        """Test Synapse pool state to Ghost status conversion."""
        from ghost.integrations.synapse import SynapseIntegration

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub-id"},
        )
        integration = SynapseIntegration(config)

        # Test state mappings
        assert integration._convert_pool_state("Running") == ClusterStatus.RUNNING
        assert integration._convert_pool_state("Paused") == ClusterStatus.TERMINATED
        assert integration._convert_pool_state("Creating") == ClusterStatus.STARTING
        assert integration._convert_pool_state("Failed") == ClusterStatus.ERROR
        assert integration._convert_pool_state("UnknownState") == ClusterStatus.UNKNOWN

    def test_synapse_exclusion_management(self):
        """Test Synapse pool exclusion management."""
        from ghost.integrations.synapse import SynapseIntegration

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub"},
        )
        integration = SynapseIntegration(config)

        pool_id = "workspace/pool"
        integration.add_exclusion(pool_id)
        assert pool_id in integration._excluded_pools

        integration.remove_exclusion(pool_id)
        assert pool_id not in integration._excluded_pools


class TestDataprocIntegration:
    """Tests for Google Cloud Dataproc integration."""

    def test_dataproc_platform_property(self):
        """Test that Dataproc integration returns correct platform."""
        from ghost.integrations.dataproc import DataprocIntegration

        config = GhostConfig(
            platform=Platform.DATAPROC,
            platform_config={"project_id": "test-project", "region": "us-central1"},
        )
        integration = DataprocIntegration(config)
        assert integration.platform == Platform.DATAPROC

    def test_dataproc_pricing_data_exists(self):
        """Test that Dataproc pricing data is defined."""
        from ghost.integrations.dataproc import DATAPROC_PRICING

        assert "dataproc_premium" in DATAPROC_PRICING
        assert "n1-standard-4" in DATAPROC_PRICING
        assert "n1-standard-8" in DATAPROC_PRICING
        assert "n1-highmem-4" in DATAPROC_PRICING

        # Verify pricing structure
        n1_pricing = DATAPROC_PRICING["n1-standard-4"]
        assert "vcpus" in n1_pricing
        assert "memory_gb" in n1_pricing
        assert "on_demand_hourly" in n1_pricing
        assert "preemptible_hourly" in n1_pricing
        assert n1_pricing["on_demand_hourly"] > n1_pricing["preemptible_hourly"]

        # Verify Dataproc premium exists
        assert DATAPROC_PRICING["dataproc_premium"]["per_vcpu_hour"] > 0

    def test_dataproc_status_conversion(self):
        """Test Dataproc cluster state to Ghost status conversion."""
        from ghost.integrations.dataproc import DataprocIntegration

        config = GhostConfig(
            platform=Platform.DATAPROC,
            platform_config={"project_id": "test-project", "region": "us-central1"},
        )
        integration = DataprocIntegration(config)

        # Test state mappings
        assert integration._convert_cluster_state("RUNNING") == ClusterStatus.RUNNING
        assert integration._convert_cluster_state("CREATING") == ClusterStatus.STARTING
        assert integration._convert_cluster_state("STOPPED") == ClusterStatus.TERMINATED
        assert integration._convert_cluster_state("ERROR") == ClusterStatus.ERROR
        assert integration._convert_cluster_state("UNKNOWN") == ClusterStatus.UNKNOWN

    def test_dataproc_exclusion_management(self):
        """Test Dataproc cluster exclusion management."""
        from ghost.integrations.dataproc import DataprocIntegration

        config = GhostConfig(
            platform=Platform.DATAPROC,
            platform_config={"project_id": "test-project"},
        )
        integration = DataprocIntegration(config)

        cluster_id = "project/region/cluster"
        integration.add_exclusion(cluster_id)
        assert cluster_id in integration._excluded_clusters

        integration.remove_exclusion(cluster_id)
        assert cluster_id not in integration._excluded_clusters


class TestIntegrationFactory:
    """Tests for the integration factory function."""

    def test_get_databricks_integration(self):
        """Test getting Databricks integration."""
        from ghost.integrations import get_integration
        from ghost.integrations.databricks import DatabricksIntegration

        config = GhostConfig(
            platform=Platform.DATABRICKS,
            workspace_url="https://test.cloud.databricks.com",
        )
        integration = get_integration(Platform.DATABRICKS, config)
        assert isinstance(integration, DatabricksIntegration)

    def test_get_emr_integration(self):
        """Test getting EMR integration."""
        from ghost.integrations import get_integration
        from ghost.integrations.emr import EMRIntegration

        config = GhostConfig(
            platform=Platform.EMR,
            platform_config={"region": "us-east-1"},
        )
        integration = get_integration(Platform.EMR, config)
        assert isinstance(integration, EMRIntegration)

    def test_get_synapse_integration(self):
        """Test getting Synapse integration."""
        from ghost.integrations import get_integration
        from ghost.integrations.synapse import SynapseIntegration

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub"},
        )
        integration = get_integration(Platform.SYNAPSE, config)
        assert isinstance(integration, SynapseIntegration)

    def test_get_dataproc_integration(self):
        """Test getting Dataproc integration."""
        from ghost.integrations import get_integration
        from ghost.integrations.dataproc import DataprocIntegration

        config = GhostConfig(
            platform=Platform.DATAPROC,
            platform_config={"project_id": "test-project"},
        )
        integration = get_integration(Platform.DATAPROC, config)
        assert isinstance(integration, DataprocIntegration)


class TestPlatformCostCalculations:
    """Tests for cost calculations across platforms."""

    def test_emr_pricing_completeness(self):
        """Test EMR pricing data completeness."""
        from ghost.integrations.emr import EMR_INSTANCE_PRICING

        # Verify all expected instance types have complete pricing
        for instance_type, pricing in EMR_INSTANCE_PRICING.items():
            assert "on_demand" in pricing, f"{instance_type} missing on_demand"
            assert "spot" in pricing, f"{instance_type} missing spot"
            assert "emr" in pricing, f"{instance_type} missing emr"

    def test_synapse_cost_estimation(self):
        """Test Synapse pool cost estimation."""
        from ghost.integrations.synapse import SynapseIntegration, SYNAPSE_SPARK_PRICING, SynapseSparkPool

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub"},
        )
        integration = SynapseIntegration(config)

        # Create test pool
        pool = SynapseSparkPool(
            name="test-pool",
            workspace_name="test-ws",
            resource_group="test-rg",
            subscription_id="test-sub",
            node_size="Medium",
            node_count=5,
            min_node_count=3,
            max_node_count=10,
            auto_scale_enabled=True,
            auto_pause_enabled=False,
            auto_pause_delay_minutes=15,
            state="Running",
            spark_version="3.3",
        )

        # Test cost estimation
        cost = integration._estimate_pool_cost(pool, hours=730)
        pricing = SYNAPSE_SPARK_PRICING["Medium"]
        expected_cost = pricing["node_cost_per_hour"] * 5 * 730
        assert cost == expected_cost

    def test_synapse_cost_with_autopause(self):
        """Test Synapse cost estimation with auto-pause enabled."""
        from ghost.integrations.synapse import SynapseIntegration, SYNAPSE_SPARK_PRICING, SynapseSparkPool

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub"},
        )
        integration = SynapseIntegration(config)

        # Create test pool with auto-pause
        pool = SynapseSparkPool(
            name="test-pool",
            workspace_name="test-ws",
            resource_group="test-rg",
            subscription_id="test-sub",
            node_size="Medium",
            node_count=5,
            min_node_count=3,
            max_node_count=10,
            auto_scale_enabled=True,
            auto_pause_enabled=True,  # Auto-pause enabled
            auto_pause_delay_minutes=15,
            state="Running",
            spark_version="3.3",
        )

        # Test cost estimation - should be ~40% of full cost due to auto-pause
        cost = integration._estimate_pool_cost(pool, hours=730)
        pricing = SYNAPSE_SPARK_PRICING["Medium"]
        full_cost = pricing["node_cost_per_hour"] * 5 * 730
        assert cost < full_cost  # Should be less due to auto-pause
        assert cost == full_cost * 0.4  # 40% utilization with auto-pause

    def test_dataproc_cost_calculation(self):
        """Test Dataproc cluster cost calculation."""
        from ghost.integrations.dataproc import DataprocIntegration, DATAPROC_PRICING, DataprocCluster

        config = GhostConfig(
            platform=Platform.DATAPROC,
            platform_config={"project_id": "test-project"},
        )
        integration = DataprocIntegration(config)

        # Create test cluster
        cluster = DataprocCluster(
            cluster_name="test-cluster",
            project_id="test-project",
            region="us-central1",
            zone="us-central1-a",
            state="RUNNING",
            master_machine_type="n1-standard-4",
            master_num_instances=1,
            worker_machine_type="n1-standard-4",
            worker_num_instances=4,
            preemptible_num_instances=0,
            secondary_worker_num_instances=0,
            image_version="2.0",
        )

        # Test cost calculation
        cost = integration._calculate_cluster_hourly_cost(cluster)

        # Verify cost includes Dataproc premium
        pricing = DATAPROC_PRICING["n1-standard-4"]
        premium = DATAPROC_PRICING["dataproc_premium"]["per_vcpu_hour"]

        # Master: 1 * (on_demand + premium * vcpus)
        # Workers: 4 * (on_demand + premium * vcpus)
        expected = (
            (pricing["on_demand_hourly"] + premium * pricing["vcpus"]) * 1 +  # Master
            (pricing["on_demand_hourly"] + premium * pricing["vcpus"]) * 4    # Workers
        )
        assert abs(cost - expected) < 0.01


class TestStrategyManagement:
    """Tests for strategy management across platforms."""

    def test_synapse_strategy_stop(self):
        """Test Synapse strategy stop tracking."""
        from ghost.integrations.synapse import SynapseIntegration

        config = GhostConfig(
            platform=Platform.SYNAPSE,
            platform_config={"subscription_id": "test-sub"},
        )
        integration = SynapseIntegration(config)

        # Stop should work even without active strategies
        integration.stop_strategy(Strategy.HIBERNATE)
        assert Strategy.HIBERNATE not in integration._active_strategies or not integration._active_strategies.get(Strategy.HIBERNATE)

    def test_dataproc_strategy_stop(self):
        """Test Dataproc strategy stop tracking."""
        from ghost.integrations.dataproc import DataprocIntegration

        config = GhostConfig(
            platform=Platform.DATAPROC,
            platform_config={"project_id": "test-project"},
        )
        integration = DataprocIntegration(config)

        integration.stop_strategy(Strategy.SPOT)
        assert Strategy.SPOT not in integration._active_strategies or not integration._active_strategies.get(Strategy.SPOT)


class TestCLIPlatforms:
    """Tests for CLI platform support."""

    def test_cli_platforms_command_exists(self):
        """Test that platforms command is available."""
        from ghost.cli.main import app, platforms
        assert platforms is not None

    def test_cli_connect_supports_all_platforms(self):
        """Test that connect command accepts all platforms."""
        from ghost.cli.main import connect
        # Just verify the function exists and has the right signature
        import inspect
        sig = inspect.signature(connect)
        params = list(sig.parameters.keys())
        assert "platform" in params
        assert "region" in params
        assert "subscription_id" in params
        assert "project_id" in params
