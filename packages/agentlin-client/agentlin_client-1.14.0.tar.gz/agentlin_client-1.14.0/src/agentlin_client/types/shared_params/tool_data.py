# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict
from typing_extensions import Literal, Required, TypedDict

__all__ = ["ToolData", "Function"]


class Function(TypedDict, total=False):
    """函数工具定义（名称/参数/描述）。"""

    name: Required[str]
    """工具/函数名称（唯一标识）。"""

    parameters: Required[Dict[str, object]]
    """JSON Schema for the function parameters."""

    description: str
    """函数的用途说明。"""

    strict: bool
    """是否启用严格参数校验。"""


class ToolData(TypedDict, total=False):
    function: Required[Function]
    """函数工具定义（名称/参数/描述）。"""

    type: Required[Literal["function"]]
    """工具类型，此处固定为 function。"""
