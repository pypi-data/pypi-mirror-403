"""Length validator implementation."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator
from accuralai_core.utils.tokenizer import DEFAULT_TOKENIZER, SimpleTokenizer

from ..base import ValidationEvent, append_event, update_finish_reason
from ..config import LengthValidatorOptions, parse_options


class LengthValidator(Validator):
    """Enforces prompt and completion length limits."""

    def __init__(
        self,
        *,
        options: LengthValidatorOptions,
        validator_id: str,
    ) -> None:
        self._options = options
        self._validator_id = validator_id
        self._tokenizer: SimpleTokenizer | None = DEFAULT_TOKENIZER if options.mode == "token" else None

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        prompt_length = self._count_prompt(request)
        completion_length = self._count_completion(response)

        updated = response

        if self._options.max_prompt_tokens is not None and prompt_length > self._options.max_prompt_tokens:
            updated = self._record_violation(
                updated,
                category="prompt_max",
                details={
                    "observed": prompt_length,
                    "limit": self._options.max_prompt_tokens,
                    "mode": self._options.mode,
                },
            )

        if self._options.max_completion_tokens is not None and completion_length > self._options.max_completion_tokens:
            updated = self._handle_completion_overflow(updated, completion_length)

        if (
            self._options.min_completion_tokens is not None
            and completion_length < self._options.min_completion_tokens
        ):
            updated = self._record_violation(
                updated,
                category="completion_min",
                details={
                    "observed": completion_length,
                    "limit": self._options.min_completion_tokens,
                    "mode": self._options.mode,
                },
            )

        return updated

    def _record_violation(self, response: GenerateResponse, *, category: str, details: dict) -> GenerateResponse:
        updated = update_finish_reason(response, "length")
        event = ValidationEvent(
            validator_id=self._validator_id,
            category=category,
            details=details,
        )
        return append_event(updated, event)

    def _handle_completion_overflow(self, response: GenerateResponse, observed_length: int) -> GenerateResponse:
        limit = self._options.max_completion_tokens or observed_length
        updated = response

        if self._options.truncate and response.output_text:
            truncated_text = self._truncate_text(response.output_text, limit)
            updated = response.model_copy(update={"output_text": truncated_text})

        details = {"observed": observed_length, "limit": limit, "mode": self._options.mode}
        return self._record_violation(updated, category="completion_max", details=details)

    def _count_prompt(self, request: GenerateRequest) -> int:
        if self._options.mode == "token":
            assert self._tokenizer is not None
            return self._tokenizer.count_request_tokens(request)
        if self._options.mode == "character":
            base = len(request.prompt or "")
            if request.system_prompt:
                base += len(request.system_prompt)
            return base
        return len((request.prompt or "").split())

    def _count_completion(self, response: GenerateResponse) -> int:
        text = response.output_text or ""
        if self._options.mode == "token":
            assert self._tokenizer is not None
            return self._tokenizer.count_response_tokens(response)
        if self._options.mode == "character":
            return len(text)
        return len(text.split())

    def _truncate_text(self, text: str, limit: int) -> str:
        if self._options.mode == "character":
            return text[:limit]
        if self._options.mode == "word":
            words = text.split()
            if len(words) <= limit:
                return text
            return " ".join(words[:limit])
        if self._options.mode == "token":
            # Token-aware truncation would require preserving original spacing;
            # for the initial implementation we leave the text unchanged while
            # still emitting the violation event.
            return text
        return text


async def build_length_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    validator_id: Optional[str] = None,
    **_: Any,
) -> Validator:
    """Factory registered for the length validator."""
    options_payload: Mapping[str, Any] | LengthValidatorOptions | None = None
    if isinstance(config, ValidatorSettings):
        options_payload = config.options or {}
        validator_id = validator_id or config.id or "validator.length"
    else:
        options_payload = config
        validator_id = validator_id or "validator.length"

    options = parse_options(LengthValidatorOptions, options_payload)
    return LengthValidator(options=options, validator_id=validator_id)
