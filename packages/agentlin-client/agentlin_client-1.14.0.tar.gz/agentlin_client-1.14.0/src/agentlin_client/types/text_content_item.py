# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel
from .log_prob import LogProb
from .annotation_file_path import AnnotationFilePath
from .annotation_url_citation import AnnotationURLCitation
from .annotation_file_citation import AnnotationFileCitation
from .annotation_container_file_citation import AnnotationContainerFileCitation

__all__ = ["TextContentItem", "Annotation"]

Annotation: TypeAlias = Annotated[
    Union[AnnotationFileCitation, AnnotationURLCitation, AnnotationContainerFileCitation, AnnotationFilePath],
    PropertyInfo(discriminator="type"),
]


class TextContentItem(BaseModel):
    text: str
    """文本内容。"""

    type: Literal["text", "input_text", "output_text", "reasoning_text", "summary_text", "refusal"]
    """文本内容类型。"""

    id: Optional[int] = None
    """可选的内容引用 ID。"""

    annotations: Optional[List[Annotation]] = None
    """文本注释（如引用、链接、文件路径等），与后端 Annotation 模型一致。"""

    logprobs: Optional[List[LogProb]] = None
    """每个 token 的对数概率信息（可选）。"""

    tags: Optional[List[str]] = None
    """可选标签，用于标记内容来源或用途（如 "added_by_reference_manager"）。"""
