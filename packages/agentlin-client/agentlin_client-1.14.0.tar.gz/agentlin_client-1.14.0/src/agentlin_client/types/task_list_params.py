# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Optional
from typing_extensions import Literal, TypedDict

__all__ = ["TaskListParams"]


class TaskListParams(TypedDict, total=False):
    ending_before: Optional[str]
    """Cursor for pagination"""

    limit: Optional[int]
    """Maximum number of tasks to return"""

    session_id: Optional[str]
    """Session ID filter"""

    starting_after: Optional[str]
    """Cursor for pagination"""

    status: Optional[
        List[
            Literal[
                "created", "queued", "working", "input-required", "paused", "completed", "canceled", "expired", "failed"
            ]
        ]
    ]
    """Task status filter"""

    user_id: Optional[str]
    """User ID filter"""
