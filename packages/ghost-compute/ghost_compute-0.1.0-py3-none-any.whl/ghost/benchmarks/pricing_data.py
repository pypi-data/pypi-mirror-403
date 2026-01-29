"""
Real-world pricing data for cloud compute resources.

Data sourced from:
- AWS EC2 Pricing: https://aws.amazon.com/ec2/pricing/on-demand/
- AWS Spot Pricing: https://aws.amazon.com/ec2/spot/pricing/
- Databricks Pricing: https://www.databricks.com/product/pricing
- Azure Pricing: https://azure.microsoft.com/en-us/pricing/
- instances.vantage.sh for detailed instance comparisons

Last updated: January 2025
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class InstanceFamily(str, Enum):
    """Instance family categories."""
    GENERAL_PURPOSE = "general_purpose"  # m5, m6i, Standard_D
    COMPUTE_OPTIMIZED = "compute_optimized"  # c5, c6i
    MEMORY_OPTIMIZED = "memory_optimized"  # r5, r6i
    STORAGE_OPTIMIZED = "storage_optimized"  # i3, i3en, d2


@dataclass
class InstancePricing:
    """Pricing information for a specific instance type."""

    instance_type: str
    provider: CloudProvider
    region: str
    vcpus: int
    memory_gb: float
    storage_gb: Optional[float]  # Local SSD storage

    # Pricing (USD per hour)
    on_demand_hourly: float
    spot_hourly: float  # Average spot price
    spot_min_hourly: float  # Minimum observed spot price
    spot_max_hourly: float  # Maximum observed spot price

    # Databricks DBU rates (if applicable)
    dbu_per_hour: float = 0.0

    # Metadata
    family: InstanceFamily = InstanceFamily.GENERAL_PURPOSE
    generation: str = ""

    @property
    def spot_savings_percent(self) -> float:
        """Calculate spot savings vs on-demand."""
        if self.on_demand_hourly == 0:
            return 0.0
        return (1 - self.spot_hourly / self.on_demand_hourly) * 100

    @property
    def memory_per_vcpu(self) -> float:
        """Memory to vCPU ratio."""
        return self.memory_gb / self.vcpus if self.vcpus > 0 else 0


@dataclass
class DatabricksPricing:
    """Databricks DBU pricing by compute type and tier."""

    # DBU rates per hour by compute type
    jobs_compute: float = 0.15  # Lowest cost - automated jobs
    jobs_light_compute: float = 0.07  # Most economical
    all_purpose_compute: float = 0.40  # Interactive workloads (Standard)
    all_purpose_premium: float = 0.55  # Premium tier
    all_purpose_enterprise: float = 0.65  # Enterprise tier
    sql_compute: float = 0.22  # SQL analytics
    sql_serverless: float = 0.70  # Serverless SQL (includes infra)

    # Model serving
    model_serving: float = 0.07

    # Delta Live Tables
    dlt_core: float = 0.20
    dlt_pro: float = 0.25
    dlt_advanced: float = 0.36


@dataclass
class PricingData:
    """Complete pricing data for benchmarking."""

    instances: dict[str, InstancePricing] = field(default_factory=dict)
    databricks: DatabricksPricing = field(default_factory=DatabricksPricing)

    # Cold start times (seconds)
    cold_start_times: dict[str, float] = field(default_factory=lambda: {
        "emr_standard": 480.0,  # 8 minutes
        "emr_slow": 900.0,  # 15 minutes (worst case)
        "databricks_standard": 330.0,  # 5.5 minutes
        "databricks_with_pools": 90.0,  # 1.5 minutes
        "databricks_serverless": 5.0,  # Near instant
        "glue": 660.0,  # 11 minutes
        "dataproc": 120.0,  # 2 minutes
        "synapse": 180.0,  # 3 minutes
    })

    # Idle detection thresholds (minutes)
    idle_thresholds: dict[str, int] = field(default_factory=lambda: {
        "aggressive": 5,
        "moderate": 10,
        "conservative": 30,
        "very_conservative": 60,
    })


# =============================================================================
# AWS EC2 Pricing Data (US-EAST-1, Linux, as of Jan 2025)
# Source: https://aws.amazon.com/ec2/pricing/on-demand/
# Source: https://instances.vantage.sh/
# =============================================================================

AWS_INSTANCE_PRICING: dict[str, InstancePricing] = {
    # M5 Family - General Purpose
    "m5.large": InstancePricing(
        instance_type="m5.large",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=2,
        memory_gb=8.0,
        storage_gb=None,
        on_demand_hourly=0.096,
        spot_hourly=0.035,
        spot_min_hourly=0.028,
        spot_max_hourly=0.045,
        dbu_per_hour=0.5,
        family=InstanceFamily.GENERAL_PURPOSE,
        generation="5th",
    ),
    "m5.xlarge": InstancePricing(
        instance_type="m5.xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=4,
        memory_gb=16.0,
        storage_gb=None,
        on_demand_hourly=0.192,
        spot_hourly=0.070,
        spot_min_hourly=0.055,
        spot_max_hourly=0.090,
        dbu_per_hour=1.0,
        family=InstanceFamily.GENERAL_PURPOSE,
        generation="5th",
    ),
    "m5.2xlarge": InstancePricing(
        instance_type="m5.2xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=8,
        memory_gb=32.0,
        storage_gb=None,
        on_demand_hourly=0.384,
        spot_hourly=0.140,
        spot_min_hourly=0.110,
        spot_max_hourly=0.180,
        dbu_per_hour=2.0,
        family=InstanceFamily.GENERAL_PURPOSE,
        generation="5th",
    ),
    "m5.4xlarge": InstancePricing(
        instance_type="m5.4xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=16,
        memory_gb=64.0,
        storage_gb=None,
        on_demand_hourly=0.768,
        spot_hourly=0.280,
        spot_min_hourly=0.220,
        spot_max_hourly=0.360,
        dbu_per_hour=4.0,
        family=InstanceFamily.GENERAL_PURPOSE,
        generation="5th",
    ),

    # R5 Family - Memory Optimized
    "r5.large": InstancePricing(
        instance_type="r5.large",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=2,
        memory_gb=16.0,
        storage_gb=None,
        on_demand_hourly=0.126,
        spot_hourly=0.045,
        spot_min_hourly=0.035,
        spot_max_hourly=0.060,
        dbu_per_hour=0.5,
        family=InstanceFamily.MEMORY_OPTIMIZED,
        generation="5th",
    ),
    "r5.xlarge": InstancePricing(
        instance_type="r5.xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=4,
        memory_gb=32.0,
        storage_gb=None,
        on_demand_hourly=0.252,
        spot_hourly=0.090,
        spot_min_hourly=0.070,
        spot_max_hourly=0.120,
        dbu_per_hour=1.0,
        family=InstanceFamily.MEMORY_OPTIMIZED,
        generation="5th",
    ),
    "r5.2xlarge": InstancePricing(
        instance_type="r5.2xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=8,
        memory_gb=64.0,
        storage_gb=None,
        on_demand_hourly=0.504,
        spot_hourly=0.180,
        spot_min_hourly=0.140,
        spot_max_hourly=0.240,
        dbu_per_hour=2.0,
        family=InstanceFamily.MEMORY_OPTIMIZED,
        generation="5th",
    ),
    "r5.4xlarge": InstancePricing(
        instance_type="r5.4xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=16,
        memory_gb=128.0,
        storage_gb=None,
        on_demand_hourly=1.008,
        spot_hourly=0.360,
        spot_min_hourly=0.280,
        spot_max_hourly=0.480,
        dbu_per_hour=4.0,
        family=InstanceFamily.MEMORY_OPTIMIZED,
        generation="5th",
    ),

    # I3 Family - Storage Optimized (Popular for Spark)
    "i3.large": InstancePricing(
        instance_type="i3.large",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=2,
        memory_gb=15.25,
        storage_gb=475.0,
        on_demand_hourly=0.156,
        spot_hourly=0.047,
        spot_min_hourly=0.035,
        spot_max_hourly=0.065,
        dbu_per_hour=0.5,
        family=InstanceFamily.STORAGE_OPTIMIZED,
        generation="3rd",
    ),
    "i3.xlarge": InstancePricing(
        instance_type="i3.xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=4,
        memory_gb=30.5,
        storage_gb=950.0,
        on_demand_hourly=0.312,
        spot_hourly=0.094,
        spot_min_hourly=0.070,
        spot_max_hourly=0.130,
        dbu_per_hour=1.0,
        family=InstanceFamily.STORAGE_OPTIMIZED,
        generation="3rd",
    ),
    "i3.2xlarge": InstancePricing(
        instance_type="i3.2xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=8,
        memory_gb=61.0,
        storage_gb=1900.0,
        on_demand_hourly=0.624,
        spot_hourly=0.187,
        spot_min_hourly=0.140,
        spot_max_hourly=0.260,
        dbu_per_hour=2.0,
        family=InstanceFamily.STORAGE_OPTIMIZED,
        generation="3rd",
    ),
    "i3.4xlarge": InstancePricing(
        instance_type="i3.4xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=16,
        memory_gb=122.0,
        storage_gb=3800.0,
        on_demand_hourly=1.248,
        spot_hourly=0.374,
        spot_min_hourly=0.280,
        spot_max_hourly=0.520,
        dbu_per_hour=4.0,
        family=InstanceFamily.STORAGE_OPTIMIZED,
        generation="3rd",
    ),
    "i3.8xlarge": InstancePricing(
        instance_type="i3.8xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=32,
        memory_gb=244.0,
        storage_gb=7600.0,
        on_demand_hourly=2.496,
        spot_hourly=0.749,
        spot_min_hourly=0.560,
        spot_max_hourly=1.040,
        dbu_per_hour=8.0,
        family=InstanceFamily.STORAGE_OPTIMIZED,
        generation="3rd",
    ),

    # C5 Family - Compute Optimized
    "c5.xlarge": InstancePricing(
        instance_type="c5.xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=4,
        memory_gb=8.0,
        storage_gb=None,
        on_demand_hourly=0.170,
        spot_hourly=0.065,
        spot_min_hourly=0.050,
        spot_max_hourly=0.085,
        dbu_per_hour=0.75,
        family=InstanceFamily.COMPUTE_OPTIMIZED,
        generation="5th",
    ),
    "c5.2xlarge": InstancePricing(
        instance_type="c5.2xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=8,
        memory_gb=16.0,
        storage_gb=None,
        on_demand_hourly=0.340,
        spot_hourly=0.130,
        spot_min_hourly=0.100,
        spot_max_hourly=0.170,
        dbu_per_hour=1.5,
        family=InstanceFamily.COMPUTE_OPTIMIZED,
        generation="5th",
    ),
    "c5.4xlarge": InstancePricing(
        instance_type="c5.4xlarge",
        provider=CloudProvider.AWS,
        region="us-east-1",
        vcpus=16,
        memory_gb=32.0,
        storage_gb=None,
        on_demand_hourly=0.680,
        spot_hourly=0.260,
        spot_min_hourly=0.200,
        spot_max_hourly=0.340,
        dbu_per_hour=3.0,
        family=InstanceFamily.COMPUTE_OPTIMIZED,
        generation="5th",
    ),
}


# =============================================================================
# Azure VM Pricing Data (US-EAST, Linux, as of Jan 2025)
# =============================================================================

AZURE_INSTANCE_PRICING: dict[str, InstancePricing] = {
    "Standard_D4s_v3": InstancePricing(
        instance_type="Standard_D4s_v3",
        provider=CloudProvider.AZURE,
        region="eastus",
        vcpus=4,
        memory_gb=16.0,
        storage_gb=32.0,
        on_demand_hourly=0.192,
        spot_hourly=0.038,
        spot_min_hourly=0.030,
        spot_max_hourly=0.050,
        dbu_per_hour=1.0,
        family=InstanceFamily.GENERAL_PURPOSE,
    ),
    "Standard_D8s_v3": InstancePricing(
        instance_type="Standard_D8s_v3",
        provider=CloudProvider.AZURE,
        region="eastus",
        vcpus=8,
        memory_gb=32.0,
        storage_gb=64.0,
        on_demand_hourly=0.384,
        spot_hourly=0.077,
        spot_min_hourly=0.060,
        spot_max_hourly=0.100,
        dbu_per_hour=2.0,
        family=InstanceFamily.GENERAL_PURPOSE,
    ),
    "Standard_E4s_v3": InstancePricing(
        instance_type="Standard_E4s_v3",
        provider=CloudProvider.AZURE,
        region="eastus",
        vcpus=4,
        memory_gb=32.0,
        storage_gb=64.0,
        on_demand_hourly=0.252,
        spot_hourly=0.050,
        spot_min_hourly=0.040,
        spot_max_hourly=0.065,
        dbu_per_hour=1.0,
        family=InstanceFamily.MEMORY_OPTIMIZED,
    ),
    "Standard_E8s_v3": InstancePricing(
        instance_type="Standard_E8s_v3",
        provider=CloudProvider.AZURE,
        region="eastus",
        vcpus=8,
        memory_gb=64.0,
        storage_gb=128.0,
        on_demand_hourly=0.504,
        spot_hourly=0.101,
        spot_min_hourly=0.080,
        spot_max_hourly=0.130,
        dbu_per_hour=2.0,
        family=InstanceFamily.MEMORY_OPTIMIZED,
    ),
    "Standard_L8s_v2": InstancePricing(
        instance_type="Standard_L8s_v2",
        provider=CloudProvider.AZURE,
        region="eastus",
        vcpus=8,
        memory_gb=64.0,
        storage_gb=1920.0,  # NVMe
        on_demand_hourly=0.624,
        spot_hourly=0.125,
        spot_min_hourly=0.095,
        spot_max_hourly=0.160,
        dbu_per_hour=2.0,
        family=InstanceFamily.STORAGE_OPTIMIZED,
    ),
}


def get_aws_pricing() -> dict[str, InstancePricing]:
    """Get AWS EC2 pricing data."""
    return AWS_INSTANCE_PRICING.copy()


def get_azure_pricing() -> dict[str, InstancePricing]:
    """Get Azure VM pricing data."""
    return AZURE_INSTANCE_PRICING.copy()


def get_databricks_pricing() -> DatabricksPricing:
    """Get Databricks DBU pricing."""
    return DatabricksPricing()


def get_spot_pricing(provider: CloudProvider = CloudProvider.AWS) -> dict[str, float]:
    """
    Get spot pricing as percentage of on-demand.

    Returns dict mapping instance type to spot discount percentage.
    """
    if provider == CloudProvider.AWS:
        return {
            instance_type: pricing.spot_savings_percent
            for instance_type, pricing in AWS_INSTANCE_PRICING.items()
        }
    elif provider == CloudProvider.AZURE:
        return {
            instance_type: pricing.spot_savings_percent
            for instance_type, pricing in AZURE_INSTANCE_PRICING.items()
        }
    else:
        return {}


def get_all_pricing() -> PricingData:
    """Get complete pricing data for benchmarking."""
    all_instances = {}
    all_instances.update(AWS_INSTANCE_PRICING)
    all_instances.update(AZURE_INSTANCE_PRICING)

    return PricingData(
        instances=all_instances,
        databricks=DatabricksPricing(),
    )


# =============================================================================
# Industry Benchmark Data
# Source: Various cloud cost optimization reports and case studies
# =============================================================================

INDUSTRY_BENCHMARKS = {
    # Average idle time percentages observed in enterprise clusters
    "idle_time_percentage": {
        "no_optimization": 35.0,  # 35% of cluster time is idle
        "native_autoscaling": 20.0,  # 20% with native autoscaling
        "basic_scheduling": 25.0,  # 25% with basic job scheduling
        "advanced_optimization": 8.0,  # 8% with advanced tools
        "ghost_target": 4.0,  # Ghost target: 4%
    },

    # Cold start frequency (per day for typical workloads)
    "cold_starts_per_day": {
        "always_on": 0,  # Clusters always running
        "scheduled": 2,  # Morning/evening startups
        "on_demand": 8,  # Frequent cold starts
        "interactive": 15,  # Many ad-hoc queries
    },

    # Spot interruption rates (per 100 hours)
    "spot_interruptions_per_100h": {
        "high_demand_instances": 15.0,  # Popular instance types
        "medium_demand_instances": 8.0,
        "low_demand_instances": 3.0,
        "diversified_fleet": 2.0,  # Using multiple instance types
    },

    # Utilization rates
    "cluster_utilization": {
        "typical_enterprise": 30.0,  # 30% average utilization
        "well_optimized": 55.0,  # 55% with optimization
        "highly_optimized": 75.0,  # 75% with advanced tools
    },
}
