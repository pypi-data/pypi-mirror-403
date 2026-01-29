"""
Core data models for Ghost Compute.

This module defines the fundamental data structures used throughout Ghost,
including cluster states, statistics, optimization results, and enumerations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class Platform(str, Enum):
    """Supported data platforms."""

    DATABRICKS = "databricks"
    EMR = "emr"
    SYNAPSE = "synapse"
    DATAPROC = "dataproc"
    CLOUDERA = "cloudera"
    SPARK_STANDALONE = "spark_standalone"


class Strategy(str, Enum):
    """Optimization strategies available in Ghost."""

    PREDICT = "predict"      # Predictive cluster provisioning
    HIBERNATE = "hibernate"  # State preservation and fast resume
    POOL = "pool"           # Cross-workload resource sharing
    SPOT = "spot"           # Spot/preemptible instance optimization
    INSIGHT = "insight"     # Cost attribution and recommendations


class ClusterStatus(str, Enum):
    """Cluster lifecycle status."""

    UNKNOWN = "unknown"
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    RESIZING = "resizing"
    HIBERNATING = "hibernating"
    HIBERNATED = "hibernated"
    RESUMING = "resuming"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    ERROR = "error"


class InstanceType(str, Enum):
    """Instance pricing types."""

    ON_DEMAND = "on_demand"
    SPOT = "spot"
    PREEMPTIBLE = "preemptible"
    RESERVED = "reserved"


class InsightSeverity(str, Enum):
    """Severity levels for cost insights."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InsightCategory(str, Enum):
    """Categories of cost optimization insights."""

    IDLE_RESOURCES = "idle_resources"
    RIGHTSIZING = "rightsizing"
    SPOT_OPPORTUNITY = "spot_opportunity"
    SCHEDULING = "scheduling"
    RESERVED_CAPACITY = "reserved_capacity"
    ARCHITECTURE = "architecture"
    COST_ALLOCATION = "cost_allocation"


class ClusterState(BaseModel):
    """
    Represents the current state of a cluster.

    This is the core model for tracking cluster lifecycle and optimization status.
    """

    model_config = ConfigDict(use_enum_values=True)

    # Identification
    cluster_id: str = Field(..., description="Unique cluster identifier")
    cluster_name: str = Field(..., description="Human-readable cluster name")
    platform: Platform = Field(..., description="Data platform type")
    workspace_id: Optional[str] = Field(None, description="Workspace/account identifier")

    # Status
    status: ClusterStatus = Field(..., description="Current cluster status")
    ghost_managed: bool = Field(default=False, description="Whether Ghost is managing this cluster")

    # Configuration - flexible fields for different platforms
    node_type: Optional[str] = Field(None, description="Instance type (e.g., i3.xlarge)")
    instance_type: str = Field(default="", description="Instance type string")
    num_workers: Optional[int] = Field(None, ge=0, description="Number of worker nodes")
    worker_count: int = Field(default=0, ge=0, description="Number of worker nodes")
    driver_node_type: Optional[str] = Field(None, description="Driver instance type if different")
    autoscale_min: Optional[int] = Field(None, ge=0, description="Autoscale minimum workers")
    autoscale_max: Optional[int] = Field(None, ge=0, description="Autoscale maximum workers")

    # Spot/Preemptible configuration
    pricing_type: InstanceType = Field(
        default=InstanceType.ON_DEMAND,
        description="Instance pricing type"
    )
    spot_fallback_enabled: bool = Field(
        default=True,
        description="Fall back to on-demand if spot unavailable"
    )

    # Timing
    created_at: Optional[datetime] = Field(None, description="Cluster creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Last start timestamp")
    last_activity_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    idle_since: Optional[datetime] = Field(None, description="Idle start timestamp")
    uptime_seconds: int = Field(default=0, ge=0, description="Uptime in seconds")

    # Ghost-specific state
    hibernate_state_uri: Optional[str] = Field(
        None,
        description="S3/GCS/ADLS URI for hibernated state"
    )
    predicted_next_use: Optional[datetime] = Field(
        None,
        description="Predicted next usage time"
    )
    prediction_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence in next use prediction"
    )

    # Cost tracking
    hourly_cost: float = Field(default=0.0, ge=0, description="Hourly cost in USD")
    hourly_cost_usd: float = Field(default=0.0, ge=0, description="Hourly cost in USD (alias)")
    total_cost_usd: float = Field(default=0.0, ge=0, description="Total cost since creation")

    # Metadata
    tags: dict[str, str] = Field(default_factory=dict, description="User-defined tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Platform-specific metadata")


class ClusterStats(BaseModel):
    """
    Aggregated statistics for cluster optimization.

    Used for reporting and dashboard displays.
    """

    model_config = ConfigDict(use_enum_values=True)

    # Time range
    period_start: datetime = Field(..., description="Statistics period start")
    period_end: datetime = Field(..., description="Statistics period end")

    # Platform
    platform: Optional[Platform] = Field(None, description="Platform these stats are for")

    # Cluster counts
    total_clusters: int = Field(default=0, ge=0)
    ghost_managed_clusters: int = Field(default=0, ge=0)
    active_clusters: int = Field(default=0, ge=0)
    idle_clusters: int = Field(default=0, ge=0)
    hibernated_clusters: int = Field(default=0, ge=0)

    # Cost metrics
    total_spend_usd: float = Field(default=0.0, ge=0)
    total_compute_cost: float = Field(default=0.0, ge=0, description="Total compute cost in USD")
    total_dbu_cost: float = Field(default=0.0, ge=0, description="Total DBU cost (Databricks)")
    total_compute_hours: float = Field(default=0.0, ge=0, description="Total compute hours")
    savings_usd: float = Field(default=0.0, ge=0)
    savings_percentage: float = Field(default=0.0, ge=0, le=100)
    projected_monthly_savings_usd: float = Field(default=0.0, ge=0)

    # Idle metrics
    idle_hours: float = Field(default=0.0, ge=0, description="Total idle hours")

    # Performance metrics
    cold_starts: int = Field(default=0, ge=0, description="Number of cold starts")
    cold_starts_total: int = Field(default=0, ge=0)
    cold_starts_prevented: int = Field(default=0, ge=0)
    avg_cold_start_time: float = Field(default=0.0, ge=0, description="Average cold start time in seconds")
    average_cold_start_seconds: float = Field(default=0.0, ge=0)
    average_ghost_start_seconds: float = Field(default=0.0, ge=0)

    # Utilization metrics
    average_utilization_percent: float = Field(default=0.0, ge=0, le=100)
    idle_time_hours: float = Field(default=0.0, ge=0)
    idle_time_prevented_hours: float = Field(default=0.0, ge=0)

    # Spot metrics
    spot_instances_used: int = Field(default=0, ge=0)
    spot_savings: float = Field(default=0.0, ge=0, description="Savings from spot instances")
    spot_savings_usd: float = Field(default=0.0, ge=0)
    spot_interruptions: int = Field(default=0, ge=0)
    spot_interruptions_handled: int = Field(default=0, ge=0)

    # Hibernation metrics
    hibernation_savings: float = Field(default=0.0, ge=0, description="Savings from hibernation")

    # Prediction metrics
    predictions_made: int = Field(default=0, ge=0)
    predictions_accurate: int = Field(default=0, ge=0)
    prediction_accuracy_percent: float = Field(default=0.0, ge=0, le=100)


class OptimizationResult(BaseModel):
    """
    Result of an optimization operation.

    Returned when applying optimization strategies to clusters.
    """

    model_config = ConfigDict(use_enum_values=True)

    # Operation details
    operation_id: Optional[str] = Field(None, description="Unique operation identifier")
    cluster_id: str = Field(..., description="Target cluster identifier")
    action: str = Field(default="", description="Action performed (hibernate, resume, etc.)")
    strategy: Optional[Strategy] = Field(None, description="Strategy applied")

    # Outcome
    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Human-readable result message")
    error: Optional[str] = Field(None, description="Error message if failed")

    # Timing
    started_at: Optional[datetime] = Field(None, description="Operation start time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")
    duration_seconds: float = Field(default=0.0, ge=0, description="Operation duration")

    # Impact
    savings_usd: float = Field(default=0.0, ge=0, description="Savings in USD")
    estimated_savings_usd: float = Field(default=0.0, ge=0)
    cold_start_prevented: bool = Field(default=False)

    # State changes
    previous_status: Optional[ClusterStatus] = Field(None)
    new_status: Optional[ClusterStatus] = Field(None)

    # Metadata
    details: dict[str, Any] = Field(default_factory=dict)


class PredictionResult(BaseModel):
    """Result of workload prediction analysis."""

    cluster_id: str
    predicted_start_time: datetime
    confidence: float = Field(ge=0.0, le=1.0)
    prediction_basis: str = Field(description="What the prediction is based on")
    recommended_action: str
    warm_up_lead_time_seconds: int = Field(ge=0)

    # Historical context
    similar_patterns_found: int = Field(default=0, ge=0)
    historical_accuracy: Optional[float] = Field(None, ge=0.0, le=1.0)


class HibernateResult(BaseModel):
    """Result of cluster hibernation."""

    cluster_id: str
    state_uri: str = Field(description="URI where state is stored")
    state_size_bytes: int = Field(ge=0)
    hibernate_duration_seconds: float = Field(ge=0)
    estimated_resume_seconds: float = Field(ge=0)

    # Cost impact
    hourly_savings_usd: float = Field(ge=0)
    state_storage_cost_usd_monthly: float = Field(ge=0)


class SpotAllocation(BaseModel):
    """Spot instance allocation details."""

    cluster_id: str
    instance_type: str
    availability_zone: str
    spot_price_usd: float = Field(ge=0)
    on_demand_price_usd: float = Field(ge=0)
    savings_percent: float = Field(ge=0, le=100)

    # Risk metrics
    interruption_probability: float = Field(ge=0.0, le=1.0)
    average_runtime_hours: float = Field(ge=0)

    # Fallback configuration
    fallback_instance_type: Optional[str] = None
    fallback_on_demand: bool = True


class CostInsight(BaseModel):
    """Cost optimization insight/recommendation."""

    model_config = ConfigDict(use_enum_values=True)

    insight_id: str
    severity: InsightSeverity = Field(description="Insight severity level")
    category: InsightCategory = Field(description="Insight category")

    title: str
    description: str
    recommendation: str

    # Impact
    estimated_savings: float = Field(default=0.0, ge=0, description="Estimated monthly savings in USD")
    estimated_monthly_savings_usd: float = Field(default=0.0, ge=0)
    estimated_annual_savings_usd: float = Field(default=0.0, ge=0)
    implementation_effort: str = Field(default="low", description="low, medium, high")

    # Affected resources
    affected_resources: list[str] = Field(default_factory=list, description="IDs of affected resources")
    affected_clusters: list[str] = Field(default_factory=list, description="Deprecated: use affected_resources")

    # Evidence
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class WorkloadPattern(BaseModel):
    """Detected workload pattern for prediction."""

    pattern_id: str
    pattern_type: str = Field(description="scheduled, user_driven, data_triggered, seasonal")

    # Timing
    typical_start_times: list[str] = Field(description="Cron expressions or time patterns")
    typical_duration_minutes: float = Field(ge=0)
    frequency: str = Field(description="hourly, daily, weekly, monthly, irregular")

    # Confidence
    confidence: float = Field(ge=0.0, le=1.0)
    sample_size: int = Field(ge=0)
    last_occurrence: Optional[datetime] = None
    next_predicted: Optional[datetime] = None

    # Associated clusters
    cluster_ids: list[str] = Field(default_factory=list)
