# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List

from .._models import BaseModel

__all__ = ["EnvSessionsResponse", "Session"]


class Session(BaseModel):
    """会话信息响应"""

    client_id: str

    created_at: float

    env_id: str

    env_vars: Dict[str, str]

    is_active: bool

    last_accessed_at: float

    session_id: str

    user_id: str


class EnvSessionsResponse(BaseModel):
    """列出会话响应"""

    sessions: List[Session]

    total: int
