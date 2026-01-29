"""
Main Ghost client for interacting with the optimization engine.

This module provides the primary interface for using Ghost Compute,
handling platform connections, strategy execution, and monitoring.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Callable, Awaitable
import json

import structlog

from ghost.core.config import GhostConfig
from ghost.core.models import (
    Platform,
    Strategy,
    ClusterState,
    ClusterStats,
    ClusterStatus,
    OptimizationResult,
    CostInsight,
)
from ghost.core.exceptions import (
    GhostError,
    ConfigurationError,
    PlatformError,
    AuthenticationError,
)

logger = structlog.get_logger(__name__)


class GhostClient:
    """
    Main client for Ghost Compute optimization.

    The GhostClient provides a high-level interface for:
    - Connecting to data platforms (Databricks, EMR, Synapse, etc.)
    - Enabling and configuring optimization strategies
    - Monitoring cluster states and cost savings
    - Generating insights and recommendations

    Example:
        ```python
        from ghost import GhostClient

        # Initialize client
        ghost = GhostClient(
            platform="databricks",
            workspace_url="https://xxx.cloud.databricks.com",
            credentials_path="~/.ghost/credentials.json"
        )

        # Enable optimization
        ghost.optimize(strategies=["predict", "hibernate", "spot"])

        # Check status
        stats = ghost.get_stats()
        print(f"Saved ${stats.savings_usd:,.2f} this month")
        ```

    Attributes:
        config: The Ghost configuration
        platform: The data platform being optimized
        connected: Whether the client is connected to the platform
    """

    def __init__(
        self,
        platform: str | Platform | None = None,
        workspace_url: str | None = None,
        workspace_id: str | None = None,
        credentials_path: str | Path | None = None,
        config: GhostConfig | None = None,
        config_path: str | Path | None = None,
        platform_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the Ghost client.

        Args:
            platform: Data platform to connect to
            workspace_url: Platform workspace URL
            workspace_id: Platform workspace ID
            credentials_path: Path to credentials file
            config: Pre-built GhostConfig object
            config_path: Path to ghost.yaml configuration file
            platform_config: Platform-specific configuration (e.g., region, project_id)

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Load configuration
        if config:
            self.config = config
        elif config_path:
            self.config = GhostConfig.from_yaml(config_path)
        else:
            self.config = GhostConfig.discover()

        # Override with explicit parameters
        if platform:
            self.config.platform = Platform(platform) if isinstance(platform, str) else platform
        if workspace_url:
            self.config.workspace_url = workspace_url
        if workspace_id:
            self.config.workspace_id = workspace_id
        if credentials_path:
            self.config.credentials_path = Path(credentials_path).expanduser()
        if platform_config:
            self.config.platform_config = platform_config

        # State
        self._connected = False
        self._integration: Any = None
        self._optimization_active = False
        self._active_strategies: list[Strategy] = []

        # Callbacks
        self._on_optimization: Optional[Callable[[OptimizationResult], Awaitable[None]]] = None
        self._on_alert: Optional[Callable[[CostInsight], Awaitable[None]]] = None

        logger.info(
            "Ghost client initialized",
            platform=self.config.platform.value,
            workspace_url=self.config.workspace_url,
        )

    @property
    def platform(self) -> Platform:
        """Get the configured platform."""
        return self.config.platform

    @property
    def connected(self) -> bool:
        """Check if client is connected to platform."""
        return self._connected

    def connect(self) -> "GhostClient":
        """
        Connect to the data platform.

        Establishes connection using configured credentials and validates
        that Ghost has the necessary permissions.

        Returns:
            Self for method chaining

        Raises:
            AuthenticationError: If credentials are invalid
            PlatformError: If connection fails
        """
        if self._connected:
            logger.debug("Already connected to platform")
            return self

        logger.info("Connecting to platform", platform=self.config.platform.value)

        # Validate configuration
        self.config.validate_for_platform()

        # Load integration
        self._integration = self._load_integration()

        # Test connection
        try:
            self._integration.test_connection()
        except Exception as e:
            raise PlatformError(
                f"Failed to connect to {self.config.platform.value}: {e}",
                platform=self.config.platform.value,
                operation="connect",
            ) from e

        self._connected = True
        logger.info("Successfully connected to platform")

        return self

    def _load_integration(self) -> Any:
        """Load the appropriate platform integration."""
        from ghost.integrations import get_integration

        return get_integration(
            platform=self.config.platform,
            config=self.config,
        )

    def disconnect(self) -> None:
        """Disconnect from the platform and stop all optimization."""
        if not self._connected:
            return

        logger.info("Disconnecting from platform")

        if self._optimization_active:
            self.stop_optimization()

        if self._integration:
            self._integration.close()
            self._integration = None

        self._connected = False

    def optimize(
        self,
        workspace_id: str | None = None,
        strategies: list[str | Strategy] | None = None,
        target_savings: float = 0.30,
        dry_run: bool | None = None,
    ) -> "GhostClient":
        """
        Enable Ghost optimization for the workspace.

        This is the main method to start optimizing your clusters.
        Ghost will automatically apply the specified strategies to
        reduce costs and improve performance.

        Args:
            workspace_id: Workspace to optimize (uses configured if not specified)
            strategies: List of strategies to enable (uses configured if not specified)
            target_savings: Target savings percentage (0.0 to 1.0)
            dry_run: If True, don't make changes, just report

        Returns:
            Self for method chaining

        Example:
            ```python
            ghost.optimize(
                strategies=["predict", "hibernate", "spot"],
                target_savings=0.40
            )
            ```
        """
        if not self._connected:
            self.connect()

        # Parse strategies
        if strategies is None:
            self._active_strategies = self.config.strategies.get_enabled_strategies()
        else:
            self._active_strategies = [
                Strategy(s) if isinstance(s, str) else s
                for s in strategies
            ]

        # Use workspace_id from config if not specified
        workspace_id = workspace_id or self.config.workspace_id

        # Use dry_run from config if not specified
        if dry_run is None:
            dry_run = self.config.dry_run

        logger.info(
            "Starting optimization",
            workspace_id=workspace_id,
            strategies=[s.value for s in self._active_strategies],
            target_savings=target_savings,
            dry_run=dry_run,
        )

        # Start optimization for each strategy
        for strategy in self._active_strategies:
            self._start_strategy(strategy, workspace_id, target_savings, dry_run)

        self._optimization_active = True

        return self

    def _start_strategy(
        self,
        strategy: Strategy,
        workspace_id: str | None,
        target_savings: float,
        dry_run: bool,
    ) -> None:
        """Start a specific optimization strategy."""
        logger.debug(f"Starting strategy: {strategy.value}")

        if strategy == Strategy.PREDICT:
            self._integration.start_prediction_engine(
                config=self.config.strategies.predict,
                dry_run=dry_run,
            )
        elif strategy == Strategy.HIBERNATE:
            self._integration.start_hibernation_manager(
                config=self.config.strategies.hibernate,
                dry_run=dry_run,
            )
        elif strategy == Strategy.SPOT:
            self._integration.start_spot_orchestrator(
                config=self.config.strategies.spot,
                dry_run=dry_run,
            )
        elif strategy == Strategy.POOL:
            self._integration.start_pool_manager(
                config=self.config.strategies.pool,
                dry_run=dry_run,
            )
        elif strategy == Strategy.INSIGHT:
            self._integration.start_insight_engine(
                config=self.config.strategies.insight,
                dry_run=dry_run,
            )

    def stop_optimization(self) -> None:
        """Stop all optimization strategies."""
        if not self._optimization_active:
            return

        logger.info("Stopping optimization")

        for strategy in self._active_strategies:
            self._stop_strategy(strategy)

        self._active_strategies = []
        self._optimization_active = False

    def _stop_strategy(self, strategy: Strategy) -> None:
        """Stop a specific optimization strategy."""
        logger.debug(f"Stopping strategy: {strategy.value}")

        if self._integration:
            self._integration.stop_strategy(strategy)

    def get_clusters(
        self,
        status: ClusterStatus | None = None,
        ghost_managed: bool | None = None,
    ) -> list[ClusterState]:
        """
        Get list of clusters with their current states.

        Args:
            status: Filter by cluster status
            ghost_managed: Filter by Ghost management status

        Returns:
            List of ClusterState objects
        """
        if not self._connected:
            self.connect()

        clusters = self._integration.list_clusters()

        # Apply filters
        if status is not None:
            clusters = [c for c in clusters if c.status == status]

        if ghost_managed is not None:
            clusters = [c for c in clusters if c.ghost_managed == ghost_managed]

        return clusters

    def get_cluster(self, cluster_id: str) -> ClusterState:
        """
        Get details for a specific cluster.

        Args:
            cluster_id: The cluster identifier

        Returns:
            ClusterState for the cluster

        Raises:
            ResourceNotFoundError: If cluster doesn't exist
        """
        if not self._connected:
            self.connect()

        return self._integration.get_cluster(cluster_id)

    def get_stats(
        self,
        period_days: int = 30,
        workspace_id: str | None = None,
    ) -> ClusterStats:
        """
        Get aggregated statistics for Ghost optimization.

        Args:
            period_days: Number of days to include in statistics
            workspace_id: Filter to specific workspace

        Returns:
            ClusterStats with aggregated metrics
        """
        if not self._connected:
            self.connect()

        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()

        return self._integration.get_stats(
            period_start=period_start,
            period_end=period_end,
            workspace_id=workspace_id,
        )

    def get_insights(
        self,
        min_savings_usd: float = 0,
        categories: list[str] | None = None,
    ) -> list[CostInsight]:
        """
        Get cost optimization insights and recommendations.

        Args:
            min_savings_usd: Minimum estimated savings to include
            categories: Filter to specific insight categories

        Returns:
            List of CostInsight recommendations
        """
        if not self._connected:
            self.connect()

        insights = self._integration.get_insights()

        # Apply filters
        if min_savings_usd > 0:
            insights = [i for i in insights if i.estimated_monthly_savings_usd >= min_savings_usd]

        if categories:
            insights = [i for i in insights if i.category in categories]

        return sorted(insights, key=lambda i: i.estimated_monthly_savings_usd, reverse=True)

    def hibernate_cluster(self, cluster_id: str) -> OptimizationResult:
        """
        Manually hibernate a specific cluster.

        Args:
            cluster_id: The cluster to hibernate

        Returns:
            OptimizationResult with operation details
        """
        if not self._connected:
            self.connect()

        return self._integration.hibernate_cluster(cluster_id)

    def resume_cluster(self, cluster_id: str) -> OptimizationResult:
        """
        Resume a hibernated cluster.

        Args:
            cluster_id: The cluster to resume

        Returns:
            OptimizationResult with operation details
        """
        if not self._connected:
            self.connect()

        return self._integration.resume_cluster(cluster_id)

    def exclude_cluster(self, cluster_id: str) -> None:
        """
        Exclude a cluster from Ghost management.

        Args:
            cluster_id: The cluster to exclude
        """
        if not self._connected:
            self.connect()

        self._integration.add_exclusion(cluster_id)
        logger.info(f"Excluded cluster from Ghost management: {cluster_id}")

    def include_cluster(self, cluster_id: str) -> None:
        """
        Include a previously excluded cluster in Ghost management.

        Args:
            cluster_id: The cluster to include
        """
        if not self._connected:
            self.connect()

        self._integration.remove_exclusion(cluster_id)
        logger.info(f"Included cluster in Ghost management: {cluster_id}")

    def analyze(self, output_path: str | Path | None = None) -> dict[str, Any]:
        """
        Analyze current cluster usage and potential savings.

        This method performs a comprehensive analysis without making
        any changes, useful for understanding potential impact before
        enabling optimization.

        Args:
            output_path: Path to save analysis report (JSON)

        Returns:
            Dictionary with analysis results
        """
        if not self._connected:
            self.connect()

        logger.info("Running cluster analysis")

        analysis = self._integration.analyze_workspace()

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"Analysis saved to {output_path}")

        return analysis

    def on_optimization(
        self,
        callback: Callable[[OptimizationResult], Awaitable[None]],
    ) -> "GhostClient":
        """
        Register callback for optimization events.

        Args:
            callback: Async function to call on optimization events

        Returns:
            Self for method chaining
        """
        self._on_optimization = callback
        return self

    def on_alert(
        self,
        callback: Callable[[CostInsight], Awaitable[None]],
    ) -> "GhostClient":
        """
        Register callback for cost alerts.

        Args:
            callback: Async function to call on cost alerts

        Returns:
            Self for method chaining
        """
        self._on_alert = callback
        return self

    def __enter__(self) -> "GhostClient":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()

    async def __aenter__(self) -> "GhostClient":
        """Async context manager entry."""
        self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        self.disconnect()
