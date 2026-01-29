"""
Google Cloud Dataproc integration for Ghost Compute.

Provides optimization capabilities for Dataproc clusters including:
- Cluster discovery and monitoring
- Preemptible VM management
- Auto-scaling configuration
- Cost analysis and insights
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TYPE_CHECKING

import structlog

from ghost.core.models import (
    Platform,
    Strategy,
    ClusterState,
    ClusterStatus,
    ClusterStats,
    OptimizationResult,
    CostInsight,
    InsightSeverity,
    InsightCategory,
)
from ghost.core.exceptions import PlatformError, ClusterNotFoundError
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


# GCP Dataproc pricing (per vCPU-hour and per GB-hour)
# Based on us-central1 pricing
DATAPROC_PRICING: dict[str, dict[str, float]] = {
    # Dataproc Premium (on top of Compute Engine)
    "dataproc_premium": {
        "per_vcpu_hour": 0.01,  # Dataproc fee per vCPU-hour
    },
    # Standard machine types (n1-standard)
    "n1-standard-2": {
        "vcpus": 2,
        "memory_gb": 7.5,
        "on_demand_hourly": 0.0950,
        "preemptible_hourly": 0.0200,
    },
    "n1-standard-4": {
        "vcpus": 4,
        "memory_gb": 15,
        "on_demand_hourly": 0.1900,
        "preemptible_hourly": 0.0400,
    },
    "n1-standard-8": {
        "vcpus": 8,
        "memory_gb": 30,
        "on_demand_hourly": 0.3800,
        "preemptible_hourly": 0.0800,
    },
    "n1-standard-16": {
        "vcpus": 16,
        "memory_gb": 60,
        "on_demand_hourly": 0.7600,
        "preemptible_hourly": 0.1600,
    },
    "n1-standard-32": {
        "vcpus": 32,
        "memory_gb": 120,
        "on_demand_hourly": 1.5200,
        "preemptible_hourly": 0.3200,
    },
    "n1-standard-64": {
        "vcpus": 64,
        "memory_gb": 240,
        "on_demand_hourly": 3.0400,
        "preemptible_hourly": 0.6400,
    },
    # High-memory machine types (n1-highmem)
    "n1-highmem-2": {
        "vcpus": 2,
        "memory_gb": 13,
        "on_demand_hourly": 0.1184,
        "preemptible_hourly": 0.0250,
    },
    "n1-highmem-4": {
        "vcpus": 4,
        "memory_gb": 26,
        "on_demand_hourly": 0.2368,
        "preemptible_hourly": 0.0500,
    },
    "n1-highmem-8": {
        "vcpus": 8,
        "memory_gb": 52,
        "on_demand_hourly": 0.4736,
        "preemptible_hourly": 0.1000,
    },
    "n1-highmem-16": {
        "vcpus": 16,
        "memory_gb": 104,
        "on_demand_hourly": 0.9472,
        "preemptible_hourly": 0.2000,
    },
    # High-CPU machine types (n1-highcpu)
    "n1-highcpu-4": {
        "vcpus": 4,
        "memory_gb": 3.6,
        "on_demand_hourly": 0.1420,
        "preemptible_hourly": 0.0300,
    },
    "n1-highcpu-8": {
        "vcpus": 8,
        "memory_gb": 7.2,
        "on_demand_hourly": 0.2840,
        "preemptible_hourly": 0.0600,
    },
    "n1-highcpu-16": {
        "vcpus": 16,
        "memory_gb": 14.4,
        "on_demand_hourly": 0.5680,
        "preemptible_hourly": 0.1200,
    },
    # N2 machine types (newer generation)
    "n2-standard-4": {
        "vcpus": 4,
        "memory_gb": 16,
        "on_demand_hourly": 0.1942,
        "preemptible_hourly": 0.0471,
    },
    "n2-standard-8": {
        "vcpus": 8,
        "memory_gb": 32,
        "on_demand_hourly": 0.3885,
        "preemptible_hourly": 0.0942,
    },
    "n2-standard-16": {
        "vcpus": 16,
        "memory_gb": 64,
        "on_demand_hourly": 0.7769,
        "preemptible_hourly": 0.1885,
    },
}


@dataclass
class DataprocCluster:
    """Represents a Google Cloud Dataproc cluster."""

    cluster_name: str
    project_id: str
    region: str
    zone: str
    state: str  # CREATING, RUNNING, ERROR, DELETING, UPDATING, STOPPED, etc.
    master_machine_type: str
    master_num_instances: int
    worker_machine_type: str
    worker_num_instances: int
    preemptible_num_instances: int
    secondary_worker_num_instances: int  # Spot VMs
    image_version: str
    creation_time: Optional[datetime] = None
    autoscaling_policy: Optional[str] = None
    idle_delete_ttl: Optional[int] = None  # seconds
    max_idle: Optional[int] = None  # seconds
    labels: dict[str, str] | None = None


class DataprocIntegration(BaseIntegration):
    """
    Google Cloud Dataproc platform integration.

    Manages optimization for Dataproc clusters including:
    - Cluster discovery and state monitoring
    - Preemptible/Spot VM management for cost savings
    - Auto-scaling configuration
    - Idle cluster detection and cleanup
    - Cost analysis and optimization insights
    """

    def __init__(self, config: "GhostConfig") -> None:
        """
        Initialize Dataproc integration.

        Args:
            config: Ghost configuration containing GCP credentials
        """
        super().__init__(config)
        self._dataproc_client: Any = None
        self._project_id: str = ""
        self._region: str = ""
        self._excluded_clusters: set[str] = set()
        self._active_strategies: dict[Strategy, bool] = {}

    @property
    def platform(self) -> Platform:
        """Return the platform type."""
        return Platform.DATAPROC

    def _get_gcp_client(self) -> None:
        """Initialize Google Cloud Dataproc client."""
        try:
            from google.cloud import dataproc_v1
            from google.auth import default as google_auth_default
        except ImportError as e:
            raise PlatformError(
                f"Google Cloud SDK not installed. Run: pip install google-cloud-dataproc. Error: {e}"
            )

        # Get configuration from platform config
        gcp_config = self.config.platform_config or {}
        self._project_id = gcp_config.get(
            "project_id", ""
        ) or self._get_env_var("GOOGLE_CLOUD_PROJECT", "")
        self._region = gcp_config.get(
            "region", ""
        ) or self._get_env_var("DATAPROC_REGION", "us-central1")

        if not self._project_id:
            # Try to get from default credentials
            try:
                _, project = google_auth_default()
                self._project_id = project or ""
            except Exception:
                pass

        if not self._project_id:
            raise PlatformError("GCP project_id is required")

        # Initialize Dataproc cluster controller client
        self._dataproc_client = dataproc_v1.ClusterControllerClient(
            client_options={
                "api_endpoint": f"{self._region}-dataproc.googleapis.com:443"
            }
        )

    def _get_env_var(self, name: str, default: str = "") -> str:
        """Get environment variable."""
        import os
        return os.environ.get(name, default)

    def test_connection(self) -> bool:
        """
        Test connection to Google Cloud Dataproc.

        Returns:
            True if connection successful
        """
        try:
            self._get_gcp_client()

            # Try listing clusters to verify connectivity
            clusters = list(self._dataproc_client.list_clusters(
                request={
                    "project_id": self._project_id,
                    "region": self._region,
                }
            ))
            logger.info(
                "Dataproc connection successful",
                cluster_count=len(clusters),
                project_id=self._project_id,
                region=self._region,
            )
            self._connected = True
            return True
        except Exception as e:
            logger.error("Dataproc connection failed", error=str(e))
            self._connected = False
            return False

    def close(self) -> None:
        """Close GCP connections."""
        self._dataproc_client = None
        self._connected = False

    def _convert_cluster_state(self, state: str) -> ClusterStatus:
        """Convert Dataproc cluster state to Ghost ClusterStatus."""
        state_mapping = {
            "UNKNOWN": ClusterStatus.UNKNOWN,
            "CREATING": ClusterStatus.STARTING,
            "RUNNING": ClusterStatus.RUNNING,
            "ERROR": ClusterStatus.ERROR,
            "ERROR_DUE_TO_UPDATE": ClusterStatus.ERROR,
            "DELETING": ClusterStatus.TERMINATING,
            "UPDATING": ClusterStatus.RESIZING,
            "STOPPING": ClusterStatus.TERMINATING,
            "STOPPED": ClusterStatus.TERMINATED,
            "STARTING": ClusterStatus.STARTING,
        }
        return state_mapping.get(state, ClusterStatus.UNKNOWN)

    def _get_cluster_details(self, cluster: Any) -> DataprocCluster:
        """Extract cluster details from Dataproc API response."""
        config = cluster.config
        master_config = config.master_config
        worker_config = config.worker_config
        secondary_worker_config = config.secondary_worker_config

        # Get lifecycle config for idle detection
        lifecycle_config = config.lifecycle_config
        idle_delete_ttl = None
        max_idle = None
        if lifecycle_config:
            if lifecycle_config.idle_delete_ttl:
                idle_delete_ttl = lifecycle_config.idle_delete_ttl.seconds
            if hasattr(lifecycle_config, 'idle_start_time'):
                max_idle = lifecycle_config.idle_start_time

        # Get autoscaling policy
        autoscaling_policy = None
        if config.autoscaling_config:
            autoscaling_policy = config.autoscaling_config.policy_uri

        return DataprocCluster(
            cluster_name=cluster.cluster_name,
            project_id=cluster.project_id,
            region=self._region,
            zone=master_config.machine_type_uri.split('/')[-3] if '/' in master_config.machine_type_uri else "",
            state=cluster.status.state.name,
            master_machine_type=master_config.machine_type_uri.split('/')[-1] if '/' in master_config.machine_type_uri else master_config.machine_type_uri,
            master_num_instances=master_config.num_instances,
            worker_machine_type=worker_config.machine_type_uri.split('/')[-1] if worker_config and '/' in worker_config.machine_type_uri else (worker_config.machine_type_uri if worker_config else "n1-standard-4"),
            worker_num_instances=worker_config.num_instances if worker_config else 0,
            preemptible_num_instances=secondary_worker_config.num_instances if secondary_worker_config and secondary_worker_config.is_preemptible else 0,
            secondary_worker_num_instances=secondary_worker_config.num_instances if secondary_worker_config else 0,
            image_version=config.software_config.image_version if config.software_config else "",
            creation_time=cluster.status.state_start_time.ToDatetime() if hasattr(cluster.status.state_start_time, 'ToDatetime') else None,
            autoscaling_policy=autoscaling_policy,
            idle_delete_ttl=idle_delete_ttl,
            labels=dict(cluster.labels) if cluster.labels else None,
        )

    def _calculate_cluster_hourly_cost(self, cluster: DataprocCluster) -> float:
        """
        Calculate hourly cost for a Dataproc cluster.

        Args:
            cluster: Cluster details

        Returns:
            Estimated hourly cost in USD
        """
        total_cost = 0.0
        dataproc_premium = DATAPROC_PRICING["dataproc_premium"]["per_vcpu_hour"]

        # Master node cost
        master_pricing = DATAPROC_PRICING.get(
            cluster.master_machine_type,
            DATAPROC_PRICING["n1-standard-4"]
        )
        master_cost = (
            master_pricing["on_demand_hourly"] * cluster.master_num_instances +
            dataproc_premium * master_pricing["vcpus"] * cluster.master_num_instances
        )
        total_cost += master_cost

        # Worker node cost (on-demand)
        worker_pricing = DATAPROC_PRICING.get(
            cluster.worker_machine_type,
            DATAPROC_PRICING["n1-standard-4"]
        )
        worker_cost = (
            worker_pricing["on_demand_hourly"] * cluster.worker_num_instances +
            dataproc_premium * worker_pricing["vcpus"] * cluster.worker_num_instances
        )
        total_cost += worker_cost

        # Preemptible/secondary worker cost
        if cluster.secondary_worker_num_instances > 0:
            preemptible_cost = (
                worker_pricing["preemptible_hourly"] * cluster.secondary_worker_num_instances +
                dataproc_premium * worker_pricing["vcpus"] * cluster.secondary_worker_num_instances
            )
            total_cost += preemptible_cost

        return total_cost

    def list_clusters(self) -> list[ClusterState]:
        """
        List all Dataproc clusters in the project/region.

        Returns:
            List of ClusterState objects
        """
        if not self._dataproc_client:
            self._get_gcp_client()

        clusters: list[ClusterState] = []

        try:
            # List clusters in the configured region
            response = self._dataproc_client.list_clusters(
                request={
                    "project_id": self._project_id,
                    "region": self._region,
                }
            )

            for cluster in response:
                cluster_details = self._get_cluster_details(cluster)

                # Calculate total worker count
                total_workers = (
                    cluster_details.worker_num_instances +
                    cluster_details.secondary_worker_num_instances
                )

                # Calculate uptime
                uptime_seconds = 0
                if cluster_details.creation_time:
                    uptime_seconds = int(
                        (datetime.now(timezone.utc) - cluster_details.creation_time.replace(tzinfo=timezone.utc)).total_seconds()
                    )

                clusters.append(ClusterState(
                    cluster_id=f"{self._project_id}/{self._region}/{cluster_details.cluster_name}",
                    cluster_name=cluster_details.cluster_name,
                    status=self._convert_cluster_state(cluster_details.state),
                    worker_count=total_workers,
                    instance_type=cluster_details.worker_machine_type,
                    uptime_seconds=uptime_seconds,
                    hourly_cost=self._calculate_cluster_hourly_cost(cluster_details),
                    platform=Platform.DATAPROC,
                    tags=cluster_details.labels or {},
                ))

            logger.info("Listed Dataproc clusters", cluster_count=len(clusters))
            return clusters

        except Exception as e:
            logger.error("Failed to list clusters", error=str(e))
            raise PlatformError(f"Failed to list Dataproc clusters: {e}")

    def _list_all_regions(self) -> list[ClusterState]:
        """List clusters across all regions."""
        all_clusters: list[ClusterState] = []

        # Common Dataproc regions
        regions = [
            "us-central1", "us-east1", "us-east4", "us-west1", "us-west2",
            "europe-west1", "europe-west2", "europe-west4",
            "asia-east1", "asia-southeast1", "asia-northeast1",
        ]

        original_region = self._region

        for region in regions:
            try:
                self._region = region
                self._dataproc_client = None  # Reset client for new region
                self._get_gcp_client()
                clusters = self.list_clusters()
                all_clusters.extend(clusters)
            except Exception:
                pass  # Region may not be enabled

        self._region = original_region
        self._dataproc_client = None
        return all_clusters

    def get_cluster(self, cluster_id: str) -> ClusterState:
        """
        Get details for a specific Dataproc cluster.

        Args:
            cluster_id: Cluster identifier (project/region/cluster_name)

        Returns:
            ClusterState for the cluster
        """
        if not self._dataproc_client:
            self._get_gcp_client()

        try:
            # Parse cluster_id
            parts = cluster_id.split('/')
            if len(parts) != 3:
                raise ClusterNotFoundError(
                    f"Invalid cluster_id format: {cluster_id}. Expected: project_id/region/cluster_name"
                )

            project_id, region, cluster_name = parts

            # Update region if different
            if region != self._region:
                self._region = region
                self._dataproc_client = None
                self._get_gcp_client()

            # Get the cluster
            cluster = self._dataproc_client.get_cluster(
                request={
                    "project_id": project_id,
                    "region": region,
                    "cluster_name": cluster_name,
                }
            )

            cluster_details = self._get_cluster_details(cluster)

            total_workers = (
                cluster_details.worker_num_instances +
                cluster_details.secondary_worker_num_instances
            )

            uptime_seconds = 0
            if cluster_details.creation_time:
                uptime_seconds = int(
                    (datetime.now(timezone.utc) - cluster_details.creation_time.replace(tzinfo=timezone.utc)).total_seconds()
                )

            return ClusterState(
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                status=self._convert_cluster_state(cluster_details.state),
                worker_count=total_workers,
                instance_type=cluster_details.worker_machine_type,
                uptime_seconds=uptime_seconds,
                hourly_cost=self._calculate_cluster_hourly_cost(cluster_details),
                platform=Platform.DATAPROC,
                tags=cluster_details.labels or {},
            )

        except ClusterNotFoundError:
            raise
        except Exception as e:
            if "not found" in str(e).lower():
                raise ClusterNotFoundError(f"Cluster not found: {cluster_id}")
            logger.error("Failed to get cluster", cluster_id=cluster_id, error=str(e))
            raise PlatformError(f"Failed to get Dataproc cluster {cluster_id}: {e}")

    def get_stats(
        self,
        period_start: datetime,
        period_end: datetime,
        workspace_id: Optional[str] = None,
    ) -> ClusterStats:
        """
        Get aggregated statistics for Dataproc clusters.

        Args:
            period_start: Start of the statistics period
            period_end: End of the statistics period
            workspace_id: Optional project to filter by

        Returns:
            Aggregated statistics
        """
        if not self._dataproc_client:
            self._get_gcp_client()

        try:
            clusters = self.list_clusters()

            # Filter by project if specified
            if workspace_id:
                clusters = [c for c in clusters if c.cluster_id.startswith(f"{workspace_id}/")]

            # Calculate statistics
            total_hours = (period_end - period_start).total_seconds() / 3600
            total_compute_cost = 0.0
            total_vcpu_hours = 0.0

            running_clusters = [c for c in clusters if c.status == ClusterStatus.RUNNING]
            stopped_clusters = [c for c in clusters if c.status == ClusterStatus.TERMINATED]

            # Estimate costs based on running time
            for cluster in running_clusters:
                # Assume cluster ran for portion of period
                effective_hours = min(total_hours, cluster.uptime_seconds / 3600)
                total_compute_cost += cluster.hourly_cost * effective_hours

            # Estimate idle hours (clusters without recent jobs)
            estimated_idle_hours = 0.0
            for cluster in running_clusters:
                # Estimate 30% idle time for running clusters
                estimated_idle_hours += total_hours * 0.3

            # Calculate potential preemptible savings
            preemptible_potential = 0.0
            for cluster in running_clusters:
                # Estimate 60-80% savings by using preemptible VMs
                preemptible_potential += cluster.hourly_cost * total_hours * 0.7 * 0.5

            return ClusterStats(
                period_start=period_start,
                period_end=period_end,
                total_clusters=len(clusters),
                total_compute_hours=total_hours * len(running_clusters),
                total_compute_cost=total_compute_cost,
                total_dbu_cost=0.0,  # Dataproc uses premium pricing, not DBUs
                idle_hours=estimated_idle_hours,
                cold_starts=0,  # Would need job history
                avg_cold_start_time=120.0,  # Dataproc clusters typically start in ~2 mins
                spot_savings=preemptible_potential,
                hibernation_savings=0.0,  # Dataproc doesn't support hibernation
                platform=Platform.DATAPROC,
            )

        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            raise PlatformError(f"Failed to get Dataproc statistics: {e}")

    def get_insights(self) -> list[CostInsight]:
        """
        Generate cost optimization insights for Dataproc clusters.

        Returns:
            List of actionable cost insights
        """
        if not self._dataproc_client:
            self._get_gcp_client()

        insights: list[CostInsight] = []

        try:
            # Get clusters with full details
            response = self._dataproc_client.list_clusters(
                request={
                    "project_id": self._project_id,
                    "region": self._region,
                }
            )

            for cluster in response:
                cluster_details = self._get_cluster_details(cluster)
                cluster_id = f"{self._project_id}/{self._region}/{cluster_details.cluster_name}"
                hourly_cost = self._calculate_cluster_hourly_cost(cluster_details)
                monthly_cost = hourly_cost * 730

                # Insight: No preemptible workers
                if cluster_details.secondary_worker_num_instances == 0 and cluster_details.worker_num_instances > 2:
                    potential_savings = monthly_cost * 0.5  # ~70% cheaper for preemptible portion

                    insights.append(CostInsight(
                        insight_id=f"dataproc-no-preemptible-{cluster_details.cluster_name}",
                        title=f"Add preemptible workers to {cluster_details.cluster_name}",
                        description=(
                            f"Cluster '{cluster_details.cluster_name}' has {cluster_details.worker_num_instances} "
                            f"on-demand workers but no preemptible workers. Adding preemptible workers "
                            f"can significantly reduce costs for fault-tolerant workloads."
                        ),
                        category=InsightCategory.SPOT_OPPORTUNITY,
                        severity=InsightSeverity.HIGH,
                        estimated_savings=potential_savings,
                        affected_resources=[cluster_id],
                        recommendation="Add secondary worker group with preemptible VMs for batch processing workloads.",
                    ))

                # Insight: No autoscaling
                if not cluster_details.autoscaling_policy:
                    insights.append(CostInsight(
                        insight_id=f"dataproc-no-autoscaling-{cluster_details.cluster_name}",
                        title=f"Enable autoscaling for {cluster_details.cluster_name}",
                        description=(
                            f"Cluster '{cluster_details.cluster_name}' does not have an autoscaling policy. "
                            f"Autoscaling can automatically adjust worker count based on workload."
                        ),
                        category=InsightCategory.RIGHTSIZING,
                        severity=InsightSeverity.MEDIUM,
                        estimated_savings=monthly_cost * 0.3,
                        affected_resources=[cluster_id],
                        recommendation="Create and attach an autoscaling policy to dynamically scale workers.",
                    ))

                # Insight: No idle delete TTL
                if not cluster_details.idle_delete_ttl:
                    insights.append(CostInsight(
                        insight_id=f"dataproc-no-idle-delete-{cluster_details.cluster_name}",
                        title=f"Configure idle deletion for {cluster_details.cluster_name}",
                        description=(
                            f"Cluster '{cluster_details.cluster_name}' does not have idle deletion configured. "
                            f"This means the cluster will continue running and incurring costs even when idle."
                        ),
                        category=InsightCategory.IDLE_RESOURCES,
                        severity=InsightSeverity.HIGH,
                        estimated_savings=monthly_cost * 0.4,
                        affected_resources=[cluster_id],
                        recommendation="Set idle_delete_ttl in lifecycle config to auto-delete idle clusters.",
                    ))

                # Insight: Long-running cluster without jobs
                if cluster_details.state == "RUNNING":
                    cluster_state = self.get_cluster(cluster_id)
                    if cluster_state.uptime_seconds > 86400:  # > 24 hours
                        insights.append(CostInsight(
                            insight_id=f"dataproc-long-running-{cluster_details.cluster_name}",
                            title=f"Review long-running cluster {cluster_details.cluster_name}",
                            description=(
                                f"Cluster '{cluster_details.cluster_name}' has been running for "
                                f"{cluster_state.uptime_seconds // 3600} hours. Consider if it's still needed."
                            ),
                            category=InsightCategory.IDLE_RESOURCES,
                            severity=InsightSeverity.MEDIUM,
                            estimated_savings=hourly_cost * 24,  # 1 day savings
                            affected_resources=[cluster_id],
                            recommendation="Review cluster usage and delete if no longer needed, or configure idle deletion.",
                        ))

                # Insight: Oversized master node
                if cluster_details.master_machine_type in ["n1-standard-32", "n1-standard-64", "n1-highmem-16"]:
                    insights.append(CostInsight(
                        insight_id=f"dataproc-oversize-master-{cluster_details.cluster_name}",
                        title=f"Review master node size for {cluster_details.cluster_name}",
                        description=(
                            f"Cluster '{cluster_details.cluster_name}' uses {cluster_details.master_machine_type} "
                            f"for the master node. Consider if this size is necessary."
                        ),
                        category=InsightCategory.RIGHTSIZING,
                        severity=InsightSeverity.LOW,
                        estimated_savings=monthly_cost * 0.1,
                        affected_resources=[cluster_id],
                        recommendation="Evaluate if a smaller master node would suffice based on workload characteristics.",
                    ))

            logger.info("Generated Dataproc insights", insight_count=len(insights))
            return insights

        except Exception as e:
            logger.error("Failed to generate insights", error=str(e))
            raise PlatformError(f"Failed to generate Dataproc insights: {e}")

    def start_prediction_engine(self, config: "PredictConfig", dry_run: bool = False) -> None:
        """
        Start the prediction engine for Dataproc workloads.

        Predicts job patterns to optimize cluster availability.

        Args:
            config: Prediction configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Dataproc prediction engine",
            dry_run=dry_run,
            lookahead_minutes=config.lookahead_minutes,
        )
        self._active_strategies[Strategy.PREDICT] = True

        if not dry_run:
            # In production, this would:
            # 1. Analyze historical job submission patterns
            # 2. Predict upcoming resource needs
            # 3. Create clusters proactively before jobs arrive
            pass

    def start_hibernation_manager(self, config: "HibernateConfig", dry_run: bool = False) -> None:
        """
        Start the hibernation manager for Dataproc.

        Note: Dataproc doesn't support true hibernation, but this manages
        cluster lifecycle including deletion of idle clusters.

        Args:
            config: Hibernation configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Dataproc hibernation manager (lifecycle manager)",
            dry_run=dry_run,
            idle_threshold_minutes=config.idle_threshold_minutes,
        )
        self._active_strategies[Strategy.HIBERNATE] = True

        if not dry_run:
            # In production, this would:
            # 1. Monitor cluster idle time
            # 2. Update lifecycle config for idle deletion
            # 3. Delete clusters that exceed idle threshold
            pass

    def start_spot_orchestrator(self, config: "SpotConfig", dry_run: bool = False) -> None:
        """
        Start the spot (preemptible) orchestrator for Dataproc.

        Manages preemptible VM allocation for cost optimization.

        Args:
            config: Spot configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Dataproc preemptible orchestrator",
            dry_run=dry_run,
            fallback_enabled=config.fallback_to_on_demand,
        )
        self._active_strategies[Strategy.SPOT] = True

        if not dry_run:
            # In production, this would:
            # 1. Monitor preemptible VM availability
            # 2. Adjust secondary worker counts
            # 3. Handle preemption events gracefully
            pass

    def start_pool_manager(self, config: "PoolConfig", dry_run: bool = False) -> None:
        """
        Start the pool manager for Dataproc.

        Manages pre-created cluster pools for fast job starts.

        Args:
            config: Pool configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Dataproc pool manager",
            dry_run=dry_run,
            min_clusters=config.min_idle_clusters,
            max_clusters=config.max_idle_clusters,
        )
        self._active_strategies[Strategy.POOL] = True

        if not dry_run:
            # In production, this would:
            # 1. Maintain pool of warm clusters
            # 2. Route jobs to available pooled clusters
            # 3. Scale pool based on demand patterns
            pass

    def start_insight_engine(self, config: "InsightConfig", dry_run: bool = False) -> None:
        """
        Start the insight engine for Dataproc.

        Continuously analyzes clusters for optimization opportunities.

        Args:
            config: Insight configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Dataproc insight engine",
            dry_run=dry_run,
            analysis_interval=config.analysis_interval_minutes,
        )
        self._active_strategies[Strategy.INSIGHT] = True

    def stop_strategy(self, strategy: Strategy) -> None:
        """
        Stop a running optimization strategy.

        Args:
            strategy: Strategy to stop
        """
        logger.info(f"Stopping Dataproc strategy: {strategy.value}")
        self._active_strategies[strategy] = False

    def hibernate_cluster(self, cluster_id: str) -> OptimizationResult:
        """
        Stop/delete a Dataproc cluster.

        Note: Dataproc doesn't support hibernation. This deletes the cluster.
        Cluster state should be saved in GCS/BQ for recreation.

        Args:
            cluster_id: Cluster identifier (project/region/cluster_name)

        Returns:
            Result of the delete operation
        """
        if cluster_id in self._excluded_clusters:
            return OptimizationResult(
                success=False,
                cluster_id=cluster_id,
                action="hibernate",
                message=f"Cluster {cluster_id} is excluded from hibernation",
                savings_usd=0.0,
            )

        if not self._dataproc_client:
            self._get_gcp_client()

        try:
            parts = cluster_id.split('/')
            if len(parts) != 3:
                raise ClusterNotFoundError(f"Invalid cluster_id: {cluster_id}")

            project_id, region, cluster_name = parts

            # Get cluster for cost calculation
            cluster = self.get_cluster(cluster_id)

            # Delete the cluster (Dataproc doesn't support stop)
            logger.info("Deleting Dataproc cluster", cluster_id=cluster_id)

            operation = self._dataproc_client.delete_cluster(
                request={
                    "project_id": project_id,
                    "region": region,
                    "cluster_name": cluster_name,
                }
            )

            return OptimizationResult(
                success=True,
                cluster_id=cluster_id,
                action="hibernate",
                message=f"Initiated deletion of cluster {cluster_name}. Operation: {operation.operation.name}",
                savings_usd=cluster.hourly_cost,
            )

        except Exception as e:
            logger.error("Failed to delete cluster", cluster_id=cluster_id, error=str(e))
            return OptimizationResult(
                success=False,
                cluster_id=cluster_id,
                action="hibernate",
                message=f"Failed to delete cluster: {e}",
                savings_usd=0.0,
            )

    def resume_cluster(self, cluster_id: str) -> OptimizationResult:
        """
        Recreate a Dataproc cluster.

        Note: This would need cluster config stored elsewhere to recreate.

        Args:
            cluster_id: Cluster identifier (project/region/cluster_name)

        Returns:
            Result of the creation operation
        """
        # Dataproc clusters need to be recreated, not resumed
        # This would require stored cluster configuration
        return OptimizationResult(
            success=False,
            cluster_id=cluster_id,
            action="resume",
            message="Dataproc clusters must be recreated. Use stored configuration to create a new cluster.",
            savings_usd=0.0,
        )

    def add_exclusion(self, cluster_id: str) -> None:
        """
        Add a cluster to the exclusion list.

        Args:
            cluster_id: Cluster identifier to exclude
        """
        self._excluded_clusters.add(cluster_id)
        logger.info("Added cluster to exclusion list", cluster_id=cluster_id)

    def remove_exclusion(self, cluster_id: str) -> None:
        """
        Remove a cluster from the exclusion list.

        Args:
            cluster_id: Cluster identifier to remove from exclusions
        """
        self._excluded_clusters.discard(cluster_id)
        logger.info("Removed cluster from exclusion list", cluster_id=cluster_id)

    def analyze_workspace(self) -> dict[str, Any]:
        """
        Analyze GCP project for Dataproc optimization opportunities.

        Returns:
            Analysis results including costs, insights, and recommendations
        """
        if not self._dataproc_client:
            self._get_gcp_client()

        try:
            clusters = self.list_clusters()
            insights = self.get_insights()

            # Calculate costs
            now = datetime.now(timezone.utc)

            total_monthly_cost = 0.0
            potential_savings = 0.0
            clusters_without_autoscaling = 0
            clusters_without_preemptible = 0
            clusters_without_idle_delete = 0

            for cluster in clusters:
                monthly_cost = cluster.hourly_cost * 730
                total_monthly_cost += monthly_cost

            # Get detailed info for optimization analysis
            response = self._dataproc_client.list_clusters(
                request={
                    "project_id": self._project_id,
                    "region": self._region,
                }
            )

            for api_cluster in response:
                details = self._get_cluster_details(api_cluster)
                monthly_cost = self._calculate_cluster_hourly_cost(details) * 730

                if not details.autoscaling_policy:
                    clusters_without_autoscaling += 1
                    potential_savings += monthly_cost * 0.3

                if details.secondary_worker_num_instances == 0 and details.worker_num_instances > 2:
                    clusters_without_preemptible += 1
                    potential_savings += monthly_cost * 0.5

                if not details.idle_delete_ttl:
                    clusters_without_idle_delete += 1
                    potential_savings += monthly_cost * 0.4

            # Aggregate insight savings
            insight_savings = sum(i.estimated_savings for i in insights)

            return {
                "project_id": self._project_id,
                "region": self._region,
                "total_clusters": len(clusters),
                "running_clusters": len([c for c in clusters if c.status == ClusterStatus.RUNNING]),
                "stopped_clusters": len([c for c in clusters if c.status == ClusterStatus.TERMINATED]),
                "estimated_monthly_cost": total_monthly_cost,
                "potential_monthly_savings": max(potential_savings, insight_savings),
                "savings_percentage": (
                    (max(potential_savings, insight_savings) / total_monthly_cost * 100)
                    if total_monthly_cost > 0 else 0
                ),
                "optimization_opportunities": {
                    "clusters_without_autoscaling": clusters_without_autoscaling,
                    "clusters_without_preemptible": clusters_without_preemptible,
                    "clusters_without_idle_delete": clusters_without_idle_delete,
                },
                "insights": [
                    {
                        "title": i.title,
                        "severity": i.severity.value,
                        "estimated_savings": i.estimated_savings,
                    }
                    for i in insights[:10]
                ],
                "platform": Platform.DATAPROC.value,
                "analysis_time": now.isoformat(),
            }

        except Exception as e:
            logger.error("Failed to analyze project", error=str(e))
            raise PlatformError(f"Failed to analyze Dataproc project: {e}")
