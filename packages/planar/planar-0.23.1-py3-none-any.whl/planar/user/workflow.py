from planar.config import load_environment_aware_config
from planar.logging import get_logger
from planar.user import client
from planar.user.sync import sync_users_and_groups
from planar.workflows.decorators import workflow
from planar.workflows.scheduling import cron

logger = get_logger(__name__)


DEFAULT_SCHEDULE = "0 * * * *"  # hourly


@workflow(name="planar.user.sync_users")
async def sync_users() -> None:
    """Sync users and groups from the CoPlane API to the DB."""
    users = await client.query_users()
    groups = await client.query_groups()

    await sync_users_and_groups(users, groups)


def schedule_user_sync():
    """Configure the user sync workflow schedule from config, if provided."""
    config = load_environment_aware_config()

    if not config.dir_sync:
        logger.debug("user sync not configured, skipping schedule")
        return

    cron_expr = config.dir_sync.cron_schedule or DEFAULT_SCHEDULE

    # We call `cron` here rather than as a decorator because we need to have
    # context of the PlanarConfig to support overriding the default schedule.
    cron(cron_expr)(sync_users)

    logger.info(
        "user sync workflow schedule configured",
        function_name=sync_users.function_name,
        cron_expr=cron_expr,
    )

    return sync_users
