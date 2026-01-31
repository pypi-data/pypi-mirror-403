# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["AnnotationFilePath"]


class AnnotationFilePath(BaseModel):
    """A citation to a file path."""

    file_url: str
    """The URL of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_path"]
    """The type of the file citation. Always `file_path`."""
