# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AnnotationFilePathParam"]


class AnnotationFilePathParam(TypedDict, total=False):
    """A citation to a file path."""

    file_url: Required[str]
    """The URL of the file cited."""

    index: Required[int]
    """The index of the file in the list of files."""

    type: Required[Literal["file_path"]]
    """The type of the file citation. Always `file_path`."""
