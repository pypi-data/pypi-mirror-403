# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AnnotationURLCitationParam"]


class AnnotationURLCitationParam(TypedDict, total=False):
    """A citation for a web resource used to generate a model task."""

    end_index: Required[int]
    """The index of the last character of the URL citation in the message."""

    start_index: Required[int]
    """The index of the first character of the URL citation in the message."""

    title: Required[str]
    """The title of the web resource."""

    type: Required[Literal["url_citation"]]
    """The type of the URL citation. Always `url_citation`."""

    url: Required[str]
    """The URL of the web resource."""
