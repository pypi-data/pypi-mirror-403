# Agent Evaluation Design

## Overview

Planar needs a first-class evaluation framework to validate agent prompt/model changes before or after promotion. This document describes the initial design: how users define eval sets, wire them to agents through evaluation suites, register scorers, and execute durable evaluation runs automatically whenever an agent configuration changes.

## Key Concepts

- **Evaluation Set** – A persisted collection of canonical test cases (`EvalSet` + `EvalCase`). Each case captures an agent input payload and optional expected output.
- **Evaluation Suite** – A persisted entity that targets a specific agent, references exactly one eval set (MVP scope), lists scorers to run, and controls execution policy (currently just concurrency and activation flag).
- **Scorer** – A callable that receives `(input_payload, expected_output, agent_output, reasoning)` and returns a structured `ScorerResult`. Planar ships a small library of built-ins and allows apps to register custom scorers (`app.register_scorer`).
- **Evaluation Run** – A durable workflow execution of a suite against a particular agent configuration version. Runs record per-case results and can surface aggregates in UI/API (computed from case results).

> **Suite vs. Eval Set**: eval sets hold reusable ground-truth examples; suites are the wiring layer that combines an agent, an eval set, and scorer settings into an executable evaluation plan.

## MVP Scope & Simplifications


To minimise surface area for the first release:

- Agent inputs are passed directly from eval set payloads. If agent expects a specific type / format, the eval set payload should be in that format or a subset of it.
- Scorer thresholds are provided via scorer-specific settings (e.g., `{"threshold": 0.9}`) when configuring a suite, and evaluated during per-case scoring (no run-level `thresholds_passed` field).
- Evaluation runs persist agent configuration version, eval set id, and scorer details but defer richer analytics (token usage, tool deltas) to follow-up work.
- Suites are not versioned, and changes to a suite are immediately applied to all runs that reference it. In the future, we can make suites versioned and immutable like agent configurations and rules.
- Optimisation is covered in `agent_optimizer.md` and intentionally out of scope here.

## Data Model

EvalSet (agent-independent, globally scoped)
├── name, description, input_format, output_format
└── EvalCase (many)
    └── input_payload, expected_output

Agent (by agent_name)
└── EvalSuite (many) [configuration layer]
    ├── name, agent_name, is_active, concurrency
    ├── References: EvalSet (one eval set per suite)
    ├── EvalScorerConfig (embedded JSON list)
    │   └── name, scorer_name, settings
    │       └── References: Scorer Registry (by scorer_name)
    │
    └── EvalRun (many) [execution instances]
        ├── agent_name, agent_config_id, status
        ├── References: EvalSet (denormalized eval_set_id)
        ├── References: EvalSuite (suite_id)
        ├── References: AgentConfig (by version)
        │
        └── EvalCaseResult (many, 1:1 with eval cases)
            ├── References: EvalCase (eval_case_id)
            ├── input_payload, expected_output [denormalized]
            ├── agent_output, agent_reasoning, tool_calls
            └── scorer_results (embedded JSON dict)
                └── {scorer_name: ScorerResultDict}

Scorer Registry (runtime, app-level, not agent-scoped)
├── Built-in scorers
└── Custom scorers

### Persistent Entities

```python
class EvalSet(PlanarBaseEntity):
    name: str
    description: str | None = None
    input_format: Literal["text", "json"]
    output_format: Literal["text", "json", "none"] = "none"

class EvalCase(PlanarBaseEntity):
    eval_set_id: UUID = Field(foreign_key="eval_set.id")
    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None = None
```

- Payloads use the same structures Planar agents already accept/emit (including embedded PlanarFile descriptors). Cases execute in creation order (ascending `created_at`).

```python
class EvalSuite(PlanarBaseEntity):
    name: str
    agent_name: str
    eval_set_id: UUID = Field(foreign_key="eval_set.id")
    concurrency: int = 4
    is_active: bool = True
    scorers: list[EvalScorerConfig]  # stored as JSON

class EvalRun(PlanarBaseEntity):
    agent_name: str
    suite_id: UUID = Field(foreign_key="eval_suite.id")
    agent_config_id: UUID | None = Field(foreign_key="object_configuration.id")
    eval_set_id: UUID = Field(foreign_key="eval_set.id")
    status: Literal["pending", "running", "failed", "succeeded", "skipped"]
    total_cases: int
    started_at: datetime | None
    completed_at: datetime | None

class EvalCaseResult(PlanarBaseEntity):
    run_id: UUID = Field(foreign_key="eval_run.id")
    eval_case_id: UUID = Field(foreign_key="eval_case.id")
    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None
    agent_output: dict[str, Any] | str
    agent_reasoning: str | None
    tool_calls: list[dict[str, Any]]
    scorer_results: dict[str, ScorerResultDict]
    duration_ms: int
    status: Literal["passed", "failed", "skipped"]
```

`ScorerResultDict` stores `score`, `passed`, and optional `details` (the serialized form of `ScorerResult`).

### Scorer Configurations

`EvalScorerConfig` captures the `name`, `scorer_name`, and JSON `settings`. The
sanitized configs are embedded directly on `EvalSuite.scorers`, keeping the schema
flexible while allowing `scorer_registry` to enforce each scorer’s settings contract.
Only one eval set per suite is supported in MVP; future enhancements can evolve
`eval_set_id` into arrays with weighting.

## Scorer Registry

Built-in scorers (subject to implementation detail) include:

| Name | Description | Key Settings |
|------|-------------|--------------|
| `exact_match` | String equality | none |
| `case_insensitive_match` | Lower-case equality | none |
| `levenshtein` | Normalized similarity | `max_distance` |
| `numeric_tolerance` | Numeric comparison within tolerance | `abs_tol`, `rel_tol` |
| `json_equality` | Deep JSON equality | `ignore_order`, `ignore_keys` |
| `llm_judge` | LLM-as-a-judge rubric scoring for complete outputs | `rubric`, `judge_model`, `passing_threshold`, `temperature` |

Custom scorers:

```python
class ScorerResult(BaseModel):
    score: float
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)

@app.register_scorer(name="summary_bleu")
async def summary_bleu(
    input_payload: dict[str, Any] | str,
    expected_output: dict[str, Any] | str | None,
    agent_output: dict[str, Any] | str,
    reasoning: str | None,
) -> ScorerResult:
    ...
```

Suites reference scorers by `scorer_name`. Applications can update or remove scorers by re-registering with the same name.
Suite-level `settings` are applied by Planar before invocation (e.g., injecting tolerances), so custom scorers always receive the same four arguments and return `ScorerResult`.

## Workflow Definition

Durable workflow: `run_eval(agent_name: str, agent_config_id: UUID | None, suite_id: UUID)`

1. **Resolve configuration**
   - Fetch the target `AgentConfig` snapshot and the `EvalSuite` referenced by `suite_id` (ensure `is_active`).
   - Ensure the suite’s eval set is compatible (format matching agent input/output types).
2. **Load eval set cases**
   - Read all cases for the suite’s `eval_set_id`, ordered by creation time.
   - Optionally sample deterministically if future refinements add sampling controls (not in MVP).
3. **Iterate over cases**
   - Invoke the agent (`Agent.run_step`) with the eval set payload.
   - Capture `AgentRunResult` plus emitted reasoning/tool events.
   - For each `EvalScorerConfig`, resolve the scorer callable via registry, apply `settings`, compute `ScorerResult`.
   - Persist an `EvalCaseResult`.
4. **Summarise**
   - Persist `EvalRun` (with run metadata) and emit workflow notifications/SSE updates.
   - (Future) compute and cache aggregate scorer scores if needed for faster dashboards.
5. **Idempotency**
   - Use `(agent_name, agent_config_id, suite_id)` to de-duplicate or resume in-progress runs.

## Automation & Triggers

- (future) The `agent_configuration.write_config` and `promote_config` paths enqueue evaluation runs for all active suites (`EvalSuite.is_active`) targeting the modified agent.
- Manual execution: `POST /planar/v1/evals/suites/{suite_id}/runs`.
- Runs can be re-triggered if eval sets or scorers change (UI offers “Re-run Eval” action).

## API & UI Touchpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /planar/v1/evals/sets` | Create an eval set & optional initial cases |
| `GET /planar/v1/evals/sets` | List eval sets (global scope today, filterable later) |
| `PATCH /planar/v1/evals/sets/{eval_set_id}` | Update eval set metadata |
| `GET /planar/v1/evals/sets/{eval_set_id}/cases` | List ordered eval set cases |
| `POST /planar/v1/evals/sets/{eval_set_id}/cases` | Add a new eval set case |
| `PATCH /planar/v1/evals/sets/{eval_set_id}/cases/{case_id}` | Update an existing eval set case |
| `DELETE /planar/v1/evals/sets/{eval_set_id}/cases/{case_id}` | Remove an eval set case |
| `POST /planar/v1/evals/suites` | Create or update suite config (agent-scoped via payload) |
| `GET /planar/v1/evals/suites` | List suites + latest run status (supports agent filters) |
| `GET /planar/v1/evals/suites/{suite_id}` | Retrieve suite metadata |
| `PATCH /planar/v1/evals/suites/{suite_id}` | Update suite metadata, eval set reference, or scorers |
| `GET /planar/v1/evals/suites/{suite_id}/runs` | Run history & per-scorer aggregates |
| `POST /planar/v1/evals/suites/{suite_id}/runs` | Manual run trigger (still enforces agent run perms) |

UI surfaces:
- Eval set editor: create cases, edit payloads/expected outputs.
- Suite editor: select eval set, scorers, concurrency.
- Eval dashboard: latest run status, per-scorer scores, drill-down to case results.

## Integration Points

- `PlanarApp.register_scorer` exposes custom scorers to the registry.
- `PlanarApp.register_agent` unchanged; agents gain evaluation metadata automatically.
- Logging: add structured events `eval_case` and `eval_run`.
- SSE streaming upgrades reuse existing mechanisms to surface progress in CoPlane.

## Future Enhancements

- Multiple eval sets per suite with weighting/filters.
- Input templating and tool context builders.
- Richer analytics (token usage, confusion matrices, longitudinal charts).
- Bulk eval set import/export flows.
- Auto-remediation workflows triggered by scorer failures.
- Tight integration with the prompt optimizer (see `agent_optimizer.md`).
