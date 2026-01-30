"""Regex-based validator implementation."""

from __future__ import annotations

import re
from typing import Any, List, Mapping, Optional, Pattern

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator

from ..base import ValidationEvent, append_event, update_finish_reason
from ..config import RegexValidatorOptions, parse_options


class RegexValidator(Validator):
    """Blocks responses that match deny-listed regular expressions."""

    def __init__(self, *, options: RegexValidatorOptions, validator_id: str) -> None:
        flags = re.IGNORECASE if options.case_insensitive else 0
        self._deny: List[Pattern[str]] = [re.compile(pattern, flags) for pattern in options.deny]
        self._allow: List[Pattern[str]] = [re.compile(pattern, flags) for pattern in options.allow]
        self._validator_id = validator_id
        self._options = options

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        text = response.output_text or ""

        if self._allow and any(pattern.search(text) for pattern in self._allow):
            return response

        for pattern in self._deny:
            if pattern.search(text):
                updated = update_finish_reason(response, self._options.failure_reason)
                event = ValidationEvent(
                    validator_id=self._validator_id,
                    category="regex",
                    details={"pattern": pattern.pattern, "source": "response"},
                )
                return append_event(updated, event)
        return response


async def build_regex_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    validator_id: Optional[str] = None,
    **_: Any,
) -> Validator:
    """Factory registered for the regex validator."""
    options_payload: Mapping[str, Any] | RegexValidatorOptions | None = None
    if isinstance(config, ValidatorSettings):
        options_payload = config.options or {}
        validator_id = validator_id or config.id or "validator.regex"
    else:
        options_payload = config
        validator_id = validator_id or "validator.regex"

    options = parse_options(RegexValidatorOptions, options_payload)
    return RegexValidator(options=options, validator_id=validator_id)
