# Agent Prompt Optimizer (GEPA) Design

## Overview

This document builds on `agent_eval.md` and describes how Planar can automatically explore new prompt variants using GEPA (Gradient Estimation by Perturbation in Agents). The optimizer is optional; it reuses the evaluation infrastructure to score candidate prompts, then suggests or applies the best-performing configuration.

## Goals

1. Generate prompt/model candidates, evaluate them via existing suites, and aggregate results.
2. Use GEPA-style perturbation + gradient estimation to guide successive prompt updates.
3. Persist optimizer runs/candidates for traceability and manual review.
4. Optionally auto-create new `AgentConfig` overrides (with human approval by default).

## Scope Assumptions

- Evaluation suite machinery exists (datasets, scorers, evaluation workflow).
- Optimizer is invoked manually or via scheduled workflow; it does **not** auto-run on every config change.
- MVP focuses on prompt/body mutations; model selection and tool rewiring remain manual for now.

## Config Model

```python
class PromptMutationStrategy(str, Enum):
    SYSTEM_TEMPLATE = "system_template"
    USER_TEMPLATE = "user_template"

class GEPAOptimizerConfig(BaseModel):
    name: str
    agent_name: str
    suite_id: UUID = Field(foreign_key="eval_suite.id")
    base_config_version: int | None = None  # optional pin; defaults to latest active
    max_iterations: int = 8
    population_size: int = 4
    exploration_temperature: float = 0.7
    accept_threshold: float | None = None  # e.g., accuracy >= 0.9
    stop_no_improve: int = 3
    mutation_strategies: list[PromptMutationStrategy]
```

Stored via `ConfigurableObjectType.AGENT_OPTIMIZER` with the same versioning/activation semantics as suites.

## Data Model

```python
class AgentOptimizerRun(PlanarBaseEntity):
    agent_name: str
    suite_name: str
    optimizer_name: str
    status: Literal["pending", "running", "succeeded", "failed", "stopped"]
    base_config_version: int
    scores: dict[str, float] | None
    iterations: int
    winning_candidate_id: UUID | None
    started_at: datetime
    completed_at: datetime | None

class AgentOptimizerCandidate(PlanarBaseEntity):
    run_id: UUID = Field(foreign_key="agent_optimizer_run.id")
    candidate_hash: str  # hash of prompts/params
    system_prompt: str
    user_prompt: str
    extra_sections: dict[str, str]
    eval_run_id: UUID | None
    scores: dict[str, float] | None
    status: Literal["pending", "evaluating", "evaluated", "rejected", "accepted"]
    rationale: str | None  # GEPA justification/meta-reasoning
```

Candidates link back to the evaluation run that produced their scores for end-to-end traceability.

## Workflow

Durable workflow: `run_prompt_optimizer(optimizer_name: str)`

1. **Initialisation**
   - Fetch active `GEPAOptimizerConfig`, `AgentConfig` baseline, and target evaluation suite.
   - Seed initial population: base prompt plus perturbations produced by `mutation_strategies`.
2. **Iteration Loop** (`max_iterations`)
   1. Deduplicate candidates by `candidate_hash`. Skip ones already evaluated (reuse cached results).
   2. For remaining candidates, invoke `run_eval` with overridden prompt config.
   3. Collect scorer outputs from evaluation runs; compute aggregate score using suite scorer weights.
   4. Record candidate states and update Pareto frontier (score vs. complexity).
   5. Estimate gradients via GEPA (compare perturbations vs. score deltas).
   6. Generate new mutations informed by gradients + historical failures (reasoning/tool traces).
   7. Apply stopping rules (`accept_threshold`, `stop_no_improve`).
3. **Completion**
   - Select winning candidate; persist `AgentOptimizerRun` summary.
   - Allows user to manually promote the candidate to a new `AgentConfig` override.

## Mutation Strategies

Strategies define how the optimizer perturbs prompts. Initial set:

- `SYSTEM_TEMPLATE`: add/remove bullet instructions, adjust tone, reorder sections.
- `USER_TEMPLATE`: modify example formatting, add clarifying questions, tighten constraints.

Implementation leverages a meta-model (e.g., LLM call) that ingests:
- Baseline prompt sections.
- Evaluation trajectory snippets (failed cases, scorer feedback).
- Mutation strategy directives.

The meta-model returns candidate prompt edits and rationales used to populate `rationale`.

## Integration with Evaluation

- Optimizer piggybacks on evaluation datasets/scorers. No new scoring logic is introduced.
- Evaluation workflow must accept overrides for prompts/model parameters (without persisting config changes).
- Optimizer caches evaluation results keyed by `(candidate_hash, dataset_hash)` to avoid redundant runs.

## Automation & UI

API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /planar/v1/agents/{agent}/optimizers/` | Create/update optimizer configs |
| `POST /planar/v1/agents/{agent}/optimizers/{name}/run` | Start a run |
| `GET /planar/v1/agents/{agent}/optimizers/{name}/runs` | List past runs + summaries |
| `POST /planar/v1/agents/{agent}/optimizers/{name}/promote/{candidate_id}` | Manually promote |

UI surfaces:
- Optimizer config editor (mutation strategies, thresholds).
- Run dashboard showing iterations, best scores, candidate prompt diffs.
- Candidate review screen with evaluation links and promotion controls.

## Migration Steps

1. Add optimizer tables (`agent_optimizer_run`, `agent_optimizer_candidate`).
2. Introduce optimizer config object type and routers.
3. Extend evaluation workflow to accept ephemeral prompt overrides and expose scorer summary APIs.
4. Implement mutation engine (baseline heuristics + meta-model).
5. Surface API/UI to run and review optimizations.

## Future Enhancements

- Multi-objective optimisation (latency vs. accuracy).
- Model selection and temperature tuning.
- Integration with human-in-the-loop approval workflows.
- Automated scheduling (nightly optimisation runs).
- Sharing optimised prompts back into dataset authoring for regression tests.
