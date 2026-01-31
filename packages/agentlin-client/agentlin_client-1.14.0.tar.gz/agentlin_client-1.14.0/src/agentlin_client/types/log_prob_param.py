# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

from .top_log_prob_param import TopLogProbParam

__all__ = ["LogProbParam"]


class LogProbParam(TypedDict, total=False):
    """The log probability of a token."""

    token: Required[str]

    bytes: Required[Iterable[int]]

    logprob: Required[float]

    top_logprobs: Required[Iterable[TopLogProbParam]]
