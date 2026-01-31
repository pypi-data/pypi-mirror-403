# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["EnvListParams"]


class EnvListParams(TypedDict, total=False):
    ending_before: Optional[str]
    """Cursor for pagination"""

    limit: Optional[int]
    """Maximum number of environments to return"""

    starting_after: Optional[str]
    """Cursor for pagination"""
