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
