"""
Ghost Compute - Intelligent Serverless Orchestration for Data Platforms

Ghost eliminates the $44.5B annual waste from idle clusters and cold start latency
in enterprise data infrastructure. Drop-in optimization for Databricks, EMR,
Synapse, and Spark workloads.

Quick Start:
    from ghost import GhostClient

    ghost = GhostClient(
        platform="databricks",
        credentials_path="~/.ghost/credentials.json"
    )

    ghost.optimize(
        workspace_id="your-workspace",
        strategies=["predict", "hibernate", "spot"],
        target_savings=0.40
    )

For more information, visit: https://docs.ghost-compute.io
"""

from ghost.core.client import GhostClient
from ghost.core.config import GhostConfig
from ghost.core.models import (
    ClusterState,
    ClusterStats,
    OptimizationResult,
    Strategy,
    Platform,
)
from ghost.core.exceptions import (
    GhostError,
    ConfigurationError,
    PlatformError,
    OptimizationError,
)

__version__ = "0.1.0"
__author__ = "Ghost AI"
__email__ = "engineering@ghost-ai.io"

__all__ = [
    # Main client
    "GhostClient",
    # Configuration
    "GhostConfig",
    # Models
    "ClusterState",
    "ClusterStats",
    "OptimizationResult",
    "Strategy",
    "Platform",
    # Exceptions
    "GhostError",
    "ConfigurationError",
    "PlatformError",
    "OptimizationError",
    # Version
    "__version__",
]
