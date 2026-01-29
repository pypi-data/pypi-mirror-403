# Planar IO Presentation Contract

## Purpose

This document defines the data contract between the Planar IO workflow helpers and the
presentation layer (web console or other runtimes). Every IO call produces either a **Human
Task schema** (for user input) or a **Message payload** (for display-only events). The frontend
must implement the parsing rules below and may rely on them remaining stable. Likewise,
backend changes to these structures must keep this contract or version it explicitly.

## Human Task Schemas

Each IO input call (single prompts and grouped forms) generates a Pydantic model whose JSON
Schema becomes the `HumanTask.output_schema`. Schemas use draft-2020-12 and follow these
invariants:

- Root schema `type` is `"object"` with `properties` containing field definitions. The
  `required` array lists the property keys whose JSON Schema default is `...` (i.e., no default
  supplied by IO). When every field carries a default, Pydantic omits the array entirely.
- Every field definition includes `title` (user label) and `description` (help text when
  provided).
- Planar-specific rendering metadata lives under the `x-planar` extension key. The extension
  payload always includes:
  - `component`: a stable string identifier for the UI widget.
  - `props`: JSON-serializable metadata consumed by the frontend widget.
- Entity selectors also emit an `x-planar-presentation` key (see **Entity Select**).

### Single-field Prompts

`IO.input.*`, `IO.select.*`, `IO.entity.select`, and `IO.upload.file` emit a schema with a
single property named `value` unless otherwise noted. Every widget exposes a fixed component
identifier plus required/optional props as summarised below.

| Component | Schema shape | Required props | Optional props |
| --- | --- | --- | --- |
| `io.input.text` | `{ "type": "string" }` | `label`, `multiline` | `placeholder`, `help_text`, `default` |
| `io.input.boolean` | `{ "type": "boolean" }` | `label`, `default` | `help_text` |
| `io.select.single` | `{ "type": "string", "enum": [...] }` | `label`, `options`, `search` | `help_text`, `default` |
| `io.select.multiple` | `{ "type": "array", "items": { "type": "string", "enum": [...] } }` | `label`, `options`, `search` | `help_text`, `default`, `max_selections` |
| `io.entity.select` | single:`{ "type": "string" }` / multi:`{ "type": "array", "items": { "type": "string" } }` | `label`, `entity`, `multiple` | `display_field`, `help_text`, `default` |
| `io.upload.file` | PlanarFile object (`id`, `filename`, `content_type`, `size`) | `label` | `accept`, `max_size_mb`, `help_text` |

Additional notes:

- Optional props are omitted when not supplied.
- The `options` list preserves the order provided by the workflow.
- `select.multiple` defaults are lists. Fields remain required even when defaults are present.
- `entity.select` adds `x-planar-presentation`: `{ "inputType": "entity-select", "entity":
  <ModelName>, "display_field": <field-or-null> }`.
- `upload.file` sets JSON Schema `default` to ellipsis, forcing user input.
- When a default is supplied, the same value is stored in `HumanTask.suggested_data` so the UI
  can prefill the form while still allowing edits.

### Grouped Forms (`IO.form`)

Forms aggregate multiple `FieldSpec`s into a single Human Task:

- Root schema `json_schema_extra`: `{ "x-planar": { "component": "io.form", "props": {
  "submit_label": <label> } } }`.
- All field schemas appear under `properties` with the same definitions as single-field prompts
  (component, props, enum/items, etc.). Keys are derived from explicit `key` arguments or
  slugified labels; uniqueness is enforced server-side.
- The frontend must treat the root `x-planar.component` as the signal that the schema
  represents a grouped form. Submission returns an object mapping field keys to values typed
  according to the individual field schemas.
- Each field handle remains required when its schema default is ellipsis. Defaults are passed
  through as JSON Schema `default` values and duplicated inside `x-planar.props.default` for
  convenience.

### Schema Validation Guarantees

The IO backend enforces a number of early validations. The frontend can rely on them to
simplify rendering logic:

- Select option arrays are never empty and contain no duplicates.
- Default selections (single/multiple) are always valid members of the options set; multiple
  defaults respect `max_selections` and uniqueness.
- Entity defaults are either a string identifier, a list of identifiers, or `null`. Planar
  entities without IDs are rejected.
- Upload `max_size_mb`, when present, is a positive integer.

## Message Payloads

Display helpers emit workflow `message` steps with planar-typed payloads. Payloads are always
Pydantic models serialized to JSON-friendly dicts.

### Markdown Display

`IO.display.markdown(markdown_text)` produces exactly one message step argument:

```json
{
  "planar_type": "io.display.markdown",
  "markdown": "# Heading\nBody"
}
```

Contract expectations:

- `planar_type` always begins with `"io.display."` and uniquely identifies the renderer.
- Additional message helpers must follow the same pattern: a lowercase action verb and a
  namespaced `planar_type` value (e.g., `io.display.table`).
- The payload is a flat JSON object; complex variants should nest additional objects instead of
  changing the top-level shape.
- Frontend consumers should ignore unknown keys but must error (for observability) when a
  required key for a known `planar_type` is missing.

### Examples

**Text input prompt**

```json
{
  "type": "object",
  "properties": {
    "value": {
      "type": "string",
      "title": "Enter your name",
      "description": "We will display this on your profile.",
      "x-planar": {
        "component": "io.input.text",
        "props": {
          "label": "Enter your name",
          "multiline": false,
          "placeholder": "e.g. Ada Lovelace"
        }
      }
    }
  },
  "required": ["value"]
}
```

**Form root with mixed fields**

```json
{
  "type": "object",
  "properties": {
    "notes": {
      "type": "string",
      "x-planar": { "component": "io.input.text", "props": { "label": "Notes", "multiline": true } }
    },
    "approved": {
      "type": "boolean",
      "x-planar": { "component": "io.input.boolean", "props": { "label": "Approved", "default": false } }
    }
  },
  "x-planar": {
    "component": "io.form",
    "props": { "submit_label": "Send review" }
  }
}
```

## Versioning & Extensibility

- New widgets must introduce distinct `component` identifiers and document the expected
  `props` contract before rollout.
- The `x-planar` envelope is reserved for backend-driven hints; frontend clients should
  round-trip unknown `props` keys to allow forward compatibility.
- When evolving an existing widget, prefer adding optional `props` keys. Removing or renaming a
  key requires a coordinated version bump.
- Additional message types should mirror the existing `planar_type` and payload conventions,
  with the `IO.display` namespace acting as the canonical registry.
