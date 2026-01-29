# Planar IO API Design

## Context

Planar workflows already expose the `Human` step for durable human input and the `message()`
helper for outbound updates. Those primitives persist JSON Schema-backed tasks and message
steps that the UI can render, but developers previously had to hand-roll the schemas and
payloads. The IO API is a facade over those building blocks that delivers an ergonomic,
[Interval-style](https://interval.com/) experience while keeping the underlying orchestration model unchanged.

## Current Capabilities

The IO package exports a singleton `IO` with the following helpers:

| Helper | Returns | Notes |
| --- | --- | --- |
| `IO.input.text(...)` | `str` | Supports defaults, placeholder text, optional multiline.
| `IO.input.boolean(...)` | `bool` | Toggle-style input with default value.
| `IO.select.single(...)` | `str` | Enumerated choice with optional default and search flag.
| `IO.select.multiple(...)` | `list[str]` | Multi-select with optional default list and max selection cap.
| `IO.entity.select(...)` | `str` or `list[str]` | Returns entity identifiers, leveraging `EntityField` metadata.
| `IO.upload.file(...)` | `PlanarFile` | Collects a durable reference to an uploaded file.
| `IO.form(...)` | async context manager | Batch multiple fields into a single human task; exposes `form.data` and typed handles.
| `IO.display.markdown(...)` | `None` | Emits a structured message step with markdown content.

All helpers are awaited inside running workflow steps. Input calls suspend execution by
creating a `HumanTask` with the generated JSON Schema; display calls stream message payloads
without pausing the workflow.

## Developer Experience

```python
from planar.io import IO
from planar.workflows import step

@step()
async def review_vendor():
    async with IO.form(
        "vendor_review",
        title="Vendor Review",
        description="Confirm onboarding details before notifying finance.",
        submit_label="Send review",
    ) as form:
        form.input.text("Notes", key="notes", multiline=True)
        form.input.boolean("Approved", key="approved", default=False)
        form.select.single(
            "Risk category",
            options=["low", "medium", "high"],
            key="risk",
        )

    review = form.data
    await IO.display.markdown(
        "## Review captured\n"
        f"Approval: {'✅' if review['approved'] else '❌'}"
    )
    await notify_operations(review)
```

## Architecture Overview

### Schema generation

- Helper methods construct `FieldSpec` objects (see `planar/io/_field_specs.py`) that bundle the
  JSON Schema type, `x-planar` metadata, and a post-processing function for the raw result.
- When an input call executes, the helper builds a transient Pydantic model via `create_model`
  using the field spec(s). The resulting JSON Schema is attached to the `HumanTask.output_schema`.
- `_build_field_extra` standardises the `x-planar` envelope, ensuring each field declares a
  widget `component` plus a `props` dict that the presentation layer consumes. The detailed
  contract is captured in `docs/design/io_presentation_contract.md` and enforced by
  `tests/io/test_io_contract.py`.

### Form submission

- `IO.form()` returns a `FormBuilder` context manager. Field helper invocations enqueue
  `FieldSpec`s without hitting the datastore.
- On context exit, the builder materialises a composite Pydantic model whose schema collapses
  the queued fields. A single `Human` task is emitted, and the workflow resumes once the form is
  completed. Submitted data is stored both as a raw `dict` and as the validated Pydantic model to
  support typed accessors.

### Messaging

- Display helpers wrap Pydantic message models. Currently `MarkdownMessage` is implemented; new
  message types should follow the same pattern (`planar_type` discriminator plus structured
  payload) so the UI can route them consistently.

## Data Contract Highlights

- Human task schemas always use JSON Schema draft-2020-12 and decorate each property with
  `x-planar` metadata to describe rendering requirements.
- Entity selectors layer in `x-planar-presentation` data via `EntityField` so the frontend can
  retrieve display names. (should be moved to x-planar for consistency in the future)
- Message steps carry `planar-type`ed payloads—for now just `io.display.markdown`—and are retrieved
  alongside workflow step metadata for ordering.
- Default values provided to IO helpers are mirrored into `HumanTask.suggested_data` so the UI can
  prefill forms while keeping fields editable.
- The contract document and structural tests should be referenced when adding new widgets or
  tweaking existing props.

## Validation & Error Handling

- Input validation is handled automatically by the generated Pydantic models. Invalid defaults
  (e.g., options not present in a select) are rejected server-side when constructing the schema.
- QOL features such as custom validators or optional timeouts can be layered on top by passing
  through to the underlying `Human` step in future iterations.

## Roadmap & Follow-ups

- **Display widgets:** Implement table/json/timeline renderers, each with explicit payload
  contracts, before surfacing them in the public API.
- **Numeric inputs & confirm dialogs:** Extend the helper set with additional input primitives,
  ensuring the contract and tests are updated in lockstep.
- **Rich form features:** Conditional reveals, grouping metadata, and client-side validation hints
  remain future work and should reuse the `x-planar` envelope rather than introducing additional
  database columns.
