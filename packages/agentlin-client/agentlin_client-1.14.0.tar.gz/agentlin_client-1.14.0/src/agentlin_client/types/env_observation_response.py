# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from .._models import BaseModel
from .shared.tool_data import ToolData

__all__ = ["EnvObservationResponse"]


class EnvObservationResponse(BaseModel):
    """获取观察响应"""

    state: Dict[str, object]

    tools: List[ToolData]

    done: Optional[bool] = None
