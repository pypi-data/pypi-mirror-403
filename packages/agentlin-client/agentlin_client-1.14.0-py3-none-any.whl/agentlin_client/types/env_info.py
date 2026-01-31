# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional

from .._models import BaseModel

__all__ = ["EnvInfo"]


class EnvInfo(BaseModel):
    """环境信息"""

    name: str

    default_params_summary: Optional[str] = None

    importable: Union[str, bool, None] = None

    module: Optional[str] = None

    origin: Optional[str] = None

    source: Optional[str] = None
