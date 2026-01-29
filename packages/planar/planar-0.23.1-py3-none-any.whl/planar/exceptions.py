"""Shared exception and error handling utilities."""

import traceback
from typing import Self

from pydantic import BaseModel, Field


class NotFoundError(Exception):
    """Raised when a resource cannot be found."""


class ErrorDetails(BaseModel):
    """Structured error information with type, message, and optionally truncated traceback."""

    type: str = Field(description="Exception type name")
    message: str = Field(description="Error message")
    traceback: str | None = Field(default=None, description="Stack traceback")

    @classmethod
    def from_exception(
        cls,
        exc: BaseException,
        *,
        max_traceback_chars: int = 8000,
    ) -> Self:
        """Create ErrorDetails from an exception, truncating traceback to max_traceback_chars (keeps tail)."""
        tb = traceback.format_exc()

        # Truncate from the end to keep the most relevant part (the actual error)
        if len(tb) > max_traceback_chars:
            tb = tb[-max_traceback_chars:]

        return cls(
            type=type(exc).__name__,
            message=str(exc),
            traceback=tb,
        )
