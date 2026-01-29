"""File upload helpers for Planar IO."""

from collections.abc import Sequence

from planar.files import PlanarFile

from ._base import _ensure_context
from ._field_specs import _execute_single_field, _upload_field_spec


class IOUpload:
    async def file(
        self,
        label: str,
        *,
        accept: Sequence[str] | None = None,
        max_size_mb: int | None = None,
        help_text: str | None = None,
    ) -> PlanarFile:
        _ensure_context()
        spec = _upload_field_spec(
            label=label,
            accept=accept,
            max_size_mb=max_size_mb,
            help_text=help_text,
        )
        return await _execute_single_field(
            spec,
            kind="upload.file",
            model_suffix="UploadFile",
            label=label,
            help_text=help_text,
        )


__all__ = ["IOUpload"]
