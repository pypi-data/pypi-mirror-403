from uuid import UUID

from planar.human.models import HumanTaskStatus


class TaskNotFound(ValueError):
    """Raised when a task cannot be found."""

    def __init__(self, task_id: UUID):
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


class UserNotFound(ValueError):
    """Raised when a IDPUser doesn't exist for the Principal."""

    def __init__(self, val: str | None):
        self.val = val
        super().__init__(f"User for {val} not found")


class TaskNotPending(ValueError):
    """Raised when attempting to operate on a non-PENDING task."""

    def __init__(self, task_id: UUID, status: HumanTaskStatus):
        self.task_id = task_id
        self.status = status
        super().__init__(f"Task {task_id} is not pending (status: {status})")
