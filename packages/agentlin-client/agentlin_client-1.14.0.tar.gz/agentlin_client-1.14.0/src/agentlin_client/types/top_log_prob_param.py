# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

__all__ = ["TopLogProbParam"]


class TopLogProbParam(TypedDict, total=False):
    """The top log probability of a token."""

    token: Required[str]

    bytes: Required[Iterable[int]]

    logprob: Required[float]
