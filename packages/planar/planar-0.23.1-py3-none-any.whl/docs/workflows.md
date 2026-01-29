# Planar Workflows Guide

## Overview

Planar provides a durable workflow engine that enables you to build fault-tolerant, long-running business processes that can survive application restarts and continue exactly where they left off.

This guide explains the core concepts and usage patterns for working with Planar workflows.

## Core Concepts

### Workflow

A workflow is a top-level orchestration function that coordinates a series of steps to accomplish a business process. Workflows are:

- **Durable**: Persisted to the database for fault tolerance
- **Resumable**: Can be resumed from the last successful step after application restarts
- **Cancellable**: Can be cancelled during execution via API

#### Workflow Status

Workflows can be in one of the following states:

- `pending`: Workflow is waiting to be executed
- `running`: Workflow is currently being executed (actively processing steps)
- `suspended`: Workflow is waiting for an event or timeout
- `succeeded`: Workflow completed successfully
- `failed`: Workflow failed due to an error
- `cancelled`: Workflow was cancelled via the cancel API

### Step

A step is a single unit of work within a workflow. Steps are:

- **Atomic**: All database changes within a step are committed as a transaction. This is true as long as a step doesn't call other steps or calls session management methods directly (`begin`, `commit` or `rollback`)
- **Resumable**: Execution state is preserved between runs

## Key Decorators

### `@workflow()`

Declares a function as a durable workflow.

```python
from planar.workflows import workflow

@workflow()
async def my_workflow(param1: str, param2: int) -> str:
    # Orchestrate steps here
    result1 = await step1(param1)
    result2 = await step2(result1, param2)
    return await final_step(result2)
```

#### Important notes:
- Workflow functions must be coroutines (async/await)
- Workflow code must only include deterministic logic, with no side effects. Any non-deterministism (ie. random numbers, time, etc) or side effects (ie. database writes, file writes, etc) must be handled by a step. This is to ensure that the workflow can be replayed exactly the same way every time.
- Parameters and return values can be Pydantic models or native Python types (e.g., `bool`, `int`, `float`, `decimal.Decimal`, `UUID`, `datetime`).
  - Lists of the above are also supported (ie. list[SomeModel] or list[int]). Only Dicts of primitive types are supported currently (ie. str, int, bool - but no datetime, UUID, etc).
- Register workflows with your app: `app.register_workflow(my_workflow)`

#### Parent-Child Workflow Relationships

How a child workflow is started from a parent workflow determines their relationship and the parent's behavior:

1.  **Blocking workflow call:**
    When a parent workflow calls another workflow directly using `await child_workflow_func(...)`:
    *   The child workflow record will have its `parent_id` attribute set to the ID of the parent workflow.
    *   The parent workflow will automatically suspend its execution.
    *   The Planar orchestrator is designed to only resume the parent workflow after all of its child workflows (linked by `parent_id`) have completed. This is part of the orchestrator's polling logic.

    ```python
    @workflow()
    async def parent_workflow():
        # ...
        child_result = await child_workflow() # Parent suspends here
        # Parent resumes here only after child_workflow completes
        # ...
    ```

2.  **Non-blocking workflow call (calling one of the "start" methods):**
    When a parent workflow starts another workflow using `child_workflow_func.start(...)` or `child_workflow_func.start_step(...)`:
    *   This creates a new workflow instance, but its `parent_id` attribute will **not** be automatically set. There's no explicit parent-child link recorded in the database for the orchestrator to act upon directly.
    *   The parent workflow continues its execution immediately after initiating the child workflow; it does not automatically suspend.
    *   If the parent needs to wait for the child's completion, it can explicitly do so by calling `await orchestrator.wait_for_completion(child_workflow_id)`.

    ```python
    from planar.workflows.orchestrator import WorkflowOrchestrator

    @workflow()
    async def parent_workflow_explicit_start():
        # ...
        child_wf_instance = await child_workflow.start()
        # Parent continues executing immediately...
        # ...
        # If parent needs to wait for child:
        orchestrator = WorkflowOrchestrator.get()
        child_result = await orchestrator.wait_for_completion(child_wf_instance.id)
        # ...
    ```

#### Concurrent fan-out with `gather`

Use `planar.workflows.gather()` when you need to start multiple workflows or steps at the same time
**and** wait for every child to finish.

```python
from planar.workflows import gather, step, workflow

@step()
async def score_order(order_id: int) -> int:
    ...

@step()
async def notify_sales(order_id: int) -> None:
    ...

@workflow()
async def reconcile_order(order_id: int):
    score, notification_status = await gather(
        score_order(order_id),
        notify_sales(order_id),
    )
    return {"score": score, "notified": notification_status}
```

Key behaviors:
- Works inside workflows or steps (steps run inside a workflow context) and only accepts
  Planar-wrapped coroutines.
- Returns a tuple of results ordered exactly like the inputs, so destructuring works just like
  `asyncio.gather`.
- Automatically sets each child workflow's `parent_id` to the caller and suspends the caller until
  every child finishes.
- Raises the first child exception by default; pass `return_exceptions=True` to receive
  `Exception` objects in the tuple and continue handling manually.


#### Fire-and-forget fan-out with `start`

If you need to launch concurrent workflows but keep the parent workflow running, use
`planar.workflows.utils.start()`. It starts each workflow the same way as `gather`, but immediately
returns the child workflow IDs instead of suspending.

```python
from planar.workflows import workflow
from planar.workflows.utils import start

@workflow()
async def process_order(order_id: int) -> str:
    ...

@workflow()
async def kickoff_orders(order_ids: list[int]) -> dict[str, list[str]]:
    child_ids = await start(
        process_order(order_ids[0]),
        process_order(order_ids[1]),
    )
    return {"child_workflow_ids": [str(child_id) for child_id in child_ids]}
```

Key behaviors:
- Returns a tuple of `UUID`s for the started workflows; the parent keeps executing immediately
  after the start step completes.
- Accepts the same workflow/step coroutines as `gather`.
- Does not link the new workflows back to the caller. If you need their
  `parent_id` set (and for the parent to suspend until they finish), either
  `await` the workflow directly or use `gather`.
- Combine with `WorkflowOrchestrator.wait_for_completion` when you want full control over when and
  how you fan the results back in.

Use `start` for fire-and-forget style fan-out or when you need to coordinate complex fan-in logic
yourself, and use `gather` when you simply need to wait for concurrent work to finish.

### `@step(max_retries=0)`

Declares a function as a workflow step.

```python
from planar.workflows import step

@step()
async def my_step(param: str) -> int:
    # Step implementation
    session = get_session()
    # Do work
    return result
```

#### Important notes:
- Step functions must be coroutines (async/await)
- Step code can include non-deterministic logic (ie. random numbers, time, etc) and side effects (ie. database writes, file writes, etc), but only if it does not have child steps. Steps with child steps should be treated like workflows, and only include deterministic logic.
- Parameters and return values can be Pydantic models or native Python types (bool, int, float, decimal.Decimal, UUID, datetime)
- Native Python types and Pydantic models are automatically serialized/deserialized based on function type hints
- Never call `session.commit()` within a step - the framework handles this
- The `max_retries` parameter controls retry behavior:
  - `max_retries=0` (default): No retries on failure. Unless the exception is handled by a caller, the workflow will fail.
  - `max_retries=N` (positive integer): Retry up to N times on failure.
  - `max_retries=-1` (or any negative integer): Retry indefinitely on failure.
- The `display_name` parameter allows providing a custom name shown in UI or observability tools (defaults to the function name).
- The `step_type` parameter categorizes the step (e.g., `COMPUTE`, `HUMAN_IN_THE_LOOP`). This is often set automatically by constructs like `Human`.
- The `return_type` parameter can explicitly specify the step's return type, aiding serialization, especially with generics. This is more useful when defining new step types (see how Human/Agent steps are defined).

### `wait_for_event(event_key: str, max_wait_time: float = -1)`

Creates a durable step that waits for a specific event to be emitted.

```python
from planar.workflows.events import emit_event, wait_for_event

from pydantic import BaseModel

class ApprovalAction(BaseModel):
    approved: bool
    comment: Optional[str] = None

# In a workflow step:
# Wait for a specific event, e.g., an approval for a specific expense by a specific manager
await wait_for_event(f"expense_approval:{manager_id}:{expense_id}")
# The event payload (if any) is returned by wait_for_event, though often not needed
# if the next step fetches the required data.

# Elsewhere (e.g., in an API endpoint handling the approval):
await emit_event(
    f"expense_approval:{approver_id}:{expense_id}",
    payload={"approved": True, "comment": "Looks good"} # Optional payload
)
```

#### Important notes:
- The workflow will continue execution if the event key exists or suspend until the exact event key is emitted
- Event keys should be structured to be unique and specific (e.g., use IDs).
- Optional `max_wait_time` parameter (in seconds) to fail if the event is not received within the specified time. A value less than 0 means wait indefinitely (unless an event key is provided).
- `emit_event` can optionally include a JSON-serializable `payload`. This payload is returned by `wait_for_event`.
- `emit_event` can target a specific `workflow_id` or be broadcast globally (`workflow_id=None`).

### `Human()`

Creates a step that requires human interaction to complete.

```python
from pydantic import BaseModel, Field
from planar.human import Human, Timeout
from datetime import timedelta

# Define input and output models for the human task
class ExpenseRequest(BaseModel):
    request_id: str
    amount: float

class ExpenseDecision(BaseModel):
    approved: bool
    notes: str = ""

# Create the human task definition
expense_approval = Human(
    name="expense_approval",  # Unique name for this task type
    title="Expense Approval",
    description="Review expense request",
    input_type=ExpenseRequest,
    output_type=ExpenseDecision,
    timeout=Timeout(timedelta(hours=24)), # Optional timeout
)

# In a workflow:
@workflow()
async def expense_workflow(request_data: ExpenseRequest):
    # ... other steps ...
    expense_request = await validate_expense(request_data)

    # Request human approval
    result = await expense_approval(
        expense_request, # Pass the input data
        message="Please review this expense", # Optional message for the human
    )

    # Process the human's decision (result.output is an ExpenseDecision instance)
    if result.output.approved:
        await process_approval(expense_request.request_id, result.output.notes)
    else:
        await process_rejection(expense_request.request_id, result.output.notes)
```

#### Important notes:
- Define input (`input_type`) and output (`output_type`) Pydantic models.
- Use the `Human` instance like a step function within your workflow.
- The workflow suspends (using `wait_for_event` internally) until the human task is completed via the API (e.g., `/api/human-tasks/{task_id}/complete`).
- The result object contains the `output` (instance of `output_type`) provided by the human.
- An optional `timeout` (using the `Timeout` helper class) can be specified. If the task is not completed within this duration, the internal `wait_for_event` call will raise a timeout error.

### `Agent()`

Creates a step that interacts with an AI model (like OpenAI).

```python
from pydantic import BaseModel
from planar.ai import Agent, ConfiguredModelKey
from planar.files import PlanarFile

# Define the expected output structure
class ExtractedInvoiceData(BaseModel):
    invoice_number: str
    amount_total: float

# Define the agent
extraction_agent = Agent(
    name="Invoice Extraction Agent",
    model=ConfiguredModelKey("invoice_parsing_model"),
    system_prompt="Extract invoice details precisely.",
    user_prompt="Extract information from this invoice image:",
    output_type=ExtractedInvoiceData, # The Pydantic model for the result
)

# In a workflow:
@workflow()
async def invoice_processing_workflow(file: PlanarFile) -> ExtractedInvoiceData:
    # Call the agent step
    extraction_result = await extraction_agent(file)
    # Access the structured output
    return extraction_result.output
```

#### Important notes:
- The Agent returns a `str` output by default, but can return structured output if you define the expected output structure using a Pydantic model (`output_type`).
- Configure the agent with a name, model (or ConfiguredModelKey), prompts, and the result type.
- Call the agent instance like a step function. Provide the primary input value as the first argument and, when `tool_context_type` is declared, pass `tool_context=` with a matching instance.
- Tools can access context inside the agent run with `planar.ai.get_tool_context()` when `tool_context_type` is configured on the agent. The context instance should expose durable dependencies (API clients, repositories) or immutable data rather than mutable state.
- The workflow suspends while waiting for the AI model's response.
- The result object contains the structured `output` (instance of `output_type`).
- Requires AI provider configuration (e.g., OpenAI API key) in `PlanarConfig` plus an `ai_models` section defining `invoice_parsing_model`.
- Register agents with your app: `app.register_agent(extraction_agent)`.

#### Stateful agents

Agents that declare a `tool_context_type` can make shared context available across turns or workflow invocations, accessible within tools. Pass a `tool_context` object matching the declared type when calling the agent, then read it inside tools with `planar.ai.get_tool_context()`. If you need to track progress, persist it via an entity, db or service referenced by the context object instead of mutating attributes directly since durable replays do not restore in-memory mutations.

### `@rule()`

Declares a function as a business rule step, integrated with a rules engine (like JDM).

```python
from pydantic import BaseModel
from planar.rules.decorator import rule

class ExpenseRuleInput(BaseModel):
    amount: float
    category: str

class RuleOutput(BaseModel):
    approved: bool
    reason: str

# Default implementation (can be overridden by JDM)
@rule(description="Default expense approval rule")
def expense_approval_rule(input: ExpenseRuleInput) -> RuleOutput:
    if input.category == "Travel" and input.amount > 1000:
        return RuleOutput(approved=False, reason="Travel over $1000 needs manual review")
    return RuleOutput(approved=True, reason="Auto-approved")

# In a workflow:
@workflow()
async def rule_workflow(expense_data: ExpenseRuleInput):
    # ...
    approval_result = await expense_approval_rule(expense_data)
    # ... process approval_result ...

# Batch execution (single workflow step for many inputs):
@workflow()
async def batch_rule_workflow(expense_items: list[ExpenseRuleInput]):
    results = await expense_approval_rule.batch(expense_items)
    # ... handle the list of RuleOutput instances ...
```

#### Important notes:
- Input and output must be Pydantic models.
- The decorated function provides a default implementation.
- This implementation can be overridden by deploying a corresponding rule definition (e.g., a JDM graph) via the Planar API (`RuleOverride`).
- Call `rule.batch([...])` when you need to evaluate multiple inputs in one step.
- Register rules with your app: `app.register_rule(expense_approval_rule)`.

## Patterns for Workflow Development

### Waiting for External Events

A common pattern is waiting for external events (like user approvals) using the `wait_for_event` function:

1.  **Define a DTO (Optional but Recommended)**: Create a Pydantic model for the decision data.

    ```python
    from pydantic import BaseModel
    from typing import Optional

    class ApprovalAction(BaseModel):
        approved: bool
        comment: Optional[str] = None
    ```

2.  **Wait Step**: Wait for the event and fetch data.

    ```python
    from sqlmodel import select
    from planar import get_session
    from planar.workflows import step
    from planar.workflows.events import wait_for_event
    # Assuming ApprovalHistory model exists
    from .models import ApprovalHistory, ApprovalAction

    @step()
    async def get_manager_decision(expense_id: UUID, manager_id: UUID) -> ApprovalAction:
        """
        Waits for manager approval event, then fetches and returns the decision.
        """
        # Wait for the specific event for this expense and manager
        await wait_for_event(f"expense_approval:{manager_id}:{expense_id}")

        # Once the event is received, fetch the decision details from the database
        session = get_session()
        approval = (
            await session.exec(
                select(ApprovalHistory).where(
                    ApprovalHistory.expense_id == expense_id,
                    ApprovalHistory.approver_id == manager_id,
                )
            )
        ).one() # Assuming exactly one approval record will exist

        # Return the decision details using the Pydantic model
        approved = approval.decision == "approved"
        return ApprovalAction(approved=approved, comment=approval.comment)
    ```

3.  **Event Emission (e.g., in API endpoint)**: Save data and emit the event.

    ```python
    from planar.workflows.events import emit_event
    # Assuming ApprovalHistory model and session management exist
    from .models import ApprovalHistory, ApprovalAction

    async def record_approval(expense_id: UUID, approver_id: UUID, action: ApprovalAction):
        session = get_session()
        # Record approval decision in the database
        approval = ApprovalHistory(
            expense_id=expense_id,
            approver_id=approver_id,
            decision="approved" if action.approved else "rejected",
            comment=action.comment,
        )
        session.add(approval)
        await session.commit() # Commit here as it's outside a workflow step

        # Emit the event to potentially wake up a waiting workflow
        await emit_event(f"expense_approval:{approver_id}:{expense_id}")
    ```


### Error Handling

In workflows, you typically handle errors by:

1. Using try/except in the workflow function:

```python
@workflow()
async def error_handling_workflow(item_id: str):
    try:
        result = await risky_step(item_id)
        await success_step(result)
    except Exception as e:
        await error_recovery_step(item_id, str(e))
```

2. Creating specific steps for error recovery:

```python
@step()
async def error_recovery_step(item_id: str, error_message: str):
    session = get_session()
    item = session.exec(select(Item).where(Item.id == item_id)).first()
    item.status = "error"
    item.error_message = error_message
    session.add(item)
```

### Conditional Branching

Workflows can have different paths based on conditions:

```python
@workflow()
async def conditional_workflow(expense_id: UUID):
    # ... initial steps ...
    expense = await get_expense(expense_id) # Assume helper exists
    manager_id = await get_approving_manager(expense.submitter_id) # Assume helper exists

    # Get manager decision (waits internally)
    manager_decision = await get_manager_decision(expense_id, manager_id)

    # Process decision and branch
    manager_approved = await process_manager_decision(expense_id, manager_decision)

    # If manager rejected, end workflow early
    if not manager_approved:
        return "Expense rejected by manager" # Workflow ends

    # Conditional step: Check if finance approval is needed
    if await requires_finance_approval(expense_id): # Assume step exists
        finance_id = await get_finance_approver() # Assume step exists
        await update_current_approver(expense_id, finance_id) # Assume step exists

        # Get finance decision (waits internally)
        finance_decision = await get_finance_decision(expense_id, finance_id) # Assume step exists
        finance_approved = await process_finance_decision(expense_id, finance_decision) # Assume step exists

        # If finance rejected, end workflow early
        if not finance_approved:
            return "Expense rejected by finance" # Workflow ends

    # If we reach here, all approvals passed
    await process_payment(expense_id) # Assume step exists
    return "Expense approved and paid"
```

## Workflow Management

### Cancelling Workflows

Workflows can be cancelled during execution using the cancel API endpoint. When a workflow is cancelled:

- The workflow status transitions to `cancelled`
- The workflow execution is aborted before the next step begins
- A `WorkflowCancelledException` is raised during execution
- The workflow's error field is set with cancellation details

#### Using the API

Cancel a running or pending workflow:

```bash
POST /planar/v1/workflows/{run_id}/cancel
```

**Example Response:**
```json
{
  "message": "Workflow 123e4567-e89b-12d3-a456-426614174000 has been cancelled"
}
```

#### Cancellation Behavior

- **Pending workflows**: Will be marked as cancelled and will not be executed by the orchestrator
- **Running workflows**: Will be cancelled before the next step begins execution
- **Suspended workflows**: Can be cancelled while waiting for events or timeouts
- **Completed workflows**: Cannot be cancelled (returns 400 error)
- **Already cancelled workflows**: Returns 400 error

#### Example

```python
import httpx

# Start a workflow
workflow = await my_workflow.start()

# Cancel it via API
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"http://localhost:8000/planar/v1/workflows/{workflow.id}/cancel"
    )

if response.status_code == 200:
    print(f"Workflow {workflow.id} cancelled successfully")
```

#### Cancellation Detection

The framework checks for cancellation before executing each step. When a workflow is cancelled:

```python
@workflow()
async def multi_step_workflow():
    await step1()  # Completes successfully
    # Workflow cancelled here
    await step2()  # Never executed - WorkflowCancelledException raised
    await step3()  # Never executed
```

The cancellation check occurs between steps, ensuring that:
- Steps that have started will complete
- Subsequent steps will not be executed
- The workflow fails with cancellation details

## Best Practices

1.  **Use `wait_for_event` for External Dependencies**: Prefer event-driven waiting over polling for better efficiency and responsiveness.
2.  **Keep Steps Focused**: Each step should perform a single logical unit of work.
3.  **Use Pydantic Models and Native Types**: Leverage automatic serialization for clear data contracts between steps. Supported types include `bool`, `int`, `float`, `Decimal`, `UUID`, `datetime`, and Pydantic models. Avoid using Generics.
4.  **Add Type Hints**: Ensure functions have proper type hints for reliable serialization/deserialization and static analysis.
5.  **Idempotent Steps**: Design steps so they can be safely retried without unintended side effects, especially if using `max_retries > 0`.
6.  **Separate Waiting from Processing**: Use dedicated steps (like `get_manager_decision` in the example) that combine waiting (`wait_for_event`) and fetching the necessary data, returning it for the next processing step.
7.  **Never Commit Sessions in Steps**: The Planar framework manages transaction boundaries around steps.
8.  **Use `Human` for Human Tasks**: Integrate human-in-the-loop steps cleanly using the `Human` construct.
9.  **Use `Agent` for AI Interaction**: Encapsulate AI model calls within `Agent` steps for structured interaction.
10. **Use `@rule` for Business Logic**: Define configurable business logic using the `@rule` decorator and potentially override with a rules engine.
11. **Meaningful Step Names**: Use clear function names for steps to improve observability and debugging.
12. **Error Handling**: Use standard Python `try...except` blocks within workflow functions to define error handling and recovery paths. Create dedicated steps for compensation or cleanup logic.

## Example Workflow (Expense Approval)

This example combines several concepts: steps, conditional logic, and event-based waiting.

```python
# models.py (Simplified)
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ApprovalAction(BaseModel):
    approved: bool
    comment: Optional[str] = None

# main.py
from uuid import UUID
from planar import get_session
from planar.workflows import step, workflow
from planar.workflows.events import wait_for_event
from sqlmodel import select
# Assume Expense, ApprovalHistory, User models and helper functions like
# get_expense, get_approving_manager, get_finance_approver exist
from .models import Expense, ApprovalHistory, User, ExpenseStatus, ApprovalAction

@workflow()
async def expense_approval_workflow(expense_id: UUID) -> str | None:
    """Orchestrates the expense approval process."""
    await validate_expense(expense_id) # Step 1: Validate

    expense = await get_expense(expense_id)
    manager_id = await get_approving_manager(expense.submitter_id)

    # Step 2: Get manager decision (waits for event internally)
    manager_decision = await get_manager_decision(expense_id, manager_id)

    # Step 3: Process manager decision
    manager_approved = await process_manager_decision(expense_id, manager_decision)

    # End early if rejected
    if not manager_approved:
        return "Rejected by Manager"

    # Step 4: Conditional check for finance approval
    if await requires_finance_approval(expense_id):
        finance_id = await get_finance_approver()
        await update_current_approver(expense_id, finance_id) # Step 5: Update approver

        # Step 6: Get finance decision (waits for event internally)
        finance_decision = await get_finance_decision(expense_id, finance_id)

        # Step 7: Process finance decision
        finance_approved = await process_finance_decision(expense_id, finance_decision)

        # End early if rejected
        if not finance_approved:
            return "Rejected by Finance"

    # Step 8: Process payment if all approvals passed
    await process_payment(expense_id)
    return "Expense Approved and Paid"


@step()
async def validate_expense(expense_id: UUID):
    # ... implementation to validate expense status ...
    pass

@step()
async def get_manager_decision(expense_id: UUID, manager_id: UUID) -> ApprovalAction:
    """Waits for manager approval event, fetches, and returns the decision."""
    await wait_for_event(f"expense_approval:{manager_id}:{expense_id}")
    session = get_session()
    approval = (await session.exec(
        select(ApprovalHistory).where(
            ApprovalHistory.expense_id == expense_id,
            ApprovalHistory.approver_id == manager_id)
    )).one()
    return ApprovalAction(approved=(approval.decision == "approved"), comment=approval.comment)

@step()
async def process_manager_decision(expense_id: UUID, decision: ApprovalAction) -> bool:
    # ... implementation to update expense based on decision ...
    # Return True if approved, False if rejected
    session = get_session()
    expense = await get_expense(expense_id)
    if decision.approved:
        expense.status = ExpenseStatus.MANAGER_APPROVED
        session.add(expense)
        return True
    else:
        expense.status = ExpenseStatus.REJECTED
        expense.rejection_reason = f"Manager: {decision.comment or ''}"
        session.add(expense)
        return False

@step()
async def requires_finance_approval(expense_id: UUID) -> bool:
    # ... implementation to check expense amount > threshold ...
    expense = await get_expense(expense_id)
    return expense.amount > 1000

# ... (Implementations for get_finance_decision, process_finance_decision, process_payment etc.)
```
