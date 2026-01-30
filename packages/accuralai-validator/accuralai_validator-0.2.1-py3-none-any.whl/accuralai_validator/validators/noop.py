"""No-op validator implementation."""

from __future__ import annotations

from typing import Any, Mapping

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator


class NoOpValidator(Validator):
    """Pass-through validator used as baseline."""

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:  # noqa: D401
        return response


async def build_noop_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    **_: Any,
) -> Validator:
    """Factory registered via entry point."""
    return NoOpValidator()
