"""Configuration schemas for validator plugins."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class RegexValidatorOptions(BaseModel):
    """Options for the regex validator."""

    deny: Sequence[str] = Field(default_factory=list)
    allow: Sequence[str] = Field(default_factory=list)
    case_insensitive: bool = True
    failure_reason: str = "content_filter"

    @model_validator(mode="after")
    def _ensure_patterns(self) -> "RegexValidatorOptions":
        if not self.deny and not self.allow:
            msg = "Regex validator requires at least one deny or allow pattern."
            raise ValueError(msg)
        return self


class LengthValidatorOptions(BaseModel):
    """Options controlling length limits."""

    max_prompt_tokens: Optional[int] = Field(default=None, ge=1)
    max_completion_tokens: Optional[int] = Field(default=None, ge=1)
    min_completion_tokens: Optional[int] = Field(default=None, ge=0)
    mode: str = Field(default="token")
    truncate: bool = False

    @model_validator(mode="after")
    def _validate(self) -> "LengthValidatorOptions":
        if (
            self.max_prompt_tokens is None
            and self.max_completion_tokens is None
            and self.min_completion_tokens is None
        ):
            msg = "Length validator requires at least one constraint."
            raise ValueError(msg)
        if self.mode not in {"token", "character", "word"}:
            msg = "Length validator mode must be one of 'token', 'character', or 'word'."
            raise ValueError(msg)
        return self


class ToxicityValidatorOptions(BaseModel):
    """Options for the toxicity validator."""

    provider: Optional[str] = None
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    category_thresholds: Dict[str, float] = Field(default_factory=dict)
    block_categories: Sequence[str] = Field(default_factory=list)
    cache_key_suffix: Optional[str] = None


class PromptInjectionValidatorOptions(BaseModel):
    """Options for prompt injection heuristics."""

    ban_keywords: Sequence[str] = Field(
        default_factory=lambda: [
            "ignore previous",
            "disregard above",
            "override instructions",
        ]
    )
    max_instruction_ratio: float = Field(default=0.6, ge=0.0, le=1.0)
    flag_system_override: bool = True


class JsonValidatorOptions(BaseModel):
    """Options for JSON schema validation."""

    model_config = ConfigDict(populate_by_name=True)

    inline_schema: Optional[Dict[str, Any]] = Field(default=None, alias="schema")
    schema_source: str = Field(default="metadata")
    schema_key: str = Field(default="json_schema")
    mode: str = Field(default="schema")  # "schema" or "structure"
    metadata_flag: str = Field(default="json_validation")

    @model_validator(mode="after")
    def _validate(self) -> "JsonValidatorOptions":
        if self.mode not in {"schema", "structure"}:
            msg = "JsonValidator mode must be 'schema' or 'structure'"
            raise ValueError(msg)
        if self.schema_source not in {"metadata", "parameters", "options"}:
            msg = "JsonValidator schema_source must be 'metadata', 'parameters', or 'options'"
            raise ValueError(msg)
        return self


def parse_options(model: type[BaseModel], payload: Mapping[str, Any] | BaseModel | None) -> BaseModel:
    """Normalize validator option payloads."""
    if payload is None:
        return model()
    if isinstance(payload, model):
        return payload
    if isinstance(payload, BaseModel):
        return model.model_validate(payload.model_dump())
    if isinstance(payload, Mapping):
        try:
            return model.model_validate(dict(payload))
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
    msg = f"Unsupported validator configuration payload: {type(payload)!r}"
    raise TypeError(msg)
