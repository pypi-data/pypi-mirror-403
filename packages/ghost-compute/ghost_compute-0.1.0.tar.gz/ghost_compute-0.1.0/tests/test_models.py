"""
Tests for Ghost core models.
"""

import pytest
from datetime import datetime

from ghost.core.models import (
    Platform,
    Strategy,
    ClusterState,
    ClusterStatus,
    ClusterStats,
    InstanceType,
    OptimizationResult,
    CostInsight,
)


class TestPlatform:
    def test_platform_values(self):
        assert Platform.DATABRICKS.value == "databricks"
        assert Platform.EMR.value == "emr"
        assert Platform.SYNAPSE.value == "synapse"
        assert Platform.DATAPROC.value == "dataproc"

    def test_platform_from_string(self):
        assert Platform("databricks") == Platform.DATABRICKS


class TestStrategy:
    def test_strategy_values(self):
        assert Strategy.PREDICT.value == "predict"
        assert Strategy.HIBERNATE.value == "hibernate"
        assert Strategy.POOL.value == "pool"
        assert Strategy.SPOT.value == "spot"
        assert Strategy.INSIGHT.value == "insight"


class TestClusterState:
    def test_cluster_state_creation(self):
        state = ClusterState(
            cluster_id="cluster-123",
            cluster_name="test-cluster",
            platform=Platform.DATABRICKS,
            status=ClusterStatus.RUNNING,
            node_type="i3.xlarge",
            num_workers=4,
            created_at=datetime.utcnow(),
            hourly_cost_usd=2.50,
        )

        assert state.cluster_id == "cluster-123"
        assert state.cluster_name == "test-cluster"
        assert state.platform == Platform.DATABRICKS
        assert state.status == ClusterStatus.RUNNING
        assert state.num_workers == 4
        assert state.hourly_cost_usd == 2.50
        assert state.ghost_managed is False

    def test_cluster_state_with_optional_fields(self):
        state = ClusterState(
            cluster_id="cluster-456",
            cluster_name="autoscale-cluster",
            platform=Platform.EMR,
            status=ClusterStatus.IDLE,
            node_type="m5.xlarge",
            num_workers=2,
            autoscale_min=2,
            autoscale_max=10,
            instance_type=InstanceType.SPOT,
            created_at=datetime.utcnow(),
            hourly_cost_usd=1.20,
            tags={"env": "dev", "team": "data"},
        )

        assert state.autoscale_min == 2
        assert state.autoscale_max == 10
        assert state.instance_type == InstanceType.SPOT
        assert state.tags["env"] == "dev"


class TestClusterStats:
    def test_cluster_stats_creation(self):
        stats = ClusterStats(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            total_clusters=10,
            ghost_managed_clusters=6,
            active_clusters=4,
            idle_clusters=2,
            total_spend_usd=5000.00,
            savings_usd=1500.00,
        )

        assert stats.total_clusters == 10
        assert stats.ghost_managed_clusters == 6
        assert stats.total_spend_usd == 5000.00
        assert stats.savings_usd == 1500.00

    def test_cluster_stats_defaults(self):
        stats = ClusterStats(
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow(),
        )

        assert stats.total_clusters == 0
        assert stats.savings_percentage == 0.0
        assert stats.cold_starts_prevented == 0


class TestOptimizationResult:
    def test_success_result(self):
        result = OptimizationResult(
            operation_id="op-123",
            cluster_id="cluster-123",
            strategy=Strategy.HIBERNATE,
            success=True,
            message="Cluster hibernated successfully",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=5.5,
            estimated_savings_usd=24.00,
        )

        assert result.success is True
        assert result.strategy == Strategy.HIBERNATE
        assert result.estimated_savings_usd == 24.00
        assert result.error is None

    def test_failure_result(self):
        result = OptimizationResult(
            operation_id="op-456",
            cluster_id="cluster-456",
            strategy=Strategy.SPOT,
            success=False,
            message="Operation failed",
            error="Insufficient spot capacity",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=2.0,
        )

        assert result.success is False
        assert result.error == "Insufficient spot capacity"


class TestCostInsight:
    def test_cost_insight_creation(self):
        from ghost.core.models import InsightSeverity, InsightCategory

        insight = CostInsight(
            insight_id="insight-123",
            severity=InsightSeverity.HIGH,
            category=InsightCategory.IDLE_RESOURCES,
            title="5 Idle Clusters Detected",
            description="These clusters are running but idle.",
            recommendation="Enable Ghost Hibernate.",
            estimated_monthly_savings_usd=2500.00,
            estimated_annual_savings_usd=30000.00,
            implementation_effort="low",
            affected_clusters=["c1", "c2", "c3", "c4", "c5"],
            created_at=datetime.utcnow(),
        )

        assert insight.severity == "high"  # Enum value is serialized as string
        assert insight.category == "idle_resources"
        assert insight.estimated_monthly_savings_usd == 2500.00
        assert len(insight.affected_clusters) == 5
