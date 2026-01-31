# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

__all__ = ["EnvResetParams"]


class EnvResetParams(TypedDict, total=False):
    session_id: Required[str]

    options: Optional[Dict[str, object]]

    seed: Optional[int]
