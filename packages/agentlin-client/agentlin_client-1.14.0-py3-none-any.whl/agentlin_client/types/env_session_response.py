# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict

from .._models import BaseModel

__all__ = ["EnvSessionResponse"]


class EnvSessionResponse(BaseModel):
    """会话信息响应"""

    client_id: str

    created_at: float

    env_id: str

    env_vars: Dict[str, str]

    is_active: bool

    last_accessed_at: float

    session_id: str

    user_id: str
