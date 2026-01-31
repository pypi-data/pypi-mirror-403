# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel
from .env_info import EnvInfo

__all__ = ["EnvInfoResponse"]


class EnvInfoResponse(BaseModel):
    """环境详细信息响应"""

    details: List[EnvInfo]

    name: str
