"""Telemetry helpers for validators."""

from __future__ import annotations

from typing import Protocol


class ValidatorMetricsRecorder(Protocol):
    """Protocol describing minimal validator telemetry hooks."""

    def record_event(self, *, validator_id: str, category: str) -> None:
        """Record that a validator emitted an event."""


class NullValidatorMetricsRecorder:
    """No-op telemetry implementation."""

    def record_event(self, *, validator_id: str, category: str) -> None:  # noqa: D401
        return None


def resolve_metrics(metrics: ValidatorMetricsRecorder | None = None) -> ValidatorMetricsRecorder:
    """Return a usable metrics recorder."""
    if metrics is None:
        return NullValidatorMetricsRecorder()
    return metrics
