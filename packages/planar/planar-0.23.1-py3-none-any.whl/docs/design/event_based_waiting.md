# Event-Based Waiting and Human-in-the-Loop Tasks

## Overview

This document describes the design for enhancing Planar's workflow engine with two new capabilities:

1. **Event-Based Waiting**: A mechanism for steps to await events rather than polling for conditions
2. **Human-in-the-Loop Tasks**: A specialized workflow step that allows human input mid-workflow

These features enable more efficient execution of workflows that depend on external triggers or human decision-making.

## Event-Based Waiting

### Problem

The current `@wait` decorator implements a pull-based polling mechanism where a workflow suspends and periodically checks if a condition is met. While effective for many scenarios, this approach has limitations:

1. **Inefficiency**: Regular polling consumes resources even when no change has occurred
2. **Latency**: Workflows only respond to changes on the next poll interval
3. **Limited Scope**: Only effective for conditions that can be actively checked

### Solution

Enhance the `@wait` decorator to support push-based event waiting in addition to its current poll-based functionality.

### Design Principles

1. **Immutable Event Log**: Events are immutable records in an append-only log
2. **Immediate Execution**: If a step awaits an event that already exists, it proceeds immediately
3. **Global Scope**: Events can be scoped to a specific workflow or accessible globally
4. **Integration with Orchestrator**: The workflow orchestrator manages event-to-workflow relationships

### Event Model

```python
class WorkflowEvent(TimestampMixin, PlanarBaseModel, table=True):
    # Unique identifier for this event occurrence
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Event type identifier (e.g., "order_approved", "payment_received")
    event_key: str = Field(index=True)
    
    # Optional association with a specific workflow
    workflow_id: Optional[UUID] = Field(default=None, index=True)
    
    # Optional payload data associated with the event
    payload: dict = Field(default_factory=dict)
    
    # When the event was created
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )
```

### Event-Based Waiting Approach

For event-based waiting, we'll introduce a dedicated step method `wait_for_event()` that is distinct from the `@wait` decorator. This separation provides a cleaner API and allows the event payload to be returned as the step output.

```python
@step()
async def wait_for_event(
    event_key: str,
    max_wait_time: float = 3600.0,
) -> dict:
    """
    Creates a durable step that waits for a specific event to be emitted.
    
    Args:
        event_key: The event identifier to wait for
        max_wait_time: Maximum time to wait before failing
    
    Returns:
        The event payload as a dictionary
    """
    # Implementation details omitted
```

The original `@wait` decorator will retain its poll-based waiting functionality:

```python
def wait(
    poll_interval: float = 60.0,
    max_wait_time: float = 3600.0,
):
    """
    Creates a durable wait step that polls a condition function until it returns True.
    
    Args:
        poll_interval: How often to check the condition
        max_wait_time: Maximum time to wait before failing
    """
    # Implementation details omitted
```

### Workflow Orchestration

The workflow orchestrator will be enhanced to:

1. Identify suspended workflows waiting for events that have occurred
2. Wake up the relevant workflows

### Event API

```python
async def emit_event(
    event_key: str, 
    payload: dict = None, 
    workflow_id: Optional[UUID] = None
)

async def check_event_exists(
    event_key: str, 
    since: Optional[datetime] = None,
    workflow_id: Optional[UUID] = None
) -> bool

async def get_latest_event(
    event_key: str,
    workflow_id: Optional[UUID] = None
) -> Optional[WorkflowEvent]
```

## Human-in-the-Loop Tasks

### Problem

Many business workflows require human input at specific decision points. The workflow must suspend until a human completes a task, then proceed with the human's decision.

### Solution

Build a specialized `@human` decorator on top of the event system that:

1. Creates a human task record with input data and form schema
2. Suspends the workflow using event-based waiting
3. Resumes when a human completes the task
4. Returns the human's input to the workflow

### Human Task Model

```python
class HumanTask(TimestampMixin, PlanarBaseModel, table=True):
    # Unique identifier for this task
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Human-readable title and description
    title: str
    description: Optional[str] = None
    
    # Workflow association
    workflow_id: UUID
    
    # Input data for context
    input_data: dict
    
    # Schema for expected output (derived from function annotation)
    output_schema: dict
    
    # Output data when completed
    output_data: Optional[dict] = None
    
    # Task status
    status: str = "pending"  # pending, completed, cancelled, expired
    
    # Assignment and completion tracking
    assigned_to: Optional[str] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    # Time constraints
    deadline: Optional[datetime] = None
```

### Human Task Flow

1. **Creation**: Workflow calls `@human` decorated function
   - System creates HumanTask record
   - Workflow suspends, awaiting "human_task_completed_<task_id>" event

2. **UI Interaction**: 
   - Human accesses UI that displays task
   - UI renders form based on output schema
   - Human completes task by submitting form

3. **Completion**:
   - System validates input against schema
   - Updates HumanTask record with output_data
   - Emits "human_task_completed_<task_id>" event
   - Orchestrator detects event and resumes workflow
   - Human step decorator resumes and injects runs the decorated function with the human's input

### Human Decorator Design

The `@human` decorator will build on top of the `wait_for_event()` step method. To ensure replay safety, we'll separate the human task creation into its own step:

```python
def human(
    title: str,
    description: str = None,
    assignment_rule: Optional[str] = None,
    timeout: Optional[float] = None,
):
    """
    Human-in-the-loop step decorator.
    
    Args:
        title: Human-readable title for the task
        description: Optional detailed description
        assignment_rule: Rule for auto-assigning the task
        timeout: Maximum time to wait for human input
    """
    def decorator(func):
        # Ensure the body of the decorated function is empty
        # Raise an error if the function body is not empty
        #if not is_empty_function(func):
        #    raise ValueError("Human-in-the-loop steps must be empty.")

        @wraps(func)
        @step()
        async def human_step(*args, **kwargs):
            ctx = get_context()
            workflow_id = ctx.workflow.id
            
            # Extract input data and output schema from function signature
            input_data = {...}  # Derived from args/kwargs
            output_schema = {...}  # Derived from function annotations
            
            # Create the human task as a separate step for replay safety
            task_id = await create_human_task(
                title=title,
                description=description,
                input_data=input_data, 
                output_schema=output_schema,
                workflow_id=workflow_id
            )
            
            # Wait for the task completion event
            event_key = f"human_task_completed_{task_id}"
            task_result = await wait_for_event(event_key, max_wait_time=timeout)
            
            # Return the human input as the output of the step
            return task_result["output_data"]
        
        return human_step
    
    return decorator
```

The decorator extracts input and output types from function annotations, ensuring type safety between the workflow code and human interface.

## Implementation Strategy

### Phase 1: Core Event System

1. Create WorkflowEvent model and add migrations
2. Implement event API (emit, check, get)
3. Enhance Suspend class to track awaited events
4. Implement the wait_for_event step method
5. Refactor the wait decorator to focus on condition polling only
6. Update workflow orchestrator to handle event-based resumption

### Phase 2: Human-in-the-Loop System

1. Create HumanTask model and add migrations
2. Implement human decorator
3. Create REST API endpoints for task management
4. Build basic UI for task listing and completion

### Phase 3: UI Enhancements

1. Develop dynamic form rendering based on output schemas
2. Implement task assignment and filtering
3. Add dashboards for task monitoring
4. Develop retry and cancellation mechanisms

## Benefits

1. **Efficiency**: Eliminates polling overhead for event-driven workflows
2. **Responsiveness**: Workflows resume immediately when events occur
3. **Flexibility**: Supports both time-based and event-based waiting
4. **Type Safety**: Maintains strong typing between workflow code and human interfaces
5. **Auditability**: Creates an immutable log of events and human decisions

## Use Cases

1. **Approval Workflows**: Wait for manager approval of expenses, time off, etc.
2. **External System Integration**: Wait for webhook callbacks from payment processors
3. **Human Data Entry**: Collect specialized input mid-workflow
4. **Inter-Workflow Communication**: Allow workflows to signal each other

## Example Usage

### Event-Based Waiting

```python
@workflow
async def order_processing():
    order_id = await create_order(...)

    event_key = f"payment_received_{order_id}"
    payment_info = await wait_for_event(event_key)

    await process_payment(order_id, payment_info["amount"])
    shipping_info = await wait_for_event(f"order_shipped_{order_id}")
    await update_tracking(order_id, shipping_info["tracking_number"])
```

### Human-in-the-Loop

```python
# Get manager approval
@human(
    title="Approve Expense Report",
    description="Please review and approve or reject this expense report"
)
async def get_approval(report_data: dict) -> ApprovalDecision:
    # Human in the loop steps don't have a body.
    # The human input is returned as the output of the step.
    pass
    
@workflow
async def expense_approval():
    report = await create_expense_report(...)
    decision = await get_approval(report)
    
    if decision.approved:
        await process_payment(report.id, decision.amount)
    else:
        await notify_rejection(report.id, decision.reason)
```