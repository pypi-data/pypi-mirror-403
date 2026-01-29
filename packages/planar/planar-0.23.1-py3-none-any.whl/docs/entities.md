# Planar Entities Guide

## Overview

Planar entities are the core data models for your application. They define the structure of your data and how it's stored in the database. This guide explains the best practices and patterns for working with entities in Planar.

## Core Concepts

### Entity

An entity is a data model that is mapped to a database table. Entities in Planar are built on SQLModel, which combines SQLAlchemy and Pydantic to provide both database ORM capabilities and data validation.

### Key Attributes

- **Tables**: Entities are mapped to database tables when they have `table=True`
- **Validation**: Entities benefit from Pydantic validation
- **Type Safety**: Fields use Python type hints for both runtime validation and static analysis

### Schemas / Namespaces

- **System tables** live in the `planar` schema.
- **User tables** (entities inheriting from `PlanarBaseEntity`) use a configurable default schema.
- Default user schema is `planar_entity` on PostgreSQL; SQLite ignores schemas.
- Models can still override per-table schema with `__table_args__ = {"schema": "my_schema"}`.


## Defining Entities

### Basic Entity Structure

```python
>>> db_manager = DatabaseManager(db_url)
>>> db_manager.connect()
>>> engine = db_manager.get_engine()
>>> session = new_session(engine)

```

```python
>>> from datetime import datetime
>>> from planar.modeling.mixins.timestamp import TimestampMixin
>>> from planar.modeling.orm import PlanarBaseEntity
>>> from sqlmodel import Field, select

>>> class AppUser(PlanarBaseEntity, TimestampMixin, table=True):
...     username: str = Field(unique=True, index=True)
...     email: str = Field(unique=True)
...     full_name: str = Field()
...     is_active: bool = Field(default=True)
...     last_login: datetime | None = Field(default=None)

```

#### Important notes:

- Inherit from `PlanarBaseEntity` to get the base functionality
- Use `table=True` to indicate this model should be mapped to a database table
- Include descriptive docstrings for your entities
- Use `Field()` to define additional properties for each field

### Common Field Types

Planar entities support various field types:

```python
>>> from typing import List, Dict
>>> from datetime import datetime
>>> from uuid import UUID
>>> from enum import Enum
>>> from sqlmodel import Field, JSON, Column

>>> class TaskStatus(str, Enum):
...     TODO = "todo"
...     IN_PROGRESS = "in_progress"
...     DONE = "done"

>>> class Task(PlanarBaseEntity, TimestampMixin, table=True):
...     title: str = Field()
...     description: str | None = Field(default=None)
...     status: TaskStatus = Field(default=TaskStatus.TODO)
...     due_date: datetime | None = Field(default=None)
...     priority: int = Field(default=0)
...     assignee_id: UUID | None = Field(default=None, foreign_key="appuser.id")
...     tags: List[str] | None = Field(default=None, sa_column=Column(JSON))

```

## Best Practices

### Use Appropriate Mixins

Planar provides several useful mixins to add common functionality to your entities:

```python
>>> from planar.modeling.mixins.timestamp import TimestampMixin

>>> class Document(PlanarBaseEntity, TimestampMixin, table=True):
...     """Document entity."""
...     title: str = Field()
...     content: str = Field()

```

### Field Definitions

When defining fields:

- Use `unique=True` for fields that must be unique
- Use `index=True` for fields you'll frequently query on
- Provide clear defaults for optional fields
- Use `Optional[Type]` for nullable fields
- Provide descriptive docstrings for complex fields

### Relationships

Define relationships between entities using foreign keys:

```python
>>> class Comment(PlanarBaseEntity, TimestampMixin, table=True):
...     """Comment entity related to a document."""
...     text: str = Field()
...     document_id: UUID = Field(foreign_key="document.id")
...     author_id: UUID = Field(foreign_key="appuser.id")

```

### Enum Values

Use string-based enums for better database compatibility:

```python
>>> class ReportType(str, Enum):
...     DAILY = "daily"
...     WEEKLY = "weekly"
...     MONTHLY = "monthly"

>>> class Report(PlanarBaseEntity, table=True):
...     type: ReportType = Field()
...     name: str = Field()

```

### JSON/JSONB Fields

For complex data structures, use the SQLAlchemy JSON column type:

```python
>>> from sqlmodel import Column, JSON
>>> from typing import Any

>>> class Product(PlanarBaseEntity, table=True):
...     name: str = Field()
...     attributes: dict[str, Any] = Field(sa_column=Column(JSON))

```

## Entity Registration

Entities must be registered with the Planar app for API generation and UI usage:

```python
from planar import PlanarApp

app = PlanarApp()
app.register_entity(AppUser)
app.register_entity(Task)
app.register_entity(Document)
app.register_entity(Comment)
```

## Configuring Entity Schema

- Global default via config:

```yaml
app:
  db_connection: app
  entity_schema: planar_entity  # set to 'public' to keep legacy behavior
```

- Per-model override:

```python
class AppUser(PlanarBaseEntity, table=True):
    __table_args__ = {"schema": "customer"}
    # fields...
```

Notes:
- Planar ensures the `planar` schema exists for system tables and creates the configured `entity_schema` on PostgreSQL at startup. On SQLite, schemas are ignored.

## Common Pitfalls

### Avoid Complex Base Models

- **Don't** use entities for complex inheritance hierarchies
- **Do** prefer composition over inheritance

### Planar Convention Issues

Avoid these common issues:

- **Don't** name fields that overlap with standard fields from included mixins:
  - `id` from `UUIDPrimaryKeyMixin` or `PlanarBaseEntity`
  - `created_at` and `updated_at` from `TimestampMixin`
  - `created_by` and `updated_by` from `AuditableMixin` or `PlanarBaseEntity`
- **Don't** use workflow status fields (use durable workflows instead)
- **Don't** add processing status flags (use workflow states)
- **Don't** use SQLAlchemy models directly - use SQLModel

### Choosing Between PlanarBaseEntity and Individual Mixins

- **Use `PlanarBaseEntity`** for application entities that need all standard fields (id, audit trail)
- **Use individual mixins** when you need more control over which fields are included and are managing the database schema yourself

## Working with Entities

SQLModel automatically registers all classes which inherit from `SQLModel` (like `PlanarBaseEntity`).

PlanarBaseEntity automatically registers itself to the `PLANAR_APPLICATION_METADATA` metadata object. We can ensure all tables are created like this:

```python
>>> from sqlmodel import SQLModel
>>> from planar.modeling.orm import PLANAR_APPLICATION_METADATA
>>> async with engine.begin() as conn:
...     await conn.run_sync(PLANAR_APPLICATION_METADATA.create_all)
>>> print("Database tables created - if they didn't exist.")
Database tables created - if they didn't exist.

```

**You won't need to do this, as Planar will handle this for you.**

### Creating Entities

This example demonstrates creating a new `AppUser` instance and persisting it to the database.

```python
>>> user = AppUser(
...     username="liveuser",
...     email="live@example.com",
...     full_name="Live User",
... )
>>> async with session.begin(): # Manages transaction: commit on success, rollback on error
...     session.add(user)
...     # The user object will be populated with its ID after this block.
>>> print(f"User '{user.username}' created with ID type: {type(user.id)}")
User 'liveuser' created with ID type: <class 'uuid.UUID'>

```

### Querying Entities

This example shows how to query for active users. We'll look for the user created in the previous step.

```python
>>> found_usernames = []
>>> async with session.begin():
...     stmt = select(AppUser).where(AppUser.is_active == True).where(AppUser.username == "liveuser")
...     result = await session.exec(stmt)
...     active_users = result.all()
...     found_usernames = [user.username for user in active_users]
>>> if found_usernames:
...     print(f"Found active user(s): {found_usernames}")
... else:
...     print("No active user named 'liveuser' found.")
Found active user(s): ['liveuser']

```

For more information on updating and deleting entities, see the [SQLAlchemy Usage](sqlalchemy_usage.md) guide.

## Mixins

Planar provides several mixins to add common functionality to your entities:

- `TimestampMixin` - Adds `created_at` and `updated_at` fields
- `UUIDPrimaryKeyMixin` - Adds a UUID primary key field (`id`)
- `AuditableMixin` - Adds audit trail fields (`created_by`, `updated_by`)

In the example above, we use the `TimestampMixin` to add the `created_at` and `updated_at` fields to the `AppUser` entity.
Those fields are automatically populated when the entity is created or updated.

```python
>>> async with session.begin():
...     user.is_active = False
...     session.add(user)
>>> async with session:
...     await session.refresh(user)
...     print(f"User updated at after creation: {user.updated_at > user.created_at}")
User updated at after creation: True

```
