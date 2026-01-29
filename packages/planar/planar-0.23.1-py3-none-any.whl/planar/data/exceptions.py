"""Exceptions for the Planar data module."""

from planar.exceptions import NotFoundError


class DataError(Exception):
    """Base exception for data-related errors."""

    pass


class DatasetNotFoundError(DataError, NotFoundError):
    """Raised when a dataset is not found."""

    pass


class DatasetAlreadyExistsError(DataError):
    """Raised when trying to create a dataset that already exists."""

    pass
