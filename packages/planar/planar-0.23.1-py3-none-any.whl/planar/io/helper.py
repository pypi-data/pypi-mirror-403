"""Facade for exposing Planar IO functionality."""

from .entity import IOEntity
from .forms import FormBuilder
from .input import IOInput
from .messages import IODisplay
from .select import IOSelect
from .upload import IOUpload


class IOHelper:
    def __init__(self) -> None:
        self.input = IOInput()
        self.display = IODisplay()
        self.select = IOSelect()
        self.entity = IOEntity()
        self.upload = IOUpload()
        # form helper exposed via method

    def form(
        self,
        name: str,
        *,
        title: str | None = None,
        description: str | None = None,
        submit_label: str = "Continue",
    ) -> FormBuilder:
        return FormBuilder(
            name=name,
            title=title or name,
            description=description,
            submit_label=submit_label,
        )


__all__ = ["IOHelper"]
