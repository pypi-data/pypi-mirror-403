# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ..types import (
    env_list_params,
    env_step_params,
    env_close_params,
    env_reset_params,
    env_create_params,
    env_sessions_params,
    env_observation_params,
    env_clean_session_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncListEnvs, AsyncListEnvs
from .._base_client import AsyncPaginator, make_request_options
from ..types.env_info import EnvInfo
from ..types.env_info_response import EnvInfoResponse
from ..types.env_close_response import EnvCloseResponse
from ..types.env_reset_response import EnvResetResponse
from ..types.env_create_response import EnvCreateResponse
from ..types.env_session_response import EnvSessionResponse
from ..types.env_sessions_response import EnvSessionsResponse
from ..types.env_observation_response import EnvObservationResponse

__all__ = ["EnvResource", "AsyncEnvResource"]


class EnvResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EnvResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LinXueyuanStdio/agentlin-client-python#accessing-raw-response-data-eg-headers
        """
        return EnvResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> EnvResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LinXueyuanStdio/agentlin-client-python#with_streaming_response
        """
        return EnvResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        client_id: str | Omit = omit,
        env_class_path: Optional[str] | Omit = omit,
        env_id: Optional[str] | Omit = omit,
        env_init_kwargs: Optional[Dict[str, object]] | Omit = omit,
        env_vars: Optional[Dict[str, str]] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvCreateResponse:
        """
        创建新的环境实例

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/env/create",
            body=maybe_transform(
                {
                    "client_id": client_id,
                    "env_class_path": env_class_path,
                    "env_id": env_id,
                    "env_init_kwargs": env_init_kwargs,
                    "env_vars": env_vars,
                    "session_id": session_id,
                    "user_id": user_id,
                },
                env_create_params.EnvCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvCreateResponse,
        )

    def list(
        self,
        *,
        ending_before: Optional[str] | Omit = omit,
        limit: Optional[int] | Omit = omit,
        starting_after: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncListEnvs[EnvInfo]:
        """
        列出所有可用的环境

        Args:
          ending_before: Cursor for pagination

          limit: Maximum number of environments to return

          starting_after: Cursor for pagination

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/env",
            page=SyncListEnvs[EnvInfo],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "limit": limit,
                        "starting_after": starting_after,
                    },
                    env_list_params.EnvListParams,
                ),
            ),
            model=EnvInfo,
        )

    def clean_session(
        self,
        *,
        inactive_seconds: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        清理不活跃的会话

        Args:
          inactive_seconds: Inactive threshold in seconds

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/env/sessions/cleanup",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"inactive_seconds": inactive_seconds}, env_clean_session_params.EnvCleanSessionParams
                ),
            ),
            cast_to=object,
        )

    def close(
        self,
        *,
        session_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvCloseResponse:
        """
        关闭并清理环境

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/env/close",
            body=maybe_transform({"session_id": session_id}, env_close_params.EnvCloseParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvCloseResponse,
        )

    def delete_session(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        删除指定会话

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._delete(
            f"/env/session/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def info(
        self,
        env_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvInfoResponse:
        """
        获取指定环境的详细信息

        Args:
          env_id: Environment module path or name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not env_id:
            raise ValueError(f"Expected a non-empty value for `env_id` but received {env_id!r}")
        return self._get(
            f"/env/{env_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvInfoResponse,
        )

    def observation(
        self,
        *,
        session_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvObservationResponse:
        """
        获取当前环境观察、工具列表和完成状态

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/env/observation",
            body=maybe_transform({"session_id": session_id}, env_observation_params.EnvObservationParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvObservationResponse,
        )

    def reset(
        self,
        *,
        session_id: str,
        options: Optional[Dict[str, object]] | Omit = omit,
        seed: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvResetResponse:
        """
        重置环境到初始状态

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/env/reset",
            body=maybe_transform(
                {
                    "session_id": session_id,
                    "options": options,
                    "seed": seed,
                },
                env_reset_params.EnvResetParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvResetResponse,
        )

    def session(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvSessionResponse:
        """
        获取会话详细信息

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return self._get(
            f"/env/session/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvSessionResponse,
        )

    def sessions(
        self,
        *,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvSessionsResponse:
        """
        列出所有或指定用户的会话

        Args:
          user_id: Filter by user ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/env/sessions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"user_id": user_id}, env_sessions_params.EnvSessionsParams),
            ),
            cast_to=EnvSessionsResponse,
        )

    def step(
        self,
        *,
        session_id: str,
        tool_name: str,
        env_vars: Optional[Dict[str, str]] | Omit = omit,
        request_id: Optional[str] | Omit = omit,
        stream: bool | Omit = omit,
        task_id: Optional[str] | Omit = omit,
        tool_args: Dict[str, object] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        在环境中执行工具调用步骤（支持流式和非流式）

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/env/step",
            body=maybe_transform(
                {
                    "session_id": session_id,
                    "tool_name": tool_name,
                    "env_vars": env_vars,
                    "request_id": request_id,
                    "stream": stream,
                    "task_id": task_id,
                    "tool_args": tool_args,
                    "user_id": user_id,
                },
                env_step_params.EnvStepParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncEnvResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEnvResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/LinXueyuanStdio/agentlin-client-python#accessing-raw-response-data-eg-headers
        """
        return AsyncEnvResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncEnvResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/LinXueyuanStdio/agentlin-client-python#with_streaming_response
        """
        return AsyncEnvResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        client_id: str | Omit = omit,
        env_class_path: Optional[str] | Omit = omit,
        env_id: Optional[str] | Omit = omit,
        env_init_kwargs: Optional[Dict[str, object]] | Omit = omit,
        env_vars: Optional[Dict[str, str]] | Omit = omit,
        session_id: Optional[str] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvCreateResponse:
        """
        创建新的环境实例

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/env/create",
            body=await async_maybe_transform(
                {
                    "client_id": client_id,
                    "env_class_path": env_class_path,
                    "env_id": env_id,
                    "env_init_kwargs": env_init_kwargs,
                    "env_vars": env_vars,
                    "session_id": session_id,
                    "user_id": user_id,
                },
                env_create_params.EnvCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvCreateResponse,
        )

    def list(
        self,
        *,
        ending_before: Optional[str] | Omit = omit,
        limit: Optional[int] | Omit = omit,
        starting_after: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[EnvInfo, AsyncListEnvs[EnvInfo]]:
        """
        列出所有可用的环境

        Args:
          ending_before: Cursor for pagination

          limit: Maximum number of environments to return

          starting_after: Cursor for pagination

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/env",
            page=AsyncListEnvs[EnvInfo],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ending_before": ending_before,
                        "limit": limit,
                        "starting_after": starting_after,
                    },
                    env_list_params.EnvListParams,
                ),
            ),
            model=EnvInfo,
        )

    async def clean_session(
        self,
        *,
        inactive_seconds: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        清理不活跃的会话

        Args:
          inactive_seconds: Inactive threshold in seconds

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/env/sessions/cleanup",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"inactive_seconds": inactive_seconds}, env_clean_session_params.EnvCleanSessionParams
                ),
            ),
            cast_to=object,
        )

    async def close(
        self,
        *,
        session_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvCloseResponse:
        """
        关闭并清理环境

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/env/close",
            body=await async_maybe_transform({"session_id": session_id}, env_close_params.EnvCloseParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvCloseResponse,
        )

    async def delete_session(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        删除指定会话

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._delete(
            f"/env/session/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def info(
        self,
        env_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvInfoResponse:
        """
        获取指定环境的详细信息

        Args:
          env_id: Environment module path or name

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not env_id:
            raise ValueError(f"Expected a non-empty value for `env_id` but received {env_id!r}")
        return await self._get(
            f"/env/{env_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvInfoResponse,
        )

    async def observation(
        self,
        *,
        session_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvObservationResponse:
        """
        获取当前环境观察、工具列表和完成状态

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/env/observation",
            body=await async_maybe_transform({"session_id": session_id}, env_observation_params.EnvObservationParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvObservationResponse,
        )

    async def reset(
        self,
        *,
        session_id: str,
        options: Optional[Dict[str, object]] | Omit = omit,
        seed: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvResetResponse:
        """
        重置环境到初始状态

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/env/reset",
            body=await async_maybe_transform(
                {
                    "session_id": session_id,
                    "options": options,
                    "seed": seed,
                },
                env_reset_params.EnvResetParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvResetResponse,
        )

    async def session(
        self,
        session_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvSessionResponse:
        """
        获取会话详细信息

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not session_id:
            raise ValueError(f"Expected a non-empty value for `session_id` but received {session_id!r}")
        return await self._get(
            f"/env/session/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=EnvSessionResponse,
        )

    async def sessions(
        self,
        *,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> EnvSessionsResponse:
        """
        列出所有或指定用户的会话

        Args:
          user_id: Filter by user ID

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/env/sessions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"user_id": user_id}, env_sessions_params.EnvSessionsParams),
            ),
            cast_to=EnvSessionsResponse,
        )

    async def step(
        self,
        *,
        session_id: str,
        tool_name: str,
        env_vars: Optional[Dict[str, str]] | Omit = omit,
        request_id: Optional[str] | Omit = omit,
        stream: bool | Omit = omit,
        task_id: Optional[str] | Omit = omit,
        tool_args: Dict[str, object] | Omit = omit,
        user_id: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        在环境中执行工具调用步骤（支持流式和非流式）

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/env/step",
            body=await async_maybe_transform(
                {
                    "session_id": session_id,
                    "tool_name": tool_name,
                    "env_vars": env_vars,
                    "request_id": request_id,
                    "stream": stream,
                    "task_id": task_id,
                    "tool_args": tool_args,
                    "user_id": user_id,
                },
                env_step_params.EnvStepParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class EnvResourceWithRawResponse:
    def __init__(self, env: EnvResource) -> None:
        self._env = env

        self.create = to_raw_response_wrapper(
            env.create,
        )
        self.list = to_raw_response_wrapper(
            env.list,
        )
        self.clean_session = to_raw_response_wrapper(
            env.clean_session,
        )
        self.close = to_raw_response_wrapper(
            env.close,
        )
        self.delete_session = to_raw_response_wrapper(
            env.delete_session,
        )
        self.info = to_raw_response_wrapper(
            env.info,
        )
        self.observation = to_raw_response_wrapper(
            env.observation,
        )
        self.reset = to_raw_response_wrapper(
            env.reset,
        )
        self.session = to_raw_response_wrapper(
            env.session,
        )
        self.sessions = to_raw_response_wrapper(
            env.sessions,
        )
        self.step = to_raw_response_wrapper(
            env.step,
        )


class AsyncEnvResourceWithRawResponse:
    def __init__(self, env: AsyncEnvResource) -> None:
        self._env = env

        self.create = async_to_raw_response_wrapper(
            env.create,
        )
        self.list = async_to_raw_response_wrapper(
            env.list,
        )
        self.clean_session = async_to_raw_response_wrapper(
            env.clean_session,
        )
        self.close = async_to_raw_response_wrapper(
            env.close,
        )
        self.delete_session = async_to_raw_response_wrapper(
            env.delete_session,
        )
        self.info = async_to_raw_response_wrapper(
            env.info,
        )
        self.observation = async_to_raw_response_wrapper(
            env.observation,
        )
        self.reset = async_to_raw_response_wrapper(
            env.reset,
        )
        self.session = async_to_raw_response_wrapper(
            env.session,
        )
        self.sessions = async_to_raw_response_wrapper(
            env.sessions,
        )
        self.step = async_to_raw_response_wrapper(
            env.step,
        )


class EnvResourceWithStreamingResponse:
    def __init__(self, env: EnvResource) -> None:
        self._env = env

        self.create = to_streamed_response_wrapper(
            env.create,
        )
        self.list = to_streamed_response_wrapper(
            env.list,
        )
        self.clean_session = to_streamed_response_wrapper(
            env.clean_session,
        )
        self.close = to_streamed_response_wrapper(
            env.close,
        )
        self.delete_session = to_streamed_response_wrapper(
            env.delete_session,
        )
        self.info = to_streamed_response_wrapper(
            env.info,
        )
        self.observation = to_streamed_response_wrapper(
            env.observation,
        )
        self.reset = to_streamed_response_wrapper(
            env.reset,
        )
        self.session = to_streamed_response_wrapper(
            env.session,
        )
        self.sessions = to_streamed_response_wrapper(
            env.sessions,
        )
        self.step = to_streamed_response_wrapper(
            env.step,
        )


class AsyncEnvResourceWithStreamingResponse:
    def __init__(self, env: AsyncEnvResource) -> None:
        self._env = env

        self.create = async_to_streamed_response_wrapper(
            env.create,
        )
        self.list = async_to_streamed_response_wrapper(
            env.list,
        )
        self.clean_session = async_to_streamed_response_wrapper(
            env.clean_session,
        )
        self.close = async_to_streamed_response_wrapper(
            env.close,
        )
        self.delete_session = async_to_streamed_response_wrapper(
            env.delete_session,
        )
        self.info = async_to_streamed_response_wrapper(
            env.info,
        )
        self.observation = async_to_streamed_response_wrapper(
            env.observation,
        )
        self.reset = async_to_streamed_response_wrapper(
            env.reset,
        )
        self.session = async_to_streamed_response_wrapper(
            env.session,
        )
        self.sessions = async_to_streamed_response_wrapper(
            env.sessions,
        )
        self.step = async_to_streamed_response_wrapper(
            env.step,
        )
