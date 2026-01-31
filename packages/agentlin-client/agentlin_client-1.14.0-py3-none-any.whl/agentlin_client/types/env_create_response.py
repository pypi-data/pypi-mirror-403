# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from .._models import BaseModel
from .shared.tool_data import ToolData

__all__ = ["EnvCreateResponse"]


class EnvCreateResponse(BaseModel):
    """创建环境响应"""

    env_id: str

    initial_state: Dict[str, object]

    session_id: str

    tools: List[ToolData]

    done: Optional[bool] = None
