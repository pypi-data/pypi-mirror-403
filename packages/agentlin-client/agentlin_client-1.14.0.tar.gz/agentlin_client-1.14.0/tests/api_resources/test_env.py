# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from agentlin_client import Client, AsyncClient
from agentlin_client.types import (
    EnvInfo,
    EnvInfoResponse,
    EnvCloseResponse,
    EnvResetResponse,
    EnvCreateResponse,
    EnvSessionResponse,
    EnvSessionsResponse,
    EnvObservationResponse,
)
from agentlin_client.pagination import SyncListEnvs, AsyncListEnvs

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEnv:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Client) -> None:
        env = client.env.create()
        assert_matches_type(EnvCreateResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Client) -> None:
        env = client.env.create(
            client_id="client_id",
            env_class_path="env_class_path",
            env_id="env_id",
            env_init_kwargs={"foo": "bar"},
            env_vars={"foo": "string"},
            session_id="session_id",
            user_id="user_id",
        )
        assert_matches_type(EnvCreateResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Client) -> None:
        response = client.env.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvCreateResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Client) -> None:
        with client.env.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvCreateResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Client) -> None:
        env = client.env.list()
        assert_matches_type(SyncListEnvs[EnvInfo], env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Client) -> None:
        env = client.env.list(
            ending_before="ending_before",
            limit=0,
            starting_after="starting_after",
        )
        assert_matches_type(SyncListEnvs[EnvInfo], env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Client) -> None:
        response = client.env.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(SyncListEnvs[EnvInfo], env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Client) -> None:
        with client.env.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(SyncListEnvs[EnvInfo], env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_clean_session(self, client: Client) -> None:
        env = client.env.clean_session()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_clean_session_with_all_params(self, client: Client) -> None:
        env = client.env.clean_session(
            inactive_seconds=0,
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_clean_session(self, client: Client) -> None:
        response = client.env.with_raw_response.clean_session()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_clean_session(self, client: Client) -> None:
        with client.env.with_streaming_response.clean_session() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(object, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_close(self, client: Client) -> None:
        env = client.env.close(
            session_id="session_id",
        )
        assert_matches_type(EnvCloseResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_close(self, client: Client) -> None:
        response = client.env.with_raw_response.close(
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvCloseResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_close(self, client: Client) -> None:
        with client.env.with_streaming_response.close(
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvCloseResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_session(self, client: Client) -> None:
        env = client.env.delete_session(
            "session_id",
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete_session(self, client: Client) -> None:
        response = client.env.with_raw_response.delete_session(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete_session(self, client: Client) -> None:
        with client.env.with_streaming_response.delete_session(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(object, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete_session(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.env.with_raw_response.delete_session(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_info(self, client: Client) -> None:
        env = client.env.info(
            "env_id",
        )
        assert_matches_type(EnvInfoResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_info(self, client: Client) -> None:
        response = client.env.with_raw_response.info(
            "env_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvInfoResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_info(self, client: Client) -> None:
        with client.env.with_streaming_response.info(
            "env_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvInfoResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_info(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `env_id` but received ''"):
            client.env.with_raw_response.info(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_observation(self, client: Client) -> None:
        env = client.env.observation(
            session_id="session_id",
        )
        assert_matches_type(EnvObservationResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_observation(self, client: Client) -> None:
        response = client.env.with_raw_response.observation(
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvObservationResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_observation(self, client: Client) -> None:
        with client.env.with_streaming_response.observation(
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvObservationResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_reset(self, client: Client) -> None:
        env = client.env.reset(
            session_id="session_id",
        )
        assert_matches_type(EnvResetResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_reset_with_all_params(self, client: Client) -> None:
        env = client.env.reset(
            session_id="session_id",
            options={"foo": "bar"},
            seed=0,
        )
        assert_matches_type(EnvResetResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_reset(self, client: Client) -> None:
        response = client.env.with_raw_response.reset(
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvResetResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_reset(self, client: Client) -> None:
        with client.env.with_streaming_response.reset(
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvResetResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_session(self, client: Client) -> None:
        env = client.env.session(
            "session_id",
        )
        assert_matches_type(EnvSessionResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_session(self, client: Client) -> None:
        response = client.env.with_raw_response.session(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvSessionResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_session(self, client: Client) -> None:
        with client.env.with_streaming_response.session(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvSessionResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_session(self, client: Client) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.env.with_raw_response.session(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sessions(self, client: Client) -> None:
        env = client.env.sessions()
        assert_matches_type(EnvSessionsResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_sessions_with_all_params(self, client: Client) -> None:
        env = client.env.sessions(
            user_id="user_id",
        )
        assert_matches_type(EnvSessionsResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_sessions(self, client: Client) -> None:
        response = client.env.with_raw_response.sessions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(EnvSessionsResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_sessions(self, client: Client) -> None:
        with client.env.with_streaming_response.sessions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(EnvSessionsResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_step(self, client: Client) -> None:
        env = client.env.step(
            session_id="session_id",
            tool_name="tool_name",
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_step_with_all_params(self, client: Client) -> None:
        env = client.env.step(
            session_id="session_id",
            tool_name="tool_name",
            env_vars={"foo": "string"},
            request_id="request_id",
            stream=True,
            task_id="task_id",
            tool_args={"foo": "bar"},
            user_id="user_id",
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_step(self, client: Client) -> None:
        response = client.env.with_raw_response.step(
            session_id="session_id",
            tool_name="tool_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = response.parse()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_step(self, client: Client) -> None:
        with client.env.with_streaming_response.step(
            session_id="session_id",
            tool_name="tool_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = response.parse()
            assert_matches_type(object, env, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncEnv:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncClient) -> None:
        env = await async_client.env.create()
        assert_matches_type(EnvCreateResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncClient) -> None:
        env = await async_client.env.create(
            client_id="client_id",
            env_class_path="env_class_path",
            env_id="env_id",
            env_init_kwargs={"foo": "bar"},
            env_vars={"foo": "string"},
            session_id="session_id",
            user_id="user_id",
        )
        assert_matches_type(EnvCreateResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvCreateResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvCreateResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncClient) -> None:
        env = await async_client.env.list()
        assert_matches_type(AsyncListEnvs[EnvInfo], env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncClient) -> None:
        env = await async_client.env.list(
            ending_before="ending_before",
            limit=0,
            starting_after="starting_after",
        )
        assert_matches_type(AsyncListEnvs[EnvInfo], env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(AsyncListEnvs[EnvInfo], env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(AsyncListEnvs[EnvInfo], env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_clean_session(self, async_client: AsyncClient) -> None:
        env = await async_client.env.clean_session()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_clean_session_with_all_params(self, async_client: AsyncClient) -> None:
        env = await async_client.env.clean_session(
            inactive_seconds=0,
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_clean_session(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.clean_session()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_clean_session(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.clean_session() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(object, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_close(self, async_client: AsyncClient) -> None:
        env = await async_client.env.close(
            session_id="session_id",
        )
        assert_matches_type(EnvCloseResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_close(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.close(
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvCloseResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_close(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.close(
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvCloseResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_session(self, async_client: AsyncClient) -> None:
        env = await async_client.env.delete_session(
            "session_id",
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete_session(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.delete_session(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete_session(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.delete_session(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(object, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete_session(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.env.with_raw_response.delete_session(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_info(self, async_client: AsyncClient) -> None:
        env = await async_client.env.info(
            "env_id",
        )
        assert_matches_type(EnvInfoResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_info(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.info(
            "env_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvInfoResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_info(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.info(
            "env_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvInfoResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_info(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `env_id` but received ''"):
            await async_client.env.with_raw_response.info(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_observation(self, async_client: AsyncClient) -> None:
        env = await async_client.env.observation(
            session_id="session_id",
        )
        assert_matches_type(EnvObservationResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_observation(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.observation(
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvObservationResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_observation(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.observation(
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvObservationResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_reset(self, async_client: AsyncClient) -> None:
        env = await async_client.env.reset(
            session_id="session_id",
        )
        assert_matches_type(EnvResetResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_reset_with_all_params(self, async_client: AsyncClient) -> None:
        env = await async_client.env.reset(
            session_id="session_id",
            options={"foo": "bar"},
            seed=0,
        )
        assert_matches_type(EnvResetResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_reset(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.reset(
            session_id="session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvResetResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_reset(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.reset(
            session_id="session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvResetResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_session(self, async_client: AsyncClient) -> None:
        env = await async_client.env.session(
            "session_id",
        )
        assert_matches_type(EnvSessionResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_session(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.session(
            "session_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvSessionResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_session(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.session(
            "session_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvSessionResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_session(self, async_client: AsyncClient) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.env.with_raw_response.session(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sessions(self, async_client: AsyncClient) -> None:
        env = await async_client.env.sessions()
        assert_matches_type(EnvSessionsResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_sessions_with_all_params(self, async_client: AsyncClient) -> None:
        env = await async_client.env.sessions(
            user_id="user_id",
        )
        assert_matches_type(EnvSessionsResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_sessions(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.sessions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(EnvSessionsResponse, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_sessions(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.sessions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(EnvSessionsResponse, env, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_step(self, async_client: AsyncClient) -> None:
        env = await async_client.env.step(
            session_id="session_id",
            tool_name="tool_name",
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_step_with_all_params(self, async_client: AsyncClient) -> None:
        env = await async_client.env.step(
            session_id="session_id",
            tool_name="tool_name",
            env_vars={"foo": "string"},
            request_id="request_id",
            stream=True,
            task_id="task_id",
            tool_args={"foo": "bar"},
            user_id="user_id",
        )
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_step(self, async_client: AsyncClient) -> None:
        response = await async_client.env.with_raw_response.step(
            session_id="session_id",
            tool_name="tool_name",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        env = await response.parse()
        assert_matches_type(object, env, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_step(self, async_client: AsyncClient) -> None:
        async with async_client.env.with_streaming_response.step(
            session_id="session_id",
            tool_name="tool_name",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            env = await response.parse()
            assert_matches_type(object, env, path=["response"])

        assert cast(Any, response.is_closed) is True
