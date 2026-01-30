# accuralai-validator

`accuralai-validator` delivers reusable validator plugins for the AccuralAI pipeline. Validators apply safety policies, length constraints, and heuristic checks while emitting structured `validator_events` for downstream observability.

## Included Validators

- **noop** – explicit pass-through validator.
- **regex** – deny/allow lists backed by compiled regular expressions.
- **length** – prompt/completion length guards with token/character modes.
- **toxicity** – pluggable moderation adapter that integrates external scoring providers.
- **prompt_injection** – heuristic jailbreak detector using keyword and ratio checks.
- **json_schema** – validates responses against JSON structure or schemas declared inline or per-request.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e packages/accuralai-core[dev]
pip install -e packages/accuralai-validator[dev]
pytest packages/accuralai-validator/tests -q
```

Validators register entry points under `accuralai_core.validators` so `accuralai-core` can compose them into validation chains.
