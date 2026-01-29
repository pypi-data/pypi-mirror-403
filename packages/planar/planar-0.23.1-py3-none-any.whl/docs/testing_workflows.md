# Testing Workflows

## Basic Setup

Create an `app` fixture for your test file:

```python
import pytest
from planar import PlanarApp, sqlite_config

@pytest.fixture(name="app")
def app_fixture(tmp_db_path: str):
    app = PlanarApp(
        config=sqlite_config(tmp_db_path),
        title="Test App",
        description="Testing",
    )
    yield app
```

## Important: Avoid Internal Orchestrator APIs

**Do not use internal orchestrator APIs like `execute()` in tests that use `PlanarTestClient` or `PlanarApp` fixtures.** These fixtures run a full orchestrator that automatically calls `execute()` on started workflows. Using `execute()` directly will cause conflicts and unpredictable behavior.

```python
# WRONG - Never do this in tests with PlanarApp/PlanarTestClient
async def test_bad_example(app: PlanarApp, client: PlanarTestClient):
    wf = await my_workflow.start()
    result = await execute(wf)  # ❌ Don't call execute() directly!

# CORRECT - Use the orchestrator's wait_for_completion
async def test_good_example(app: PlanarApp, client: PlanarTestClient):
    resp = await client.post("/planar/v1/workflows/my_workflow/start", json={})
    workflow_id = UUID(resp.json()["id"])
    result = await app.orchestrator.wait_for_completion(workflow_id)  # ✓ Correct
```

## Simple Workflow Test

```python
async def test_simple_workflow(
    client: PlanarTestClient,
    app: PlanarApp
):
    @step()
    async def process_data(value: int):
        return value * 2

    @workflow()
    async def my_workflow(input_value: int):
        result = await process_data(input_value)
        return result

    app.register_workflow(my_workflow)

    resp = await client.post(
        "/planar/v1/workflows/my_workflow/start",
        json={"input_value": 5}
    )
    workflow_id = UUID(resp.json()["id"])

    result = await app.orchestrator.wait_for_completion(workflow_id)
    assert result == 10
```

## Using asyncio.Event for Coordination

```python
async def test_workflow_coordination(
    client: PlanarTestClient,
    app: PlanarApp
):
    signal = asyncio.Event()

    @step()
    async def long_step():
        return "done"

    @workflow()
    async def blocking_workflow():
        await signal.wait()  # Block until signal is set
        result = await long_step()
        return result

    app.register_workflow(blocking_workflow)

    resp = await client.post(
        "/planar/v1/workflows/blocking_workflow/start",
        json={}
    )
    workflow_id = UUID(resp.json()["id"])

    # Do something while workflow is blocked
    # ...

    signal.set()  # Unblock the workflow
    result = await app.orchestrator.wait_for_completion(workflow_id)
    assert result == "done"
```

## Using WorkflowObserver

```python
async def test_with_observer(
    client: PlanarTestClient,
    app: PlanarApp,
    observer: WorkflowObserver,
):
    @step()
    async def quick_step():
        return "step_done"

    @workflow()
    async def observable_workflow():
        await quick_step()
        await suspend(interval=timedelta(seconds=60))
        return "done"

    app.register_workflow(observable_workflow)

    resp = await client.post(
        "/planar/v1/workflows/observable_workflow/start",
        json={}
    )
    workflow_id = UUID(resp.json()["id"])

    # Wait for workflow to suspend
    await observer.wait(Notification.WORKFLOW_SUSPENDED, workflow_id)

    # Verify suspended state
    async with session.begin_read():
        wf = await session.get(Workflow, workflow_id)
        assert wf
    assert wf.status == WorkflowStatus.PENDING
    assert wf.wakeup_at is not None
```

## Verifying Database State

```python
async def test_workflow_state(
    client: PlanarTestClient,
    session: PlanarSession,
    app: PlanarApp
):
    @workflow()
    async def simple_workflow():
        return "completed"

    app.register_workflow(simple_workflow)

    resp = await client.post(
        "/planar/v1/workflows/simple_workflow/start",
        json={}
    )
    workflow_id = UUID(resp.json()["id"])

    await app.orchestrator.wait_for_completion(workflow_id)

    # Verify database state
    async with session.begin_read():
        wf = await session.get(Workflow, workflow_id)
        assert wf
    assert wf.status == WorkflowStatus.SUCCEEDED
```

## Key Points

- Always register workflows with `app.register_workflow()`
- Use `client.post()` to start workflows via the API
- Use `app.orchestrator.wait_for_completion()` to wait for results
- **Never call `execute()` directly in tests with `PlanarApp` or `PlanarTestClient` fixtures**
- Use `asyncio.Event()` to coordinate workflow execution timing
- Use `observer.wait()` to wait for specific workflow events
- Verify database state with `session.begin_read()` and `session.get()`
