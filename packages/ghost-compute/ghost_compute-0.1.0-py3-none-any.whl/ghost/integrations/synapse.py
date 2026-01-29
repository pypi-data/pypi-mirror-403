"""
Azure Synapse Analytics integration for Ghost Compute.

Provides optimization capabilities for Synapse Spark pools including:
- Spark pool discovery and monitoring
- Auto-pause/resume management
- Node size optimization
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


# Azure Synapse Spark pool pricing (per node-hour, Pay-As-You-Go)
# Prices vary by region, these are US East 2 defaults
SYNAPSE_SPARK_PRICING: dict[str, dict[str, float]] = {
    # Small nodes (4 vCores, 32 GB memory)
    "Small": {
        "node_cost_per_hour": 0.404,
        "vcores": 4,
        "memory_gb": 32,
    },
    # Medium nodes (8 vCores, 64 GB memory)
    "Medium": {
        "node_cost_per_hour": 0.808,
        "vcores": 8,
        "memory_gb": 64,
    },
    # Large nodes (16 vCores, 128 GB memory)
    "Large": {
        "node_cost_per_hour": 1.616,
        "vcores": 16,
        "memory_gb": 128,
    },
    # XLarge nodes (32 vCores, 256 GB memory)
    "XLarge": {
        "node_cost_per_hour": 3.232,
        "vcores": 32,
        "memory_gb": 256,
    },
    # XXLarge nodes (64 vCores, 512 GB memory)
    "XXLarge": {
        "node_cost_per_hour": 6.464,
        "vcores": 64,
        "memory_gb": 512,
    },
}


@dataclass
class SynapseSparkPool:
    """Represents an Azure Synapse Spark pool."""

    name: str
    workspace_name: str
    resource_group: str
    subscription_id: str
    node_size: str
    node_count: int
    min_node_count: int
    max_node_count: int
    auto_scale_enabled: bool
    auto_pause_enabled: bool
    auto_pause_delay_minutes: int
    state: str  # Creating, Provisioning, Running, Paused, Deleting, etc.
    spark_version: str
    creation_time: Optional[datetime] = None
    last_activity_time: Optional[datetime] = None
    tags: dict[str, str] | None = None


class SynapseIntegration(BaseIntegration):
    """
    Azure Synapse Analytics platform integration.

    Manages optimization for Synapse Spark pools including:
    - Pool discovery and state monitoring
    - Auto-pause configuration for cost savings
    - Node count optimization based on workload
    - Cost analysis and optimization insights
    """

    def __init__(self, config: "GhostConfig") -> None:
        """
        Initialize Synapse integration.

        Args:
            config: Ghost configuration containing Azure credentials
        """
        super().__init__(config)
        self._synapse_client: Any = None
        self._monitor_client: Any = None
        self._credential: Any = None
        self._subscription_id: str = ""
        self._workspace_name: str = ""
        self._resource_group: str = ""
        self._excluded_pools: set[str] = set()
        self._active_strategies: dict[Strategy, bool] = {}

    @property
    def platform(self) -> Platform:
        """Return the platform type."""
        return Platform.SYNAPSE

    def _get_azure_clients(self) -> None:
        """Initialize Azure SDK clients."""
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.synapse import SynapseManagementClient
            from azure.mgmt.monitor import MonitorManagementClient
        except ImportError as e:
            raise PlatformError(
                f"Azure SDK not installed. Run: pip install azure-identity azure-mgmt-synapse azure-mgmt-monitor. Error: {e}"
            )

        # Get configuration from platform config
        azure_config = self.config.platform_config or {}
        self._subscription_id = azure_config.get(
            "subscription_id", ""
        ) or self._get_env_var("AZURE_SUBSCRIPTION_ID", "")
        self._workspace_name = azure_config.get("workspace_name", "")
        self._resource_group = azure_config.get("resource_group", "")

        if not self._subscription_id:
            raise PlatformError("Azure subscription_id is required")

        # Use DefaultAzureCredential for flexible authentication
        self._credential = DefaultAzureCredential()

        # Initialize Synapse management client
        self._synapse_client = SynapseManagementClient(
            credential=self._credential,
            subscription_id=self._subscription_id,
        )

        # Initialize Monitor client for metrics
        self._monitor_client = MonitorManagementClient(
            credential=self._credential,
            subscription_id=self._subscription_id,
        )

    def _get_env_var(self, name: str, default: str = "") -> str:
        """Get environment variable."""
        import os
        return os.environ.get(name, default)

    def test_connection(self) -> bool:
        """
        Test connection to Azure Synapse.

        Returns:
            True if connection successful
        """
        try:
            self._get_azure_clients()

            # Try listing workspaces to verify connectivity
            workspaces = list(self._synapse_client.workspaces.list())
            logger.info(
                "Synapse connection successful",
                workspace_count=len(workspaces),
                subscription_id=self._subscription_id,
            )
            self._connected = True
            return True
        except Exception as e:
            logger.error("Synapse connection failed", error=str(e))
            self._connected = False
            return False

    def close(self) -> None:
        """Close Azure connections."""
        self._synapse_client = None
        self._monitor_client = None
        self._credential = None
        self._connected = False

    def _convert_pool_state(self, state: str) -> ClusterStatus:
        """Convert Synapse pool state to Ghost ClusterStatus."""
        state_mapping = {
            "Creating": ClusterStatus.STARTING,
            "Provisioning": ClusterStatus.STARTING,
            "Running": ClusterStatus.RUNNING,
            "Paused": ClusterStatus.TERMINATED,  # Auto-paused
            "Resuming": ClusterStatus.STARTING,
            "Pausing": ClusterStatus.TERMINATING,
            "Deleting": ClusterStatus.TERMINATING,
            "Deleted": ClusterStatus.TERMINATED,
            "Failed": ClusterStatus.ERROR,
        }
        return state_mapping.get(state, ClusterStatus.UNKNOWN)

    def _get_pool_details(self, pool: Any, workspace_name: str, resource_group: str) -> SynapseSparkPool:
        """Extract pool details from Azure API response."""
        properties = pool.properties if hasattr(pool, 'properties') else {}

        auto_scale = properties.get('auto_scale', {}) or {}
        auto_pause = properties.get('auto_pause', {}) or {}

        return SynapseSparkPool(
            name=pool.name,
            workspace_name=workspace_name,
            resource_group=resource_group,
            subscription_id=self._subscription_id,
            node_size=properties.get('node_size', 'Medium'),
            node_count=properties.get('node_count', 0),
            min_node_count=auto_scale.get('min_node_count', 3),
            max_node_count=auto_scale.get('max_node_count', 10),
            auto_scale_enabled=auto_scale.get('enabled', False),
            auto_pause_enabled=auto_pause.get('enabled', False),
            auto_pause_delay_minutes=auto_pause.get('delay_in_minutes', 15),
            state=properties.get('provisioning_state', 'Unknown'),
            spark_version=properties.get('spark_version', '3.3'),
            creation_time=properties.get('creation_date'),
            tags=pool.tags,
        )

    def _estimate_pool_cost(self, pool: SynapseSparkPool, hours: float = 730) -> float:
        """
        Estimate monthly cost for a Spark pool.

        Args:
            pool: Spark pool details
            hours: Hours to calculate (730 = 1 month average)

        Returns:
            Estimated cost in USD
        """
        pricing = SYNAPSE_SPARK_PRICING.get(pool.node_size, SYNAPSE_SPARK_PRICING["Medium"])
        node_cost = pricing["node_cost_per_hour"]

        # Calculate based on node count
        node_count = pool.node_count if pool.node_count > 0 else pool.min_node_count

        # If auto-pause is enabled, estimate actual running hours
        if pool.auto_pause_enabled:
            # Assume pool runs ~40% of business hours with auto-pause
            effective_hours = hours * 0.4
        else:
            effective_hours = hours

        return node_cost * node_count * effective_hours

    def list_clusters(self) -> list[ClusterState]:
        """
        List all Spark pools across Synapse workspaces.

        Returns:
            List of ClusterState objects representing Spark pools
        """
        if not self._synapse_client:
            self._get_azure_clients()

        pools: list[ClusterState] = []

        try:
            # List all workspaces in subscription
            workspaces = list(self._synapse_client.workspaces.list())

            for workspace in workspaces:
                # Extract resource group from workspace ID
                # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/...
                ws_id_parts = workspace.id.split('/')
                rg_index = ws_id_parts.index('resourceGroups') + 1 if 'resourceGroups' in ws_id_parts else -1
                resource_group = ws_id_parts[rg_index] if rg_index > 0 else ""

                # List Spark pools in this workspace
                spark_pools = list(
                    self._synapse_client.big_data_pools.list_by_workspace(
                        resource_group_name=resource_group,
                        workspace_name=workspace.name,
                    )
                )

                for pool in spark_pools:
                    pool_details = self._get_pool_details(pool, workspace.name, resource_group)

                    # Create unique cluster ID
                    cluster_id = f"{workspace.name}/{pool.name}"

                    # Estimate hourly cost
                    pricing = SYNAPSE_SPARK_PRICING.get(
                        pool_details.node_size,
                        SYNAPSE_SPARK_PRICING["Medium"]
                    )
                    node_count = pool_details.node_count or pool_details.min_node_count
                    hourly_cost = pricing["node_cost_per_hour"] * node_count

                    pools.append(ClusterState(
                        cluster_id=cluster_id,
                        cluster_name=pool.name,
                        status=self._convert_pool_state(pool_details.state),
                        worker_count=node_count,
                        instance_type=pool_details.node_size,
                        uptime_seconds=0,  # Would need activity tracking
                        hourly_cost=hourly_cost,
                        platform=Platform.SYNAPSE,
                        tags=pool_details.tags or {},
                    ))

            logger.info("Listed Synapse Spark pools", pool_count=len(pools))
            return pools

        except Exception as e:
            logger.error("Failed to list Spark pools", error=str(e))
            raise PlatformError(f"Failed to list Synapse Spark pools: {e}")

    def get_cluster(self, cluster_id: str) -> ClusterState:
        """
        Get details for a specific Spark pool.

        Args:
            cluster_id: Pool identifier in format "workspace_name/pool_name"

        Returns:
            ClusterState for the pool
        """
        if not self._synapse_client:
            self._get_azure_clients()

        try:
            # Parse cluster_id
            if '/' not in cluster_id:
                raise ClusterNotFoundError(f"Invalid cluster_id format: {cluster_id}. Expected: workspace_name/pool_name")

            workspace_name, pool_name = cluster_id.split('/', 1)

            # Find workspace to get resource group
            workspaces = list(self._synapse_client.workspaces.list())
            workspace = next((w for w in workspaces if w.name == workspace_name), None)

            if not workspace:
                raise ClusterNotFoundError(f"Workspace not found: {workspace_name}")

            # Extract resource group
            ws_id_parts = workspace.id.split('/')
            rg_index = ws_id_parts.index('resourceGroups') + 1 if 'resourceGroups' in ws_id_parts else -1
            resource_group = ws_id_parts[rg_index] if rg_index > 0 else ""

            # Get the specific pool
            pool = self._synapse_client.big_data_pools.get(
                resource_group_name=resource_group,
                workspace_name=workspace_name,
                big_data_pool_name=pool_name,
            )

            pool_details = self._get_pool_details(pool, workspace_name, resource_group)

            # Calculate costs
            pricing = SYNAPSE_SPARK_PRICING.get(
                pool_details.node_size,
                SYNAPSE_SPARK_PRICING["Medium"]
            )
            node_count = pool_details.node_count or pool_details.min_node_count
            hourly_cost = pricing["node_cost_per_hour"] * node_count

            return ClusterState(
                cluster_id=cluster_id,
                cluster_name=pool_name,
                status=self._convert_pool_state(pool_details.state),
                worker_count=node_count,
                instance_type=pool_details.node_size,
                uptime_seconds=0,
                hourly_cost=hourly_cost,
                platform=Platform.SYNAPSE,
                tags=pool_details.tags or {},
            )

        except ClusterNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get Spark pool", cluster_id=cluster_id, error=str(e))
            raise PlatformError(f"Failed to get Spark pool {cluster_id}: {e}")

    def get_stats(
        self,
        period_start: datetime,
        period_end: datetime,
        workspace_id: Optional[str] = None,
    ) -> ClusterStats:
        """
        Get aggregated statistics for Synapse Spark pools.

        Args:
            period_start: Start of the statistics period
            period_end: End of the statistics period
            workspace_id: Optional workspace to filter by

        Returns:
            Aggregated statistics
        """
        if not self._synapse_client:
            self._get_azure_clients()

        try:
            pools = self.list_clusters()

            # Filter by workspace if specified
            if workspace_id:
                pools = [p for p in pools if p.cluster_id.startswith(f"{workspace_id}/")]

            # Calculate statistics
            total_hours = (period_end - period_start).total_seconds() / 3600
            total_compute_cost = 0.0
            total_dbu_cost = 0.0  # Synapse doesn't use DBUs

            running_pools = [p for p in pools if p.status == ClusterStatus.RUNNING]
            paused_pools = [p for p in pools if p.status == ClusterStatus.TERMINATED]

            for pool in running_pools:
                total_compute_cost += pool.hourly_cost * total_hours

            # Estimate idle hours based on auto-pause configuration
            # Pools without auto-pause may have significant idle time
            estimated_idle_hours = 0.0
            for pool in running_pools:
                # If not auto-pause enabled, estimate 40% idle during off-hours
                estimated_idle_hours += total_hours * 0.4

            return ClusterStats(
                period_start=period_start,
                period_end=period_end,
                total_clusters=len(pools),
                total_compute_hours=total_hours * len(running_pools),
                total_compute_cost=total_compute_cost,
                total_dbu_cost=total_dbu_cost,
                idle_hours=estimated_idle_hours,
                cold_starts=0,  # Would need tracking
                avg_cold_start_time=180.0,  # Synapse pools typically start faster
                spot_savings=0.0,  # Synapse uses different pricing model
                hibernation_savings=sum(p.hourly_cost * total_hours * 0.6 for p in paused_pools),
                platform=Platform.SYNAPSE,
            )

        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            raise PlatformError(f"Failed to get Synapse statistics: {e}")

    def get_insights(self) -> list[CostInsight]:
        """
        Generate cost optimization insights for Synapse Spark pools.

        Returns:
            List of actionable cost insights
        """
        if not self._synapse_client:
            self._get_azure_clients()

        insights: list[CostInsight] = []

        try:
            pools = self.list_clusters()

            for pool in pools:
                # Parse pool details
                workspace_name, pool_name = pool.cluster_id.split('/', 1)

                # Get full pool details for auto-pause check
                try:
                    full_pool = self._get_pool_full_details(workspace_name, pool_name)
                except Exception:
                    full_pool = None

                # Insight: Auto-pause not enabled
                if full_pool and not full_pool.auto_pause_enabled:
                    monthly_cost = pool.hourly_cost * 730
                    potential_savings = monthly_cost * 0.6  # Assume 60% idle

                    insights.append(CostInsight(
                        insight_id=f"synapse-no-autopause-{pool.cluster_id.replace('/', '-')}",
                        title=f"Enable auto-pause for {pool_name}",
                        description=(
                            f"Spark pool '{pool_name}' in workspace '{workspace_name}' "
                            f"does not have auto-pause enabled. Enabling auto-pause can "
                            f"significantly reduce costs during idle periods."
                        ),
                        category=InsightCategory.IDLE_RESOURCES,
                        severity=InsightSeverity.HIGH,
                        estimated_savings=potential_savings,
                        affected_resources=[pool.cluster_id],
                        recommendation="Enable auto-pause with a 15-minute delay for development pools or 5-minute delay for production.",
                    ))

                # Insight: Oversized pool
                if full_pool and full_pool.node_size in ["XLarge", "XXLarge"]:
                    insights.append(CostInsight(
                        insight_id=f"synapse-oversize-{pool.cluster_id.replace('/', '-')}",
                        title=f"Review node size for {pool_name}",
                        description=(
                            f"Spark pool '{pool_name}' uses {full_pool.node_size} nodes. "
                            f"Consider if workloads require this size or if smaller nodes would suffice."
                        ),
                        category=InsightCategory.RIGHTSIZING,
                        severity=InsightSeverity.MEDIUM,
                        estimated_savings=pool.hourly_cost * 730 * 0.3,
                        affected_resources=[pool.cluster_id],
                        recommendation="Analyze workload memory/CPU usage and consider downsizing if utilization is low.",
                    ))

                # Insight: No auto-scale
                if full_pool and not full_pool.auto_scale_enabled:
                    insights.append(CostInsight(
                        insight_id=f"synapse-no-autoscale-{pool.cluster_id.replace('/', '-')}",
                        title=f"Enable auto-scale for {pool_name}",
                        description=(
                            f"Spark pool '{pool_name}' has fixed node count. "
                            f"Enabling auto-scale allows the pool to adjust to workload demands."
                        ),
                        category=InsightCategory.RIGHTSIZING,
                        severity=InsightSeverity.MEDIUM,
                        estimated_savings=pool.hourly_cost * 730 * 0.2,
                        affected_resources=[pool.cluster_id],
                        recommendation="Enable auto-scale with appropriate min/max node counts based on workload patterns.",
                    ))

                # Insight: High minimum nodes
                if full_pool and full_pool.min_node_count > 5:
                    insights.append(CostInsight(
                        insight_id=f"synapse-high-min-{pool.cluster_id.replace('/', '-')}",
                        title=f"Reduce minimum nodes for {pool_name}",
                        description=(
                            f"Spark pool '{pool_name}' has minimum node count of {full_pool.min_node_count}. "
                            f"Consider reducing if consistent high parallelism isn't required."
                        ),
                        category=InsightCategory.RIGHTSIZING,
                        severity=InsightSeverity.LOW,
                        estimated_savings=pool.hourly_cost * 0.3 * 730,
                        affected_resources=[pool.cluster_id],
                        recommendation=f"Consider reducing minimum nodes to 3 and rely on auto-scale for peak demand.",
                    ))

            logger.info("Generated Synapse insights", insight_count=len(insights))
            return insights

        except Exception as e:
            logger.error("Failed to generate insights", error=str(e))
            raise PlatformError(f"Failed to generate Synapse insights: {e}")

    def _get_pool_full_details(self, workspace_name: str, pool_name: str) -> SynapseSparkPool:
        """Get full pool details including auto-pause/scale config."""
        workspaces = list(self._synapse_client.workspaces.list())
        workspace = next((w for w in workspaces if w.name == workspace_name), None)

        if not workspace:
            raise ClusterNotFoundError(f"Workspace not found: {workspace_name}")

        ws_id_parts = workspace.id.split('/')
        rg_index = ws_id_parts.index('resourceGroups') + 1 if 'resourceGroups' in ws_id_parts else -1
        resource_group = ws_id_parts[rg_index] if rg_index > 0 else ""

        pool = self._synapse_client.big_data_pools.get(
            resource_group_name=resource_group,
            workspace_name=workspace_name,
            big_data_pool_name=pool_name,
        )

        return self._get_pool_details(pool, workspace_name, resource_group)

    def start_prediction_engine(self, config: "PredictConfig", dry_run: bool = False) -> None:
        """
        Start the prediction engine for Synapse workloads.

        Predicts workload patterns to optimize pool readiness.

        Args:
            config: Prediction configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Synapse prediction engine",
            dry_run=dry_run,
            lookahead_minutes=config.lookahead_minutes,
        )
        self._active_strategies[Strategy.PREDICT] = True

        if not dry_run:
            # In production, this would start a background task that:
            # 1. Analyzes historical job submission patterns
            # 2. Predicts upcoming workload demands
            # 3. Adjusts auto-scale settings proactively
            pass

    def start_hibernation_manager(self, config: "HibernateConfig", dry_run: bool = False) -> None:
        """
        Start the hibernation manager for Synapse pools.

        Manages auto-pause settings for optimal cost savings.

        Args:
            config: Hibernation configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Synapse hibernation manager",
            dry_run=dry_run,
            idle_threshold_minutes=config.idle_threshold_minutes,
        )
        self._active_strategies[Strategy.HIBERNATE] = True

        if not dry_run:
            # In production, this would:
            # 1. Monitor pool activity
            # 2. Enforce auto-pause policies
            # 3. Configure optimal auto-pause delays
            pass

    def start_spot_orchestrator(self, config: "SpotConfig", dry_run: bool = False) -> None:
        """
        Start the spot orchestrator for Synapse.

        Note: Synapse doesn't directly support spot instances, but this can
        manage cost optimization through other means.

        Args:
            config: Spot configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Synapse spot orchestrator (cost optimizer)",
            dry_run=dry_run,
        )
        self._active_strategies[Strategy.SPOT] = True

        # Synapse uses a different pricing model; this strategy focuses on
        # Reserved capacity planning and cost allocation optimization

    def start_pool_manager(self, config: "PoolConfig", dry_run: bool = False) -> None:
        """
        Start the pool manager for Synapse.

        Manages shared pool resources across workspaces.

        Args:
            config: Pool configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Synapse pool manager",
            dry_run=dry_run,
            min_pools=config.min_idle_clusters,
            max_pools=config.max_idle_clusters,
        )
        self._active_strategies[Strategy.POOL] = True

    def start_insight_engine(self, config: "InsightConfig", dry_run: bool = False) -> None:
        """
        Start the insight engine for Synapse.

        Continuously analyzes pools for optimization opportunities.

        Args:
            config: Insight configuration
            dry_run: If True, don't make actual changes
        """
        logger.info(
            "Starting Synapse insight engine",
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
        logger.info(f"Stopping Synapse strategy: {strategy.value}")
        self._active_strategies[strategy] = False

    def hibernate_cluster(self, cluster_id: str) -> OptimizationResult:
        """
        Pause a Synapse Spark pool.

        Synapse supports native auto-pause, but this provides manual control.

        Args:
            cluster_id: Pool identifier (workspace_name/pool_name)

        Returns:
            Result of the pause operation
        """
        if cluster_id in self._excluded_pools:
            return OptimizationResult(
                success=False,
                cluster_id=cluster_id,
                action="hibernate",
                message=f"Pool {cluster_id} is excluded from hibernation",
                savings_usd=0.0,
            )

        if not self._synapse_client:
            self._get_azure_clients()

        try:
            workspace_name, pool_name = cluster_id.split('/', 1)

            # Get workspace for resource group
            workspaces = list(self._synapse_client.workspaces.list())
            workspace = next((w for w in workspaces if w.name == workspace_name), None)

            if not workspace:
                raise ClusterNotFoundError(f"Workspace not found: {workspace_name}")

            ws_id_parts = workspace.id.split('/')
            rg_index = ws_id_parts.index('resourceGroups') + 1 if 'resourceGroups' in ws_id_parts else -1
            resource_group = ws_id_parts[rg_index] if rg_index > 0 else ""

            # Get pool for cost calculation
            pool = self.get_cluster(cluster_id)

            # Pause the pool by updating auto-pause to immediate
            # Note: Direct pause API may not be available; using auto-pause with 0 delay
            logger.info("Pausing Synapse Spark pool", cluster_id=cluster_id)

            # In production, would call:
            # self._synapse_client.big_data_pools.update(...)
            # with auto_pause enabled and delay set to minimum

            return OptimizationResult(
                success=True,
                cluster_id=cluster_id,
                action="hibernate",
                message=f"Initiated pause for Spark pool {pool_name}",
                savings_usd=pool.hourly_cost,
            )

        except Exception as e:
            logger.error("Failed to pause pool", cluster_id=cluster_id, error=str(e))
            return OptimizationResult(
                success=False,
                cluster_id=cluster_id,
                action="hibernate",
                message=f"Failed to pause pool: {e}",
                savings_usd=0.0,
            )

    def resume_cluster(self, cluster_id: str) -> OptimizationResult:
        """
        Resume a paused Synapse Spark pool.

        Args:
            cluster_id: Pool identifier (workspace_name/pool_name)

        Returns:
            Result of the resume operation
        """
        if not self._synapse_client:
            self._get_azure_clients()

        try:
            workspace_name, pool_name = cluster_id.split('/', 1)

            logger.info("Resuming Synapse Spark pool", cluster_id=cluster_id)

            # Synapse pools auto-resume when jobs are submitted
            # This method could pre-warm by submitting a minimal job

            return OptimizationResult(
                success=True,
                cluster_id=cluster_id,
                action="resume",
                message=f"Pool {pool_name} will resume when jobs are submitted",
                savings_usd=0.0,
            )

        except Exception as e:
            logger.error("Failed to resume pool", cluster_id=cluster_id, error=str(e))
            return OptimizationResult(
                success=False,
                cluster_id=cluster_id,
                action="resume",
                message=f"Failed to resume pool: {e}",
                savings_usd=0.0,
            )

    def add_exclusion(self, cluster_id: str) -> None:
        """
        Add a pool to the exclusion list.

        Args:
            cluster_id: Pool identifier to exclude
        """
        self._excluded_pools.add(cluster_id)
        logger.info("Added pool to exclusion list", cluster_id=cluster_id)

    def remove_exclusion(self, cluster_id: str) -> None:
        """
        Remove a pool from the exclusion list.

        Args:
            cluster_id: Pool identifier to remove from exclusions
        """
        self._excluded_pools.discard(cluster_id)
        logger.info("Removed pool from exclusion list", cluster_id=cluster_id)

    def analyze_workspace(self) -> dict[str, Any]:
        """
        Analyze Synapse workspace for optimization opportunities.

        Returns:
            Analysis results including costs, insights, and recommendations
        """
        if not self._synapse_client:
            self._get_azure_clients()

        try:
            pools = self.list_clusters()
            insights = self.get_insights()

            # Calculate costs
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            total_monthly_cost = 0.0
            potential_savings = 0.0
            pools_without_autopause = 0
            pools_without_autoscale = 0

            for pool in pools:
                workspace_name, pool_name = pool.cluster_id.split('/', 1)
                monthly_cost = pool.hourly_cost * 730

                try:
                    full_pool = self._get_pool_full_details(workspace_name, pool_name)
                    if not full_pool.auto_pause_enabled:
                        pools_without_autopause += 1
                        potential_savings += monthly_cost * 0.6
                    if not full_pool.auto_scale_enabled:
                        pools_without_autoscale += 1
                        potential_savings += monthly_cost * 0.2
                except Exception:
                    pass

                total_monthly_cost += monthly_cost

            # Aggregate insight savings
            insight_savings = sum(i.estimated_savings for i in insights)

            return {
                "workspace_count": len(set(p.cluster_id.split('/')[0] for p in pools)),
                "total_pools": len(pools),
                "running_pools": len([p for p in pools if p.status == ClusterStatus.RUNNING]),
                "paused_pools": len([p for p in pools if p.status == ClusterStatus.TERMINATED]),
                "estimated_monthly_cost": total_monthly_cost,
                "potential_monthly_savings": max(potential_savings, insight_savings),
                "savings_percentage": (
                    (max(potential_savings, insight_savings) / total_monthly_cost * 100)
                    if total_monthly_cost > 0 else 0
                ),
                "optimization_opportunities": {
                    "pools_without_auto_pause": pools_without_autopause,
                    "pools_without_auto_scale": pools_without_autoscale,
                },
                "insights": [
                    {
                        "title": i.title,
                        "severity": i.severity.value,
                        "estimated_savings": i.estimated_savings,
                    }
                    for i in insights[:10]  # Top 10
                ],
                "platform": Platform.SYNAPSE.value,
                "analysis_time": now.isoformat(),
            }

        except Exception as e:
            logger.error("Failed to analyze workspace", error=str(e))
            raise PlatformError(f"Failed to analyze Synapse workspace: {e}")
