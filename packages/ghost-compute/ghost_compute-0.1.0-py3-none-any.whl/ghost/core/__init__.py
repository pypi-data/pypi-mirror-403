"""
Core Ghost Compute components.

This package contains the fundamental building blocks of Ghost:
- Client: Main interface for using Ghost
- Config: Configuration management
- Models: Data structures
- Exceptions: Error types
"""

from ghost.core.client import GhostClient
from ghost.core.config import GhostConfig, get_config
from ghost.core.models import (
    Platform,
    Strategy,
    ClusterState,
    ClusterStatus,
    ClusterStats,
    InstanceType,
    OptimizationResult,
    PredictionResult,
    HibernateResult,
    SpotAllocation,
    CostInsight,
    WorkloadPattern,
)
from ghost.core.exceptions import (
    GhostError,
    ConfigurationError,
    PlatformError,
    AuthenticationError,
    OptimizationError,
    HibernationError,
    PredictionError,
    SpotError,
    PoolError,
    ResourceNotFoundError,
    RateLimitError,
    ValidationError,
    StateError,
)

__all__ = [
    # Client
    "GhostClient",
    # Config
    "GhostConfig",
    "get_config",
    # Models
    "Platform",
    "Strategy",
    "ClusterState",
    "ClusterStatus",
    "ClusterStats",
    "InstanceType",
    "OptimizationResult",
    "PredictionResult",
    "HibernateResult",
    "SpotAllocation",
    "CostInsight",
    "WorkloadPattern",
    # Exceptions
    "GhostError",
    "ConfigurationError",
    "PlatformError",
    "AuthenticationError",
    "OptimizationError",
    "HibernationError",
    "PredictionError",
    "SpotError",
    "PoolError",
    "ResourceNotFoundError",
    "RateLimitError",
    "ValidationError",
    "StateError",
]
