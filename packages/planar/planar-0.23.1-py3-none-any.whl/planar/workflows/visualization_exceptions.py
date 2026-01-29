"""Exceptions for workflow visualization service."""


class WorkflowVisualizationNotConfiguredError(RuntimeError):
    """Raised when AI models are not configured."""

    pass


class WorkflowVisualizationNotFoundError(RuntimeError):
    """Raised when workflow does not exist."""

    pass


class WorkflowVisualizationSourceError(RuntimeError):
    """Raised when workflow source code cannot be read."""

    pass


class WorkflowVisualizationGenerationError(RuntimeError):
    """Raised when visualization generation fails."""

    pass
