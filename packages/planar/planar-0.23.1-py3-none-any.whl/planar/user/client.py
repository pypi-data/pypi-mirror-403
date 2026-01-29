import httpx

from planar.logging import get_logger
from planar.session import get_config
from planar.user.models import DirectoryGroup, DirectoryUser

logger = get_logger(__name__)


async def query_groups() -> list[DirectoryGroup]:
    config = get_config()

    if not config.dir_sync:
        raise ValueError("dir_sync configuration is required for directory sync")

    async with httpx.AsyncClient(base_url=config.dir_sync.coplane_api_url) as client:
        response = await client.get(
            "/v1/dir_sync/groups/",
            headers={
                "Authorization": f"Bearer {config.dir_sync.coplane_api_token.get_secret_value()}"
            },
        )
        response = response.raise_for_status()
        return [DirectoryGroup.model_validate(i) for i in response.json()]


async def query_users() -> list[DirectoryUser]:
    config = get_config()

    if not config.dir_sync:
        raise ValueError("user_sync configuration is required for directory sync")

    async with httpx.AsyncClient(base_url=config.dir_sync.coplane_api_url) as client:
        response = await client.get(
            "/v1/dir_sync/users/",
            headers={
                "Authorization": f"Bearer {config.dir_sync.coplane_api_token.get_secret_value()}"
            },
        )
        response = response.raise_for_status()
        return [DirectoryUser.model_validate(i) for i in response.json()]
