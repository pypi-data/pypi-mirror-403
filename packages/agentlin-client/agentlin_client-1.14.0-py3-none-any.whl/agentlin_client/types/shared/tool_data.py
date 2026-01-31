# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["ToolData", "Function"]


class Function(BaseModel):
    """函数工具定义（名称/参数/描述）。"""

    name: str
    """工具/函数名称（唯一标识）。"""

    parameters: Dict[str, object]
    """JSON Schema for the function parameters."""

    description: Optional[str] = None
    """函数的用途说明。"""

    strict: Optional[bool] = None
    """是否启用严格参数校验。"""


class ToolData(BaseModel):
    function: Function
    """函数工具定义（名称/参数/描述）。"""

    type: Literal["function"]
    """工具类型，此处固定为 function。"""
