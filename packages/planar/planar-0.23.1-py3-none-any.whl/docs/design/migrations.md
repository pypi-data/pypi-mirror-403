## 1. Abstract

This document outlines the database migration system for the Planar framework. It describes two key components:

1.  The **implemented** system for managing schema evolution for **system tables**, which are internal tables managed by the Planar framework.
2.  The **proposed design** for managing **user-defined tables**, which application developers create.

The system uses Alembic to provide a robust and clear approach to database migrations.

## 2. Goals

- Implement a reliable migration system using Alembic for schema evolution.
- Support distinct migration paths and management for:
  - **System tables:** Internal tables required by the Planar framework (e.g., `Workflow`, `WorkflowStep`, `PlanarFileMetadata`, `AgentConfig`, `HumanTask`, `RuleOverride`). These are managed by the Planar library.
  - **User tables:** Tables defined by application developers by subclassing `PlanarBaseEntity`.
- Provide CLI tools for users to initialize, generate, and manage migrations for their application-specific tables.
- Ensure a clear separation of concerns and responsibilities between framework migrations and user migrations.
- Offer a sensible and configurable strategy for applying migrations, balancing automation with explicit user control.

## 3. Non-Goals

- Migrations for multiple disparate database backends simultaneously within a single Planar application (focus is on the primary application database).
- Complex migration script branching and merging strategies beyond standard Alembic capabilities.

## 4. System Table Migration (Implemented)

### How it Works

Planar's internal models (e.g., `Workflow`, `PlanarFileMetadata`, `LockedResource`) are defined to use a dedicated `MetaData` object targeting a `planar` schema in the database. This isolates framework tables from user application tables.

User tables created from `PlanarBaseEntity` default to a configurable schema. By default, this schema is `planar_entity` on PostgreSQL (configurable via `app.entity_schema`). On SQLite, schemas are ignored. You can still override schema per model with `__table_args__ = {"schema": "..."}`.

The Planar library includes a bundled Alembic environment located in `planar/db/alembic`. Migration scripts for all system tables are developed and versioned as part of the Planar framework itself. When a Planar application starts, it automatically runs these system migrations to ensure the internal database schema is synchronized with the installed Planar library version.

### How to Create a New System Migration (For Contributors)

When making changes to Planar's internal `SQLModel` definitions that require a database schema change, contributors must also generate a corresponding migration script.

**Prerequisites:**

1.  A local PostgreSQL server must be running.
2.  The server must have a database, user, and password all named `postgres`.
3.  You must connect to the `postgres` database and create the `planar` schema for the first time: `CREATE SCHEMA planar;`.

**Steps to Generate a Migration:**

1.  **Modify Models:** Make the necessary changes to the system's `SQLModel` classes (e.g., in `planar/workflows/models.py`) that subclass `PlanarInternalBase`. Ensure it is imported in `env.py`.
2.  **Generate Revision:** From the `planar/db/` directory, run the following command. This will connect to your local database, detect the model changes, and generate a new migration script.
    ```bash
    uv run alembic revision --autogenerate -m "Your brief description of the schema change"
    ```
3.  **Verify Script:** Alembic will create a new file in `planar/db/alembic/versions/`. Always review this file to ensure the generated `upgrade` and `downgrade` functions are correct and match your intent.
4.  **Test Migration:** You can test the migration in two ways:
    - **Manually with Alembic:** From the `planar/db/` directory, run `uv run alembic upgrade head` to apply the migration. To test the downgrade path, run `uv run alembic downgrade <previous_revision_id>`.
    - **Automatically via Planar App:** Start any example Planar application. The framework will automatically apply all "head" migrations on startup.

## 5. User Table Migration (Future Design)

This section outlines the proposed design for a migration system that will allow application developers to manage the lifecycle of their own custom database tables. This feature has **not yet been implemented**.

### High-Level Design

The proposed solution will leverage a second Alembic environment, distinct from the system environment, which will be initialized and managed by the application developer within their Planar project.

- This environment will contain migration scripts for user-defined tables (those subclassing `planar.modeling.orm.PlanarBaseEntity`).
- These tables would typically reside in the default database schema (e.g., `public`) or a user-specified schema (but not the `planar` schema).
- Users would generate and manage these migration scripts via `planar db ...` CLI commands.

This dual-environment approach ensures that framework updates can be applied automatically without interfering with user schemas, while giving developers explicit control over their own application's schema evolution.

### Detailed Design

#### User Models

User-defined models (subclasses of `planar.modeling.orm.PlanarBaseEntity`) will use the global `SQLModel.metadata` by default. These tables will typically reside in the configured `app.entity_schema` (default `planar_entity` on PostgreSQL), or any schema specified by the user in their model definitions using `__table_args__ = {"schema": "my_custom_schema"}`. Avoid using the `planar` schema for user tables.

#### Alembic Setup (User Project)

A CLI command `planar db init` will initialize an Alembic environment in the user's project, creating a `migrations/` directory. This will contain a standard `alembic.ini`, a `script.py.mako`, and a custom `env.py`.

The key to this setup is the user's `migrations/env.py`, which will be responsible for:

1.  Dynamically loading the user's `PlanarApp` instance to ensure all user models are registered with `SQLModel.metadata`.
2.  Setting `target_metadata = SQLModel.metadata`.
3.  Using an `include_object` function to explicitly filter out any tables belonging to the `planar` schema, ensuring user migrations only operate on user tables.

#### CLI Commands for User Migrations

The `planar` CLI will be extended with a `db` subcommand group for managing user migrations:

- `planar db init`: Creates the user's `migrations/` directory and configuration.
- `planar db revision -m "<message>" [--autogenerate]`: Generates a new revision script based on changes to user models.
- `planar db upgrade <revision>`: Applies migrations.
- `planar db downgrade <revision>`: Reverts migrations.
- `planar db history`: Shows migration history.
- `planar db current`: Shows the current database revision.

These commands will handle setting the necessary environment variables so that Alembic's `env.py` can correctly locate and load the user's application and configuration.

#### Applying User Migrations

- **Manual (Recommended for Production):** Users would run `planar db upgrade head` via the CLI.
- **Automatic (Optional for Development):** A configuration flag (`auto_apply_user_migrations`) could allow the framework to automatically apply user migrations on startup, similar to how system migrations work. This would be enabled by default in development for convenience and disabled in production for safety.
