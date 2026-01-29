from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from planar.security.auth_context import get_current_principal
from planar.security.authorization import (
    GroupAction,
    GroupResource,
    UserAction,
    UserResource,
    validate_authorization_for,
)
from planar.session import get_session
from planar.user.models import IDPGroup, IDPUser


class User(BaseModel):
    id: UUID
    external_id: str
    email: str
    first_name: str | None
    last_name: str | None

    group_ids: list[UUID]

    @classmethod
    def from_(cls, user: IDPUser):
        return User(
            id=user.id,
            external_id=user.external_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            group_ids=[g.id for g in user.groups],
        )


class Group(BaseModel):
    id: UUID
    external_id: str
    name: str

    user_ids: list[UUID]

    @classmethod
    def from_(cls, group: IDPGroup):
        return Group(
            id=group.id,
            external_id=group.external_id,
            name=group.name,
            user_ids=[u.id for u in group.users],
        )


def create_user_router() -> APIRouter:
    router = APIRouter(tags=["Users"])

    @router.get("/", response_model=list[User])
    async def users():
        """All active users."""
        validate_authorization_for(UserResource(), UserAction.USER_LIST)

        session = get_session()
        result = await session.exec(
            select(IDPUser)
            .where(col(IDPUser.disabled_at).is_(None))
            .options(selectinload(IDPUser.groups))  # pyright: ignore[reportArgumentType]
        )
        users = result.all()

        return [User.from_(user) for user in users]

    @router.get("/current-user", response_model=User)
    async def current_user():
        """Current authenticated user."""

        principal = get_current_principal()
        if not principal:
            raise HTTPException(status_code=401, detail="not authenticated")

        email = principal.user_email
        if not email:
            raise HTTPException(status_code=404, detail="active user has no email")

        session = get_session()
        result = await session.exec(
            select(IDPUser)
            .where(col(IDPUser.email) == email, col(IDPUser.disabled_at).is_(None))
            .options(selectinload(IDPUser.groups))  # pyright: ignore[reportArgumentType]
        )
        user = result.one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail=f"no user for {email}")

        validate_authorization_for(
            UserResource.from_user(user),
            UserAction.USER_VIEW_DETAILS,
        )

        return User.from_(user)

    @router.get("/{user_id}", response_model=User)
    async def user(user_id: UUID):
        """User by ID."""
        session = get_session()
        result = await session.exec(
            select(IDPUser)
            .where(col(IDPUser.id) == user_id, col(IDPUser.disabled_at).is_(None))
            .options(selectinload(IDPUser.groups))  # pyright: ignore[reportArgumentType]
        )
        user = result.one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="user not found")

        validate_authorization_for(
            UserResource.from_user(user),
            UserAction.USER_VIEW_DETAILS,
        )

        return User.from_(user)

    return router


def create_group_router() -> APIRouter:
    router = APIRouter(tags=["Groups"])

    @router.get("/", response_model=list[Group])
    async def groups():
        """All active groups."""
        validate_authorization_for(GroupResource(), GroupAction.GROUP_LIST)

        session = get_session()
        result = await session.exec(
            select(IDPGroup)
            .where(col(IDPGroup.disabled_at).is_(None))
            .options(selectinload(IDPGroup.users))  # pyright: ignore[reportArgumentType]
        )
        groups = result.all()

        return [Group.from_(group) for group in groups]

    @router.get("/{group_id}", response_model=Group)
    async def group(group_id: UUID):
        """Group by ID."""
        session = get_session()
        result = await session.exec(
            select(IDPGroup)
            .where(col(IDPGroup.id) == group_id, col(IDPGroup.disabled_at).is_(None))
            .options(selectinload(IDPGroup.users))  # pyright: ignore[reportArgumentType]
        )
        group = result.one_or_none()

        if not group:
            raise HTTPException(status_code=404, detail="group not found")

        validate_authorization_for(
            GroupResource.from_group(group), GroupAction.GROUP_VIEW_DETAILS
        )

        return Group.from_(group)

    return router
