from uuid import UUID

from sqlmodel import Field, SQLModel
from uuid_utils import uuid7 as _uuid7


def uuid7() -> UUID:
    """Generate a UUID v7 (time-ordered) as a standard uuid.UUID object."""
    return UUID(bytes=_uuid7().bytes)


class UUIDPrimaryKeyMixin(SQLModel, table=False):
    """
    Mixin that provides a UUID primary key field.

    This standardizes primary key handling across all models that need
    a UUID-based primary key. Uses UUID v7 for time-ordered IDs which
    improves database index performance.

    Attributes:
        id: UUID primary key field with automatic generation
    """

    __abstract__ = True

    id: UUID = Field(default_factory=uuid7, primary_key=True)
