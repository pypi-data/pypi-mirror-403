# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .log_prob_param import LogProbParam
from .annotation_file_path_param import AnnotationFilePathParam
from .annotation_url_citation_param import AnnotationURLCitationParam
from .annotation_file_citation_param import AnnotationFileCitationParam
from .annotation_container_file_citation_param import AnnotationContainerFileCitationParam

__all__ = ["TextContentItemParam", "Annotation"]

Annotation: TypeAlias = Union[
    AnnotationFileCitationParam,
    AnnotationURLCitationParam,
    AnnotationContainerFileCitationParam,
    AnnotationFilePathParam,
]


class TextContentItemParam(TypedDict, total=False):
    text: Required[str]
    """文本内容。"""

    type: Required[Literal["text", "input_text", "output_text", "reasoning_text", "summary_text", "refusal"]]
    """文本内容类型。"""

    id: int
    """可选的内容引用 ID。"""

    annotations: Iterable[Annotation]
    """文本注释（如引用、链接、文件路径等），与后端 Annotation 模型一致。"""

    logprobs: Iterable[LogProbParam]
    """每个 token 的对数概率信息（可选）。"""

    tags: SequenceNotStr[str]
    """可选标签，用于标记内容来源或用途（如 "added_by_reference_manager"）。"""
