# Planar

This documentation covers the main aspects of Planar, a AI-native workflow orchestration framework.

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


# Agents

Agent steps let a workflow call an LLM through a first-class `Agent` object. Each agent bundles its prompts, model choice, validation, and optional tool integrations so you can reuse it across many workflows while keeping the workflow code itself focused on business logic.

## Create an Agent

```python
from pydantic import BaseModel, Field
from planar.ai import Agent


class OrderInput(BaseModel):
    order_id: str
    customer_tier: str


class PricingDecision(BaseModel):
    final_price: float = Field(description="Price after discounts")
    reasoning: str


pricing_agent = Agent(
    name="order_pricing",
    system_prompt="you decide the right price given our pricing policy.",
    user_prompt="Order details:\n\n{input}",
    input_type=OrderInput,
    output_type=PricingDecision,
    model="anthropic:claude-3-5-sonnet",
    model_parameters={"temperature": 0.2},
)
```

- `input_type` and `output_type` are optional but recommended. When omitted, the agent expects and returns strings.
- Prompts are regular Python format strings. `{input}` expands to the serialized `input_type`. You can also refer to individual fields (for example `{input.customer_tier}`).
- Use `model_parameters` for provider-specific tuning such as temperature or top_p.

## Call an Agent inside a Workflow

```python
from planar.workflows import workflow


@workflow()
async def price_order(order: OrderInput) -> PricingDecision:
    result = await pricing_agent(order)
    return result.output
```

Agent calls return `AgentRunResult[TOutput]`, which always contains the `.output`. Future releases may add telemetry fields, so prefer accessing data through the result object.

## Configured Models

Planar can pull agent models directly from configuration so you can swap providers per environment without touching code.

Add an `ai_models` block in `planar.dev.yaml`/`planar.prod.yaml`:

```yaml
ai_models:
  default: invoice_parsing_model
  providers:
    public_openai:
      factory: openai_responses
      options:
        api_key: ${OPENAI_API_KEY}
  models:
    invoice_parsing_model:
      provider: public_openai
      options: gpt-4o-mini
```

For Azure OpenAI endpoints:

```yaml
ai_models:
  providers:
    azure_llm:
      factory: azure_openai_responses
      options:
        endpoint_env: AZURE_OPENAI_ENDPOINT
        deployment_env: AZURE_OPENAI_DEPLOYMENT
        # Optional: omit these to use DefaultAzureCredential instead
        static_api_key: AZURE_OPENAI_KEY
  models:
    invoice_parsing_model:
      provider: azure_llm
      options:
        deployment: gpt-4o-mini
```

- `default` must match one of the `models` keys and is used whenever an agent omits the `model` argument.
- `models` exposes named models that agents can reference through `ConfiguredModelKey`.
- Providers let you declare credentials/transport once. Models merge provider options with their own options (model/deployment/etc.). A string entry like `openai:gpt-4o-mini` still works for quick setups. For full control, register a callable with `PlanarApp.register_model_factory("key", factory)` and point provider `factory` at that key. The callable can accept `options` and/or `config` keyword arguments; Planar passes the merged options plus the active `PlanarConfig` instance. Planar ships built-in factories keyed as `openai_responses` (Responses API) and `azure_openai_responses` (Azure).

```python
from planar import PlanarApp

app = PlanarApp(...)
app.register_model_factory("vertex_gemini", vertex_gemini_model_factory)
```

Leave out the API key settings when you want the factory to authenticate with
`DefaultAzureCredential` (managed identity or user login). Override the Azure AD scope via
`token_scope` or `token_scope_env` if your deployment requires a custom scope.

Factories can be regular sync callables or `async def` coroutines; Planar will await them and
cache the returned model objects automatically.

Use the configured key inside your agent:

```python
from planar.ai import Agent, ConfiguredModelKey

invoice_agent = Agent(
    name="invoice_agent",
    system_prompt="Extract vendor and amount from invoice text.",
    user_prompt="{{input}}",
    input_type=PlanarFile,
    output_type=InvoiceData,
    model=ConfiguredModelKey("invoice_parsing_model"),
)
```

In dev you might point `invoice_parsing_model` at `openai:gpt-4o-mini`, while prod uses an Azure-hosted deployment created by your factory. Agents that leave `model=None` automatically resolve to the configured default (and fall back to `openai:gpt-4o` if no config entry exists).

Here you may find list of Pydanctic AI model names: https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.KnownModelName 

## Tool-Enabled Agents

Add async callables to the `tools` argument to let the model inspect or update external systems during the run. Each tool must accept and return JSON-serializable types (Pydantic models are supported).

```python
from planar.ai import Agent, get_tool_context


async def fetch_customer(customer_id: str) -> dict:
    return await crm_client.get_customer(customer_id)


async def record_discount(order_id: str, amount: float) -> None:
    await billing_client.store_discount(order_id, amount)


ops_agent = Agent(
    name="reprice_with_tools",
    system_prompt="use the tools to justify each discount.",
    user_prompt="Order:\n{input}",
    input_type=OrderInput,
    output_type=PricingDecision,
    tools=[fetch_customer, record_discount],
    model="openai:gpt-4.1",
    max_turns=4,
)
```

### Tool Context

If tools need shared state (for example, database clients or API credentials), define a context schema with `tool_context_type` and pass the matching object when you call the agent. Access it inside tools with `planar.ai.get_tool_context()`.

```python
from dataclasses import dataclass


@dataclass
class OpsContext:
    crm_client: CRMClient
    billing_client: BillingClient


@workflow()
async def reprice(order: OrderInput) -> PricingDecision:
    ctx = OpsContext(crm_client=create_crm(), billing_client=create_billing())
    result = await ops_agent(order, tool_context=ctx)
    return result.output
```

Keep the context limited to durable resources or immutable data. Ephemeral counters and other transient state will not survive partial replays.

## File and Image Inputs

`PlanarFile` instances can be part of the agent input model. The agent runtime streams file content to the provider with no extra code. This also works when the file is nested deeper inside the Pydantic model.

## Runtime Overrides

Planar stores the agent defaults in code, but the CoPlane UI/API can override prompts, models, and model parameters at runtime. Overrides are merged with the defaults just before execution. Use this to let business users iterate on prompts without redeploying code.

## Recommendations

- Keep agent prompts focused and consistent with the workflow purpose.
- Provide structured outputs whenever the workflow needs to branch or make decisions based on the agent response.
- Limit `max_turns` to the minimum needed to control cost and latency.
- Treat tool functions like regular workflow steps: make them idempotent and safe to replay.


# Human Tasks

## Overview

Human tasks let workflows pause and wait for a person to review data, make a decision,
or provide inputs. Use the `Human` step directly for structured, schema-driven tasks,
or use the IO helpers (refer to docs/io.md) for higher-level form-style interactions.

## Create a Human Step

```python
from datetime import timedelta
from pydantic import BaseModel
from planar.human import Human, Timeout, workflow

class ExpenseRequest(BaseModel):
    request_id: str
    amount: float

class ExpenseDecision(BaseModel):
    approved: bool
    notes: str = ""

expense_approval = Human(
    name="expense_approval",
    title="Expense Approval",
    description="Review the expense request",
    input_type=ExpenseRequest,
    output_type=ExpenseDecision,
    timeout=Timeout(timedelta(hours=24)),
)

@workflow()
async def approve_expense(request: ExpenseRequest) -> ExpenseDecision:
    result = await expense_approval(request, message="Please review")
    return result.output
```

## Task Lifecycle

- The workflow suspends after creating the task.
- A human completes the task via the API or UI.
- The workflow resumes with the validated output.

## Task APIs

Common endpoints:

- `GET /planar/v1/human-tasks` (filter by status, workflow_id, name)
- `GET /planar/v1/human-tasks/{task_id}`
- `POST /planar/v1/human-tasks/{task_id}/complete`
- `POST /planar/v1/human-tasks/{task_id}/cancel`
- `POST /planar/v1/human-tasks/{task_id}/reassign`

Assignment and scoping helpers:

- `GET /planar/v1/human-tasks/assigned/user/{user_id}`
- `GET /planar/v1/human-tasks/unassigned`
- `GET /planar/v1/human-tasks/scoped/user/{user_id}`
- `GET /planar/v1/human-tasks/scoped/group/{group_id}`

## Best Practices

- Keep input/output models small and explicit.
- Use timeouts for tasks that must not block indefinitely.


# Evals

## Overview

Evals let you validate agent changes against a repeatable set of test cases before or after
promotion. The core flow is:

1. Build an eval set with canonical inputs (and optional expected outputs).
2. Create an eval suite that targets an agent and defines which scorers to run.
3. Trigger eval runs to execute the suite against a specific agent configuration.

Eval runs are durable workflows that capture per-case results and scorer outputs.

## Core Concepts

- **Eval set**: A named collection of test cases.
- **Eval suite**: A binding between an agent, an eval set, and scorer configs.
- **Scorer**: A callable that compares expected output to agent output.
- **Eval run**: An execution of a suite that produces case results.

## Scorers

Planar ships with built-in scorers:

- `exact_match`: Full output equality; supports `field_path` to compare a nested field.
- `case_insensitive_match`: Case-insensitive string equality with optional trimming.
- `numeric_tolerance`: Numeric comparison with `abs_tol`.
- `llm_judge`: Uses a judge model plus a rubric to score outputs.

You can register custom scorers with `PlanarApp.register_scorer`.

## Typical Workflow

## Programmatic Usage

You can drive evals directly in Python, which is useful for scripts, notebooks, or
bootstrapping evals alongside agent configuration.

```python
import json
from uuid import uuid4

from planar.ai import Agent
from planar.ai.agent_utils import agent_configuration
from planar.app import PlanarApp
from planar.evals.models import EvalSetInputFormat, EvalSetOutputFormat
from planar.evals.schemas import (
    AddEvalCasePayload,
    EvalRunCreate,
    EvalScorerConfig,
    EvalSetCreate,
    EvalSuiteCreate,
)
from planar.evals.service import (
    add_eval_case,
    create_eval_set,
    create_run,
    create_suite,
    list_case_results,
)
from planar.evals.workflows import execute_eval_run


backoffice_agent = Agent(
    name="ops_triage_agent",
    system_prompt="Resolve tickets and flag risk.",
    user_prompt="Ticket payload: {{ input }}",
    output_type=dict,
    model="openai:gpt-4.1-mini",
)


async def run_eval() -> None:
    eval_set = await create_eval_set(
        EvalSetCreate(
            name=f"ops_eval_{uuid4().hex[:8]}",
            description="Ops triage eval set",
            input_format=EvalSetInputFormat.JSON,
            output_format=EvalSetOutputFormat.JSON,
        )
    )

    await add_eval_case(
        eval_set.id,
        AddEvalCasePayload(
            input_payload=json.dumps({"ticket_id": "TCK-1"}),
            expected_output=json.dumps({"ticket_id": "TCK-1", "ok": True}),
        ),
    )

    config_record = await agent_configuration.write_config(
        backoffice_agent.name, backoffice_agent.to_config()
    )

    suite = await create_suite(
        EvalSuiteCreate(
            name=f"ops_suite_{uuid4().hex[:8]}",
            agent_name=backoffice_agent.name,
            eval_set_id=eval_set.id,
            concurrency=2,
            scorers=[
                EvalScorerConfig(
                    name="exact_ticket",
                    scorer_name="exact_match",
                    settings={"field_path": "ticket_id"},
                )
            ],
        )
    )

    run = await create_run(
        EvalRunCreate(
            agent_name=backoffice_agent.name,
            suite_id=suite.id,
            agent_config_id=config_record.id,
        )
    )

    await execute_eval_run(run.id)
    results = await list_case_results(run.id)
    print(f"cases={len(results)}")


app = PlanarApp(title="Eval Script")
app.register_agent(backoffice_agent)

# Run with: uv run examples/eval_example.py
# asyncio.run(app.run_standalone(run_eval))
```

### 1) Create an eval set and cases

Create the eval set and add cases via the eval set API:

- `POST /planar/v1/evals/sets`
- `POST /planar/v1/evals/sets/{eval_set_id}/cases`

Example payloads:

```json
{
  "name": "invoice_extraction",
  "description": "baseline invoice parsing",
  "input_format": "json",
  "output_format": "json",
  "cases": [
    {
      "input_payload": {"text": "Invoice #123 for $42"},
      "expected_output": {"invoice_number": "123", "amount_total": 42}
    }
  ]
}
```

```json
{
  "input_payload": {"text": "Invoice #456 for $25"},
  "expected_output": {"invoice_number": "456", "amount_total": 25}
}
```

### 2) Create an eval suite for an agent

Suites are scoped to agents:

- `POST /planar/v1/agents/{agent_name}/evals`

```json
{
  "name": "invoice_parsing_suite",
  "agent_name": "invoice_agent",
  "eval_set_id": "<eval-set-uuid>",
  "concurrency": 4,
  "scorers": [
    {
      "name": "exact_output",
      "scorer_name": "exact_match",
      "settings": {"field_path": "invoice_number"}
    },
    {
      "name": "amount_with_tolerance",
      "scorer_name": "numeric_tolerance",
      "settings": {"abs_tol": 0.5}
    }
  ]
}
```

### 3) Trigger a run

- `POST /planar/v1/agents/{agent_name}/evals/{suite_id}/runs`

The response includes the run id. Fetch results:

- `GET /planar/v1/agents/{agent_name}/evals/{suite_id}/runs`
- `GET /planar/v1/agents/{agent_name}/evals/{suite_id}/runs/{run_id}/cases`

## Tips

- Keep eval inputs aligned with the agent's input schema.
- Use structured outputs (Pydantic models) for stable scoring.
- Prefer smaller, targeted eval sets per agent to keep feedback fast.
- Set suite `concurrency` based on model rate limits and latency; higher values run more cases in parallel.
- `agent_name` in suite payloads must match the URL path.


# IO

## Overview

Planar IO provides higher-level building blocks for human input and workflow messaging.
It wraps the `Human` step and message APIs with a small set of typed helpers so you can
collect inputs and display updates without hand-rolling JSON Schemas.

All IO calls must run inside workflow steps.

## Inputs

Use `IO.input.*` for single fields. Each call yields a typed value.

```python
from planar.io import IO
from planar.workflows import step

@step()
async def capture_name() -> str:
    name = await IO.input.text(
        "Your name",
        key="name",
        placeholder="Ada Lovelace",
    )
    return name
```

Available primitives:

- `IO.input.text(...)` -> `str`
- `IO.input.boolean(...)` -> `bool`
- `IO.select.single(...)` -> `str`
- `IO.select.multiple(...)` -> `list[str]`
- `IO.entity.select(...)` -> `str | list[str]`
- `IO.upload.file(...)` -> `PlanarFile`

## Forms

Use `IO.form(...)` to bundle multiple inputs into a single human task.

```python
from planar.io import IO
from planar.workflows import step

@step()
async def vendor_review() -> dict[str, str]:
    async with IO.form(
        "vendor_review",
        title="Vendor Review",
        description="Confirm onboarding details.",
        submit_label="Send review",
    ) as form:
        form.input.text("Notes", key="notes", multiline=True)
        form.input.boolean("Approved", key="approved", default=False)
        form.select.single("Risk", options=["low", "medium", "high"], key="risk")

    return form.data
```

`form.data` exposes the validated data as a plain dict, and typed accessors are available
on the `form` instance if you need them.

## Display Messages

Send read-only messages using `IO.display.*` helpers.

```python
from planar.io import IO
from planar.workflows import step

@step()
async def notify_ops() -> None:
    await IO.display.markdown("## Review captured\nThanks for the update.")
```

Other display helpers include:

- `IO.display.table(...)` - Display tabular data
- `IO.display.object(...)` - Display structured objects

## Entity Selectors

`IO.entity.select(...)` lets users pick Planar entities by display fields. Entity
metadata is sourced from `EntityField` and `PlanarBaseEntity` registration.

```python
from planar.io import IO
from planar.workflows import step

@step()
async def choose_customer() -> str:
    customer_id = await IO.entity.select(
        "Customer",
        entity="customer",
        key="customer_id",
    )
    return customer_id
```

## File Uploads

`IO.upload.file(...)` creates a file upload task and returns a `PlanarFile` reference.
Use `PlanarFile` for content access and metadata.

```python
from planar.io import IO
from planar.workflows import step

@step()
async def upload_invoice() -> str:
    invoice = await IO.upload.file("Invoice PDF", key="invoice_file")
    content = await invoice.get_content()
    return f"received {len(content)} bytes"
```

## Best Practices

- Keep inputs small and focused; split large tasks into multiple steps.
- Use `IO.form` when inputs should be submitted together.
- Treat IO steps as durable: avoid relying on in-memory mutable state across replays.


# Files

## Overview

PlanarFile is the lightweight, serializable reference used by workflows, agents, and
IO tasks to represent uploaded files. The file metadata is stored in the database while
content is stored in the configured backend (local directory, S3-compatible, or Azure
Blob Storage).

## PlanarFile Basics

```python
from planar.files import PlanarFile

async def ingest_file(file: PlanarFile) -> int:
    metadata = await file.get_metadata()
    content = await file.get_content()
    return metadata.size
```

`PlanarFile` stores only metadata in workflow steps. Fetch content via
`PlanarFile.get_content()` when needed.

## Uploading Files

### API

- `POST /planar/v1/file/upload`

Upload one or more files as `multipart/form-data`. The response is a list of
`PlanarFile` metadata objects.

### Programmatic Uploads

```python
from pathlib import Path
from planar.files import PlanarFile

async def upload_report(path: Path) -> PlanarFile:
    return await PlanarFile.upload(content=path, filename=path.name)
```

## Fetching Content and Metadata

- `GET /planar/v1/file/{file_id}/content`
- `GET /planar/v1/file/{file_id}/metadata`

If the storage backend supports external URLs, the content endpoint responds with a
redirect. Otherwise it streams the content directly.

## Storage Configuration

Configure storage in your Planar config:

```yaml
storage:
  backend: localdir
  directory: .data/files
```

Supported backends:

- `localdir`
- `s3`
- `azure_blob`

## Best Practices

- Treat `PlanarFile` as an immutable reference; store the file id in entities when
  you need durable links.
- Avoid loading large files into memory; stream content when possible.
- Use `IO.upload.file(...)` for human-driven uploads inside workflows.


# Planar Entities Guide

## Overview

Planar entities are the core data models for your application. They define the structure of your data and how it's stored in the database. This guide explains the best practices and patterns for working with entities in Planar.

## Core Concepts

### Entity

An entity is a data model that is mapped to a database table. Entities in Planar are built on SQLModel, which combines SQLAlchemy and Pydantic to provide both database ORM capabilities and data validation.

### Key Attributes

- **Tables**: Entities are mapped to database tables when they have `table=True`
- **Validation**: Entities benefit from Pydantic validation
- **Type Safety**: Fields use Python type hints for both runtime validation and static analysis

### Schemas / Namespaces

- **System tables** live in the `planar` schema.
- **User tables** (entities inheriting from `PlanarBaseEntity`) use a configurable default schema.
- Default user schema is `planar_entity` on PostgreSQL; SQLite ignores schemas.
- Models can still override per-table schema with `__table_args__ = {"schema": "my_schema"}`.


## Defining Entities

### Basic Entity Structure

```python
>>> db_manager = DatabaseManager(db_url)
>>> db_manager.connect()
>>> engine = db_manager.get_engine()
>>> session = new_session(engine)

```

```python
>>> from datetime import datetime
>>> from planar.modeling.mixins.timestamp import TimestampMixin
>>> from planar.modeling.orm import PlanarBaseEntity
>>> from sqlmodel import Field, select

>>> class AppUser(PlanarBaseEntity, TimestampMixin, table=True):
...     username: str = Field(unique=True, index=True)
...     email: str = Field(unique=True)
...     full_name: str = Field()
...     is_active: bool = Field(default=True)
...     last_login: datetime | None = Field(default=None)

```

#### Important notes:

- Inherit from `PlanarBaseEntity` to get the base functionality
- Use `table=True` to indicate this model should be mapped to a database table
- Include descriptive docstrings for your entities
- Use `Field()` to define additional properties for each field

### Common Field Types

Planar entities support various field types:

```python
>>> from typing import List, Dict
>>> from datetime import datetime
>>> from uuid import UUID
>>> from enum import Enum
>>> from sqlmodel import Field, JSON, Column

>>> class TaskStatus(str, Enum):
...     TODO = "todo"
...     IN_PROGRESS = "in_progress"
...     DONE = "done"

>>> class Task(PlanarBaseEntity, TimestampMixin, table=True):
...     title: str = Field()
...     description: str | None = Field(default=None)
...     status: TaskStatus = Field(default=TaskStatus.TODO)
...     due_date: datetime | None = Field(default=None)
...     priority: int = Field(default=0)
...     assignee_id: UUID | None = Field(default=None, foreign_key="appuser.id")
...     tags: List[str] | None = Field(default=None, sa_column=Column(JSON))

```

## Best Practices

### Use Appropriate Mixins

Planar provides several useful mixins to add common functionality to your entities:

```python
>>> from planar.modeling.mixins.timestamp import TimestampMixin

>>> class Document(PlanarBaseEntity, TimestampMixin, table=True):
...     """Document entity."""
...     title: str = Field()
...     content: str = Field()

```

### Field Definitions

When defining fields:

- Use `unique=True` for fields that must be unique
- Use `index=True` for fields you'll frequently query on
- Provide clear defaults for optional fields
- Use `Optional[Type]` for nullable fields
- Provide descriptive docstrings for complex fields

### Relationships

Define relationships between entities using foreign keys:

```python
>>> class Comment(PlanarBaseEntity, TimestampMixin, table=True):
...     """Comment entity related to a document."""
...     text: str = Field()
...     document_id: UUID = Field(foreign_key="document.id")
...     author_id: UUID = Field(foreign_key="appuser.id")

```

### Enum Values

Use string-based enums for better database compatibility:

```python
>>> class ReportType(str, Enum):
...     DAILY = "daily"
...     WEEKLY = "weekly"
...     MONTHLY = "monthly"

>>> class Report(PlanarBaseEntity, table=True):
...     type: ReportType = Field()
...     name: str = Field()

```

### JSON/JSONB Fields

For complex data structures, use the SQLAlchemy JSON column type:

```python
>>> from sqlmodel import Column, JSON
>>> from typing import Any

>>> class Product(PlanarBaseEntity, table=True):
...     name: str = Field()
...     attributes: dict[str, Any] = Field(sa_column=Column(JSON))

```

## Entity Registration

Entities must be registered with the Planar app for API generation and UI usage:

```python
from planar import PlanarApp

app = PlanarApp()
app.register_entity(AppUser)
app.register_entity(Task)
app.register_entity(Document)
app.register_entity(Comment)
```

## Configuring Entity Schema

- Global default via config:

```yaml
app:
  db_connection: app
  entity_schema: planar_entity  # set to 'public' to keep legacy behavior
```

- Per-model override:

```python
class AppUser(PlanarBaseEntity, table=True):
    __table_args__ = {"schema": "customer"}
    # fields...
```

Notes:
- Planar ensures the `planar` schema exists for system tables and creates the configured `entity_schema` on PostgreSQL at startup. On SQLite, schemas are ignored.

## Common Pitfalls

### Avoid Complex Base Models

- **Don't** use entities for complex inheritance hierarchies
- **Do** prefer composition over inheritance

### Planar Convention Issues

Avoid these common issues:

- **Don't** name fields that overlap with standard fields from included mixins:
  - `id` from `UUIDPrimaryKeyMixin` or `PlanarBaseEntity`
  - `created_at` and `updated_at` from `TimestampMixin`
  - `created_by` and `updated_by` from `AuditableMixin` or `PlanarBaseEntity`
- **Don't** use workflow status fields (use durable workflows instead)
- **Don't** add processing status flags (use workflow states)
- **Don't** use SQLAlchemy models directly - use SQLModel

### Choosing Between PlanarBaseEntity and Individual Mixins

- **Use `PlanarBaseEntity`** for application entities that need all standard fields (id, audit trail)
- **Use individual mixins** when you need more control over which fields are included and are managing the database schema yourself

## Working with Entities

SQLModel automatically registers all classes which inherit from `SQLModel` (like `PlanarBaseEntity`).

PlanarBaseEntity automatically registers itself to the `PLANAR_APPLICATION_METADATA` metadata object. We can ensure all tables are created like this:

```python
>>> from sqlmodel import SQLModel
>>> from planar.modeling.orm import PLANAR_APPLICATION_METADATA
>>> async with engine.begin() as conn:
...     await conn.run_sync(PLANAR_APPLICATION_METADATA.create_all)
>>> print("Database tables created - if they didn't exist.")
Database tables created - if they didn't exist.

```

**You won't need to do this, as Planar will handle this for you.**

### Creating Entities

This example demonstrates creating a new `AppUser` instance and persisting it to the database.

```python
>>> user = AppUser(
...     username="liveuser",
...     email="live@example.com",
...     full_name="Live User",
... )
>>> async with session.begin(): # Manages transaction: commit on success, rollback on error
...     session.add(user)
...     # The user object will be populated with its ID after this block.
>>> print(f"User '{user.username}' created with ID type: {type(user.id)}")
User 'liveuser' created with ID type: <class 'uuid.UUID'>

```

### Querying Entities

This example shows how to query for active users. We'll look for the user created in the previous step.

```python
>>> found_usernames = []
>>> async with session.begin():
...     stmt = select(AppUser).where(AppUser.is_active == True).where(AppUser.username == "liveuser")
...     result = await session.exec(stmt)
...     active_users = result.all()
...     found_usernames = [user.username for user in active_users]
>>> if found_usernames:
...     print(f"Found active user(s): {found_usernames}")
... else:
...     print("No active user named 'liveuser' found.")
Found active user(s): ['liveuser']

```

For more information on updating and deleting entities, see the [SQLAlchemy Usage](sqlalchemy_usage.md) guide.

## Mixins

Planar provides several mixins to add common functionality to your entities:

- `TimestampMixin` - Adds `created_at` and `updated_at` fields
- `UUIDPrimaryKeyMixin` - Adds a UUID primary key field (`id`)
- `AuditableMixin` - Adds audit trail fields (`created_by`, `updated_by`)

In the example above, we use the `TimestampMixin` to add the `created_at` and `updated_at` fields to the `AppUser` entity.
Those fields are automatically populated when the entity is created or updated.

```python
>>> async with session.begin():
...     user.is_active = False
...     session.add(user)
>>> async with session:
...     await session.refresh(user)
...     print(f"User updated at after creation: {user.updated_at > user.created_at}")
User updated at after creation: True

```


# Planar SQLAlchemy/SQLModel Usage Guide

This guide provides essential information for working with databases in the Planar
framework using SQLModel and SQLAlchemy, focusing on transaction management.

This documentation is written in doctest format and verified by Planar CI, so
it is guaranteed to be correct, at least within the context of the Planar
framework.

## Core Concepts

*   **SQLModel:** Built on Pydantic and SQLAlchemy, SQLModel allows defining
    database models that are also Pydantic models, simplifying data validation
    and serialization.
*   **SQLAlchemy Core/ORM:** We use SQLAlchemy's asynchronous features
    (`AsyncSession`, `AsyncEngine`) for database interactions.
*   **Unit of Work:** The `Session` object manages a "Unit of Work". Changes to
    objects tracked by the session (e.g., adding, modifying, deleting) are
    collected and flushed to the database within a transaction.

## SQLModel & SQLAlchemy Core API Cheat Sheet

Most operations will be performed within the context of a `PlanarSession`,
which is a SQLAlchemy's `AsyncSession` subclass.

Normally within the Planar framework, you will obtain a session using
`get_session()`.

On FastAPI request handlers, `get_session()` will return a session with a
lifetime bound to the `asyncio.Task` responsible for handling the HTTP request.

On workflows/steps, `get_session()` will return a session with a lifetime
bound to the `asyncio.Task` responsible for the workflow's execution.


For the examples shown here, we'll need to create our own engine/session using
the database URL injected in the environment as `db_url`:


```python
>>> db_manager = DatabaseManager(db_url)
>>> db_manager.connect()
>>> engine = db_manager.get_engine()
>>> session = new_session(engine)

```

We'll also need some SQLModel classes we'll use in the examples:

```python
>>> from sqlmodel import Field, SQLModel

>>> class Customer(SQLModel, table=True):
...     id: int | None = Field(default=None, primary_key=True)
...     name: str = Field(index=True)
...     email: str | None = Field(default=None)

>>> class Profile(SQLModel, table=True):
...     id: int | None = Field(default=None, primary_key=True)
...     customer_id: int = Field(foreign_key="customer.id")
...     bio: str | None = None

```

SQLModel automatically registers all classes which inherit from `SQLModel`.

We can ensure all tables are created like this:

```python
>>> async with engine.begin() as conn:
...     await conn.run_sync(SQLModel.metadata.create_all)

```

Now, let's look at the operations:

**1. Adding a New Object (`session.add`)**

Adds a new model instance to the session. It will be inserted into the database
upon the next flush/commit:

```python

>>> async with session.begin(): # Use a transaction block, which will commit at the end
...     new_customer = Customer(name="Alice", email="alice@example.com")
...     session.add(new_customer)
...     # new_customer is now 'pending', will be inserted on commit
...     # Let's verify it's pending (has no ID yet)
...     print(f"Customer ID before commit: {new_customer.id}")
Customer ID before commit: None

```

Verify insertion after commit:

```python
>>> async with session:
...    added_customer = (await session.exec(select(Customer).where(Customer.name == "Alice"))).one()
...    print(f"Added Customer: {added_customer.name}, Email: {added_customer.email}, ID: {added_customer.id}")
Added Customer: Alice, Email: alice@example.com, ID: 1

```

**2. Fetching and Updating an Object**

Retrieve an object, modify its attributes, and commit the changes:

```python

>>> async with session.begin():
...     # Fetch using session.get (for primary key lookup)
...     customer_to_update = await session.get(Customer, 1) # Alice's ID is 1
...     print(f"Fetched Customer: {customer_to_update.name}, Email: {customer_to_update.email}")
...     if customer_to_update:
...         customer_to_update.email = "alice_updated@example.com"
Fetched Customer: Alice, Email: alice@example.com

```

Verify the update in a separate session:

```python
>>> async with new_session(engine) as session2:
...    updated_customer = await session2.get(Customer, 1)
...    print(f"Updated Customer: {updated_customer.name}, Email: {updated_customer.email}")
Updated Customer: Alice, Email: alice_updated@example.com

```

**3. Refreshing Object State (`session.refresh`)**

Update an object's attributes with the latest data from the database. Useful
if the data might have changed externally or after a flush.

```python
>>> async with session.begin():
...     customer = await session.get(Customer, 1)
...     print(f"Customer email before refresh: {customer.email}")
Customer email before refresh: alice_updated@example.com

```

Create a separate session/connection to update the database

```python
>>> async with new_session(engine) as session2:
...    stmt = update(Customer).where(Customer.id == 1).values(email="external_change@example.com")
...    await session2.execute(stmt)
...    await session2.commit()

```

Finally, refresh the first session customer from DB

```python
>>> async with session:
...     await session.refresh(customer)
...     print(f"Customer email after refresh: {customer.email}")
Customer email after refresh: external_change@example.com

```

**4. Flushing Changes (`session.flush`)**

Send pending changes (INSERTs, UPDATEs, DELETEs) to the database *without*
committing the transaction. This is useful to get database-generated values
(like auto-increment IDs) or to enforce constraints before the final commit.

```python
>>> async with session.begin():
...     new_customer = Customer(name="Bob", email="bob@example.com")
...     session.add(new_customer)
...     print(f"Customer ID before flush: {new_customer.id}") # Shows "None"
...     await session.flush() # Sends INSERT to DB, populates ID
...     print(f"Customer ID after flush: {new_customer.id}") # Shows the generated ID
...     # The customer is in the DB now for this transaction, but not committed yet.
...     # Let's verify we can fetch Bob within the same transaction post-flush
...     bob_in_tx = await session.get(Customer, new_customer.id)
...     print(f"Bob fetched post-flush: {bob_in_tx.name if bob_in_tx else 'Not found'}")
Customer ID before flush: None
Customer ID after flush: 2
Bob fetched post-flush: Bob

```

Verify Bob exists after commit:

```python
>>> async with session:
...    bob = await session.get(Customer, 2)
...    print(f"Bob exists after commit: {bob is not None}")
Bob exists after commit: True

```

**5. Merging Detached Objects (`session.merge`)**

If you have an object instance that didn't originate from the current session
(e.g., deserialized from a request), `session.merge()` reconciles its state
with the session. It fetches the object with the same primary key from the DB
(if it exists) and copies the state of the *given* object onto the
*persistent* object.

*Caution:* `merge` can be complex. Often, it's clearer to fetch the
existing object and update its attributes directly.


First, create a detached Customer with the same id as Bob's

```python
>>> detached_customer = Customer(id=2, name="Charlie Updated", email="charlie@new.com")

```

Now in a new transaction, merge the detached object with the session:

```python
>>> async with session.begin():
...     # Customer with id=2 (Bob) exists, its name and email will be updated.
...     merged_customer = await session.merge(detached_customer)
...     # merged_customer is the persistent instance tracked by the session
...     print(f"Merged Customer (in session): ID={merged_customer.id}, Name={merged_customer.name}, Email={merged_customer.email}")
Merged Customer (in session): ID=2, Name=Charlie Updated, Email=charlie@new.com

```

Side note: Pydantic models can be compared for equality with `==`:

```python
>>> merged_customer == detached_customer
True

```

But the merged_customer object returned by `await session.merge` has a different identity than the detached_customer:


```python
>>> merged_customer is detached_customer
False

```

Verify the changes persisted after commit:

```python
>>> async with session:
...    charlie = await session.get(Customer, 2)
...    print(f"Customer 2 after merge commit: Name={charlie.name}, Email={charlie.email}")
Customer 2 after merge commit: Name=Charlie Updated, Email=charlie@new.com

```

**6. Using SQLAlchemy Core (`session.exec`)**

Execute statements built with the SQLAlchemy Core Expression Language
(e.g., `select`, `insert`, `update`, `delete`). This is powerful for
complex queries, bulk operations, or when you don't need the ORM object
tracking overhead.

```python
>>> # Setup: Add David for Core API tests
>>> async with session.begin():
...    session.add(Customer(name="David", email="david@example.com"))

```

Select specific columns

```python
>>> async with session: # Often used for reads
...     # Find Alice (ID 1)
...     statement = select(Customer.name, Customer.email).where(Customer.id == 1)
...     result = await session.exec(statement)
...     name, email = result.first() # Returns a tuple (name, email) or None
...     print(f"Core Select (Specific Cols): Name={name}, Email={email}")
Core Select (Specific Cols): Name=Alice, Email=external_change@example.com

```

Select entire objects (more common with SQLModel):

```python
>>> async with session:
...     # Find customers starting with A or C
...     statement = select(Customer).where(col(Customer.name).like("A%")).order_by(Customer.name)
...     result = await session.exec(statement)
...     customers_starting_with_a = result.all() # Returns a list of Customer objects
...     print(f"Core Select (Objects): {[customer.name for customer in customers_starting_with_a]}")
Core Select (Objects): ['Alice']

```

Insert using core (less common than session.add with SQLModel):

```python
>>> async with session.begin():
...     statement = insert(Customer).values(name="Eve", email="eve@core.com")
...     await session.exec(statement)

```

Verify the new customer exists using a separate session/connection:

```python
>>> async with new_session(engine) as session2:
...    eve = (await session2.exec(select(Customer).where(Customer.name == "Eve"))).first()
...    print(f"Core Insert: Eve exists? {eve is not None}, Email: {eve.email if eve else 'N/A'}")
Core Insert: Eve exists? True, Email: eve@core.com

```

Update using core, which can be useful for batch updates without loading the data:

```python
>>> async with session.begin():
...     statement = (
...         update(Customer)
...         .where(Customer.email == "david@example.com")
...         .values(email="david.updated@core.com")
...     )
...     update_result = await session.exec(statement)
...     # Note: rowcount might not be reliable on all backends/drivers, but
...     # should work in SQLite/PostgreSQL which are supported by Planar.
...     print(f"Core Update: Rows matched? {update_result.rowcount > 0}")
Core Update: Rows matched? True

```

Verify the update using a new session/connection:

```python
>>> async with new_session(engine) as session2:
...    david = (await session2.exec(select(Customer).where(Customer.name == "David"))).one()
...    print(f"Core Update Verify: David's email={david.email}")
Core Update Verify: David's email=david.updated@core.com

```

Delete using core, which can be useful for batch deletes without loading the data:

```python
>>> async with session.begin():
...     statement = delete(Customer).where(Customer.name == "David")
...     delete_result = await session.exec(statement)
...     print(f"Core Delete: Rows matched? {delete_result.rowcount > 0}")
Core Delete: Rows matched? True

```

Verify the deletion using a new session/connection:

```python
>>> async with new_session(engine) as session2:
...    david = (await session2.exec(select(Customer).where(Customer.name == "David"))).first()
...    print(f"Core Delete Verify: David exists? {david is not None}")
Core Delete Verify: David exists? False

```

## Planar's Transaction Model: "Commit As You Go"

Planar configures SQLAlchemy for a "commit as you go" pattern:

1.  **Implicit BEGIN:** A transaction is automatically started (`BEGIN`) the
    *first* time a query is sent to the database within a session if no
    explicit transaction is active.
2.  **SQLite `BEGIN IMMEDIATE`:** For SQLite, we force `BEGIN IMMEDIATE` to
    acquire a write lock immediately, preventing "database is locked" errors
    when read operations might escalate to writes later in the same implicit
    transaction.
3.  **Mandatory Transaction Closure:** Because a transaction is often implicitly
    opened, **you MUST explicitly close every transaction** using one of the
    patterns below. Failure to do so can lead to connections being held open,
    transaction deadlocks, or data inconsistencies.

## Required Transaction Management Patterns

Always use one of these patterns to manage your database interactions and
ensure transactions are properly handled.

**1. Explicit Transaction Block (`async with session.begin()`):**

*   **Best Practice:** This is the **preferred** method for units of work
    involving multiple operations (reads and writes) that should succeed or
    fail together.
*   **Behavior:** Automatically commits the transaction if the block completes
    successfully, otherwise rolls back on exception.

```python
>>> async with session.begin():
...     # Create customer
...     customer = Customer(name="Frank", email="frank@tx.com")
...     session.add(customer)
...     await session.flush() # Flush to get customer.id if needed for profile
...     print(f"Customer created in tx: {customer.name}, ID: {customer.id}")
...
...     # Create profile linked to customer
...     profile = Profile(bio="Frank's bio", customer_id=customer.id)
...     session.add(profile)
...     print(f"Profile created for customer {customer.id}")
Customer created in tx: Frank, ID: 5
Profile created for customer 5

```

Verify both customer and profile exist after commit:

```python
>>> async with session:
...    frank = (await session.exec(select(Customer).where(Customer.name == "Frank"))).one()
...    profile = (await session.exec(select(Profile).where(Profile.customer_id == frank.id))).one()
...    print(f"Verification: Frank exists? {frank is not None}, Profile exists? {profile is not None}, Profile bio: {profile.bio}")
Verification: Frank exists? True, Profile exists? True, Profile bio: Frank's bio

```

Test rollback on exception within session.begin()

```python
>>> try:
...     async with session.begin():
...         customer = Customer(name="Grace", email="grace@fail.com")
...         session.add(customer)
...         await session.flush()
...         print(f"Customer created in (failing) tx: {customer.name}, ID: {customer.id}")
...         raise ValueError("Simulated error during profile creation")
... except ValueError as e:
...     print(f"Caught expected error: {e}")
Customer created in (failing) tx: Grace, ID: 6
Caught expected error: Simulated error during profile creation

```

Verify Grace does not exist due to rollback

```python
>>> async with session:
...    grace = (await session.exec(select(Customer).where(Customer.name == "Grace"))).first()
...    print(f"Verification: Grace exists after failed tx? {grace is not None}")
Verification: Grace exists after failed tx? False

```

**2. Read-Only Transaction Block (`async with session.begin_read()`):**

*   **Use Case:** Specifically designed for read-only operations. It ensures
    that if a transaction was not already active, the session will attempt to
    commit after the block (if successful) or rollback (on exception). If a
    transaction was already active, `begin_read` does not interfere with its
    management. This is useful for ensuring that read operations are consistent
    and don't leave transactions open unnecessarily.
*   **Behavior:**
    *   If no transaction is active when `begin_read` is entered:
        *   It allows read operations.
        *   If the block completes successfully, it commits.
        *   If an exception occurs, it rolls back.
    *   If a transaction is already active:
        *   It participates in the existing transaction.
        *   Commit/rollback is handled by the outer transaction management.

```python
>>> async with session.begin_read():
...     alice = await session.get(Customer, 1)
...     print(f"Read-only result with begin_read: Alice's email = {alice.email if alice else 'Not Found'}")
...     # No explicit commit/rollback needed here; begin_read handles it.
Read-only result with begin_read: Alice's email = external_change@example.com

```

Let's test `begin_read` when an outer transaction is already active.

```python
>>> async with session.begin(): # Outer transaction
...     # Modify Alice's email within the outer transaction
...     alice_in_outer_tx = await session.get(Customer, 1)
...     alice_in_outer_tx.email = "alice.outer.tx.change@example.com"
...     session.add(alice_in_outer_tx)
...
...     async with session.begin_read(): # Inner begin_read
...         alice_in_inner_read = await session.get(Customer, 1)
...         # This will see the change from the outer transaction because it's part of it
...         print(f"Alice's email in begin_read (within outer tx): {alice_in_inner_read.email}")
...     # begin_read does not commit or rollback here, outer transaction controls it.
...     print(f"Outer transaction still active, Alice's email: {alice_in_outer_tx.email}")
...     await session.rollback()
...
Alice's email in begin_read (within outer tx): alice.outer.tx.change@example.com
Outer transaction still active, Alice's email: alice.outer.tx.change@example.com

```

**3. Manual Commit/Rollback (`async with session:`):**

*   **Use Case:** Suitable for single operations or when fine-grained control
    over commit/rollback points is needed *within* a single logical block
    (use with caution). Often used for read-only operations where an explicit
    transaction block isn't strictly necessary but cleanup is. This is the
    pattern we use the most in the planar framework, especially when calling
    customer code since it might not even send any queries (so any follow up
    commit/rollbacks will be no-op).
*   **Behavior:** The `async with session:` block ensures the session is closed
    (which typically issues a ROLLBACK if a transaction was implicitly started
    and not committed), but **you must call `session.commit()` explicitly** if
    you perform writes. It is still possible to reuse closed sessions (as you
    might have seen in the examples so far), but it detaches all of its managed
    objects.

Read-only example (no explicit commit/rollback needed):

```python
>>> async with session:
...     print(f"Getting customer 1")
...     alice = await session.get(Customer, 1)
...     print(f"Alice in session: {alice in session}")
...     print(f"Read-only result: Alice's email = {alice.email if alice else 'Not Found'}")
...     # For reads, no explicit commit/rollback is needed.
...     # If a transaction was implicitly started (e.g., SQLite BEGIN IMMEDIATE),
...     # the session context manager's exit will handle rollback if needed.
Getting customer 1
Alice in session: True
Read-only result: Alice's email = external_change@example.com

```

After the end of the `async with session` block, the session is closed and the Customer instance is detached (but still has the data).

```python
>>> alice in session
False
>>> alice.email, alice.id
('external_change@example.com', 1)

```

Example of manual commit:

```python
>>> customer_id = 1
>>> new_email = "alice.manual@tx.com"
>>> async with session:
...     customer = await session.get(Customer, customer_id)
...     if customer:
...         print(f"Updating email for customer {customer_id}")
...         customer.email = new_email
...         session.add(customer)
...         try:
...             await session.commit() # Explicit commit needed
...             print("Commit successful")
...         except Exception as e:
...             print(f"Caught exception during commit: {e}, rolling back.")
...             await session.rollback() # Explicit rollback on error
...             raise
...     else:
...         print(f"Customer {customer_id} not found for update.")
Updating email for customer 1
Commit successful
>>> async with session:
...    alice = await session.get(Customer, 1)
...    print(f"Verification after manual commit: Alice's email = {alice.email}")
Verification after manual commit: Alice's email = alice.manual@tx.com

```

Example of manual rollback (simulated failure):

```python
>>> customer_id = 1
>>> new_email = "alice.failed.update@tx.com"
>>> async with session:
...     customer = await session.get(Customer, customer_id)
...     if customer:
...         original_email = customer.email
...         print(f"Attempting to update email for customer {customer_id} to {new_email} (will fail)")
...         customer.email = new_email
...         session.add(customer)
...         try:
...             # Simulate a failure before commit
...             raise DBAPIError("Simulated DB constraint error", params=(), orig=ValueError("Constraint fail"))
...             # await session.commit() # This line won't be reached
...         except DBAPIError as e:
...             print(f"Caught simulated DBAPIError: {e.orig}, rolling back.")
...             await session.rollback() # Explicit rollback on error
...             # Verify state after rollback within the same session context
...             await session.refresh(customer) # Refresh to get DB state post-rollback
...             print(f"Email after rollback (within context): {customer.email}")
...             assert customer.email == original_email # Should be back to original
...         except Exception as e:
...             print(f"Caught unexpected exception: {e}, rolling back.")
...             await session.rollback()
...             raise
Attempting to update email for customer 1 to alice.failed.update@tx.com (will fail)
Caught simulated DBAPIError: Constraint fail, rolling back.
Email after rollback (within context): alice.manual@tx.com

```

Verify email is unchanged in DB after failed attempt:

```python
>>> async with new_session(engine) as session2:
...    alice = await session2.get(Customer, 1)
...    print(f"Verification after failed manual commit: Alice's email = {alice.email}")
Verification after failed manual commit: Alice's email = alice.manual@tx.com

```

## Key Takeaways

*   Planar uses an "implicit BEGIN" transaction strategy.
*   **Always** manage transaction boundaries explicitly using `async with
    session.begin()` (preferred) or manual `session.commit()` within an `async
    with session:` block.
*   Failure to close transactions will lead to issues.
*   Whenever possible, use the framework provided session by calling `get_session()`.


# Workflow Scheduling Guide

## Overview

Planar provides built-in support for scheduling workflows to run automatically using cron expressions. This allows you to create workflows that execute at specific times or intervals without manual intervention.

## Core Concepts

### Cron Expressions

Cron expressions are a standard way to define time-based schedules. Planar uses the 5-field cron format:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, SUN-SAT)
│ │ │ └───── Month (1-12, JAN-DEC)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

Common examples:
- `* * * * *` - Every minute
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour on the hour
- `0 9 * * *` - Daily at 9:00 AM
- `0 0 * * MON` - Every Monday at midnight
- `30 2 15 * *` - On the 15th of every month at 2:30 AM

### Catch-up Window

The catch-up window defines how far back the scheduler will look for missed runs. If your application was down or the scheduler was paused, workflows scheduled during that time will be caught up when the scheduler resumes, but only if they fall within the window period.

The effective window is determined by the `window` and `start_time` parameters:
- Default (no parameters): 50 seconds
- With `window` only: Uses the specified window
- With `start_time` only: Window is `now - start_time`
- With both: Uses `min(window, now - start_time)`

For example, with `window=timedelta(hours=2)`, if your application was down for 3 hours, only the runs from the last 2 hours will be scheduled when it comes back up.

## Using the @cron Decorator

The `@cron` decorator is used to schedule workflows. It must be applied to functions already decorated with `@workflow()`.

**Important**: The decorator validates that `args` and `kwargs` match the workflow function's signature at registration time. This helps catch configuration errors early.

### Basic Usage

```python
from datetime import timedelta
from planar.workflows import cron, workflow

@cron("*/5 * * * *")  # Run every 5 minutes
@workflow()
async def my_scheduled_workflow():
    # Workflow implementation
    pass
```

### With Arguments

Pass arguments to scheduled workflow runs using the `args` and `kwargs` parameters:

```python
@cron("0 * * * *", args=(100,), kwargs={"mode": "production"})
@workflow()
async def process_batch(batch_size: int, mode: str = "test"):
    # Process batch_size items in the specified mode
    pass
```

### Configuring the Catch-up Window

The catch-up window determines how far back the scheduler will look for missed runs. The actual window used depends on the combination of the `window` and `start_time` parameters:

1. **No window, no start_time**: Defaults to 50 seconds
2. **Window only**: Uses the specified window
3. **Start_time only**: Window is calculated as `now - start_time`
4. **Both window and start_time**: Uses `min(window, now - start_time)`

```python
# Default: 50-second catch-up window
@cron("*/10 * * * *")
@workflow()
async def quick_workflow():
    pass

# Explicit window: catch up runs missed in the last 30 minutes
@cron("*/10 * * * *", window=timedelta(minutes=30))
@workflow()
async def time_sensitive_workflow():
    pass

# Start time only: catch up all runs since Jan 1, 2025
@cron("0 0 * * *", start_time=datetime(2025, 1, 1))
@workflow()
async def historical_workflow():
    pass

# Both specified: uses the smaller of the two
@cron("0 * * * *",
      window=timedelta(days=7),
      start_time=datetime(2025, 1, 1))
@workflow()
async def bounded_workflow():
    # If running on Jan 3, window is 2 days (now - start_time)
    # If running on Jan 10, window is 7 days (explicit window)
    pass
```

### Scheduling with Start Times

The `start_time` parameter allows you to control when a workflow should begin its schedule. This is useful for:
- Delaying the start of scheduled workflows
- Coordinating workflows to start at specific dates
- Testing schedules with future start times

```python
from datetime import datetime, timezone

# Start scheduling on a specific date
@cron("0 9 * * MON", start_time=datetime(2025, 2, 1))
@workflow()
async def weekly_report():
    # Will only start scheduling after February 1, 2025
    pass

# Timezone-aware start times are automatically converted to UTC
pst = timezone(timedelta(hours=-8))
@cron("0 12 * * *", start_time=datetime(2025, 1, 15, 12, 0, tzinfo=pst))
@workflow()
async def daily_task():
    # Starts at noon PST on Jan 15, 2025 (20:00 UTC)
    pass
```

### Multiple Schedules

You can apply multiple `@cron` decorators to the same workflow to create different schedules with different parameters:

```python
@cron("*/15 * * * *", args=(50,))      # Every 15 minutes, process 50 items
@cron("0 * * * *", args=(500,))        # Every hour, process 500 items
@cron("0 0 * * *", args=(10000,))      # Daily at midnight, process 10000 items
@workflow()
async def adaptive_processor(batch_size: int):
    # Process different batch sizes at different frequencies
    pass
```

## How Scheduling Works

### Scheduling Loop

The Planar scheduler runs a background loop that:
1. Checks all registered cron schedules every 30 seconds
2. Calculates which runs should have occurred since the last check
3. Creates workflow entries for any missed runs within the catch-up window
4. Ensures idempotency - each scheduled time is only created once

### Idempotency

Each scheduled run has a unique idempotency key composed of:
- The cron expression (normalized)
- The workflow function name
- The arguments and keyword arguments
- The scheduled run time

This ensures that even if the scheduling loop runs multiple times, each specific run is only created once.

### Workflow Execution

Scheduled workflows are created with:
- Status: `PENDING`
- `idempotency_key`: Unique key to prevent duplicate scheduling (contains the scheduled timestamp)
- `scheduled_time`: The scheduled execution time for the workflow

The Planar orchestrator picks up these pending workflows and executes them like any other workflow.

## Complete Example

```python
from datetime import timedelta
from planar.app import PlanarApp
from planar.workflows import cron, step, workflow

@step()
async def fetch_metrics() -> dict:
    """Fetch system metrics."""
    # Implementation to fetch metrics
    return {"cpu": 45.2, "memory": 67.8}

@step()
async def analyze_metrics(metrics: dict) -> dict:
    """Analyze fetched metrics."""
    alerts = []
    if metrics["cpu"] > 80:
        alerts.append("High CPU usage")
    if metrics["memory"] > 90:
        alerts.append("High memory usage")
    return {"metrics": metrics, "alerts": alerts}

@step()
async def send_report(analysis: dict):
    """Send metrics report."""
    print(f"Metrics: {analysis['metrics']}")
    if analysis["alerts"]:
        print(f"ALERTS: {', '.join(analysis['alerts'])}")

# Run every 5 minutes with a 10-minute catch-up window
@cron("*/5 * * * *", window=timedelta(minutes=10))
@workflow()
async def monitor_system():
    """System monitoring workflow that runs every 5 minutes."""
    metrics = await fetch_metrics()
    analysis = await analyze_metrics(metrics)
    await send_report(analysis)
    return analysis

app = PlanarApp(
    title="System Monitor",
    description="Automated system monitoring with scheduled workflows"
).register_workflow(monitor_system)
```

## Best Practices

### 1. Choose Appropriate Windows

- **Short windows** (seconds/minutes) for time-sensitive workflows that lose relevance if delayed
- **Medium windows** (hours/days) for regular batch processing workflows
- **Long windows** (days/weeks) for critical batch jobs that must not be skipped
- **Default window** (50 seconds) is very short - explicitly set a window for production workflows

### 2. Design Idempotent Workflows

Since catch-up may run multiple workflow instances in quick succession, ensure your workflows are idempotent:

```python
@cron("0 * * * *", window=timedelta(hours=24))
@workflow()
async def hourly_aggregation():
    # Use the scheduled_time to determine which hour to process
    # This ensures each hour is processed exactly once
    pass
```

### 3. Monitor Scheduled Workflows

Track your scheduled workflows to ensure they're running as expected:

```python
from planar.workflows.models import Workflow
from sqlmodel import select

# Query scheduled workflows
scheduled = await session.exec(
    select(Workflow).where(
        Workflow.scheduled_time.is_not(None)
    )
)
```

### 4. Handle Time Zones

All scheduling operations use timezone-naive UTC datetimes internally:

- **Cron expressions**: Evaluated against timezone-naive UTC datetimes.
- **start_time**: Timezone-aware datetimes are converted to UTC and stripped of timezone info
- **scheduled_time**: Stored as timezone-naive UTC in the database
- **Scheduling calculations**: All performed in timezone-naive UTC space

```python
from datetime import datetime, timezone, timedelta

# This runs at midnight UTC (timezone-naive evaluation)
@cron("0 0 * * *")
@workflow()
async def daily_task():
    pass

# Timezone-aware start_time is converted to timezone-naive UTC
eastern = timezone(timedelta(hours=-5))
@cron("0 8 * * *", start_time=datetime(2025, 1, 1, 8, 0, tzinfo=eastern))
@workflow()
async def morning_task():
    # start_time becomes datetime(2025, 1, 1, 13, 0) (no tzinfo)
    # Cron "0 8 * * *" will run at 08:00 UTC
    pass
```

**Important**: Since all times are normalized to UTC, make sure your cron expressions account for this. A workflow scheduled for "0 9 * * *" will run at 9:00 AM UTC, regardless of your local timezone. To simplify things, never use timezone-aware datetime objects and things will just work.
  
### 5. Test Your Schedules

Use the cron expression normalizer to verify your expressions:

```python
from planar.cron_expression_normalizer import normalize_cron

# Test that your expression is valid and see its normalized form
expr = "*/5 * * * MON-FRI"
normalized = normalize_cron(expr)  # "0,5,10,15,20,25,30,35,40,45,50,55 * * * 1-5"
```

## Advanced Topics

### Expression Normalization

Planar normalizes all cron expressions to ensure consistent scheduling and idempotency. This means:
- `MON-FRI` becomes `1-5`
- `*/5` expands to `0,5,10,15,20,25,30,35,40,45,50,55`
- Ranges are compressed: `1,2,3,5` becomes `1-3,5`

### Database Schema

Scheduled workflows add two fields to the workflow table:
- `idempotency_key`: Unique key preventing duplicate scheduling (format: `{timestamp}:{hash}`)
- `scheduled_time`: The scheduled execution time for the workflow

### Integration with Orchestrator

The scheduling system integrates seamlessly with the Planar orchestrator:
1. Scheduler creates workflow entries with `PENDING` status
2. Orchestrator picks up pending workflows based on standard polling logic
3. Workflows execute normally, with access to their scheduled time if needed

## Troubleshooting

### Workflows Not Scheduling

1. **Check registration**: Ensure the workflow is registered with the app
   ```python
   app.register_workflow(my_scheduled_workflow)
   ```

2. **Verify cron expression**: Test your expression is valid
   ```python
   from croniter import croniter
   croniter.is_valid("your expression here")
   ```

3. **Check the window**: Ensure your window is large enough to catch missed runs

### Too Many Catch-up Runs

If you're getting too many historical runs after downtime:
- Reduce the `window` parameter
- Consider adding logic to skip outdated runs in your workflow

### Debugging Schedules

Enable debug logging to see scheduling decisions:

```python
import logging
logging.getLogger("planar.workflows.scheduling").setLevel(logging.DEBUG)
```

This will show:
- When schedules are synchronized
- Which workflows are being scheduled
- The idempotency keys being used


# PlanarDataset

## Overview

PlanarDataset is a lightweight reference to a Ducklake-backed table. It lets
you persist tabular data between steps without passing large payloads around.
You create a named dataset, write data to it, and read it later from other
steps using a small, serializable reference.

## Quick Start

```python
from planar.data import PlanarDataset
from planar.workflows import step
import polars as pl

@step()
async def load_transactions(csv_path: str) -> PlanarDataset:
    df = pl.read_csv(csv_path)
    dataset = await PlanarDataset.create("transactions_2024_07")
    await dataset.write(df, mode="overwrite")
    return dataset

@step()
async def load_transactions_lazy(csv_path: str) -> PlanarDataset:
    # Use LazyFrame for better performance and to avoid blocking the event loop
    lf = pl.scan_csv(csv_path).with_columns(
        pl.col("amount").cast(pl.Float64),
        pl.col("date").str.to_date()
    )
    dataset = await PlanarDataset.create("transactions_2024_07")
    await dataset.write(lf, mode="overwrite")
    return dataset

@step()
async def aggregate_transactions(transactions: PlanarDataset) -> PlanarDataset:
    df = await transactions.to_polars()
    aggregated = df.group_by("merchant_id").sum()
    output = await PlanarDataset.create("merchant_aggregates")
    await output.write(aggregated, mode="overwrite")
    return output
```

## API Reference

- Class: PlanarDataset
  - name: str — dataset (table) name in Ducklake

- Classmethod `create(name: str, if_not_exists: bool = True) -> PlanarDataset`
  - Creates a dataset reference. The physical table is created on first write.
  - Raises `DatasetAlreadyExistsError` when the dataset exists and
    `if_not_exists` is False.

- `exists() -> bool`
  - Checks whether the dataset table exists.

- `write(data, mode: Literal["overwrite", "append"] = "append") -> None`
  - Writes data to the dataset. Creates the table if it does not exist.
  - Supported `data` types:
    - `polars.DataFrame`
    - `polars.LazyFrame`
    - `pyarrow.Table`
    - `ibis.Table`
    - Row-like Python data: `list[dict]` or `dict[str, list]`
  - Modes:
    - `overwrite`: replaces existing rows
    - `append`: adds rows to the existing table
  - Raises `DataError` on failures.

- `read(columns: list[str] | None = None, limit: int | None = None) -> ibis.Table`
  - Returns an `ibis.Table` for further filtering/aggregation.
  - Optional column projection and row limit.
  - Raises `DatasetNotFoundError` if the dataset does not exist.

- `to_polars() -> polars.DataFrame`
  - Reads the entire dataset into a Polars DataFrame.

- `to_pyarrow() -> pyarrow.Table`
  - Reads the entire dataset into a PyArrow Table.

- `delete() -> None`
  - Drops the dataset table. Raises `DataError` on failures.

## Behavior and Notes

- Reference semantics: steps pass around a compact reference, not the data.
- Lazy creation: the underlying table is created on the first successful write.
- Async-first: all operations are `async` to avoid blocking the event loop.
- Errors: operations raise `DataError`, `DatasetAlreadyExistsError`, or
  `DatasetNotFoundError` for common cases.
- Blocking operations: when doing CPU-bound or blocking work in steps
  (for example, Polars file IO or heavy transforms), wrap the call with
  `asyncio.to_thread`, or use the `@asyncify` decorator / `asyncify()` helper
  from `planar.utils`, to keep the event loop responsive.

```python
from asyncio import to_thread
import polars as pl

@step()
async def ingest_fast(csv_path: str) -> PlanarDataset:
    # Run blocking CSV parse off the event loop
    df = await to_thread(pl.read_csv, csv_path)
    ds = await PlanarDataset.create("raw_transactions")
    await ds.write(df, mode="overwrite")
    return ds
```

Alternatively, you can use the `asyncify` helper to convert a synchronous
function into an async one:

```python
from planar.utils import asyncify
import polars as pl

# Wrap a sync function as async
read_csv_async = asyncify(pl.read_csv)

@step()
async def ingest_fast(csv_path: str) -> PlanarDataset:
    df = await read_csv_async(csv_path)
    ds = await PlanarDataset.create("raw_transactions")
    await ds.write(df, mode="overwrite")
    return ds
```

## Configuration

PlanarDataset uses the app's `data` configuration to connect to Ducklake. In a
local dev setup, a typical configuration looks like this:

```yaml
data:
  catalog:
    type: duckdb
    path: .data/catalog.ducklake
  catalog_name: planar_data
  storage:
    backend: localdir
    directory: .data/ducklake_files
```

Other supported catalogs include `postgres` and `sqlite`; storage backends
include `localdir` and `s3`. Ensure `app.config.data` is set or data operations
will raise `DataError`.

## Examples

### Ingest and Clean

```python
from planar.workflows import step
import polars as pl

@step()
async def ingest_csv_to_dataset(csv_path: str) -> PlanarDataset:
    df = pl.read_csv(csv_path)
    dataset = await PlanarDataset.create("raw_transactions")
    await dataset.write(df, mode="overwrite")
    return dataset

@step()
async def clean_transactions(raw: PlanarDataset) -> PlanarDataset:
    df = await raw.to_polars()
    cleaned = df.filter(pl.col("amount") > 0).drop_nulls()
    output = await PlanarDataset.create("cleaned_transactions")
    await output.write(cleaned, mode="overwrite")
    return output
```

### Read with Ibis Filters

```python
from typing import Dict
from planar.workflows import step

@step()
async def analyze_high_value_transactions(transactions: PlanarDataset) -> Dict[str, float]:
    table = await transactions.read()
    high_value = table.filter(table.amount > 1000)
    summary = high_value.group_by("merchant_id").agg(
        total=high_value.amount.sum(),
        count=high_value.amount.count(),
    )
    result = summary.to_polars()
    return result.to_dict()
```

### Error Handling

```python
from typing import Optional
import polars as pl

@step()
async def safe_read_dataset(dataset_name: str) -> Optional[pl.DataFrame]:
    try:
        dataset = PlanarDataset(name=dataset_name)
        if not await dataset.exists():
            return None
        return await dataset.to_polars()
    except DatasetNotFoundError:
        logger.error("dataset not found", dataset_name=dataset_name)
        return None
    except DataError:
        logger.exception("failed to read dataset", dataset_name=dataset_name)
        raise
```

## Limitations

- No explicit snapshot/time-travel selection yet.
- No partitioning controls; write/append semantics are table-wide.


## Planned Features

- Snapshot versioning support
- Partition column support
- Schema evolution capabilities
- Data lineage tracking (e.g., set metadata on snapshot version during write)
- Data validation and quality checks
- Data transformation utilities (e.g., `@model` decorator)
