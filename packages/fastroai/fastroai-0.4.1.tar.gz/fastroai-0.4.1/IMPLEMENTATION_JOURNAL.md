# Implementation Journal: Pluggable Executor Architecture

**Started:** 2025-12-23
**Status:** Planning
**Branch:** `feature/pluggable-executors` (to be created)

---

## 1. Problem Statement

PydanticAI now has native Prefect integration for durable execution, which overlaps with FastroAI's pipeline orchestration. However:

1. **Durable execution isn't always desirable** - it breaks real-time streaming, adds latency, requires infrastructure
2. **FastroAI has unique value** - cost tracking, budgets, microcent precision that Prefect lacks
3. **Users need choice** - lightweight for dev/simple cases, durable for production

**Solution:** Make the execution engine pluggable. FastroAI becomes the unified API layer with cost tracking, while the executor (InMemory vs Prefect) is swappable.

```
┌─────────────────────────────────────────────────────┐
│              FastroAI Pipeline API                  │
│  (steps, dependencies, cost tracking, budgets)     │
├─────────────────────────────────────────────────────┤
│              Executor (pluggable)                   │
│  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ InMemoryExecutor│  │    PrefectExecutor      │  │
│  │ • Fast          │  │ • Durable               │  │
│  │ • Real-time     │  │ • Persistent            │  │
│  │ • No infra      │  │ • Scheduled             │  │
│  │ • Default       │  │ • Optional              │  │
│  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 2. Design Decisions

### 2.1 What Changes

| Component | Change |
|-----------|--------|
| `PipelineExecutor` | Rename to `InMemoryExecutor`, extract `Executor` protocol |
| `Pipeline` | Add optional `executor` parameter |
| `StepConfig` | Add Prefect-specific optional fields |
| New module | `fastroai/executors/` with protocol + implementations |

### 2.2 What Stays the Same

| Component | Status |
|-----------|--------|
| `FastroAgent` | Unchanged |
| `BaseStep`, `@step`, `agent.as_step()` | Unchanged |
| `StepContext`, `ctx.run()` | Unchanged (cost tracking happens here) |
| `ChatResponse`, `StepUsage`, `PipelineUsage` | Unchanged |
| `ConversationState/Status` | Unchanged |
| `CostCalculator` | Unchanged |
| `@safe_tool` | Unchanged |
| Tracers | Unchanged |

### 2.3 StepConfig to Prefect TaskConfig Mapping

| FastroAI `StepConfig` | Prefect `TaskConfig` | Notes |
|-----------------------|---------------------|-------|
| `timeout` | `timeout_seconds` | Direct map |
| `retries` | `retries` | Direct map |
| `retry_delay` | `retry_delay_seconds` | Direct map (extend to support list) |
| `cost_budget` | — | FastroAI-specific, enforced in ctx.run() |
| `persist_result` (new) | `persist_result` | Prefect-specific |
| `result_storage` (new) | `result_storage` | Prefect-specific |
| `cache_policy` (new) | `cache_policy` | Prefect-specific |

### 2.4 Key Insight: Complementary Layers

Cost tracking happens **inside** `ctx.run()`, which executes regardless of executor:

```python
async def execute(self, ctx: StepContext[MyDeps]) -> str:
    # This works identically with InMemory or Prefect executor
    response = await ctx.run(agent, "message")  # Cost tracked here
    return response.content
```

The executor controls **scheduling/persistence**, not what happens inside steps.

---

## 3. Implementation Plan

### Phase 1: Extract Executor Protocol

**Goal:** Create executor abstraction without breaking existing code.

#### Step 1.1: Create executors module structure
- [ ] Create `fastroai/executors/__init__.py`
- [ ] Create `fastroai/executors/protocol.py` with `Executor` protocol
- [ ] Create `fastroai/executors/in_memory.py`

**New file:** `fastroai/executors/protocol.py`
```python
from typing import Protocol, Any
from ..pipelines.base import BaseStep
from ..pipelines.config import PipelineConfig, StepConfig
from ..tracing import Tracer

class ExecutionResult(Protocol):
    outputs: dict[str, Any]
    usages: dict[str, StepUsage]
    conversation_state: ConversationState | None
    stopped_early: bool

class Executor(Protocol):
    async def execute(
        self,
        steps: dict[str, BaseStep],
        dependencies: dict[str, list[str]],
        inputs: dict[str, Any],
        deps: Any,
        tracer: Tracer | None,
        pipeline_config: PipelineConfig | None,
        step_configs: dict[str, StepConfig],
    ) -> ExecutionResult: ...
```

#### Step 1.2: Refactor PipelineExecutor to InMemoryExecutor
- [ ] Move `PipelineExecutor` from `executor.py` to `executors/in_memory.py`
- [ ] Rename class to `InMemoryExecutor`
- [ ] Ensure it implements `Executor` protocol
- [ ] Keep `executor.py` as re-export for backward compatibility

**File:** `fastroai/pipelines/executor.py` (becomes thin re-export)
```python
# Backward compatibility
from ..executors import InMemoryExecutor as PipelineExecutor
from ..executors import StepExecutionError, ExecutionResult
```

#### Step 1.3: Update Pipeline to accept executor
- [ ] Add `executor: Executor | None = None` parameter to `__init__`
- [ ] Default to `InMemoryExecutor()` if not provided
- [ ] Update `execute()` to use the executor instance

**File:** `fastroai/pipelines/pipeline.py`

---

### Phase 2: Extend StepConfig

**Goal:** Add Prefect-specific configuration fields.

#### Step 2.1: Update StepConfig with optional Prefect fields
- [ ] Add `persist_result: bool | None = None`
- [ ] Add `result_storage: str | None = None`
- [ ] Add `cache_policy: Any | None = None`
- [ ] Change `retry_delay: float | list[float] = 1.0` (support exponential backoff)

**File:** `fastroai/pipelines/config.py`

#### Step 2.2: Update InMemoryExecutor to ignore new fields
- [ ] Ensure new fields are simply ignored (no behavior change)

---

### Phase 3: Implement PrefectExecutor

**Goal:** Create optional Prefect-based executor.

#### Step 3.1: Create PrefectExecutor class
- [ ] Create `fastroai/executors/prefect.py`
- [ ] Implement `Executor` protocol
- [ ] Map StepConfig fields to Prefect TaskConfig
- [ ] Wrap steps as Prefect tasks
- [ ] Handle result persistence

**File:** `fastroai/executors/prefect.py`
```python
from prefect import flow, task
from prefect.cache_policies import CachePolicy

class PrefectExecutor:
    def __init__(
        self,
        result_storage: str | None = None,
        default_task_config: TaskConfig | None = None,
    ): ...

    async def execute(self, ...) -> ExecutionResult:
        # Create Prefect flow
        # Wrap each step as a task
        # Execute with Prefect's DAG scheduler
        ...
```

#### Step 3.2: Handle cost tracking in Prefect context
- [ ] Ensure ctx.run() still works inside Prefect tasks
- [ ] Verify usage accumulation works correctly
- [ ] Test cost budget enforcement

#### Step 3.3: Add optional dependency handling
- [ ] PrefectExecutor requires `prefect` package
- [ ] Graceful error if prefect not installed
- [ ] Document installation: `pip install fastroai[prefect]`

---

### Phase 4: Update Exports and Documentation

#### Step 4.1: Update package exports
- [ ] Export `Executor`, `InMemoryExecutor` from `fastroai`
- [ ] Export `PrefectExecutor` from `fastroai.executors.prefect`
- [ ] Maintain backward compatibility for `PipelineExecutor` name

**File:** `fastroai/__init__.py`

#### Step 4.2: Update pyproject.toml
- [ ] Add `prefect` as optional dependency
- [ ] Create `[prefect]` extras group

**File:** `pyproject.toml`
```toml
[project.optional-dependencies]
prefect = ["prefect>=3.0.0"]
```

---

### Phase 5: Testing

#### Step 5.1: Unit tests for executor protocol
- [ ] Test InMemoryExecutor matches protocol
- [ ] Test executor parameter in Pipeline

#### Step 5.2: Unit tests for PrefectExecutor
- [ ] Test StepConfig mapping to TaskConfig
- [ ] Test step wrapping as tasks
- [ ] Test cost tracking inside Prefect tasks
- [ ] Mock Prefect to avoid requiring actual Prefect server

#### Step 5.3: Integration tests
- [ ] Test Pipeline with InMemoryExecutor (existing behavior)
- [ ] Test Pipeline with PrefectExecutor
- [ ] Test executor switching

---

## 4. Architecture Notes

### 4.1 Module Structure (After)

```
fastroai/
├── __init__.py                    # Add Executor, InMemoryExecutor exports
├── executors/
│   ├── __init__.py               # Executor protocol, InMemoryExecutor, ExecutionResult
│   ├── protocol.py               # Executor protocol definition
│   ├── in_memory.py              # Current PipelineExecutor, renamed
│   └── prefect.py                # Optional PrefectExecutor
├── pipelines/
│   ├── executor.py               # Backward compat re-exports
│   ├── pipeline.py               # Updated with executor param
│   ├── config.py                 # Extended StepConfig
│   └── ...
└── ...
```

### 4.2 API Changes

**Before:**
```python
pipeline = Pipeline(
    name="processor",
    steps={"extract": extract, "classify": classify},
    dependencies={"classify": ["extract"]},
)
result = await pipeline.execute(data, deps)
```

**After (default behavior unchanged):**
```python
# This still works exactly the same (InMemoryExecutor is default)
pipeline = Pipeline(
    name="processor",
    steps={"extract": extract, "classify": classify},
    dependencies={"classify": ["extract"]},
)
result = await pipeline.execute(data, deps)

# Opt-in to Prefect execution
from fastroai.executors.prefect import PrefectExecutor

pipeline = Pipeline(
    name="processor",
    steps={"extract": extract, "classify": classify},
    dependencies={"classify": ["extract"]},
    executor=PrefectExecutor(result_storage="s3://my-bucket"),
    step_configs={
        "classify": StepConfig(
            timeout=30.0,
            retries=3,
            cost_budget=100_000,      # FastroAI-specific
            persist_result=True,       # Prefect-specific
        ),
    },
)
```

### 4.3 Backward Compatibility

| Change | Compatibility |
|--------|--------------|
| New `executor` param | Optional, defaults to current behavior |
| `PipelineExecutor` name | Kept as alias to `InMemoryExecutor` |
| New `StepConfig` fields | Optional with None defaults |
| Existing tests | Must pass without modification |

---

## 5. Progress Log

### 2025-12-23: Architecture Design

- [x] Analyzed PydanticAI + Prefect integration
- [x] Identified overlap with FastroAI pipelines
- [x] Identified FastroAI's unique value (cost tracking)
- [x] Designed pluggable executor architecture
- [x] Mapped StepConfig to Prefect TaskConfig
- [x] Created implementation plan

---

## 6. Open Questions

1. **Executor on Pipeline vs execute():** Should executor be a Pipeline property or passed to execute()?
   - **Decision:** Pipeline property. Executor choice is a deployment decision, not per-call.

2. **PrefectExecutor configuration:** Should we mirror all Prefect options or keep it simple?
   - **Leaning:** Start simple (result_storage, default_task_config), expand as needed.

3. **Streaming with Prefect:** Prefect breaks real-time streaming. Should we warn users?
   - **Decision:** Document clearly. PrefectExecutor is for durability, not real-time.

4. **BasePipeline (Router):** Does it need executor support?
   - **Leaning:** Yes, it should inherit executor from registered pipelines or accept its own.

---

## 7. Files to Modify/Create

| File | Action | Changes |
|------|--------|---------|
| `fastroai/executors/__init__.py` | Create | Protocol, InMemoryExecutor exports |
| `fastroai/executors/protocol.py` | Create | Executor protocol definition |
| `fastroai/executors/in_memory.py` | Create | Move + rename PipelineExecutor |
| `fastroai/executors/prefect.py` | Create | PrefectExecutor implementation |
| `fastroai/pipelines/executor.py` | Modify | Backward compat re-exports |
| `fastroai/pipelines/pipeline.py` | Modify | Add executor parameter |
| `fastroai/pipelines/config.py` | Modify | Extend StepConfig |
| `fastroai/__init__.py` | Modify | Export new classes |
| `pyproject.toml` | Modify | Add prefect optional dep |
| `tests/test_executors.py` | Create | Executor tests |

---

## 8. References

- PydanticAI Prefect docs: https://ai.pydantic.dev/integrations/prefect/
- Prefect TaskConfig: `retries`, `retry_delay_seconds`, `timeout_seconds`, `cache_policy`, `persist_result`, `result_storage`
- Current executor: `fastroai/pipelines/executor.py`
- Current config: `fastroai/pipelines/config.py`
