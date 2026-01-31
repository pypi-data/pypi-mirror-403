# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["EnvCloseResponse"]


class EnvCloseResponse(BaseModel):
    """关闭环境响应"""

    message: Optional[str] = None

    status: Optional[str] = None
