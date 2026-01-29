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
