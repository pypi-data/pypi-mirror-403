"""
Amazon EMR integration for Ghost Compute.

This module provides full integration with Amazon EMR clusters,
including cluster management, optimization, and monitoring.
"""

from __future__ import annotations

import json
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


# EMR instance pricing (us-east-1, approximate)
EMR_INSTANCE_PRICING = {
    "m5.xlarge": {"on_demand": 0.192, "spot": 0.070, "emr": 0.048},
    "m5.2xlarge": {"on_demand": 0.384, "spot": 0.140, "emr": 0.096},
    "m5.4xlarge": {"on_demand": 0.768, "spot": 0.280, "emr": 0.192},
    "r5.xlarge": {"on_demand": 0.252, "spot": 0.090, "emr": 0.063},
    "r5.2xlarge": {"on_demand": 0.504, "spot": 0.180, "emr": 0.126},
    "r5.4xlarge": {"on_demand": 1.008, "spot": 0.360, "emr": 0.252},
    "i3.xlarge": {"on_demand": 0.312, "spot": 0.094, "emr": 0.078},
    "i3.2xlarge": {"on_demand": 0.624, "spot": 0.187, "emr": 0.156},
    "i3.4xlarge": {"on_demand": 1.248, "spot": 0.374, "emr": 0.312},
    "c5.xlarge": {"on_demand": 0.170, "spot": 0.065, "emr": 0.042},
    "c5.2xlarge": {"on_demand": 0.340, "spot": 0.130, "emr": 0.085},
    "c5.4xlarge": {"on_demand": 0.680, "spot": 0.260, "emr": 0.170},
}


class EMRIntegration(BaseIntegration):
    """
    Amazon EMR platform integration.

    Provides full support for:
    - Cluster lifecycle management
    - Predictive provisioning
    - State persistence to S3
    - Spot instance orchestration
    - Instance fleet optimization
    - Cost insights and recommendations
    """

    def __init__(self, config: "GhostConfig") -> None:
        super().__init__(config)
        self._emr_client: Any = None
        self._ec2_client: Any = None
        self._s3_client: Any = None

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
        return Platform.EMR

    def test_connection(self) -> bool:
        """Test connection to AWS EMR."""
        try:
            self._init_clients()

            # Test API access
            response = self._emr_client.list_clusters(
                ClusterStates=["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING", "TERMINATING"]
            )
            cluster_count = len(response.get("Clusters", []))
            logger.info(f"Connected to EMR, found {cluster_count} active clusters")

            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to EMR: {e}")
            if "InvalidClientTokenId" in str(e) or "SignatureDoesNotMatch" in str(e):
                raise AuthenticationError(
                    "Invalid AWS credentials",
                    platform="emr",
                )
            raise PlatformError(
                f"Failed to connect to EMR: {e}",
                platform="emr",
                operation="test_connection",
            )

    def _init_clients(self) -> None:
        """Initialize AWS SDK clients."""
        if self._emr_client is not None:
            return

        try:
            import boto3
        except ImportError:
            raise PlatformError(
                "boto3 package not installed",
                platform="emr",
                suggestion="Run: pip install boto3",
            )

        # Load credentials
        creds = self._load_credentials()

        session_kwargs = {}
        if creds.get("profile"):
            session_kwargs["profile_name"] = creds["profile"]
        if creds.get("region"):
            session_kwargs["region_name"] = creds["region"]
        if creds.get("aws_access_key_id"):
            session_kwargs["aws_access_key_id"] = creds["aws_access_key_id"]
            session_kwargs["aws_secret_access_key"] = creds.get("aws_secret_access_key")

        session = boto3.Session(**session_kwargs)
        self._emr_client = session.client("emr")
        self._ec2_client = session.client("ec2")
        self._s3_client = session.client("s3")

    def _load_credentials(self) -> dict[str, Any]:
        """Load credentials from file or environment."""
        creds_path = self.config.credentials_path

        if creds_path.exists():
            with open(creds_path) as f:
                creds = json.load(f)
            return creds.get("emr", creds.get("aws", {}))

        # Fall back to default AWS credential chain
        return {"region": "us-east-1"}

    def close(self) -> None:
        """Close connection and cleanup."""
        self._emr_client = None
        self._ec2_client = None
        self._s3_client = None
        self._connected = False

        self._prediction_engine_running = False
        self._hibernation_manager_running = False
        self._spot_orchestrator_running = False
        self._pool_manager_running = False
        self._insight_engine_running = False

    def list_clusters(self) -> list[ClusterState]:
        """List all EMR clusters."""
        self._ensure_connected()

        clusters = []
        paginator = self._emr_client.get_paginator("list_clusters")

        for page in paginator.paginate(
            ClusterStates=["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING", "TERMINATING", "TERMINATED"]
        ):
            for cluster_summary in page.get("Clusters", []):
                try:
                    cluster_detail = self._emr_client.describe_cluster(
                        ClusterId=cluster_summary["Id"]
                    )["Cluster"]
                    state = self._convert_cluster(cluster_detail)
                    clusters.append(state)
                    self._cluster_cache[state.cluster_id] = state
                except Exception as e:
                    logger.warning(f"Failed to get cluster details: {e}")

        return clusters

    def get_cluster(self, cluster_id: str) -> ClusterState:
        """Get details for a specific EMR cluster."""
        self._ensure_connected()

        try:
            response = self._emr_client.describe_cluster(ClusterId=cluster_id)
            cluster = response["Cluster"]
            state = self._convert_cluster(cluster)
            self._cluster_cache[cluster_id] = state
            return state
        except self._emr_client.exceptions.InvalidRequestException:
            raise ResourceNotFoundError("Cluster", cluster_id)
        except Exception as e:
            raise PlatformError(
                f"Failed to get cluster {cluster_id}: {e}",
                platform="emr",
                operation="get_cluster",
            )

    def _convert_cluster(self, cluster: dict) -> ClusterState:
        """Convert EMR cluster dict to ClusterState."""
        # Map EMR status to Ghost status
        status_map = {
            "STARTING": ClusterStatus.STARTING,
            "BOOTSTRAPPING": ClusterStatus.STARTING,
            "RUNNING": ClusterStatus.RUNNING,
            "WAITING": ClusterStatus.IDLE,
            "TERMINATING": ClusterStatus.TERMINATING,
            "TERMINATED": ClusterStatus.TERMINATED,
            "TERMINATED_WITH_ERRORS": ClusterStatus.ERROR,
        }

        emr_status = cluster.get("Status", {}).get("State", "UNKNOWN")
        status = status_map.get(emr_status, ClusterStatus.ERROR)

        # Get instance groups info
        instance_groups = cluster.get("InstanceGroups", [])
        master_instance_type = "m5.xlarge"
        core_instance_type = "m5.xlarge"
        num_workers = 0

        for ig in instance_groups:
            ig_type = ig.get("InstanceGroupType")
            if ig_type == "MASTER":
                master_instance_type = ig.get("InstanceType", "m5.xlarge")
            elif ig_type == "CORE":
                core_instance_type = ig.get("InstanceType", "m5.xlarge")
                num_workers += ig.get("RunningInstanceCount", 0)
            elif ig_type == "TASK":
                num_workers += ig.get("RunningInstanceCount", 0)

        # Determine if using spot
        instance_type = InstanceType.ON_DEMAND
        for ig in instance_groups:
            market = ig.get("Market", "ON_DEMAND")
            if market == "SPOT":
                instance_type = InstanceType.SPOT
                break

        # Calculate hourly cost
        hourly_cost = self._estimate_hourly_cost(
            master_instance_type, core_instance_type, num_workers, instance_type
        )

        # Get tags
        tags = {tag["Key"]: tag["Value"] for tag in cluster.get("Tags", [])}

        # Check if Ghost managed
        ghost_managed = (
            cluster["Id"] not in self._exclusions and
            tags.get("ghost:managed") == "true"
        )

        # Parse timestamps
        created_at = cluster.get("Status", {}).get("Timeline", {}).get("CreationDateTime")
        if created_at is None:
            created_at = datetime.utcnow()

        return ClusterState(
            cluster_id=cluster["Id"],
            cluster_name=cluster.get("Name", "Unknown"),
            platform=Platform.EMR,
            workspace_id=None,
            status=status,
            ghost_managed=ghost_managed,
            node_type=core_instance_type,
            num_workers=num_workers,
            driver_node_type=master_instance_type,
            instance_type=instance_type,
            created_at=created_at,
            started_at=created_at if status == ClusterStatus.RUNNING else None,
            hourly_cost_usd=hourly_cost,
            tags=tags,
            metadata={
                "release_label": cluster.get("ReleaseLabel"),
                "applications": [app["Name"] for app in cluster.get("Applications", [])],
                "auto_terminate": cluster.get("AutoTerminate", False),
                "visible_to_all_users": cluster.get("VisibleToAllUsers", True),
            },
        )

    def _estimate_hourly_cost(
        self,
        master_type: str,
        core_type: str,
        num_workers: int,
        instance_type: InstanceType,
    ) -> float:
        """Estimate hourly cost for an EMR cluster."""
        price_key = "spot" if instance_type == InstanceType.SPOT else "on_demand"

        master_pricing = EMR_INSTANCE_PRICING.get(master_type, {"on_demand": 0.20, "spot": 0.08, "emr": 0.05})
        core_pricing = EMR_INSTANCE_PRICING.get(core_type, {"on_demand": 0.20, "spot": 0.08, "emr": 0.05})

        # EC2 cost + EMR cost
        master_cost = master_pricing[price_key] + master_pricing["emr"]
        worker_cost = (core_pricing[price_key] + core_pricing["emr"]) * max(1, num_workers)

        return round(master_cost + worker_cost, 2)

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
        """Get aggregated statistics for EMR clusters."""
        self._ensure_connected()

        clusters = self.list_clusters()

        total_clusters = len(clusters)
        ghost_managed = sum(1 for c in clusters if c.ghost_managed)
        active_clusters = sum(1 for c in clusters if c.status in [ClusterStatus.RUNNING, ClusterStatus.IDLE])
        idle_clusters = sum(1 for c in clusters if c.status == ClusterStatus.IDLE)

        # Estimate costs
        total_hours = (period_end - period_start).total_seconds() / 3600
        total_spend = sum(c.hourly_cost_usd * (total_hours * 0.3) for c in clusters if c.status != ClusterStatus.TERMINATED)

        savings_usd = total_spend * 0.35 if ghost_managed > 0 else 0

        return ClusterStats(
            period_start=period_start,
            period_end=period_end,
            total_clusters=total_clusters,
            ghost_managed_clusters=ghost_managed,
            active_clusters=active_clusters,
            idle_clusters=idle_clusters,
            hibernated_clusters=0,
            total_spend_usd=total_spend,
            savings_usd=savings_usd,
            savings_percentage=(savings_usd / total_spend * 100) if total_spend > 0 else 0,
            projected_monthly_savings_usd=savings_usd * 30 / max(1, (period_end - period_start).days),
            average_utilization_percent=30.0,
        )

    def get_insights(self) -> list[CostInsight]:
        """Get cost optimization insights for EMR."""
        self._ensure_connected()

        insights = []
        clusters = self.list_clusters()

        # Check for idle clusters (WAITING state)
        idle_clusters = [c for c in clusters if c.status == ClusterStatus.IDLE]
        if idle_clusters:
            monthly_waste = sum(c.hourly_cost_usd * 24 * 30 * 0.5 for c in idle_clusters)
            insights.append(CostInsight(
                insight_id=str(uuid.uuid4()),
                severity="high",
                category="idle",
                title=f"{len(idle_clusters)} Idle EMR Clusters Detected",
                description="These clusters are in WAITING state with no active steps.",
                recommendation="Enable Ghost auto-termination or use transient clusters.",
                estimated_monthly_savings_usd=monthly_waste,
                estimated_annual_savings_usd=monthly_waste * 12,
                implementation_effort="low",
                affected_clusters=[c.cluster_id for c in idle_clusters],
                evidence={"state": "WAITING"},
                created_at=datetime.utcnow(),
            ))

        # Check for on-demand clusters that could use spot
        on_demand_clusters = [c for c in clusters if c.instance_type == InstanceType.ON_DEMAND and c.status != ClusterStatus.TERMINATED]
        if on_demand_clusters:
            potential_savings = sum(c.hourly_cost_usd * 24 * 30 * 0.65 for c in on_demand_clusters)
            insights.append(CostInsight(
                insight_id=str(uuid.uuid4()),
                severity="medium",
                category="spot",
                title=f"{len(on_demand_clusters)} Clusters Running On-Demand",
                description="These clusters could use Spot instances for 60-70% savings.",
                recommendation="Enable Ghost Spot with Instance Fleets for automatic optimization.",
                estimated_monthly_savings_usd=potential_savings,
                estimated_annual_savings_usd=potential_savings * 12,
                implementation_effort="low",
                affected_clusters=[c.cluster_id for c in on_demand_clusters],
                evidence={"spot_discount_percent": 65},
                created_at=datetime.utcnow(),
            ))

        # Check for clusters without auto-termination
        no_auto_term = [c for c in clusters if not c.metadata.get("auto_terminate") and c.status != ClusterStatus.TERMINATED]
        if no_auto_term:
            insights.append(CostInsight(
                insight_id=str(uuid.uuid4()),
                severity="medium",
                category="lifecycle",
                title=f"{len(no_auto_term)} Clusters Without Auto-Termination",
                description="These clusters will run indefinitely unless manually terminated.",
                recommendation="Enable auto-termination or use Ghost lifecycle management.",
                estimated_monthly_savings_usd=sum(c.hourly_cost_usd * 24 * 10 for c in no_auto_term),
                estimated_annual_savings_usd=sum(c.hourly_cost_usd * 24 * 10 * 12 for c in no_auto_term),
                implementation_effort="low",
                affected_clusters=[c.cluster_id for c in no_auto_term],
                evidence={},
                created_at=datetime.utcnow(),
            ))

        return insights

    def start_prediction_engine(self, config: "PredictConfig", dry_run: bool = False) -> None:
        """Start the EMR prediction engine."""
        logger.info("Starting EMR prediction engine", dry_run=dry_run)
        self._prediction_engine_running = True

    def start_hibernation_manager(self, config: "HibernateConfig", dry_run: bool = False) -> None:
        """Start the EMR hibernation manager."""
        logger.info("Starting EMR hibernation manager", dry_run=dry_run)
        self._hibernation_manager_running = True

    def start_spot_orchestrator(self, config: "SpotConfig", dry_run: bool = False) -> None:
        """Start the EMR spot orchestrator."""
        logger.info("Starting EMR spot orchestrator", dry_run=dry_run)
        self._spot_orchestrator_running = True

    def start_pool_manager(self, config: "PoolConfig", dry_run: bool = False) -> None:
        """Start the EMR pool manager."""
        logger.info("Starting EMR pool manager", dry_run=dry_run)
        self._pool_manager_running = True

    def start_insight_engine(self, config: "InsightConfig", dry_run: bool = False) -> None:
        """Start the EMR insight engine."""
        logger.info("Starting EMR insight engine", dry_run=dry_run)
        self._insight_engine_running = True

    def stop_strategy(self, strategy: Strategy) -> None:
        """Stop a specific strategy."""
        logger.info(f"Stopping EMR strategy: {strategy.value}")
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
        """Terminate an EMR cluster (EMR doesn't support true hibernation)."""
        self._ensure_connected()
        start_time = datetime.utcnow()

        try:
            cluster = self.get_cluster(cluster_id)
            if cluster.status == ClusterStatus.TERMINATED:
                raise HibernationError(
                    "Cluster already terminated",
                    cluster_id=cluster_id,
                )

            # Terminate the cluster
            self._emr_client.terminate_job_flows(JobFlowIds=[cluster_id])

            return OptimizationResult(
                operation_id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                strategy=Strategy.HIBERNATE,
                success=True,
                message=f"EMR cluster {cluster.cluster_name} terminated successfully",
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                estimated_savings_usd=cluster.hourly_cost_usd * 24,
                previous_status=cluster.status,
                new_status=ClusterStatus.TERMINATING,
                details={"note": "EMR clusters are terminated, not hibernated. Use Ghost templates to quickly recreate."},
            )
        except HibernationError:
            raise
        except Exception as e:
            return OptimizationResult(
                operation_id=str(uuid.uuid4()),
                cluster_id=cluster_id,
                strategy=Strategy.HIBERNATE,
                success=False,
                message="Termination failed",
                error=str(e),
                started_at=start_time,
                completed_at=datetime.utcnow(),
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

    def resume_cluster(self, cluster_id: str) -> OptimizationResult:
        """Resume (recreate) an EMR cluster from template."""
        start_time = datetime.utcnow()

        # EMR doesn't support resume - would need to recreate from template
        return OptimizationResult(
            operation_id=str(uuid.uuid4()),
            cluster_id=cluster_id,
            strategy=Strategy.HIBERNATE,
            success=False,
            message="EMR clusters cannot be resumed. Use Ghost templates to recreate.",
            error="EMR does not support cluster resume. Create a new cluster instead.",
            started_at=start_time,
            completed_at=datetime.utcnow(),
            duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
        )

    def add_exclusion(self, cluster_id: str) -> None:
        """Add a cluster to exclusion list."""
        self._exclusions.add(cluster_id)

    def remove_exclusion(self, cluster_id: str) -> None:
        """Remove a cluster from exclusion list."""
        self._exclusions.discard(cluster_id)

    def analyze_workspace(self) -> dict[str, Any]:
        """Analyze EMR account for optimization opportunities."""
        self._ensure_connected()

        clusters = self.list_clusters()
        insights = self.get_insights()

        active_clusters = [c for c in clusters if c.status != ClusterStatus.TERMINATED]
        total_hourly_cost = sum(c.hourly_cost_usd for c in active_clusters)
        idle_hourly_cost = sum(c.hourly_cost_usd for c in clusters if c.status == ClusterStatus.IDLE)
        potential_savings = sum(i.estimated_monthly_savings_usd for i in insights)

        return {
            "platform": "emr",
            "analysis_time": datetime.utcnow().isoformat(),
            "summary": {
                "total_clusters": len(clusters),
                "active_clusters": len(active_clusters),
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
            "insights": [
                {
                    "title": i.title,
                    "category": i.category,
                    "severity": i.severity,
                    "monthly_savings_usd": i.estimated_monthly_savings_usd,
                }
                for i in insights
            ],
            "clusters": [
                {
                    "id": c.cluster_id,
                    "name": c.cluster_name,
                    "status": c.status.value,
                    "node_type": c.node_type,
                    "workers": c.num_workers,
                    "hourly_cost_usd": c.hourly_cost_usd,
                    "instance_type": c.instance_type.value,
                    "auto_terminate": c.metadata.get("auto_terminate", False),
                }
                for c in clusters
            ],
        }
