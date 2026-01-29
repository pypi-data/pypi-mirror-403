# Nested Steps in Planar

planar workflows allows for arbitrary levels of nesting `@step` functions. `planar` will then guarantee that the execution path is deterministic upon workflow resumption.

### Core Components

1. **Step Stack**: An in-memory list of currently executing steps that tracks the execution hierarchy
2. **dynamically-determined sequential step_id**: `step_id` primary key is determined dynamically based on function call order

### Conceptual Execution Flow of Nested Steps

When a workflow executes nested steps, the following occurs:

1. Parent step begins execution and is pushed onto the step stack
2. Parent step calls a child step
3. Child step is created with `parent_step_id` set to the parent's step ID
4. Child step is pushed onto the step stack (now containing both parent and child)
5. Child step executes
6. Child step is popped from the stack upon completion
7. Parent step continues execution
8. Parent step is popped from the stack upon completion

This creates a tree structure of execution where each step can have one parent and multiple children.


Hence the last element of `step_stack` represents the immediate parent step of the currently executing step.


### Walkthrough of code in `step_core.py`

1. The `ExecutionContext` class in `context.py` maintains a `step_stack` which tracks the hierarchy of steps during execution:

```python
@dataclass(kw_only=True)
class ExecutionContext:
    workflow: Workflow
    current_step_id: int
    step_stack: list[WorkflowStep]
```

2. When a step begins execution, it checks the stack to determine its parent:

```python
parent_step_id = None
if ctx.step_stack:
    parent_step_id = ctx.step_stack[-1].step_id

step = WorkflowStep(
    step_id=step_id,
    # other steps elided
    parent_step_id=parent_step_id,
)
```

3. Subsequently it appends itself to the `step_stack` before running the actual wrapped function:

```python
ctx.step_stack.append(step)

try:
    result = await func(*args, **kwargs)
    # ...
finally:
    ctx.step_stack.pop()
```

### Parent-Child Relationship Model

The `WorkflowStep` model includes a `parent_step_id` field to persist the parent-child relationship:

```python
class WorkflowStep(SQLModel, table=True):
    step_id: int = Field(primary_key=True)
    parent_step_id: int | None = Field(default=None, index=True)
    # ... other fields ...
```

### Determinism Validation

During workflow retries and resumptions, Planar enforces deterministic execution by validating that the parent-child relationships remain consistent:

```python
# During step retry
current_parent_id = None if not ctx.step_stack else ctx.step_stack[-1].step_id
if step.parent_step_id != current_parent_id:
    step.status = StepStatus.FAILED
    await Suspend(
        exception=NonDeterministicStepCallError(
            f"Non-deterministic parent step detected for step ID {step_id}. "
            f"Previous parent: {step.parent_step_id}, current: {current_parent_id}"
        )
    )
    assert False, "Non-deterministic parent step detected"
```

This ensures that the execution hierarchy is maintained across workflow runs.

### Hierarchy Navigation

Planar provides utility functions for navigating the step hierarchy:

```python
async def get_step_parent(step: WorkflowStep) -> WorkflowStep | None:
```

```python
async def get_step_children(step: WorkflowStep) -> list[WorkflowStep]:
```

```python
async def get_step_descendants(step: WorkflowStep) -> list[WorkflowStep]:
```

```python
async def get_step_ancestors(step: WorkflowStep) -> list[WorkflowStep]:
```

### Example Scenario

Consider a workflow with nested steps:
```python
@workflow()
async def example_workflow():
    await step_a()  # ID: 1
    return "done"

@step()
async def step_a():
    await step_b()  # ID: 2
    await step_c()  # ID: 3
    return "a"

@step()
async def step_b():
    return "b"

@step()
async def step_c():
    return "c"
```

When this workflow completes:
- `step_a` has `step_id = 1` and `sub_step_count = 2` (steps 2 and 3 were executed within it)
- `step_b` has `step_id = 2` and `sub_step_count = 0` (no nested steps)
- `step_c` has `step_id = 3` and `sub_step_count = 0` (no nested steps)

If the workflow is resumed and `step_a` is already completed, the system:
1. Finds `step_a` with `step_id = 1`
2. Sees it's already completed (`status = SUCCEEDED`)
3. Adds its `sub_step_count` (2) to the current step ID counter
4. Returns the cached result without re-executing it or its child steps

This ensures that any subsequent steps would continue with `step_id = 4`, maintaining consistency with the original execution.