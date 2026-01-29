# Planar SQLAlchemy/SQLModel Usage Guide

This guide provides essential information for working with databases in the Planar
framework using SQLModel and SQLAlchemy, focusing on transaction management.

This documentation is written in doctest format and verified by Planar CI, so
it is guaranteed to be correct, at least within the context of the Planar
framework.

## Core Concepts

*   **SQLModel:** Built on Pydantic and SQLAlchemy, SQLModel allows defining
    database models that are also Pydantic models, simplifying data validation
    and serialization.
*   **SQLAlchemy Core/ORM:** We use SQLAlchemy's asynchronous features
    (`AsyncSession`, `AsyncEngine`) for database interactions.
*   **Unit of Work:** The `Session` object manages a "Unit of Work". Changes to
    objects tracked by the session (e.g., adding, modifying, deleting) are
    collected and flushed to the database within a transaction.

## SQLModel & SQLAlchemy Core API Cheat Sheet

Most operations will be performed within the context of a `PlanarSession`,
which is a SQLAlchemy's `AsyncSession` subclass.

Normally within the Planar framework, you will obtain a session using
`get_session()`.

On FastAPI request handlers, `get_session()` will return a session with a
lifetime bound to the `asyncio.Task` responsible for handling the HTTP request.

On workflows/steps, `get_session()` will return a session with a lifetime
bound to the `asyncio.Task` responsible for the workflow's execution.


For the examples shown here, we'll need to create our own engine/session using
the database URL injected in the environment as `db_url`:


```python
>>> db_manager = DatabaseManager(db_url)
>>> db_manager.connect()
>>> engine = db_manager.get_engine()
>>> session = new_session(engine)

```

We'll also need some SQLModel classes we'll use in the examples:

```python
>>> from sqlmodel import Field, SQLModel

>>> class Customer(SQLModel, table=True):
...     id: int | None = Field(default=None, primary_key=True)
...     name: str = Field(index=True)
...     email: str | None = Field(default=None)

>>> class Profile(SQLModel, table=True):
...     id: int | None = Field(default=None, primary_key=True)
...     customer_id: int = Field(foreign_key="customer.id")
...     bio: str | None = None

```

SQLModel automatically registers all classes which inherit from `SQLModel`.

We can ensure all tables are created like this:

```python
>>> async with engine.begin() as conn:
...     await conn.run_sync(SQLModel.metadata.create_all)

```

Now, let's look at the operations:

**1. Adding a New Object (`session.add`)**

Adds a new model instance to the session. It will be inserted into the database
upon the next flush/commit:

```python

>>> async with session.begin(): # Use a transaction block, which will commit at the end
...     new_customer = Customer(name="Alice", email="alice@example.com")
...     session.add(new_customer)
...     # new_customer is now 'pending', will be inserted on commit
...     # Let's verify it's pending (has no ID yet)
...     print(f"Customer ID before commit: {new_customer.id}")
Customer ID before commit: None

```

Verify insertion after commit:

```python
>>> async with session:
...    added_customer = (await session.exec(select(Customer).where(Customer.name == "Alice"))).one()
...    print(f"Added Customer: {added_customer.name}, Email: {added_customer.email}, ID: {added_customer.id}")
Added Customer: Alice, Email: alice@example.com, ID: 1

```

**2. Fetching and Updating an Object**

Retrieve an object, modify its attributes, and commit the changes:

```python

>>> async with session.begin():
...     # Fetch using session.get (for primary key lookup)
...     customer_to_update = await session.get(Customer, 1) # Alice's ID is 1
...     print(f"Fetched Customer: {customer_to_update.name}, Email: {customer_to_update.email}")
...     if customer_to_update:
...         customer_to_update.email = "alice_updated@example.com"
Fetched Customer: Alice, Email: alice@example.com

```

Verify the update in a separate session:

```python
>>> async with new_session(engine) as session2:
...    updated_customer = await session2.get(Customer, 1)
...    print(f"Updated Customer: {updated_customer.name}, Email: {updated_customer.email}")
Updated Customer: Alice, Email: alice_updated@example.com

```

**3. Refreshing Object State (`session.refresh`)**

Update an object's attributes with the latest data from the database. Useful
if the data might have changed externally or after a flush.

```python
>>> async with session.begin():
...     customer = await session.get(Customer, 1)
...     print(f"Customer email before refresh: {customer.email}")
Customer email before refresh: alice_updated@example.com

```

Create a separate session/connection to update the database

```python
>>> async with new_session(engine) as session2:
...    stmt = update(Customer).where(Customer.id == 1).values(email="external_change@example.com")
...    await session2.execute(stmt)
...    await session2.commit()

```

Finally, refresh the first session customer from DB

```python
>>> async with session:
...     await session.refresh(customer)
...     print(f"Customer email after refresh: {customer.email}")
Customer email after refresh: external_change@example.com

```

**4. Flushing Changes (`session.flush`)**

Send pending changes (INSERTs, UPDATEs, DELETEs) to the database *without*
committing the transaction. This is useful to get database-generated values
(like auto-increment IDs) or to enforce constraints before the final commit.

```python
>>> async with session.begin():
...     new_customer = Customer(name="Bob", email="bob@example.com")
...     session.add(new_customer)
...     print(f"Customer ID before flush: {new_customer.id}") # Shows "None"
...     await session.flush() # Sends INSERT to DB, populates ID
...     print(f"Customer ID after flush: {new_customer.id}") # Shows the generated ID
...     # The customer is in the DB now for this transaction, but not committed yet.
...     # Let's verify we can fetch Bob within the same transaction post-flush
...     bob_in_tx = await session.get(Customer, new_customer.id)
...     print(f"Bob fetched post-flush: {bob_in_tx.name if bob_in_tx else 'Not found'}")
Customer ID before flush: None
Customer ID after flush: 2
Bob fetched post-flush: Bob

```

Verify Bob exists after commit:

```python
>>> async with session:
...    bob = await session.get(Customer, 2)
...    print(f"Bob exists after commit: {bob is not None}")
Bob exists after commit: True

```

**5. Merging Detached Objects (`session.merge`)**

If you have an object instance that didn't originate from the current session
(e.g., deserialized from a request), `session.merge()` reconciles its state
with the session. It fetches the object with the same primary key from the DB
(if it exists) and copies the state of the *given* object onto the
*persistent* object.

*Caution:* `merge` can be complex. Often, it's clearer to fetch the
existing object and update its attributes directly.


First, create a detached Customer with the same id as Bob's

```python
>>> detached_customer = Customer(id=2, name="Charlie Updated", email="charlie@new.com")

```

Now in a new transaction, merge the detached object with the session:

```python
>>> async with session.begin():
...     # Customer with id=2 (Bob) exists, its name and email will be updated.
...     merged_customer = await session.merge(detached_customer)
...     # merged_customer is the persistent instance tracked by the session
...     print(f"Merged Customer (in session): ID={merged_customer.id}, Name={merged_customer.name}, Email={merged_customer.email}")
Merged Customer (in session): ID=2, Name=Charlie Updated, Email=charlie@new.com

```

Side note: Pydantic models can be compared for equality with `==`:

```python
>>> merged_customer == detached_customer
True

```

But the merged_customer object returned by `await session.merge` has a different identity than the detached_customer:


```python
>>> merged_customer is detached_customer
False

```

Verify the changes persisted after commit:

```python
>>> async with session:
...    charlie = await session.get(Customer, 2)
...    print(f"Customer 2 after merge commit: Name={charlie.name}, Email={charlie.email}")
Customer 2 after merge commit: Name=Charlie Updated, Email=charlie@new.com

```

**6. Using SQLAlchemy Core (`session.exec`)**

Execute statements built with the SQLAlchemy Core Expression Language
(e.g., `select`, `insert`, `update`, `delete`). This is powerful for
complex queries, bulk operations, or when you don't need the ORM object
tracking overhead.

```python
>>> # Setup: Add David for Core API tests
>>> async with session.begin():
...    session.add(Customer(name="David", email="david@example.com"))

```

Select specific columns

```python
>>> async with session: # Often used for reads
...     # Find Alice (ID 1)
...     statement = select(Customer.name, Customer.email).where(Customer.id == 1)
...     result = await session.exec(statement)
...     name, email = result.first() # Returns a tuple (name, email) or None
...     print(f"Core Select (Specific Cols): Name={name}, Email={email}")
Core Select (Specific Cols): Name=Alice, Email=external_change@example.com

```

Select entire objects (more common with SQLModel):

```python
>>> async with session:
...     # Find customers starting with A or C
...     statement = select(Customer).where(col(Customer.name).like("A%")).order_by(Customer.name)
...     result = await session.exec(statement)
...     customers_starting_with_a = result.all() # Returns a list of Customer objects
...     print(f"Core Select (Objects): {[customer.name for customer in customers_starting_with_a]}")
Core Select (Objects): ['Alice']

```

Insert using core (less common than session.add with SQLModel):

```python
>>> async with session.begin():
...     statement = insert(Customer).values(name="Eve", email="eve@core.com")
...     await session.exec(statement)

```

Verify the new customer exists using a separate session/connection:

```python
>>> async with new_session(engine) as session2:
...    eve = (await session2.exec(select(Customer).where(Customer.name == "Eve"))).first()
...    print(f"Core Insert: Eve exists? {eve is not None}, Email: {eve.email if eve else 'N/A'}")
Core Insert: Eve exists? True, Email: eve@core.com

```

Update using core, which can be useful for batch updates without loading the data:

```python
>>> async with session.begin():
...     statement = (
...         update(Customer)
...         .where(Customer.email == "david@example.com")
...         .values(email="david.updated@core.com")
...     )
...     update_result = await session.exec(statement)
...     # Note: rowcount might not be reliable on all backends/drivers, but
...     # should work in SQLite/PostgreSQL which are supported by Planar.
...     print(f"Core Update: Rows matched? {update_result.rowcount > 0}")
Core Update: Rows matched? True

```

Verify the update using a new session/connection:

```python
>>> async with new_session(engine) as session2:
...    david = (await session2.exec(select(Customer).where(Customer.name == "David"))).one()
...    print(f"Core Update Verify: David's email={david.email}")
Core Update Verify: David's email=david.updated@core.com

```

Delete using core, which can be useful for batch deletes without loading the data:

```python
>>> async with session.begin():
...     statement = delete(Customer).where(Customer.name == "David")
...     delete_result = await session.exec(statement)
...     print(f"Core Delete: Rows matched? {delete_result.rowcount > 0}")
Core Delete: Rows matched? True

```

Verify the deletion using a new session/connection:

```python
>>> async with new_session(engine) as session2:
...    david = (await session2.exec(select(Customer).where(Customer.name == "David"))).first()
...    print(f"Core Delete Verify: David exists? {david is not None}")
Core Delete Verify: David exists? False

```

## Planar's Transaction Model: "Commit As You Go"

Planar configures SQLAlchemy for a "commit as you go" pattern:

1.  **Implicit BEGIN:** A transaction is automatically started (`BEGIN`) the
    *first* time a query is sent to the database within a session if no
    explicit transaction is active.
2.  **SQLite `BEGIN IMMEDIATE`:** For SQLite, we force `BEGIN IMMEDIATE` to
    acquire a write lock immediately, preventing "database is locked" errors
    when read operations might escalate to writes later in the same implicit
    transaction.
3.  **Mandatory Transaction Closure:** Because a transaction is often implicitly
    opened, **you MUST explicitly close every transaction** using one of the
    patterns below. Failure to do so can lead to connections being held open,
    transaction deadlocks, or data inconsistencies.

## Required Transaction Management Patterns

Always use one of these patterns to manage your database interactions and
ensure transactions are properly handled.

**1. Explicit Transaction Block (`async with session.begin()`):**

*   **Best Practice:** This is the **preferred** method for units of work
    involving multiple operations (reads and writes) that should succeed or
    fail together.
*   **Behavior:** Automatically commits the transaction if the block completes
    successfully, otherwise rolls back on exception.

```python
>>> async with session.begin():
...     # Create customer
...     customer = Customer(name="Frank", email="frank@tx.com")
...     session.add(customer)
...     await session.flush() # Flush to get customer.id if needed for profile
...     print(f"Customer created in tx: {customer.name}, ID: {customer.id}")
...
...     # Create profile linked to customer
...     profile = Profile(bio="Frank's bio", customer_id=customer.id)
...     session.add(profile)
...     print(f"Profile created for customer {customer.id}")
Customer created in tx: Frank, ID: 5
Profile created for customer 5

```

Verify both customer and profile exist after commit:

```python
>>> async with session:
...    frank = (await session.exec(select(Customer).where(Customer.name == "Frank"))).one()
...    profile = (await session.exec(select(Profile).where(Profile.customer_id == frank.id))).one()
...    print(f"Verification: Frank exists? {frank is not None}, Profile exists? {profile is not None}, Profile bio: {profile.bio}")
Verification: Frank exists? True, Profile exists? True, Profile bio: Frank's bio

```

Test rollback on exception within session.begin()

```python
>>> try:
...     async with session.begin():
...         customer = Customer(name="Grace", email="grace@fail.com")
...         session.add(customer)
...         await session.flush()
...         print(f"Customer created in (failing) tx: {customer.name}, ID: {customer.id}")
...         raise ValueError("Simulated error during profile creation")
... except ValueError as e:
...     print(f"Caught expected error: {e}")
Customer created in (failing) tx: Grace, ID: 6
Caught expected error: Simulated error during profile creation

```

Verify Grace does not exist due to rollback

```python
>>> async with session:
...    grace = (await session.exec(select(Customer).where(Customer.name == "Grace"))).first()
...    print(f"Verification: Grace exists after failed tx? {grace is not None}")
Verification: Grace exists after failed tx? False

```

**2. Read-Only Transaction Block (`async with session.begin_read()`):**

*   **Use Case:** Specifically designed for read-only operations. It ensures
    that if a transaction was not already active, the session will attempt to
    commit after the block (if successful) or rollback (on exception). If a
    transaction was already active, `begin_read` does not interfere with its
    management. This is useful for ensuring that read operations are consistent
    and don't leave transactions open unnecessarily.
*   **Behavior:**
    *   If no transaction is active when `begin_read` is entered:
        *   It allows read operations.
        *   If the block completes successfully, it commits.
        *   If an exception occurs, it rolls back.
    *   If a transaction is already active:
        *   It participates in the existing transaction.
        *   Commit/rollback is handled by the outer transaction management.

```python
>>> async with session.begin_read():
...     alice = await session.get(Customer, 1)
...     print(f"Read-only result with begin_read: Alice's email = {alice.email if alice else 'Not Found'}")
...     # No explicit commit/rollback needed here; begin_read handles it.
Read-only result with begin_read: Alice's email = external_change@example.com

```

Let's test `begin_read` when an outer transaction is already active.

```python
>>> async with session.begin(): # Outer transaction
...     # Modify Alice's email within the outer transaction
...     alice_in_outer_tx = await session.get(Customer, 1)
...     alice_in_outer_tx.email = "alice.outer.tx.change@example.com"
...     session.add(alice_in_outer_tx)
...
...     async with session.begin_read(): # Inner begin_read
...         alice_in_inner_read = await session.get(Customer, 1)
...         # This will see the change from the outer transaction because it's part of it
...         print(f"Alice's email in begin_read (within outer tx): {alice_in_inner_read.email}")
...     # begin_read does not commit or rollback here, outer transaction controls it.
...     print(f"Outer transaction still active, Alice's email: {alice_in_outer_tx.email}")
...     await session.rollback()
...
Alice's email in begin_read (within outer tx): alice.outer.tx.change@example.com
Outer transaction still active, Alice's email: alice.outer.tx.change@example.com

```

**3. Manual Commit/Rollback (`async with session:`):**

*   **Use Case:** Suitable for single operations or when fine-grained control
    over commit/rollback points is needed *within* a single logical block
    (use with caution). Often used for read-only operations where an explicit
    transaction block isn't strictly necessary but cleanup is. This is the
    pattern we use the most in the planar framework, especially when calling
    customer code since it might not even send any queries (so any follow up
    commit/rollbacks will be no-op).
*   **Behavior:** The `async with session:` block ensures the session is closed
    (which typically issues a ROLLBACK if a transaction was implicitly started
    and not committed), but **you must call `session.commit()` explicitly** if
    you perform writes. It is still possible to reuse closed sessions (as you
    might have seen in the examples so far), but it detaches all of its managed
    objects.

Read-only example (no explicit commit/rollback needed):

```python
>>> async with session:
...     print(f"Getting customer 1")
...     alice = await session.get(Customer, 1)
...     print(f"Alice in session: {alice in session}")
...     print(f"Read-only result: Alice's email = {alice.email if alice else 'Not Found'}")
...     # For reads, no explicit commit/rollback is needed.
...     # If a transaction was implicitly started (e.g., SQLite BEGIN IMMEDIATE),
...     # the session context manager's exit will handle rollback if needed.
Getting customer 1
Alice in session: True
Read-only result: Alice's email = external_change@example.com

```

After the end of the `async with session` block, the session is closed and the Customer instance is detached (but still has the data).

```python
>>> alice in session
False
>>> alice.email, alice.id
('external_change@example.com', 1)

```

Example of manual commit:

```python
>>> customer_id = 1
>>> new_email = "alice.manual@tx.com"
>>> async with session:
...     customer = await session.get(Customer, customer_id)
...     if customer:
...         print(f"Updating email for customer {customer_id}")
...         customer.email = new_email
...         session.add(customer)
...         try:
...             await session.commit() # Explicit commit needed
...             print("Commit successful")
...         except Exception as e:
...             print(f"Caught exception during commit: {e}, rolling back.")
...             await session.rollback() # Explicit rollback on error
...             raise
...     else:
...         print(f"Customer {customer_id} not found for update.")
Updating email for customer 1
Commit successful
>>> async with session:
...    alice = await session.get(Customer, 1)
...    print(f"Verification after manual commit: Alice's email = {alice.email}")
Verification after manual commit: Alice's email = alice.manual@tx.com

```

Example of manual rollback (simulated failure):

```python
>>> customer_id = 1
>>> new_email = "alice.failed.update@tx.com"
>>> async with session:
...     customer = await session.get(Customer, customer_id)
...     if customer:
...         original_email = customer.email
...         print(f"Attempting to update email for customer {customer_id} to {new_email} (will fail)")
...         customer.email = new_email
...         session.add(customer)
...         try:
...             # Simulate a failure before commit
...             raise DBAPIError("Simulated DB constraint error", params=(), orig=ValueError("Constraint fail"))
...             # await session.commit() # This line won't be reached
...         except DBAPIError as e:
...             print(f"Caught simulated DBAPIError: {e.orig}, rolling back.")
...             await session.rollback() # Explicit rollback on error
...             # Verify state after rollback within the same session context
...             await session.refresh(customer) # Refresh to get DB state post-rollback
...             print(f"Email after rollback (within context): {customer.email}")
...             assert customer.email == original_email # Should be back to original
...         except Exception as e:
...             print(f"Caught unexpected exception: {e}, rolling back.")
...             await session.rollback()
...             raise
Attempting to update email for customer 1 to alice.failed.update@tx.com (will fail)
Caught simulated DBAPIError: Constraint fail, rolling back.
Email after rollback (within context): alice.manual@tx.com

```

Verify email is unchanged in DB after failed attempt:

```python
>>> async with new_session(engine) as session2:
...    alice = await session2.get(Customer, 1)
...    print(f"Verification after failed manual commit: Alice's email = {alice.email}")
Verification after failed manual commit: Alice's email = alice.manual@tx.com

```

## Key Takeaways

*   Planar uses an "implicit BEGIN" transaction strategy.
*   **Always** manage transaction boundaries explicitly using `async with
    session.begin()` (preferred) or manual `session.commit()` within an `async
    with session:` block.
*   Failure to close transactions will lead to issues.
*   Whenever possible, use the framework provided session by calling `get_session()`.
