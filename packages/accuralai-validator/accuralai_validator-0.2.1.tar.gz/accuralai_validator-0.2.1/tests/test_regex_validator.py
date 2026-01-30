import pytest

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_validator.validators.regex import build_regex_validator


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
async def test_regex_validator_blocks_deny_pattern():
    validator = await build_regex_validator(
        config={
            "deny": [r"secret"],
            "failure_reason": "content_filter",
        },
        validator_id="validator.regex.test",
    )
    response = make_response("Top secret instructions")
    request = GenerateRequest(prompt="Hello")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "content_filter"
    assert updated.validator_events[-1]["category"] == "regex"


@pytest.mark.anyio
async def test_regex_validator_respects_allow_list():
    validator = await build_regex_validator(
        config={
            "deny": [r"secret"],
            "allow": [r"secret sauce"],
        }
    )
    response = make_response("This secret sauce recipe is safe.")
    request = GenerateRequest(prompt="Hello")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "stop"
