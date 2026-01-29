"""
Authentication context management for Planar.

This module provides context variables and utilities for managing the current
authenticated principal (user) throughout the request lifecycle.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from planar.security.models import Principal


# Context variable for the current principal
principal_var: ContextVar[Principal | None] = ContextVar("principal", default=None)


def get_current_principal() -> Principal | None:
    """
    Get the current authenticated principal from context.

    Returns:
        The current Principal or None if not authenticated.
    """
    return principal_var.get()


def require_principal() -> Principal:
    """
    Get the current authenticated principal from context.

    Returns:
        The current Principal.

    Raises:
        RuntimeError: If no principal is set in context.
    """
    principal = get_current_principal()
    if principal is None:
        raise RuntimeError("No authenticated principal in context")
    return principal


def has_role(role: str) -> bool:
    """
    Check if the current principal has the given role.
    """
    principal = get_current_principal()
    return principal is not None and principal.role == role


def set_principal(principal: Principal) -> Any:
    """
    Set the current principal in context.

    Args:
        principal: The principal to set.

    Returns:
        A token that can be used to reset the context.
    """
    return principal_var.set(principal)


def clear_principal(token: Any) -> None:
    """
    Clear the current principal from context.

    Args:
        token: The token returned from set_principal.
    """
    principal_var.reset(token)


@contextmanager
def as_principal(principal: Principal) -> Iterator[None]:
    """
    Context manager that sets the current principal in context.

    Args:
        principal: The principal to set.
    """
    token = set_principal(principal)
    try:
        yield
    finally:
        clear_principal(token)
