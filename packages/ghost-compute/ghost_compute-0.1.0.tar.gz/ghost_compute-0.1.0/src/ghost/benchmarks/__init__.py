"""
Ghost Compute Benchmarking Framework.

This module provides tools for benchmarking Ghost optimization performance
against baseline (no optimization) and competitor solutions.
"""

from ghost.benchmarks.pricing_data import (
    PricingData,
    get_aws_pricing,
    get_azure_pricing,
    get_databricks_pricing,
    get_spot_pricing,
)
from ghost.benchmarks.competitors import (
    CompetitorModel,
    PepperdataModel,
    SyncComputingModel,
    UnravelModel,
    NativeAutoscalingModel,
    NoOptimizationModel,
)
from ghost.benchmarks.simulator import (
    WorkloadSimulator,
    ClusterSimulation,
    BenchmarkResult,
)
from ghost.benchmarks.runner import (
    BenchmarkRunner,
    ComparisonReport,
    run_full_benchmark,
)

__all__ = [
    # Pricing
    "PricingData",
    "get_aws_pricing",
    "get_azure_pricing",
    "get_databricks_pricing",
    "get_spot_pricing",
    # Competitors
    "CompetitorModel",
    "PepperdataModel",
    "SyncComputingModel",
    "UnravelModel",
    "NativeAutoscalingModel",
    "NoOptimizationModel",
    # Simulator
    "WorkloadSimulator",
    "ClusterSimulation",
    "BenchmarkResult",
    # Runner
    "BenchmarkRunner",
    "ComparisonReport",
    "run_full_benchmark",
]
