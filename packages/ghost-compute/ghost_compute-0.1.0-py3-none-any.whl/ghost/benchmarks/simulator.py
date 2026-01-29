"""
Workload simulation for benchmarking.

Simulates realistic enterprise data platform workloads to compare
optimization solutions under various scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import random
import math


class WorkloadType(str, Enum):
    """Types of data platform workloads."""

    ETL_BATCH = "etl_batch"  # Scheduled ETL jobs
    INTERACTIVE = "interactive"  # Ad-hoc queries, notebooks
    STREAMING = "streaming"  # Real-time processing
    ML_TRAINING = "ml_training"  # Machine learning workloads
    REPORTING = "reporting"  # BI and reporting queries
    MIXED = "mixed"  # Combination of above


class ClusterSize(str, Enum):
    """Cluster size categories."""

    SMALL = "small"  # 2-4 workers
    MEDIUM = "medium"  # 5-10 workers
    LARGE = "large"  # 11-20 workers
    XLARGE = "xlarge"  # 21-50 workers
    ENTERPRISE = "enterprise"  # 50+ workers


@dataclass
class WorkloadProfile:
    """Configuration for a simulated workload."""

    name: str
    workload_type: WorkloadType
    cluster_size: ClusterSize

    # Time characteristics (hours per month)
    expected_runtime_hours: float
    idle_percentage: float  # % of runtime that is idle

    # Cold start characteristics
    cold_starts_per_month: int
    cold_start_time_seconds: float  # Time to cold start

    # Cost characteristics
    instance_type: str = "i3.xlarge"
    num_workers: int = 4
    instance_hourly_cost: float = 0.312  # i3.xlarge default
    dbu_rate: float = 0.40  # All-purpose DBU rate

    # Spot eligibility
    spot_eligible_percent: float = 70.0  # % that can run on spot

    # Variability (for monte carlo simulation)
    runtime_variance: float = 0.15  # +/- 15% variance
    idle_variance: float = 0.20  # +/- 20% variance


@dataclass
class ClusterSimulation:
    """A single cluster simulation run."""

    profile: WorkloadProfile
    month: int = 1

    # Simulated values (with variance applied)
    actual_runtime_hours: float = 0.0
    actual_idle_hours: float = 0.0
    actual_cold_starts: int = 0

    # Calculated costs
    baseline_compute_cost: float = 0.0
    baseline_dbu_cost: float = 0.0
    baseline_total_cost: float = 0.0

    def __post_init__(self) -> None:
        """Apply variance and calculate baseline costs."""
        self._apply_variance()
        self._calculate_baseline()

    def _apply_variance(self) -> None:
        """Apply random variance to simulate real-world conditions."""
        # Runtime variance
        runtime_factor = 1 + random.uniform(
            -self.profile.runtime_variance,
            self.profile.runtime_variance
        )
        self.actual_runtime_hours = self.profile.expected_runtime_hours * runtime_factor

        # Idle variance
        idle_factor = 1 + random.uniform(
            -self.profile.idle_variance,
            self.profile.idle_variance
        )
        self.actual_idle_hours = (
            self.actual_runtime_hours *
            (self.profile.idle_percentage / 100) *
            idle_factor
        )

        # Cold starts (Poisson distribution)
        self.actual_cold_starts = max(1, int(random.gauss(
            self.profile.cold_starts_per_month,
            self.profile.cold_starts_per_month * 0.2
        )))

    def _calculate_baseline(self) -> None:
        """Calculate baseline costs without optimization."""
        # Compute cost = (driver + workers) * hours * hourly_rate
        total_instances = 1 + self.profile.num_workers
        self.baseline_compute_cost = (
            total_instances *
            self.actual_runtime_hours *
            self.profile.instance_hourly_cost
        )

        # DBU cost = DBUs per hour * hours * DBU rate
        dbu_per_instance = self._get_dbu_for_instance()
        total_dbus = total_instances * dbu_per_instance * self.actual_runtime_hours
        self.baseline_dbu_cost = total_dbus * self.profile.dbu_rate

        self.baseline_total_cost = self.baseline_compute_cost + self.baseline_dbu_cost

    def _get_dbu_for_instance(self) -> float:
        """Get DBU rate for instance type."""
        dbu_map = {
            "i3.xlarge": 1.0,
            "i3.2xlarge": 2.0,
            "i3.4xlarge": 4.0,
            "m5.xlarge": 1.0,
            "m5.2xlarge": 2.0,
            "r5.xlarge": 1.0,
            "r5.2xlarge": 2.0,
        }
        return dbu_map.get(self.profile.instance_type, 1.0)


@dataclass
class BenchmarkResult:
    """Aggregated benchmark results across multiple simulations."""

    solution_name: str
    num_simulations: int = 0

    # Cost metrics (averages)
    avg_baseline_cost: float = 0.0
    avg_optimized_cost: float = 0.0
    avg_savings_usd: float = 0.0
    avg_savings_percent: float = 0.0

    # Tool cost
    avg_tool_cost: float = 0.0
    avg_net_savings: float = 0.0

    # Performance metrics
    avg_cold_starts: float = 0.0
    avg_cold_starts_prevented: float = 0.0
    cold_start_prevention_rate: float = 0.0

    avg_idle_hours: float = 0.0
    idle_reduction_percent: float = 0.0

    # Spot metrics
    avg_spot_interruptions: float = 0.0
    spot_handling_rate: float = 0.0

    # Variability
    savings_std_dev: float = 0.0
    savings_min: float = 0.0
    savings_max: float = 0.0

    # Raw data for analysis
    all_savings_percents: list[float] = field(default_factory=list)


class WorkloadSimulator:
    """
    Simulates workloads and compares optimization solutions.

    Uses Monte Carlo simulation to model real-world variability.
    """

    # Predefined workload profiles representing common enterprise scenarios
    STANDARD_PROFILES: dict[str, WorkloadProfile] = {
        "small_etl": WorkloadProfile(
            name="Small ETL Cluster",
            workload_type=WorkloadType.ETL_BATCH,
            cluster_size=ClusterSize.SMALL,
            expected_runtime_hours=200,  # ~6.5 hrs/day
            idle_percentage=25,
            cold_starts_per_month=60,  # 2x per day
            cold_start_time_seconds=330,  # 5.5 minutes
            instance_type="m5.xlarge",
            num_workers=2,
            instance_hourly_cost=0.192,
            spot_eligible_percent=80,
        ),
        "medium_analytics": WorkloadProfile(
            name="Medium Analytics Cluster",
            workload_type=WorkloadType.INTERACTIVE,
            cluster_size=ClusterSize.MEDIUM,
            expected_runtime_hours=400,  # ~13 hrs/day
            idle_percentage=35,
            cold_starts_per_month=30,  # 1x per day
            cold_start_time_seconds=360,  # 6 minutes
            instance_type="r5.xlarge",
            num_workers=6,
            instance_hourly_cost=0.252,
            spot_eligible_percent=60,  # Less spot-eligible due to interactive
        ),
        "large_data_warehouse": WorkloadProfile(
            name="Large Data Warehouse",
            workload_type=WorkloadType.REPORTING,
            cluster_size=ClusterSize.LARGE,
            expected_runtime_hours=600,  # ~20 hrs/day
            idle_percentage=40,
            cold_starts_per_month=10,  # ~3x per week
            cold_start_time_seconds=420,  # 7 minutes
            instance_type="i3.2xlarge",
            num_workers=15,
            instance_hourly_cost=0.624,
            spot_eligible_percent=50,
        ),
        "ml_training": WorkloadProfile(
            name="ML Training Cluster",
            workload_type=WorkloadType.ML_TRAINING,
            cluster_size=ClusterSize.XLARGE,
            expected_runtime_hours=300,  # Periodic training
            idle_percentage=20,  # Less idle during training
            cold_starts_per_month=20,
            cold_start_time_seconds=480,  # 8 minutes (larger cluster)
            instance_type="i3.4xlarge",
            num_workers=25,
            instance_hourly_cost=1.248,
            spot_eligible_percent=90,  # Training is interruptible
        ),
        "always_on_production": WorkloadProfile(
            name="Always-On Production",
            workload_type=WorkloadType.MIXED,
            cluster_size=ClusterSize.LARGE,
            expected_runtime_hours=720,  # 24/7
            idle_percentage=45,  # Significant overnight idle
            cold_starts_per_month=4,  # Rare restarts
            cold_start_time_seconds=600,  # 10 minutes
            instance_type="r5.2xlarge",
            num_workers=12,
            instance_hourly_cost=0.504,
            spot_eligible_percent=30,  # Production = less spot
        ),
        "dev_test": WorkloadProfile(
            name="Dev/Test Environment",
            workload_type=WorkloadType.INTERACTIVE,
            cluster_size=ClusterSize.SMALL,
            expected_runtime_hours=180,  # Business hours only
            idle_percentage=50,  # High idle during debugging
            cold_starts_per_month=100,  # Frequent restarts
            cold_start_time_seconds=300,  # 5 minutes
            instance_type="m5.xlarge",
            num_workers=3,
            instance_hourly_cost=0.192,
            spot_eligible_percent=95,  # Dev can use spot
        ),
        "streaming_pipeline": WorkloadProfile(
            name="Streaming Pipeline",
            workload_type=WorkloadType.STREAMING,
            cluster_size=ClusterSize.MEDIUM,
            expected_runtime_hours=720,  # 24/7
            idle_percentage=15,  # Low idle for streaming
            cold_starts_per_month=2,  # Very rare
            cold_start_time_seconds=300,
            instance_type="c5.2xlarge",
            num_workers=8,
            instance_hourly_cost=0.340,
            spot_eligible_percent=40,  # Streaming needs reliability
        ),
    }

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Initialize simulator.

        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)

    def simulate_workload(
        self,
        profile: WorkloadProfile,
        num_months: int = 12,
    ) -> list[ClusterSimulation]:
        """
        Simulate a workload over multiple months.

        Args:
            profile: Workload profile to simulate
            num_months: Number of months to simulate

        Returns:
            List of monthly simulations
        """
        return [
            ClusterSimulation(profile=profile, month=i + 1)
            for i in range(num_months)
        ]

    def simulate_enterprise_portfolio(
        self,
        num_months: int = 12,
        scale_factor: float = 1.0,
    ) -> dict[str, list[ClusterSimulation]]:
        """
        Simulate a realistic enterprise portfolio of clusters.

        Args:
            num_months: Number of months to simulate
            scale_factor: Multiply cluster counts (1.0 = medium enterprise)

        Returns:
            Dict mapping profile name to list of simulations
        """
        # Enterprise cluster distribution
        cluster_counts = {
            "small_etl": int(15 * scale_factor),
            "medium_analytics": int(8 * scale_factor),
            "large_data_warehouse": int(3 * scale_factor),
            "ml_training": int(2 * scale_factor),
            "always_on_production": int(2 * scale_factor),
            "dev_test": int(20 * scale_factor),
            "streaming_pipeline": int(4 * scale_factor),
        }

        portfolio: dict[str, list[ClusterSimulation]] = {}

        for profile_name, count in cluster_counts.items():
            profile = self.STANDARD_PROFILES[profile_name]
            simulations = []

            for _ in range(count):
                simulations.extend(self.simulate_workload(profile, num_months))

            portfolio[profile_name] = simulations

        return portfolio

    def get_profile(self, name: str) -> WorkloadProfile:
        """Get a standard workload profile by name."""
        if name not in self.STANDARD_PROFILES:
            raise ValueError(f"Unknown profile: {name}. Available: {list(self.STANDARD_PROFILES.keys())}")
        return self.STANDARD_PROFILES[name]

    def create_custom_profile(
        self,
        name: str,
        workload_type: WorkloadType,
        runtime_hours: float,
        idle_percent: float,
        cold_starts: int,
        num_workers: int,
        instance_type: str = "m5.xlarge",
        instance_cost: float = 0.192,
    ) -> WorkloadProfile:
        """Create a custom workload profile."""
        # Determine cluster size
        if num_workers <= 4:
            size = ClusterSize.SMALL
        elif num_workers <= 10:
            size = ClusterSize.MEDIUM
        elif num_workers <= 20:
            size = ClusterSize.LARGE
        elif num_workers <= 50:
            size = ClusterSize.XLARGE
        else:
            size = ClusterSize.ENTERPRISE

        # Estimate cold start time based on cluster size
        cold_start_time = 300 + (num_workers * 10)  # Base + per worker

        # Estimate spot eligibility based on workload type
        spot_eligible = {
            WorkloadType.ETL_BATCH: 80,
            WorkloadType.INTERACTIVE: 50,
            WorkloadType.STREAMING: 30,
            WorkloadType.ML_TRAINING: 90,
            WorkloadType.REPORTING: 60,
            WorkloadType.MIXED: 50,
        }.get(workload_type, 50)

        return WorkloadProfile(
            name=name,
            workload_type=workload_type,
            cluster_size=size,
            expected_runtime_hours=runtime_hours,
            idle_percentage=idle_percent,
            cold_starts_per_month=cold_starts,
            cold_start_time_seconds=cold_start_time,
            instance_type=instance_type,
            num_workers=num_workers,
            instance_hourly_cost=instance_cost,
            spot_eligible_percent=spot_eligible,
        )
