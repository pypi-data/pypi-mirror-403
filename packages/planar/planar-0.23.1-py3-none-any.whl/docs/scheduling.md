# Workflow Scheduling Guide

## Overview

Planar provides built-in support for scheduling workflows to run automatically using cron expressions. This allows you to create workflows that execute at specific times or intervals without manual intervention.

## Core Concepts

### Cron Expressions

Cron expressions are a standard way to define time-based schedules. Planar uses the 5-field cron format:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, SUN-SAT)
│ │ │ └───── Month (1-12, JAN-DEC)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

Common examples:
- `* * * * *` - Every minute
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Every hour on the hour
- `0 9 * * *` - Daily at 9:00 AM
- `0 0 * * MON` - Every Monday at midnight
- `30 2 15 * *` - On the 15th of every month at 2:30 AM

### Catch-up Window

The catch-up window defines how far back the scheduler will look for missed runs. If your application was down or the scheduler was paused, workflows scheduled during that time will be caught up when the scheduler resumes, but only if they fall within the window period.

The effective window is determined by the `window` and `start_time` parameters:
- Default (no parameters): 50 seconds
- With `window` only: Uses the specified window
- With `start_time` only: Window is `now - start_time`
- With both: Uses `min(window, now - start_time)`

For example, with `window=timedelta(hours=2)`, if your application was down for 3 hours, only the runs from the last 2 hours will be scheduled when it comes back up.

## Using the @cron Decorator

The `@cron` decorator is used to schedule workflows. It must be applied to functions already decorated with `@workflow()`.

**Important**: The decorator validates that `args` and `kwargs` match the workflow function's signature at registration time. This helps catch configuration errors early.

### Basic Usage

```python
from datetime import timedelta
from planar.workflows import cron, workflow

@cron("*/5 * * * *")  # Run every 5 minutes
@workflow()
async def my_scheduled_workflow():
    # Workflow implementation
    pass
```

### With Arguments

Pass arguments to scheduled workflow runs using the `args` and `kwargs` parameters:

```python
@cron("0 * * * *", args=(100,), kwargs={"mode": "production"})
@workflow()
async def process_batch(batch_size: int, mode: str = "test"):
    # Process batch_size items in the specified mode
    pass
```

### Configuring the Catch-up Window

The catch-up window determines how far back the scheduler will look for missed runs. The actual window used depends on the combination of the `window` and `start_time` parameters:

1. **No window, no start_time**: Defaults to 50 seconds
2. **Window only**: Uses the specified window
3. **Start_time only**: Window is calculated as `now - start_time`
4. **Both window and start_time**: Uses `min(window, now - start_time)`

```python
# Default: 50-second catch-up window
@cron("*/10 * * * *")
@workflow()
async def quick_workflow():
    pass

# Explicit window: catch up runs missed in the last 30 minutes
@cron("*/10 * * * *", window=timedelta(minutes=30))
@workflow()
async def time_sensitive_workflow():
    pass

# Start time only: catch up all runs since Jan 1, 2025
@cron("0 0 * * *", start_time=datetime(2025, 1, 1))
@workflow()
async def historical_workflow():
    pass

# Both specified: uses the smaller of the two
@cron("0 * * * *",
      window=timedelta(days=7),
      start_time=datetime(2025, 1, 1))
@workflow()
async def bounded_workflow():
    # If running on Jan 3, window is 2 days (now - start_time)
    # If running on Jan 10, window is 7 days (explicit window)
    pass
```

### Scheduling with Start Times

The `start_time` parameter allows you to control when a workflow should begin its schedule. This is useful for:
- Delaying the start of scheduled workflows
- Coordinating workflows to start at specific dates
- Testing schedules with future start times

```python
from datetime import datetime, timezone

# Start scheduling on a specific date
@cron("0 9 * * MON", start_time=datetime(2025, 2, 1))
@workflow()
async def weekly_report():
    # Will only start scheduling after February 1, 2025
    pass

# Timezone-aware start times are automatically converted to UTC
pst = timezone(timedelta(hours=-8))
@cron("0 12 * * *", start_time=datetime(2025, 1, 15, 12, 0, tzinfo=pst))
@workflow()
async def daily_task():
    # Starts at noon PST on Jan 15, 2025 (20:00 UTC)
    pass
```

### Multiple Schedules

You can apply multiple `@cron` decorators to the same workflow to create different schedules with different parameters:

```python
@cron("*/15 * * * *", args=(50,))      # Every 15 minutes, process 50 items
@cron("0 * * * *", args=(500,))        # Every hour, process 500 items
@cron("0 0 * * *", args=(10000,))      # Daily at midnight, process 10000 items
@workflow()
async def adaptive_processor(batch_size: int):
    # Process different batch sizes at different frequencies
    pass
```

## How Scheduling Works

### Scheduling Loop

The Planar scheduler runs a background loop that:
1. Checks all registered cron schedules every 30 seconds
2. Calculates which runs should have occurred since the last check
3. Creates workflow entries for any missed runs within the catch-up window
4. Ensures idempotency - each scheduled time is only created once

### Idempotency

Each scheduled run has a unique idempotency key composed of:
- The cron expression (normalized)
- The workflow function name
- The arguments and keyword arguments
- The scheduled run time

This ensures that even if the scheduling loop runs multiple times, each specific run is only created once.

### Workflow Execution

Scheduled workflows are created with:
- Status: `PENDING`
- `idempotency_key`: Unique key to prevent duplicate scheduling (contains the scheduled timestamp)
- `scheduled_time`: The scheduled execution time for the workflow

The Planar orchestrator picks up these pending workflows and executes them like any other workflow.

## Complete Example

```python
from datetime import timedelta
from planar.app import PlanarApp
from planar.workflows import cron, step, workflow

@step()
async def fetch_metrics() -> dict:
    """Fetch system metrics."""
    # Implementation to fetch metrics
    return {"cpu": 45.2, "memory": 67.8}

@step()
async def analyze_metrics(metrics: dict) -> dict:
    """Analyze fetched metrics."""
    alerts = []
    if metrics["cpu"] > 80:
        alerts.append("High CPU usage")
    if metrics["memory"] > 90:
        alerts.append("High memory usage")
    return {"metrics": metrics, "alerts": alerts}

@step()
async def send_report(analysis: dict):
    """Send metrics report."""
    print(f"Metrics: {analysis['metrics']}")
    if analysis["alerts"]:
        print(f"ALERTS: {', '.join(analysis['alerts'])}")

# Run every 5 minutes with a 10-minute catch-up window
@cron("*/5 * * * *", window=timedelta(minutes=10))
@workflow()
async def monitor_system():
    """System monitoring workflow that runs every 5 minutes."""
    metrics = await fetch_metrics()
    analysis = await analyze_metrics(metrics)
    await send_report(analysis)
    return analysis

app = PlanarApp(
    title="System Monitor",
    description="Automated system monitoring with scheduled workflows"
).register_workflow(monitor_system)
```

## Best Practices

### 1. Choose Appropriate Windows

- **Short windows** (seconds/minutes) for time-sensitive workflows that lose relevance if delayed
- **Medium windows** (hours/days) for regular batch processing workflows
- **Long windows** (days/weeks) for critical batch jobs that must not be skipped
- **Default window** (50 seconds) is very short - explicitly set a window for production workflows

### 2. Design Idempotent Workflows

Since catch-up may run multiple workflow instances in quick succession, ensure your workflows are idempotent:

```python
@cron("0 * * * *", window=timedelta(hours=24))
@workflow()
async def hourly_aggregation():
    # Use the scheduled_time to determine which hour to process
    # This ensures each hour is processed exactly once
    pass
```

### 3. Monitor Scheduled Workflows

Track your scheduled workflows to ensure they're running as expected:

```python
from planar.workflows.models import Workflow
from sqlmodel import select

# Query scheduled workflows
scheduled = await session.exec(
    select(Workflow).where(
        Workflow.scheduled_time.is_not(None)
    )
)
```

### 4. Handle Time Zones

All scheduling operations use timezone-naive UTC datetimes internally:

- **Cron expressions**: Evaluated against timezone-naive UTC datetimes.
- **start_time**: Timezone-aware datetimes are converted to UTC and stripped of timezone info
- **scheduled_time**: Stored as timezone-naive UTC in the database
- **Scheduling calculations**: All performed in timezone-naive UTC space

```python
from datetime import datetime, timezone, timedelta

# This runs at midnight UTC (timezone-naive evaluation)
@cron("0 0 * * *")
@workflow()
async def daily_task():
    pass

# Timezone-aware start_time is converted to timezone-naive UTC
eastern = timezone(timedelta(hours=-5))
@cron("0 8 * * *", start_time=datetime(2025, 1, 1, 8, 0, tzinfo=eastern))
@workflow()
async def morning_task():
    # start_time becomes datetime(2025, 1, 1, 13, 0) (no tzinfo)
    # Cron "0 8 * * *" will run at 08:00 UTC
    pass
```

**Important**: Since all times are normalized to UTC, make sure your cron expressions account for this. A workflow scheduled for "0 9 * * *" will run at 9:00 AM UTC, regardless of your local timezone. To simplify things, never use timezone-aware datetime objects and things will just work.
  
### 5. Test Your Schedules

Use the cron expression normalizer to verify your expressions:

```python
from planar.cron_expression_normalizer import normalize_cron

# Test that your expression is valid and see its normalized form
expr = "*/5 * * * MON-FRI"
normalized = normalize_cron(expr)  # "0,5,10,15,20,25,30,35,40,45,50,55 * * * 1-5"
```

## Advanced Topics

### Expression Normalization

Planar normalizes all cron expressions to ensure consistent scheduling and idempotency. This means:
- `MON-FRI` becomes `1-5`
- `*/5` expands to `0,5,10,15,20,25,30,35,40,45,50,55`
- Ranges are compressed: `1,2,3,5` becomes `1-3,5`

### Database Schema

Scheduled workflows add two fields to the workflow table:
- `idempotency_key`: Unique key preventing duplicate scheduling (format: `{timestamp}:{hash}`)
- `scheduled_time`: The scheduled execution time for the workflow

### Integration with Orchestrator

The scheduling system integrates seamlessly with the Planar orchestrator:
1. Scheduler creates workflow entries with `PENDING` status
2. Orchestrator picks up pending workflows based on standard polling logic
3. Workflows execute normally, with access to their scheduled time if needed

## Troubleshooting

### Workflows Not Scheduling

1. **Check registration**: Ensure the workflow is registered with the app
   ```python
   app.register_workflow(my_scheduled_workflow)
   ```

2. **Verify cron expression**: Test your expression is valid
   ```python
   from croniter import croniter
   croniter.is_valid("your expression here")
   ```

3. **Check the window**: Ensure your window is large enough to catch missed runs

### Too Many Catch-up Runs

If you're getting too many historical runs after downtime:
- Reduce the `window` parameter
- Consider adding logic to skip outdated runs in your workflow

### Debugging Schedules

Enable debug logging to see scheduling decisions:

```python
import logging
logging.getLogger("planar.workflows.scheduling").setLevel(logging.DEBUG)
```

This will show:
- When schedules are synchronized
- Which workflows are being scheduled
- The idempotency keys being used
