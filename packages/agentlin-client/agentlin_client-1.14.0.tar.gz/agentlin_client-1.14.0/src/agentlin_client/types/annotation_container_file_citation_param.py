# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AnnotationContainerFileCitationParam"]


class AnnotationContainerFileCitationParam(TypedDict, total=False):
    """A citation for a container file used to generate a model task."""

    container_id: Required[str]
    """The ID of the container file."""

    end_index: Required[int]
    """The index of the last character of the container file citation in the message."""

    file_id: Required[str]
    """The ID of the file."""

    filename: Required[str]
    """The filename of the container file cited."""

    start_index: Required[int]
    """The index of the first character of the container file citation in the message."""

    type: Required[Literal["container_file_citation"]]
    """The type of the container file citation. Always `container_file_citation`."""
