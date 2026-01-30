"""Shared helpers for validator implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from accuralai_core.contracts.models import GenerateResponse


@dataclass(slots=True)
class ValidationEvent:
    """Structured event appended to GenerateResponse.validator_events."""

    validator_id: str
    category: str
    details: Dict[str, Any]


def append_event(response: GenerateResponse, event: ValidationEvent) -> GenerateResponse:
    """Return a copy of the response with the supplied validation event appended."""
    events = list(response.validator_events or [])
    events.append(
        {
            "validator_id": event.validator_id,
            "category": event.category,
            "details": event.details,
        }
    )
    return response.model_copy(update={"validator_events": events})


def update_finish_reason(response: GenerateResponse, finish_reason: str) -> GenerateResponse:
    """Return a copy of the response with an updated finish reason."""
    if response.finish_reason == finish_reason:
        return response
    return response.model_copy(update={"finish_reason": finish_reason})


def ensure_metadata(response: GenerateResponse, *, key: str, value: Any) -> GenerateResponse:
    """Return a copy with metadata augmented by the provided key/value pair."""
    metadata = dict(response.metadata or {})
    metadata[key] = value
    return response.model_copy(update={"metadata": metadata})
