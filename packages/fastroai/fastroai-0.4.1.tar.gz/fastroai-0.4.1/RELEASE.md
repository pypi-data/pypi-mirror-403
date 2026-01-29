# FastroAI 0.4.1 Release Notes

FastroAI 0.4.1 fixes incorrect model tracking when using PydanticAI's FallbackModel and other model wrappers. Cost calculations are now accurate regardless of which model in a fallback chain processes the request.

## Summary

**Bug Fixes:**
- **FallbackModel Support**: Correctly tracks the actual model that processed the request, not the configured default
- **No False Model Assumptions**: When model can't be detected (e.g., escape hatch without explicit model), returns `model=None` and `cost=0` instead of assuming `gpt-4o`

**No Breaking Changes** - `ChatResponse.model` is now `str | None` but existing code checking the model string will continue to work.

## The Problem We Solved

Previously, FastroAgent attempted to get the model name from `usage.model`, but PydanticAI's `RunUsage` class doesn't have this field. This caused two issues:

1. **FallbackModel Misreporting**: When using `FallbackModel` with DeepSeek primary and GPT-4o fallback, the tracked model was always `openai:gpt-4o` (the config default) regardless of which model actually responded.

2. **Incorrect Cost Calculation**: Costs were calculated using the wrong model's pricing, potentially overcharging or undercharging by significant amounts.

**Example: FallbackModel with DeepSeek**

```python
from pydantic_ai import Agent
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from fastroai import FastroAgent

fallback_model = FallbackModel(
    OpenAIChatModel("deepseek-chat"),  # Primary
    OpenAIChatModel("gpt-4o-mini"),    # Fallback
)

pydantic_agent = Agent(model=fallback_model, output_type=str)
agent = FastroAgent(agent=pydantic_agent)

response = await agent.run("Hello")
```

| Metric | Before (v0.4.0) | After (v0.4.1) |
|--------|-----------------|----------------|
| `response.model` | `"openai:gpt-4o"` | `"deepseek-chat"` |
| Cost Basis | GPT-4o pricing | DeepSeek pricing |

## How It Works

FastroAgent now extracts the model name from `ModelResponse.model_name` in the message history, which PydanticAI populates with the actual model that processed each request:

```python
# PydanticAI's response structure
response.all_messages()
# Returns:
# [
#     ModelRequest(...),
#     ModelResponse(
#         parts=[TextPart(content='...')],
#         model_name='deepseek-chat',  # <-- Actual model used
#         timestamp=datetime.datetime(...),
#     ),
# ]
```

### Fallback Behavior

When model extraction fails:

1. **With explicit model configured**: Falls back to the configured model
2. **Escape hatch without model**: Returns `model=None` and `cost_microcents=0`, logs a warning

```python
# Escape hatch without explicit model - model detection required
agent = FastroAgent(agent=custom_pydantic_agent)  # No model=
# If detection fails: model=None, cost=0, warning logged

# Escape hatch with explicit model - has fallback
agent = FastroAgent(agent=custom_pydantic_agent, model="gpt-4o-mini")
# If detection fails: model="gpt-4o-mini"
```

## API Changes

### ChatResponse.model

The `model` field is now `str | None`:

```python
response = await agent.run("Hello")

if response.model:
    print(f"Model: {response.model}")
    print(f"Cost: ${response.cost_dollars:.6f}")
else:
    print("Model unknown - cost not calculated")
    print(f"Tokens used: {response.total_tokens}")
```

### CostCalculator.calculate_cost()

Now accepts `model: str | None` and returns `0` for `None`:

```python
calc = CostCalculator()

# Returns 0 for unknown model
cost = calc.calculate_cost(None, input_tokens=100, output_tokens=50)
assert cost == 0
```

## Upgrade Guide

No changes required for most users. If you're using FallbackModel or custom agents:

1. **Verify model tracking**: Check that `response.model` now shows the correct model
2. **Handle None model**: If using escape hatch without explicit model, handle the case where `response.model` is `None`

```python
# Before: assumed gpt-4o pricing even with FallbackModel
# After: correct model and pricing

# If you need to handle unknown models:
if response.model is None:
    logger.warning("Model unknown, cost not calculated")
```

---

**Full Changelog**: https://github.com/benavlabs/fastroai/compare/v0.4.0...v0.4.1
