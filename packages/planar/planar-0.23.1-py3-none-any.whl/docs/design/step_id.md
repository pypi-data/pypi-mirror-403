## Step ID Generation and Management

### Step Sub-Step Count

Planar tracks how many sub-steps (descendant steps) are executed within each step via `sub_step_count`:

```python
step.sub_step_count = ctx.current_step_id - step_id
```

**This count is critical for correct step ID management during replay**, especially when skipping already-completed steps. When replaying a completed step, Planar updates the current step ID to account for all skipped sub-steps:

```python
# When replaying an already completed step
ctx.current_step_id += step.sub_step_count
```


### Step ID Determination

Step IDs are sequentially generated within each workflow execution using a counter in the `ExecutionContext`:

```python
@dataclass(kw_only=True)
class ExecutionContext:
    workflow: Workflow
    current_step_id: int
    step_stack: list[WorkflowStep]
```

When a workflow starts, the execution context initializes with `current_step_id = 0` (see execution.py). Each time a step is executed:

1. The current step ID is incremented: `ctx.current_step_id += 1`
2. This ID is assigned to the step: `step_id = ctx.current_step_id`
3. The step is then persisted with this unique ID

This ensures that:
- Each step within a workflow has a unique ID
- Steps are executed in a deterministic order
- The execution path can be reconstructed during workflow resumption

### The Role of sub_step_count

The `sub_step_count` field serves several critical purposes:

1. **Tracking Nested Execution**: It records how many steps (including nested steps) were executed within a parent step
2. **Deterministic Resumption**: During workflow resumption, when skipping already completed steps, it ensures the step ID counter advances correctly
3. **Execution Tree Reconstruction**: It helps reconstruct the execution tree without re-executing completed steps

#### How sub_step_count works:

When a step completes successfully, its `sub_step_count` is calculated as:
```python
step.sub_step_count = ctx.current_step_id - step_id
```

This represents the difference between:
- The current step ID counter after all nested steps have executed
- The original step ID of the parent step

During workflow resumption, when a completed step is encountered:
```python
# When an already completed step is found
if step.status == StepStatus.SUCCEEDED:
    # Skip execution and update step ID counter to account for all sub-steps
    ctx.current_step_id += step.sub_step_count
    # Return the cached result
    return deserialized_result
```

This mechanism ensures that:
1. The step ID counter advances correctly, maintaining deterministic step IDs
2. Child steps that would have been executed within the completed parent are accounted for
3. Step IDs remain consistent across workflow executions, even when parts are skipped
