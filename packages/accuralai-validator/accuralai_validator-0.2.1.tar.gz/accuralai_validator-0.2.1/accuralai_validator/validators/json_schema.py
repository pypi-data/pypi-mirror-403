"""JSON schema validator implementation."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional

from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError

from accuralai_core.config.schema import ValidatorSettings
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_core.contracts.protocols import Validator

from ..base import ValidationEvent, append_event, ensure_metadata, update_finish_reason
from ..config import JsonValidatorOptions, parse_options


class JsonValidator(Validator):
    """Validates responses against JSON structure or schema."""

    def __init__(
        self,
        *,
        options: JsonValidatorOptions,
        validator_id: str,
    ) -> None:
        self._options = options
        self._validator_id = validator_id
        self._inline_validator = None
        if options.inline_schema:
            self._inline_validator = Draft202012Validator(options.inline_schema)

    async def validate(self, response: GenerateResponse, *, request: GenerateRequest) -> GenerateResponse:
        parsed, parse_error = self._parse_json(response.output_text)
        metadata_flag = {
            "valid": parse_error is None,
            "schema_mode": self._options.mode,
            "schema_source": self._options.schema_source,
            "schema_key": self._options.schema_key,
            "errors": [],
        }

        if parse_error:
            updated = update_finish_reason(response, "content_filter")
            event = ValidationEvent(
                validator_id=self._validator_id,
                category="json_parse_error",
                details={"message": parse_error},
            )
            updated = append_event(updated, event)
            updated = ensure_metadata(updated, key=self._options.metadata_flag, value=metadata_flag)
            return updated

        if self._options.mode == "structure":
            metadata_flag["valid"] = True
            updated = ensure_metadata(response, key=self._options.metadata_flag, value=metadata_flag)
            return updated

        schema = self._resolve_schema(request)
        if not schema:
            metadata_flag["valid"] = True
            updated = ensure_metadata(response, key=self._options.metadata_flag, value=metadata_flag)
            return updated

        validator = self._inline_validator or Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(parsed), key=lambda error: error.path)
        if not errors:
            metadata_flag["valid"] = True
            updated = ensure_metadata(response, key=self._options.metadata_flag, value=metadata_flag)
            return updated

        metadata_flag["valid"] = False
        metadata_flag["errors"] = [_summarize_error(error) for error in errors]
        updated = update_finish_reason(response, "content_filter")
        event = ValidationEvent(
            validator_id=self._validator_id,
            category="json_schema",
            details={
                "error_count": len(errors),
                "examples": metadata_flag["errors"][:3],
            },
        )
        updated = append_event(updated, event)
        updated = ensure_metadata(updated, key=self._options.metadata_flag, value=metadata_flag)
        return updated

    def _parse_json(self, text: str) -> tuple[Optional[Any], Optional[str]]:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as error:
            return None, f"{error.msg} at line {error.lineno} column {error.colno}"
        return parsed, None

    def _resolve_schema(self, request: GenerateRequest) -> Optional[Dict[str, Any]]:
        if self._options.inline_schema:
            return self._options.inline_schema

        container: Mapping[str, Any] | None
        if self._options.schema_source == "metadata":
            container = request.metadata
        elif self._options.schema_source == "parameters":
            container = request.parameters
        else:
            container = getattr(request, "options", None)

        if not container:
            return None

        schema = container.get(self._options.schema_key)
        if isinstance(schema, Mapping):
            return dict(schema)
        return None


def _summarize_error(error: JsonSchemaError) -> Dict[str, Any]:
    path = list(error.absolute_path)
    return {
        "path": path,
        "message": error.message,
    }


async def build_json_validator(
    *,
    config: ValidatorSettings | Mapping[str, Any] | None = None,
    validator_id: Optional[str] = None,
    **_: Any,
) -> Validator:
    """Factory registered for the JSON schema validator."""
    options_payload: Mapping[str, Any] | JsonValidatorOptions | None = None
    if isinstance(config, ValidatorSettings):
        options_payload = config.options or {}
        validator_id = validator_id or config.id or "validator.json_schema"
    else:
        options_payload = config
        validator_id = validator_id or "validator.json_schema"

    options = parse_options(JsonValidatorOptions, options_payload)
    return JsonValidator(options=options, validator_id=validator_id)
