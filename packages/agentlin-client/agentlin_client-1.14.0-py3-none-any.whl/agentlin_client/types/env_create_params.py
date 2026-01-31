# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import TypedDict

__all__ = ["EnvCreateParams"]


class EnvCreateParams(TypedDict, total=False):
    client_id: str

    env_class_path: Optional[str]

    env_id: Optional[str]

    env_init_kwargs: Optional[Dict[str, object]]

    env_vars: Optional[Dict[str, str]]

    session_id: Optional[str]

    user_id: Optional[str]
