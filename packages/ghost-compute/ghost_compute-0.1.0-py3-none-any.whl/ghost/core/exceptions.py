"""
Custom exceptions for Ghost Compute.

This module defines the exception hierarchy used throughout Ghost to provide
clear, actionable error messages for different failure scenarios.
"""

from __future__ import annotations

from typing import Any, Optional


class GhostError(Exception):
    """
    Base exception for all Ghost errors.

    All Ghost-specific exceptions inherit from this class, making it easy
    to catch any Ghost-related error with a single except clause.

    Attributes:
        message: Human-readable error description
        code: Machine-readable error code
        details: Additional context about the error
        suggestion: Suggested action to resolve the error
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        self.message = message
        self.code = code or "GHOST_ERROR"
        self.details = details or {}
        self.suggestion = suggestion
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the complete error message."""
        parts = [f"[{self.code}] {self.message}"]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return " | ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion,
        }


class ConfigurationError(GhostError):
    """
    Raised when there's a configuration problem.

    This includes invalid configuration files, missing required settings,
    or incompatible configuration combinations.
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)

        suggestion = kwargs.pop(
            "suggestion",
            "Check your ghost.yaml configuration file and environment variables."
        )

        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            details=details,
            suggestion=suggestion,
            **kwargs,
        )


class PlatformError(GhostError):
    """
    Raised when there's an error communicating with a data platform.

    This includes authentication failures, API errors, and platform-specific
    issues with Databricks, EMR, Synapse, etc.
    """

    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        operation: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if platform:
            details["platform"] = platform
        if operation:
            details["operation"] = operation
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message=message,
            code="PLATFORM_ERROR",
            details=details,
            **kwargs,
        )


class AuthenticationError(PlatformError):
    """
    Raised when authentication with a platform fails.

    This is a specialized PlatformError for credential-related issues.
    """

    def __init__(
        self,
        message: str,
        platform: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        suggestion = kwargs.pop(
            "suggestion",
            "Verify your credentials and ensure they have not expired. "
            "Check the credentials file at ~/.ghost/credentials.json"
        )

        super().__init__(
            message=message,
            platform=platform,
            suggestion=suggestion,
            **kwargs,
        )
        self.code = "AUTH_ERROR"


class OptimizationError(GhostError):
    """
    Raised when an optimization operation fails.

    This includes failures in predict, hibernate, pool, or spot strategies.
    """

    def __init__(
        self,
        message: str,
        strategy: Optional[str] = None,
        cluster_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if strategy:
            details["strategy"] = strategy
        if cluster_id:
            details["cluster_id"] = cluster_id

        super().__init__(
            message=message,
            code="OPTIMIZATION_ERROR",
            details=details,
            **kwargs,
        )


class HibernationError(OptimizationError):
    """
    Raised when cluster hibernation or resume fails.
    """

    def __init__(
        self,
        message: str,
        cluster_id: Optional[str] = None,
        state_uri: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if state_uri:
            details["state_uri"] = state_uri

        super().__init__(
            message=message,
            strategy="hibernate",
            cluster_id=cluster_id,
            details=details,
            **kwargs,
        )
        self.code = "HIBERNATION_ERROR"


class PredictionError(OptimizationError):
    """
    Raised when workload prediction fails.
    """

    def __init__(
        self,
        message: str,
        cluster_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            strategy="predict",
            cluster_id=cluster_id,
            **kwargs,
        )
        self.code = "PREDICTION_ERROR"


class SpotError(OptimizationError):
    """
    Raised when spot instance management fails.
    """

    def __init__(
        self,
        message: str,
        cluster_id: Optional[str] = None,
        instance_type: Optional[str] = None,
        availability_zone: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if instance_type:
            details["instance_type"] = instance_type
        if availability_zone:
            details["availability_zone"] = availability_zone

        super().__init__(
            message=message,
            strategy="spot",
            cluster_id=cluster_id,
            details=details,
            **kwargs,
        )
        self.code = "SPOT_ERROR"


class PoolError(OptimizationError):
    """
    Raised when resource pooling fails.
    """

    def __init__(
        self,
        message: str,
        pool_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if pool_id:
            details["pool_id"] = pool_id

        super().__init__(
            message=message,
            strategy="pool",
            details=details,
            **kwargs,
        )
        self.code = "POOL_ERROR"


class ResourceNotFoundError(GhostError):
    """
    Raised when a requested resource does not exist.
    """

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs: Any,
    ) -> None:
        message = f"{resource_type} not found: {resource_id}"
        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
        }

        super().__init__(
            message=message,
            code="NOT_FOUND",
            details=details,
            **kwargs,
        )


class ClusterNotFoundError(ResourceNotFoundError):
    """
    Raised when a requested cluster does not exist.
    """

    def __init__(
        self,
        message: str,
        cluster_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        # For simple string messages, extract or use a generic resource_id
        resource_id = cluster_id or "unknown"

        # Call parent with cluster as resource type
        GhostError.__init__(
            self,
            message=message,
            code="CLUSTER_NOT_FOUND",
            details={"cluster_id": resource_id},
            **kwargs,
        )


class RateLimitError(PlatformError):
    """
    Raised when API rate limits are exceeded.
    """

    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if retry_after_seconds:
            details["retry_after_seconds"] = retry_after_seconds

        suggestion = kwargs.pop(
            "suggestion",
            f"Wait {retry_after_seconds or 60} seconds before retrying."
        )

        super().__init__(
            message=message,
            details=details,
            suggestion=suggestion,
            **kwargs,
        )
        self.code = "RATE_LIMIT"
        self.retry_after_seconds = retry_after_seconds


class ValidationError(GhostError):
    """
    Raised when input validation fails.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            **kwargs,
        )


class StateError(GhostError):
    """
    Raised when an operation is invalid for the current state.
    """

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        expected_states: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if current_state:
            details["current_state"] = current_state
        if expected_states:
            details["expected_states"] = expected_states

        super().__init__(
            message=message,
            code="STATE_ERROR",
            details=details,
            **kwargs,
        )
