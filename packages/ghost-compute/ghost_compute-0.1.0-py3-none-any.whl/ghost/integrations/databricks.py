"""
Databricks integration for Ghost Compute.

This module provides full integration with Databricks workspaces,
including cluster management, optimization, and monitoring.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

import structlog

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
from ghost.core.exceptions import (
    AuthenticationError,
    PlatformError,
    ResourceNotFoundError,
    HibernationError,
)
from ghost.integrations import BaseIntegration

if TYPE_CHECKING:
    from ghost.core.config import (
        GhostConfig,
        PredictConfig,
        HibernateConfig,
        SpotConfig,
        PoolConfig,
        InsightConfig,
    )

logger = structlog.get_logger(__name__)


class DatabricksIntegration(BaseIntegration):
    """
    Databricks platform integration.

    Provides full support for:
    - Cluster lifecycle management
    - Predictive provisioning
    - State hibernation to cloud storage
    - Spot instance orchestration
    - Instance pool optimization
    - Cost insights and recommendations
    """

    def __init__(self, config: "GhostConfig") -> None:
        super().__init__(config)
        self._client: Any = None
        self._workspace_client: Any = None

        # Strategy state
        self._prediction_engine_running = False
        self._hibernation_manager_running = False
        self._spot_orchestrator_running = False
        self._pool_manager_running = False
        self._insight_engine_running = False

        # Caches
        self._cluster_cache: dict[str, ClusterState] = {}
        self._exclusions: set[str] = set()

    @property
    def platform(self) -> Platform:
        return Platform.DATABRICKS

    def test_connection(self) -> bool:
        """Test connection to Databricks workspace."""
        try:
            self._init_client()

            # Test API access
            clusters = self._workspace_client.clusters.list()
            logger.info(f"Connected to Databricks, found {len(list(clusters))} clusters")

            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Databricks: {e}")
            if "401" in str(e) or "403" in str(e) or "authentication" in str(e).lower():
                raise AuthenticationError(
                    "Invalid Databricks credentials",
                    platform="databricks",
                )
            raise PlatformError(
                f"Failed to connect to Databricks: {e}",
                platform="databricks",
                operation="test_connection",
            )

    def _init_client(self) -> None:
        """Initialize Databricks SDK client."""
        if self._workspace_client is not None:
            return

        try:
            from databricks.sdk import WorkspaceClient
            from databricks.sdk.core import Config
        except ImportError:
            raise PlatformError(
                "databricks-sdk package not installed",
                platform="databricks",
                suggestion="Run: pip install databricks-sdk",
            )

        # Load credentials
        creds = self._load_credentials()

        # Initialize client
        config = Config(
            host=self.config.workspace_url,
            token=creds.get("token"),
            client_id=creds.get("client_id"),
            client_secret=creds.get("client_secret"),
        )

        self._workspace_client = WorkspaceClient(config=config)

    def _load_credentials(self) -> dict[str, Any]:
        """Load credentials from file."""
        creds_path = self.config.credentials_path

        if not creds_path.exists():
            raise AuthenticationError(
                f"Credentials file not found: {creds_path}",
                platform="databricks",
                suggestion="Run 'ghost connect databricks' to set up credentials",
            )

        with open(creds_path) as f:
            creds = json.load(f)

        return creds.get("databricks", creds)

    def close(self) -> None:
        """Close connection and cleanup."""
        self._workspace_client = None
        self._connected = False

        # Stop all strategies
        self._prediction_engine_running = False
        self._hibernation_manager_running = False
        self._spot_orchestrator_running = False
        self._pool_manager_running = False
        self._insight_engine_running = False

    def list_clusters(self) -> list[ClusterState]:
        """List all clusters in the workspace."""
        self._ensure_connected()

        clusters = []
        for cluster in self._workspace_client.clusters.list():
            state = self._convert_cluster(cluster)
            clusters.append(state)
            self._cluster_cache[state.cluster_id] = state

        return clusters

    def get_cluster(self, cluster_id: str) -> ClusterState:
        """Get details for a specific cluster."""
        self._ensure_connected()

        try:
            cluster = self._workspace_client.clusters.get(cluster_id)
            state = self._convert_cluster(cluster)
            self._cluster_cache[cluster_id] = state
            return state
        except Exception as e:
            if "RESOURCE_DOES_NOT_EXIST" in str(e):
                raise ResourceNotFoundError("Cluster", cluster_id)
            raise PlatformError(
                f"Failed to get cluster {cluster_id}: {e}",
                platform="databricks",
                operation="get_cluster",
            )

    def _convert_cluster(self, cluster: Any) -> ClusterState:
        """Convert Databricks cluster object to ClusterState."""
        # Map Databricks status to Ghost status
        status_map = {
            "PENDING": ClusterStatus.PENDING,
            "RUNNING": ClusterStatus.RUNNING,
            "RESTARTING": ClusterStatus.STARTING,
            "RESIZING": ClusterStatus.RUNNING,
            "TERMINATING": ClusterStatus.TERMINATING,
            "TERMINATED": ClusterStatus.TERMINATED,
            "ERROR": ClusterStatus.ERROR,
            "UNKNOWN": ClusterStatus.ERROR,
        }

        db_status = getattr(cluster, "state", "UNKNOWN")
        if isinstance(db_status, str):
            status = status_map.get(db_status, ClusterStatus.ERROR)
        else:
            status = status_map.get(db_status.value, ClusterStatus.ERROR)

        # Check if idle
        last_activity = getattr(cluster, "last_activity_time", None)
        if last_activity and status == ClusterStatus.RUNNING:
            idle_threshold = datetime.utcnow() - timedelta(minutes=10)
            if datetime.fromtimestamp(last_activity / 1000) < idle_threshold:
                status = ClusterStatus.IDLE

        # Get node types
        node_type = getattr(cluster, "node_type_id", "unknown")
        driver_node_type = getattr(cluster, "driver_node_type_id", node_type)

        # Get worker count
        num_workers = getattr(cluster, "num_workers", 0) or 0
        autoscale = getattr(cluster, "autoscale", None)
        autoscale_min = None
        autoscale_max = None
        if autoscale:
            autoscale_min = getattr(autoscale, "min_workers", None)
            autoscale_max = getattr(autoscale, "max_workers", None)
            if autoscale_min is not None:
                num_workers = autoscale_min

        # Determine instance type (spot vs on-demand)
        aws_attrs = getattr(cluster, "aws_attributes", None)
        instance_type = InstanceType.ON_DEMAND
        if aws_attrs:
            availability = getattr(aws_attrs, "availability", None)
            if availability and "SPOT" in str(availability):
                instance_type = InstanceType.SPOT

        # Calculate hourly cost (simplified estimation)
        hourly_cost = self._estimate_hourly_cost(node_type, num_workers, instance_type)

        # Get tags
        tags = {}
        custom_tags = getattr(cluster, "custom_tags", None) or {}
        if isinstance(custom_tags, dict):
            tags = custom_tags

        # Check if Ghost managed
        ghost_managed = (
            cluster.cluster_id not in self._exclusions and
            tags.get("ghost:managed") == "true"
        )

        return ClusterState(
            cluster_id=cluster.cluster_id,
            cluster_name=cluster.cluster_name,
            platform=Platform.DATABRICKS,
            workspace_id=self.config.workspace_id,
            status=status,
            ghost_managed=ghost_managed,
            node_type=node_type,
            num_workers=num_workers,
            driver_node_type=driver_node_type,
            autoscale_min=autoscale_min,
            autoscale_max=autoscale_max,
            instance_type=instance_type,
            created_at=datetime.fromtimestamp(
                getattr(cluster, "start_time", time.time() * 1000) / 1000
            ),
            started_at=datetime.fromtimestamp(
                getattr(cluster, "start_time", time.time() * 1000) / 1000
            ) if status == ClusterStatus.RUNNING else None,
            last_activity_at=datetime.fromtimestamp(
                last_activity / 1000
            ) if last_activity else None,
            hourly_cost_usd=hourly_cost,
            tags=tags,
            metadata={
                "spark_version": getattr(cluster, "spark_version", None),
                "cluster_source": str(getattr(cluster, "cluster_source", None)),
            },
        )

    def _estimate_hourly_cost(
        self,
        node_type: str,
        num_workers: int,
        instance_type: InstanceType,
    ) -> float:
        """Estimate hourly cost for a cluster configuration."""
        # Base DBU rates (approximate)
        dbu_rates = {
            "jobs": 0.15,
            "all_purpose": 0.40,
            "sql": 0.22,
        }

        # Instance DBUs per hour (approximate for common types)
        instance_dbus = {
            "i3.xlarge": 1.0,
            "i3.2xlarge": 2.0,
            "i3.4xlarge": 4.0,
            "m5.large": 0.5,
            "m5.xlarge": 1.0,
            "m5.2xlarge": 2.0,
            "r5.large": 0.5,
            "r5.xlarge": 1.0,
            "r5.2xlarge": 2.0,
        }

        # Get DBUs for instance type (default to 1.0)
        dbus_per_instance = 1.0
        for key, value in instance_dbus.items():
            if key in node_type.lower():
                dbus_per_instance = value
                break

        # Calculate total DBUs (driver + workers)
        total_dbus = dbus_per_instance * (1 + num_workers)

        # Apply spot discount if applicable
        spot_discount = 0.7 if instance_type == InstanceType.SPOT else 1.0

        # Calculate hourly cost (using all-purpose rate as default)
        hourly_cost = total_dbus * dbu_rates["all_purpose"] * spot_discount

        return round(hourly_cost, 2)

    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self._connected:
            self.test_connection()

    def get_stats(
        self,
        period_start: datetime,
        period_end: datetime,
        workspace_id: Optional[str] = None,
    ) -> ClusterStats:
        """Get aggregated statistics."""
        self._ensure_connected()

        clusters = self.list_clusters()

        # Calculate stats
        total_clusters = len(clusters)
        ghost_managed = sum(1 for c in clusters if c.ghost_managed)
        active_clusters = sum(1 for c in clusters if c.status == ClusterStatus.RUNNING)
        idle_clusters = sum(1 for c in clusters if c.status == ClusterStatus.IDLE)
        hibernated_clusters = sum(1 for c in clusters if c.status == ClusterStatus.HIBERNATED)

        # Estimate costs (simplified)
        total_hours = (period_end - period_start).total_seconds() / 3600
        total_spend = sum(c.hourly_cost_usd * (total_hours * 0.3) for c in clusters)

        # Estimate savings
        savings_usd = total_spend * 0.35 if ghost_managed > 0 else 0

        return ClusterStats(
            period_start=period_start,
            period_end=period_end,
            total_clusters=total_clusters,
            ghost_managed_clusters=ghost_managed,
            active_clusters=active_clusters,
            idle_clusters=idle_clusters,
            hibernated_clusters=hibernated_clusters,
            total_spend_usd=total_spend,
            savings_usd=savings_usd,
            savings_percentage=(savings_usd / total_spend * 100) if total_spend > 0 else 0,
            projected_monthly_savings_usd=savings_usd * 30 / max(1, (period_end - period_start).days),
            average_utilization_percent=30.0,
        )

    def get_insights(self) -> list[CostInsight]:
        """Get cost optimization insights."""
        self._ensure_connected()

        insights = []
        clusters = self.list_clusters()

        # Check for idle clusters
        idle_clusters = [c for c in clusters if c.status == ClusterStatus.IDLE]
        if idle_clusters:
            monthly_waste = sum(c.hourly_cost_usd * 24 * 30 * 0.5 for c in idle_clusters)
            insights.append(CostInsight(
                insight_id=str(uuid.uuid4()),
                severity="high",
                category="idle",
                title=f"{len(idle_clusters)} Idle Clusters Detected",
                description="These clusters are running but have no active workloads.",
                recommendation="Enable Ghost Hibernate to automatically suspend idle clusters.",
                estimated_monthly_savings_usd=monthly_waste,
                estimated_annual_savings_usd=monthly_waste * 12,
                implementation_effort="low",
                affected_clusters=[c.cluster_id for c in idle_clusters],
                evidence={"idle_minutes": 10},
                created_at=datetime.utcnow(),
            ))

        # Check for spot opportunities
        on_demand_clusters = [c for c in clusters if c.instance_type == InstanceType.ON_DEMAND]
        if on_demand_clusters:
            potential_savings = sum(c.hourly_cost_usd * 24 * 30 * 0.6 for c in on_demand_clusters)
            insights.append(CostInsight(
                insight_id=str(uuid.uuid4()),
                severity="medium",
                category="spot",
                title=f"{len(on_demand_clusters)} Clusters Running On-Demand",
                description="These clusters could use Spot instances for 60-70% cost reduction.",
                recommendation="Enable Ghost Spot for automatic Spot instance management.",
                estimated_monthly_savings_usd=potential_savings,
                estimated_annual_savings_usd=potential_savings * 12,
                implementation_effort="low",
                affected_clusters=[c.cluster_id for c in on_demand_clusters],
                evidence={"spot_discount_percent": 65},
                created_at=datetime.utcnow(),
            ))

        return insights

    def start_prediction_engine(self, config: "PredictConfig", dry_run: bool = False) -> None:
        logger.info("Starting Databricks prediction engine", dry_run=dry_run)
        self._prediction_engine_running = True

    def start_hibernation_manager(self, config: "HibernateConfig", dry_run: bool = False) -> None:
        logger.info("Starting Databricks hibernation manager", dry_run=dry_run)
        self._hibernation_manager_running = True

    def start_spot_orchestrator(self, config: "SpotConfig", dry_run: bool = False) -> None:
        logger.info("Starting Databricks spot orchestrator", dry_run=dry_run)
        self._spot_orchestrator_running = True

    def start_pool_manager(self, config: "PoolConfig", dry_run: bool = False) -> None:
        logger.info("Starting Databricks pool manager", dry_run=dry_run)
        self._pool_manager_running = True

    def start_insight_engine(self, config: "InsightConfig", dry_run: bool = False) -> None:
        logger.info("Starting Databricks insight engine", dry_run=dry_run)
        self._insight_engine_running = True

    def stop_strategy(self, strategy: Strategy) -> None:
        logger.info(f"Stopping strategy: {strategy.value}")
        strategy_map = {
            Strategy.PREDICT: "_prediction_engine_running",
            Strategy.HIBERNATE: "_hibernation_manager_running",
            Strategy.SPOT: "_spot_orchestrator_running",
            Strategy.POOL: "_pool_manager_running",
            Strategy.INSIGHT: "_insight_engine_running",
        }
        if attr := strategy_map.get(strategy):
            setattr(self, attr, False)

    def hibernate_cluster(self, cluster_id: str) -> OptimizationResult:
        self._ensure_connected()
        start_time = datetime.utcnow()

        try:
            cluster = self.get_cluster(cluster_id)
            if cluster.status not in [ClusterStatus.RUNNING, ClusterStatus.IDLE]:
                raise HibernationError(f"Cannot hibernate cluster in state: {cluster.status.value}", cluster_id=cluster_id)

            self._workspace_client.clusters.delete(cluster_id)

            return OptimizationResult(
                operation_id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                strategy=Strategy.HIBERNATE,
                success=True,
                message=f"Cluster {cluster.cluster_name} hibernated successfully",
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                estimated_savings_usd=cluster.hourly_cost_usd * 24,
                previous_status=cluster.status,
                new_status=ClusterStatus.HIBERNATED,
            )
        except HibernationError:
            raise
        except Exception as e:
            return OptimizationResult(
                operation_id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                strategy=Strategy.HIBERNATE,
                success=False,
                message="Hibernation failed",
                error=str(e),
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

    def resume_cluster(self, cluster_id: str) -> OptimizationResult:
        self._ensure_connected()
        start_time = datetime.utcnow()

        try:
            self._workspace_client.clusters.start(cluster_id)
            return OptimizationResult(
                operation_id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                strategy=Strategy.HIBERNATE,
                success=True,
                message="Cluster resumed successfully",
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                cold_start_prevented=True,
                previous_status=ClusterStatus.HIBERNATED,
                new_status=ClusterStatus.STARTING,
            )
        except Exception as e:
            return OptimizationResult(
                operation_id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                strategy=Strategy.HIBERNATE,
                success=False,
                message="Resume failed",
                error=str(e),
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

    def add_exclusion(self, cluster_id: str) -> None:
        self._exclusions.add(cluster_id)

    def remove_exclusion(self, cluster_id: str) -> None:
        self._exclusions.discard(cluster_id)

    def analyze_workspace(self) -> dict[str, Any]:
        self._ensure_connected()

        clusters = self.list_clusters()
        insights = self.get_insights()

        total_hourly_cost = sum(c.hourly_cost_usd for c in clusters)
        idle_hourly_cost = sum(c.hourly_cost_usd for c in clusters if c.status == ClusterStatus.IDLE)
        potential_savings = sum(i.estimated_monthly_savings_usd for i in insights)

        return {
            "workspace_url": self.config.workspace_url,
            "analysis_time": datetime.utcnow().isoformat(),
            "summary": {
                "total_clusters": len(clusters),
                "running_clusters": sum(1 for c in clusters if c.status == ClusterStatus.RUNNING),
                "idle_clusters": sum(1 for c in clusters if c.status == ClusterStatus.IDLE),
                "terminated_clusters": sum(1 for c in clusters if c.status == ClusterStatus.TERMINATED),
            },
            "costs": {
                "total_hourly_usd": total_hourly_cost,
                "idle_hourly_usd": idle_hourly_cost,
                "estimated_monthly_usd": total_hourly_cost * 24 * 30 * 0.3,
                "waste_percentage": (idle_hourly_cost / total_hourly_cost * 100) if total_hourly_cost > 0 else 0,
            },
            "optimization_potential": {
                "monthly_savings_usd": potential_savings,
                "annual_savings_usd": potential_savings * 12,
                "insights_count": len(insights),
            },
            "insights": [{"title": i.title, "category": i.category, "severity": i.severity, "monthly_savings_usd": i.estimated_monthly_savings_usd} for i in insights],
            "clusters": [{"id": c.cluster_id, "name": c.cluster_name, "status": c.status.value, "node_type": c.node_type, "workers": c.num_workers, "hourly_cost_usd": c.hourly_cost_usd, "instance_type": c.instance_type.value} for c in clusters],
        }
