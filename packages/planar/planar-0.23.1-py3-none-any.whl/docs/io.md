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
