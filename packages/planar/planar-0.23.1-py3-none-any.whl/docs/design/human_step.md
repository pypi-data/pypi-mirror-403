# Human-in-the-Loop Step Design

## Overview

This document outlines the design for Planar's Human-in-the-Loop functionality as a callable step class. This approach aligns with the existing Agent step design, providing a consistent API across different specialized step types in the workflow system.

The `Human()` class creates callable task objects that:
1. Handle input validation and transformation
2. Create and persist human task records
3. Leverage the event system for workflow suspension and resumption
4. Provide a consistent interface for both developers and business users
5. Support proper typing with generics for both input and output types

## Key Features

1. **Object-Based Definition**:
   - Create a `Human` instance that can be called within workflows (similar to `Agent`)
   - Clean API that separates human task definition from workflow usage

2. **Typed Input/Output**:
   - Uses Pydantic models for structured data
   - Type-safe interfaces for both developers and human operators

3. **Database Persistence**:
   - Associated `HumanTask` object in the database
   - Records task metadata, input data, and output responses
   - Maintains execution history for auditing and analysis

4. **Event-Based Waiting**:
   - Leverages the event system for suspending and resuming workflows
   - Avoids polling overhead for efficient execution

5. **Task Management**:
   - Deadline management and expiration
   - Status tracking through the task lifecycle

## High-Level Design

### Human Class

- **Location**: `planar/human/human.py`
- **Purpose**: Define the `Human` class that creates callable task instances
- **Parameters**:
  - `name`: Identifier for the task (used for logging and referencing)
  - `title`: Human-readable title for the task UI
  - `description`: Detailed explanation of the task (None if not provided)
  - `input_type`: Pydantic model for input context data structure (optional)
  - `output_type`: Pydantic model for expected human output (required)
  - `timeout`: Maximum time to wait for human input (defaults to no timeout)

### HumanTask Model

```python
class HumanTaskStatus(str, Enum):
    """Status values for human tasks."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class HumanTask(PlanarBaseEntity, PlanarInternalBase, TimestampMixin, table=True):
    """
    Database model for human tasks that require input from a human operator.

    Inherits from `PlanarBaseEntity`, `PlanarInternalBase`, and `TimestampMixin`.
    These provide ORM capabilities, common internal fields, and timestamp fields (`created_at`, `updated_at`).
    SQLModel typically manages an `id` primary key.
    Audit fields like `created_by`, `updated_by` are not standard in these base classes.
    """

    # Task identifying information
    name: str = Field(index=True)
    title: str
    description: Optional[str] = None

    # Workflow association
    workflow_id: UUID = Field(index=True)
    workflow_name: str

    # Input data for context
    input_schema: Optional[JsonSchema] = Field(default=None, sa_column=Column(JSON))
    input_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Schema for expected output
    output_schema: JsonSchema = Field(sa_column=Column(JSON))
    output_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Task status
    status: HumanTaskStatus = Field(default=HumanTaskStatus.PENDING)

    # Completion tracking
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None

    # Time constraints
    deadline: Optional[datetime] = None
```

### Usage Pattern

```python
from pydantic import BaseModel, Field
from planar.human import Human, Timeout
from planar.workflows import workflow, step

# Define structure for human input/output
class ExpenseApproval(BaseModel):
    approved: bool = Field(description="Whether the expense is approved")
    amount: float = Field(description="Approved amount (may be less than requested)")
    notes: str = Field(description="Explanation for decision", default="")

# Create human task instance
expense_approval_task = Human(
    name="expense_approval",
    title="Approve Expense Request",
    description="Review and approve or modify the expense request",
    output_type=ExpenseApproval,
    # Optional timeout defined in timedelta
    timeout=Timeout(timedelta(hours=24))
)

# Use in workflow
@workflow()
async def expense_workflow(request_data: dict):
    expense_request = await validate_expense(request_data)
    
    # Request human approval - can be called directly with data
    approval = await expense_approval_task(
        expense_request, 
        # Optional per task context message string
        message=f"Expense request details: {expense_request.amount} - {expense_request.purpose}"
    )
    
    # Process based on human decision
    if approval.output.approved:
        return await process_approval(
            expense_request.id,
            approval.output.amount,
            approval.output.notes
        )
    else:
        return await process_rejection(
            expense_request.id,
            approval.output.notes
        )
```

### Human Result Structure

- **Class**: `HumanTaskResult`
- **Fields**:
  - `output`: The structured output (of type specified by `output_type`)
  - `task_id`: Reference to the HumanTask record
  <!-- - `completed_by`: User who completed the task - for the future --> 
  - `completed_at`: When the task was completed

### Event-Based Implementation

The Human step uses the event system for workflow suspension:

1. **Creation**: When called, the Human step:
   - Validates and transforms input data
   - Creates a HumanTask record
   - Suspends workflow awaiting a "human_task_completed:{task_id}" event
   - Sets a wakeup alarm for the task deadline and handles cleanup on timeout [FUTURE]

2. **Completion**: When a human completes the task:
   - System validates input against schema
   - Updates HumanTask record with output_data
   - Emits "human_task_completed:{task_id}" event
   - Orchestrator detects event and resumes workflow
   - Human step returns a structured result (typed by output_type)


## Implementation

The Human step class and supporting functionality has been implemented in the `planar/human/human.py` module. The implementation includes:

1. **Core Classes:**
   - `Human`: A generically typed class for creating and managing human-in-the-loop tasks
   - `HumanTask`: A database model for tracking human tasks with status and metadata
   - `HumanTaskResult`: A structured result type returned when a human task is completed
   - `Timeout`: A helper class for defining timeout durations

2. **Task Management:**
   - Support for creating, completing, and canceling human tasks
   - Status tracking (pending, completed, cancelled, expired)
   - Deadline management based on optional timeouts

3. **Events:**
   - Events for task completion notifications
   - Automatic workflow resumption when tasks are completed
   - Support for future timeout handling

4. **API:**
   - Functions for listing, querying, and managing human tasks
   - Support for task completion with validation
   - Cancellation functionality with reason tracking


## UI Considerations

1. **Task List View**:
   - Filters for pending, completed tasks
   - Sorting by deadline, creation date
   - Assignment information

2. **Task Detail View**:
   - Rich rendering of input data
   - Form generation based on output schema
   - Supporting attachments and context

3. **Form Generation**:
   - Dynamic form controls based on Pydantic fields
   - Field validation from schema
   - Customizable layout via ui_config

### EntityField Helper

Use `EntityField` in the Pydantic models that define human task input or output
to indicate a field references an existing entity. The helper adds metadata to
the JSON schema so Planar's UI can present a dropdown with meaningful labels.

```python
from typing import Annotated
from planar.modeling.field_helpers import EntityField

class ApproveExpense(BaseModel):
    approver_id: Annotated[str, EntityField(entity=User, display_field="full_name")]
```

`EntityField` is only used with these Pydantic models, not with the entity
definitions themselves. It enhances the schema so Planar's UI can automatically
render dropdown selectors.

Key benefits include:

1. **Better UI Integration** – forms show meaningful labels instead of raw IDs.
2. **Improved API Docs** – relationship metadata is added to the JSON schema.
3. **Type Safety** – entity references remain strongly typed.
4. **Display Field Detection** – if you omit `display_field`, common names like
   `name`, `title`, `username`, `label`, or `display_name` are tried
   automatically.

4. **Configurability**:
   - Assignment rule configuration

## Implementation Strategy

### Phase 1: Core Functionality (Completed)

1. Create HumanTask model and migrations
2. Implement Human class using event system
3. Build basic API endpoints for task management
4. Create simple UI for task listing and completion

### Phase 2: Enhanced Features

1. Add assignment rules and resolution
2. Enhance UI with rich form generation
3. Add task search and filtering capabilities

### Phase 3: Advanced Features

1. Task batching and bulk operations
2. Deadline enforcement and escalation
3. Integration with notification systems
4. Analytics and performance metrics

## Benefits

1. **Consistency**: Aligns with Agent step API for a unified developer experience
2. **Type Safety**: Strong typing for both input and output
3. **Configurability**: Runtime adjustment without code changes
4. **Auditability**: Complete history of human decisions
5. **Efficiency**: Event-based model improves performance

## Future Considerations

As the Human step functionality evolves, we may want to consider:

1. **Configuration Management**: Support for runtime configuration overrides via API/UI
2. **Assignment Rules**: Logic for auto-assigning tasks to specific users or groups
3. **UI Configuration**: Advanced options for customizing form rendering and layout
4. **Workflow Templates**: Pre-configured human task patterns for common scenarios
5. **User Preferences**: Allowing users to customize their task views and notifications
6. **SLA Monitoring**: Advanced tracking of task completion times against service level agreements
7. **Mobile Support**: Optimized UI for completing human tasks on mobile devices

## Example Usage

### With Input Type

```python
from pydantic import BaseModel, Field
# Assuming Human and Timeout are imported correctly, e.g.:
# from planar.human import Human, Timeout
# from planar.workflows import workflow

class ExpenseRequest(BaseModel):
    request_id: str
    amount: float
    requester: str
    department: str
    purpose: str
    has_receipts: bool

class ExpenseDecision(BaseModel):
    approved: bool
    approved_amount: float
    notes: str

expense_approval = Human(
    name="expense_approval",
    title="Expense Approval",
    description="Review expense request and approve or adjust amount",
    input_type=ExpenseRequest,
    output_type=ExpenseDecision
)

@workflow()
async def expense_workflow(request_data: dict):
    # Create a validated request object
    request = ExpenseRequest(**request_data)
    
    # Pass the request object directly to the human task
    result = await expense_approval(request)
    
    # Process the result
    return await finalize_expense(
        request.request_id, 
        result.output.approved,
        result.output.approved_amount
    )
```

## Comparison with Agent Pattern

The Human class is designed to follow a similar pattern to the Agent class for consistency:

| Feature | Human | Agent |
|---------|-------|-------|
| Creation | `Human(name, title, output_type)` | `Agent(name, system_prompt, output_type)` |
| Call style | `await human_task(input_data)` | `await agent(input_data)` |
| Result type | `HumanTaskResult[T]` | `AgentRunResult[T]` |
| Wait mechanism | Suspends awaiting an external human-triggered event | Executes its defined logic (which can be a multi-step, resumable process) |
| Execution | UI form completion | LLM call |

This parallel design allows developers to use both humans and AI agents as workflow participants with a consistent API pattern.
