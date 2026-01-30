import pytest

from accuralai_core.contracts.errors import ConfigurationError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_validator.validators.toxicity import build_toxicity_validator


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
async def test_toxicity_validator_blocks_high_scores():
    async def provider(request, response):
        return {"harassment": 0.9, "self_harm": 0.1}

    validator = await build_toxicity_validator(
        config={"threshold": 0.5},
        provider=provider,
        validator_id="validator.toxicity.test",
    )

    request = GenerateRequest(prompt="hello")
    response = make_response("response")

    updated = await validator.validate(response, request=request)
    assert updated.finish_reason == "content_filter"
    assert updated.metadata["toxicity_scores"]["harassment"] == 0.9
    assert updated.validator_events[-1]["category"] == "toxicity"


@pytest.mark.anyio
async def test_toxicity_validator_requires_provider():
    with pytest.raises(ConfigurationError):
        await build_toxicity_validator(config={"threshold": 0.2})
