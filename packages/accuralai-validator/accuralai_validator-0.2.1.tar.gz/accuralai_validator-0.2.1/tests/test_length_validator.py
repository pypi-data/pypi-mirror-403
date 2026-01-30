import pytest

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_validator.validators.length import build_length_validator


def make_response(text: str, finish_reason: str = "stop") -> GenerateResponse:
    request_id = GenerateRequest(prompt="dummy").id
    return GenerateResponse(
        id=request_id,
        request_id=request_id,
        output_text=text,
        finish_reason=finish_reason,
        usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        latency_ms=0,
    )


@pytest.mark.anyio
async def test_length_validator_flags_long_completion():
    validator = await build_length_validator(
        config={
            "max_completion_tokens": 5,
            "mode": "character",
        },
        validator_id="validator.length.test",
    )
    request = GenerateRequest(prompt="short")
    response = make_response("excessively long completion")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "length"
    assert updated.validator_events[-1]["category"] == "completion_max"


@pytest.mark.anyio
async def test_length_validator_enforces_min_completion():
    validator = await build_length_validator(
        config={
            "min_completion_tokens": 5,
            "mode": "word",
        }
    )
    request = GenerateRequest(prompt="explain")
    response = make_response("too short")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "length"
    assert updated.validator_events[-1]["category"] == "completion_min"
