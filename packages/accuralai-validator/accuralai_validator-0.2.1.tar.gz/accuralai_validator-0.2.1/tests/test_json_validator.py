import pytest

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_validator.validators.json_schema import build_json_validator


def make_response(text: str) -> GenerateResponse:
    request_id = GenerateRequest(prompt="dummy").id
    return GenerateResponse(
        id=request_id,
        request_id=request_id,
        output_text=text,
        finish_reason="stop",
        usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        latency_ms=0,
    )


@pytest.mark.anyio
async def test_json_validator_validates_structure_only():
    validator = await build_json_validator(config={"mode": "structure"})
    request = GenerateRequest(prompt="hello")
    response = make_response('{"key": "value"}')

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "stop"
    assert updated.metadata["json_validation"]["valid"] is True


@pytest.mark.anyio
async def test_json_validator_flags_invalid_json():
    validator = await build_json_validator(config={"mode": "structure"})
    request = GenerateRequest(prompt="hello")
    response = make_response("{not-json")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "content_filter"
    assert updated.metadata["json_validation"]["valid"] is False
    assert updated.validator_events[-1]["category"] == "json_parse_error"


@pytest.mark.anyio
async def test_json_validator_uses_inline_schema():
    validator = await build_json_validator(
        config={
            "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            }
        }
    )
    request = GenerateRequest(prompt="hello")
    response = make_response("{}")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "content_filter"
    flag = updated.metadata["json_validation"]
    assert flag["valid"] is False
    assert flag["errors"]
    assert updated.validator_events[-1]["category"] == "json_schema"


@pytest.mark.anyio
async def test_json_validator_reads_schema_from_metadata():
    validator = await build_json_validator(
        config={
            "schema_source": "metadata",
            "schema_key": "json_schema",
        }
    )
    request = GenerateRequest(
        prompt="hello",
        metadata={
            "json_schema": {
                "type": "object",
                "properties": {"id": {"type": "number"}},
                "required": ["id"],
            }
        },
    )
    response = make_response('{"id": 42}')

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "stop"
    assert updated.metadata["json_validation"]["valid"] is True
