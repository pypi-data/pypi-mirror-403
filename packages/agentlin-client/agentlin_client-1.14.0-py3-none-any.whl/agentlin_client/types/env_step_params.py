# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

__all__ = ["EnvStepParams"]


class EnvStepParams(TypedDict, total=False):
    session_id: Required[str]

    tool_name: Required[str]

    env_vars: Optional[Dict[str, str]]

    request_id: Optional[str]

    stream: bool

    task_id: Optional[str]

    tool_args: Dict[str, object]

    user_id: Optional[str]
