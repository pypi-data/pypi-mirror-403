"""Toxicity validator integrating external moderation scores."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Mapping, Optional

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator

from ..base import ValidationEvent, append_event, ensure_metadata, update_finish_reason
from ..config import ToxicityValidatorOptions, parse_options


ToxicityScores = Mapping[str, float]
ToxicityProvider = Callable[[GenerateRequest, GenerateResponse], Awaitable[ToxicityScores]]


class ToxicityValidator(Validator):
    """Wraps an async toxicity provider and blocks responses above thresholds."""

    def __init__(
        self,
        *,
        options: ToxicityValidatorOptions,
        provider: ToxicityProvider,
        validator_id: str,
    ) -> None:
        self._options = options
        self._provider = provider
        self._validator_id = validator_id

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        scores = await self._provider(request, response)
        blocked = self._detect_blocked(scores)
        if not blocked:
            return response

        updated = update_finish_reason(response, "content_filter")
        updated = ensure_metadata(updated, key="toxicity_scores", value=dict(scores))
        event = ValidationEvent(
            validator_id=self._validator_id,
            category="toxicity",
            details={"blocked_categories": blocked},
        )
        return append_event(updated, event)

    def _detect_blocked(self, scores: ToxicityScores) -> Dict[str, float]:
        blocked: Dict[str, float] = {}
        consider = self._options.block_categories or scores.keys()
        for category in consider:
            score = scores.get(category)
            if score is None:
                continue
            threshold = self._options.category_thresholds.get(category, self._options.threshold)
            if score >= threshold:
                blocked[category] = score
        return blocked


async def build_toxicity_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    provider: ToxicityProvider | None = None,
    validator_id: Optional[str] = None,
    **_: Any,
) -> Validator:
    """Factory registered for the toxicity validator."""
    options_payload: Mapping[str, Any] | ToxicityValidatorOptions | None = None
    if isinstance(config, ValidatorSettings):
        options_payload = config.options or {}
        validator_id = validator_id or config.id or "validator.toxicity"
    else:
        options_payload = config
        validator_id = validator_id or "validator.toxicity"

    if provider is None:
        msg = "Toxicity validator requires an async provider callable."
        raise ConfigurationError(msg)

    options = parse_options(ToxicityValidatorOptions, options_payload)
    return ToxicityValidator(options=options, provider=provider, validator_id=validator_id)
