from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel
from pydantic import Field as PydanticField
from sqlalchemy import Index, and_, event, insert, inspect
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper
from sqlalchemy.orm.properties import ColumnProperty
from sqlmodel import Column, Field, Relationship, SQLModel

from planar.db import PlanarInternalBase
from planar.modeling.mixins.timestamp import TimestampMixin
from planar.modeling.mixins.uuid_primary_key import UUIDPrimaryKeyMixin
from planar.object_config.models import PydanticType
from planar.utils import one_or_raise


# API outputs
class DirectoryUser(BaseModel):
    sync_id: str
    idp_id: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    created_at: str
    updated_at: str


class UserLink(BaseModel):
    sync_id: str


class DirectoryGroup(BaseModel):
    sync_id: str
    name: str
    created_at: str
    updated_at: str
    members: list[UserLink]


class UserGroupMembership(PlanarInternalBase, TimestampMixin, table=True):
    user_id: UUID = Field(primary_key=True, foreign_key="idp_user.id")
    group_id: UUID = Field(primary_key=True, foreign_key="idp_group.id")


# `User` conflicts w/ the table in the approval workflow
class IDPUser(PlanarInternalBase, TimestampMixin, table=True):
    __table_args__: tuple[Index, ...] = (
        Index("ix_active_users", "id", postgresql_where="disabled_at IS NULL"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    external_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)

    external_created_at: str
    external_updated_at: str

    disabled_at: datetime | None = Field(default=None)

    groups: list["IDPGroup"] = Relationship(
        back_populates="users",
        link_model=UserGroupMembership,
        sa_relationship_kwargs={
            "primaryjoin": lambda: IDPUser.id == UserGroupMembership.user_id,
            "secondaryjoin": lambda: and_(
                # pyright gets confused by these sqlalchemy expressions
                IDPGroup.id == UserGroupMembership.group_id,  # pyright: ignore[reportArgumentType]
                IDPGroup.disabled_at.is_(None),  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
            ),
        },
    )

    @classmethod
    def from_directory(cls, user: DirectoryUser):
        if not user.email:
            raise ValueError("Cannot create user without email")

        return cls(
            external_id=user.sync_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            external_created_at=user.created_at,
            external_updated_at=user.updated_at,
            disabled_at=None,
        )


class IDPGroup(PlanarInternalBase, TimestampMixin, table=True):
    __table_args__: tuple[Index, ...] = (
        Index("ix_active_groups", "id", postgresql_where="disabled_at IS NULL"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    external_id: str = Field(unique=True, index=True)
    name: str

    external_created_at: str
    external_updated_at: str

    num_members: int
    disabled_at: datetime | None = Field(default=None)

    def empty_or_disabled(self) -> bool:
        return self.num_members == 0 or self.disabled_at is not None

    users: list[IDPUser] = Relationship(
        back_populates="groups",
        link_model=UserGroupMembership,
        sa_relationship_kwargs={
            "primaryjoin": lambda: IDPGroup.id == UserGroupMembership.group_id,
            "secondaryjoin": lambda: and_(
                # pyright gets confused by these sqlalchemy expressions
                IDPUser.id == UserGroupMembership.user_id,  # pyright: ignore[reportArgumentType]
                IDPUser.disabled_at.is_(None),  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
            ),
            "viewonly": True,
            "overlaps": "users",
        },
    )
    # Used to sync user state in `_sync_members`.
    users_including_disabled: list[IDPUser] = Relationship(
        link_model=UserGroupMembership,
        sa_relationship_kwargs={"overlaps": "users,groups"},
    )

    @classmethod
    def from_directory(cls, group: DirectoryGroup):
        if not group.name:
            raise ValueError("Cannot create group without name")

        return cls(
            external_id=group.sync_id,
            name=group.name,
            external_created_at=group.created_at,
            external_updated_at=group.updated_at,
            num_members=len(group.members),
        )


class UserCreated(BaseModel):
    type: Literal["user_created"] = "user_created"
    id: UUID


class UserReenabled(BaseModel):
    type: Literal["user_reenabled"] = "user_reenabled"
    id: UUID


class UserRemoved(BaseModel):
    type: Literal["user_removed"] = "user_removed"
    id: UUID


class GroupCreated(BaseModel):
    type: Literal["group_created"] = "group_created"
    id: UUID


class GroupReenabled(BaseModel):
    type: Literal["group_reenabled"] = "group_reenabled"
    id: UUID


class GroupRemoved(BaseModel):
    type: Literal["group_removed"] = "group_removed"
    id: UUID


class UserAddedToGroup(BaseModel):
    type: Literal["user_added_to_group"] = "user_added_to_group"
    user_id: UUID
    group_id: UUID


class UserRemovedFromGroup(BaseModel):
    type: Literal["user_removed_from_group"] = "user_removed_from_group"
    user_id: UUID
    group_id: UUID


IDPChange = Annotated[
    UserCreated
    | UserReenabled
    | UserRemoved
    | GroupCreated
    | GroupReenabled
    | GroupRemoved
    | UserAddedToGroup
    | UserRemovedFromGroup,
    PydanticField(discriminator="type"),
]


class IDPChangelog(PlanarInternalBase, TimestampMixin, UUIDPrimaryKeyMixin, table=True):
    # SQLModel doesn't support non-optional unions, so we use | None with nullable=False
    change: IDPChange | None = Field(
        sa_column=Column(PydanticType(IDPChange), nullable=False)
    )


def _dump_first_layer(model: BaseModel):
    """Like `.model_dump()`, but leaves attributes as pydantic class instances."""
    return {k: getattr(model, k) for k in type(model).model_fields}


# Event listeners
@event.listens_for(IDPUser, "after_insert")
def user_created(
    mapper: Mapper[IDPUser], connection: Connection, target: IDPUser
) -> None:
    change = UserCreated(id=target.id)
    changelog = IDPChangelog(change=change)
    _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])


def _null_to_nonnull(target: SQLModel, col: str) -> bool:
    """`col` went from null -> non-null."""

    hist = getattr(inspect(target).attrs, col).history  # pyright: ignore[reportOptionalMemberAccess]
    changed_and_nonnull = hist.has_changes() and getattr(target, col) is not None
    # `col` went from null -> non-null
    return changed_and_nonnull and (not hist.deleted or None in hist.deleted)


def _nonnull_to_null(target: SQLModel, col: str) -> bool:
    """`col` went from non-null -> null."""

    hist = getattr(inspect(target).attrs, col).history  # pyright: ignore[reportOptionalMemberAccess]
    changed_and_null = hist.has_changes() and getattr(target, col) is None
    # `col` went from non-null -> null
    return changed_and_null and hist.deleted and None not in hist.deleted


class ValueChanged(BaseModel):
    old: Any | None
    new: Any | None


def _value_changed(target: SQLModel, col: str) -> ValueChanged | None:
    """Return the old and new value for a ColumnProperty iff it changed."""

    inspector = inspect(target)
    attr_state = getattr(inspector.attrs, col)  # pyright: ignore[reportOptionalMemberAccess]
    hist = attr_state.history

    if not hist.has_changes():
        return

    mapper_prop = inspector.mapper.get_property(col)  # pyright: ignore[reportOptionalMemberAccess]
    if not isinstance(mapper_prop, ColumnProperty):
        raise Exception("`_value_changed` should only be called on columns")

    return ValueChanged(
        old=one_or_raise(hist.deleted) if hist.deleted else None,
        new=getattr(target, col),
    )


@event.listens_for(IDPUser, "after_update")
def user_enabled_or_disabled(
    mapper: Mapper[IDPUser], connection: Connection, target: IDPUser
) -> None:
    if _null_to_nonnull(target, "disabled_at"):
        change = UserRemoved(id=target.id)
        changelog = IDPChangelog(change=change)
        _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])
    if _nonnull_to_null(target, "disabled_at"):
        change = UserReenabled(id=target.id)
        changelog = IDPChangelog(change=change)
        _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])


@event.listens_for(IDPGroup, "after_insert")
def group_created(
    mapper: Mapper[IDPGroup], connection: Connection, target: IDPGroup
) -> None:
    change = GroupCreated(id=target.id)
    changelog = IDPChangelog(change=change)
    _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])


@event.listens_for(IDPGroup, "after_update")
def group_enabled_or_disabled(
    mapper: Mapper[IDPGroup], connection: Connection, target: IDPGroup
) -> None:
    if _null_to_nonnull(target, "disabled_at"):
        change = GroupRemoved(id=target.id)
        changelog = IDPChangelog(change=change)
        _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])
    if _nonnull_to_null(target, "disabled_at"):
        change = GroupReenabled(id=target.id)
        changelog = IDPChangelog(change=change)
        _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])


@event.listens_for(UserGroupMembership, "after_insert")
def user_added_to_group(
    mapper: Mapper[UserGroupMembership],
    connection: Connection,
    target: UserGroupMembership,
) -> None:
    change = UserAddedToGroup(user_id=target.user_id, group_id=target.group_id)
    changelog = IDPChangelog(change=change)
    _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])


@event.listens_for(UserGroupMembership, "after_delete")
def user_removed_from_group(
    mapper: Mapper[UserGroupMembership],
    connection: Connection,
    target: UserGroupMembership,
) -> None:
    change = UserRemovedFromGroup(user_id=target.user_id, group_id=target.group_id)
    changelog = IDPChangelog(change=change)
    _ = connection.execute(insert(IDPChangelog), [_dump_first_layer(changelog)])
