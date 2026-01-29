"""
Platform integrations for Ghost Compute.

This package provides integrations with various data platforms:
- Databricks
- Amazon EMR
- Azure Synapse
- Google Dataproc
- Cloudera CDP
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

from ghost.core.models import (
    Platform,
    Strategy,
    ClusterState,
    ClusterStats,
    OptimizationResult,
    CostInsight,
)

if TYPE_CHECKING:
    from ghost.core.config import (
        GhostConfig,
        PredictConfig,
        HibernateConfig,
        SpotConfig,
        PoolConfig,
        InsightConfig,
    )


class BaseIntegration(ABC):
    """
    Abstract base class for platform integrations.

    All platform integrations must implement this interface to ensure
    consistent behavior across different data platforms.
    """

    def __init__(self, config: "GhostConfig") -> None:
        """
        Initialize the integration.

        Args:
            config: Ghost configuration
        """
        self.config = config
        self._connected = False

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Return the platform this integration supports."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the platform.

        Returns:
            True if connection is successful

        Raises:
            AuthenticationError: If credentials are invalid
            PlatformError: If connection fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection and cleanup resources."""
        pass

    # Cluster Management

    @abstractmethod
    def list_clusters(self) -> list[ClusterState]:
        """
        List all clusters in the workspace.

        Returns:
            List of ClusterState objects
        """
        pass

    @abstractmethod
    def get_cluster(self, cluster_id: str) -> ClusterState:
        """
        Get details for a specific cluster.

        Args:
            cluster_id: Cluster identifier

        Returns:
            ClusterState for the cluster

        Raises:
            ResourceNotFoundError: If cluster doesn't exist
        """
        pass

    # Statistics

    @abstractmethod
    def get_stats(
        self,
        period_start: datetime,
        period_end: datetime,
        workspace_id: Optional[str] = None,
    ) -> ClusterStats:
        """
        Get aggregated statistics.

        Args:
            period_start: Start of statistics period
            period_end: End of statistics period
            workspace_id: Optional workspace filter

        Returns:
            Aggregated ClusterStats
        """
        pass

    # Insights

    @abstractmethod
    def get_insights(self) -> list[CostInsight]:
        """
        Get cost optimization insights.

        Returns:
            List of CostInsight recommendations
        """
        pass

    # Strategy Management

    @abstractmethod
    def start_prediction_engine(
        self,
        config: "PredictConfig",
        dry_run: bool = False,
    ) -> None:
        """Start the prediction engine."""
        pass

    @abstractmethod
    def start_hibernation_manager(
        self,
        config: "HibernateConfig",
        dry_run: bool = False,
    ) -> None:
        """Start the hibernation manager."""
        pass

    @abstractmethod
    def start_spot_orchestrator(
        self,
        config: "SpotConfig",
        dry_run: bool = False,
    ) -> None:
        """Start the spot instance orchestrator."""
        pass

    @abstractmethod
    def start_pool_manager(
        self,
        config: "PoolConfig",
        dry_run: bool = False,
    ) -> None:
        """Start the resource pool manager."""
        pass

    @abstractmethod
    def start_insight_engine(
        self,
        config: "InsightConfig",
        dry_run: bool = False,
    ) -> None:
        """Start the insight/recommendation engine."""
        pass

    @abstractmethod
    def stop_strategy(self, strategy: Strategy) -> None:
        """Stop a specific strategy."""
        pass

    # Operations

    @abstractmethod
    def hibernate_cluster(self, cluster_id: str) -> OptimizationResult:
        """Hibernate a cluster."""
        pass

    @abstractmethod
    def resume_cluster(self, cluster_id: str) -> OptimizationResult:
        """Resume a hibernated cluster."""
        pass

    @abstractmethod
    def add_exclusion(self, cluster_id: str) -> None:
        """Add a cluster to exclusion list."""
        pass

    @abstractmethod
    def remove_exclusion(self, cluster_id: str) -> None:
        """Remove a cluster from exclusion list."""
        pass

    @abstractmethod
    def analyze_workspace(self) -> dict[str, Any]:
        """
        Analyze workspace for optimization opportunities.

        Returns:
            Analysis results dictionary
        """
        pass


def get_integration(platform: Platform, config: "GhostConfig") -> BaseIntegration:
    """
    Factory function to get the appropriate integration.

    Args:
        platform: Target platform
        config: Ghost configuration

    Returns:
        Platform-specific integration instance

    Raises:
        ValueError: If platform is not supported
    """
    from ghost.integrations.databricks import DatabricksIntegration
    from ghost.integrations.emr import EMRIntegration
    from ghost.integrations.synapse import SynapseIntegration
    from ghost.integrations.dataproc import DataprocIntegration

    integrations = {
        Platform.DATABRICKS: DatabricksIntegration,
        Platform.EMR: EMRIntegration,
        Platform.SYNAPSE: SynapseIntegration,
        Platform.DATAPROC: DataprocIntegration,
    }

    integration_class = integrations.get(platform)
    if not integration_class:
        raise ValueError(f"Unsupported platform: {platform.value}")

    return integration_class(config)


__all__ = [
    "BaseIntegration",
    "get_integration",
]
