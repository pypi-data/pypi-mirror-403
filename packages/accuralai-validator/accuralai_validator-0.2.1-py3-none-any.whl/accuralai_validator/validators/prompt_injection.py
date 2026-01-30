"""Prompt injection heuristic validator."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Set

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator

from ..base import ValidationEvent, append_event, update_finish_reason
from ..config import PromptInjectionValidatorOptions, parse_options


class PromptInjectionValidator(Validator):
    """Detects obvious prompt-injection attempts using keyword heuristics."""

    def __init__(self, *, options: PromptInjectionValidatorOptions, validator_id: str) -> None:
        self._options = options
        self._validator_id = validator_id
        self._keywords = {keyword.lower() for keyword in options.ban_keywords}

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        hits = self._keyword_hits(request, response)
        ratio = self._instruction_ratio(request, response)

        should_flag = bool(hits)
        if ratio > self._options.max_instruction_ratio:
            should_flag = True

        if not should_flag:
            return response

        updated = update_finish_reason(response, "content_filter")
        event = ValidationEvent(
            validator_id=self._validator_id,
            category="prompt_injection",
            details={
                "keyword_hits": sorted(hits),
                "instruction_ratio": ratio,
                "max_ratio": self._options.max_instruction_ratio,
            },
        )
        return append_event(updated, event)

    def _keyword_hits(self, request: GenerateRequest, response: GenerateResponse) -> Set[str]:
        text_sections = [
            request.prompt or "",
            request.system_prompt or "",
            response.output_text or "",
        ]
        for item in request.history:
            part = str(item.get("content") or item.get("text") or "")
            text_sections.append(part)

        combined = " ".join(text_sections).lower()
        hits: Set[str] = set()
        for keyword in self._keywords:
            if keyword in combined:
                hits.add(keyword)
        return hits

    def _instruction_ratio(self, request: GenerateRequest, response: GenerateResponse) -> float:
        instruction_len = len(request.prompt or "")
        if request.system_prompt and self._options.flag_system_override:
            instruction_len += len(request.system_prompt)

        total_len = instruction_len + len(response.output_text or "")
        if total_len == 0:
            return 0.0
        return instruction_len / total_len


async def build_prompt_injection_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    validator_id: Optional[str] = None,
    **_: Any,
) -> Validator:
    """Factory registered for the prompt injection validator."""
    options_payload: Mapping[str, Any] | PromptInjectionValidatorOptions | None = None
    if isinstance(config, ValidatorSettings):
        options_payload = config.options or {}
        validator_id = validator_id or config.id or "validator.prompt_injection"
    else:
        options_payload = config
        validator_id = validator_id or "validator.prompt_injection"

    options = parse_options(PromptInjectionValidatorOptions, options_payload)
    return PromptInjectionValidator(options=options, validator_id=validator_id)
