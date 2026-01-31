# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types.actions import (
    ExecuteExecuteResponse,
    ExecuteExecuteByIDResponse,
)

# pyright: reportDeprecated=false

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExecute:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute(self, client: ModerationAPI) -> None:
        execute = client.actions.execute.execute(
            action_key="actionKey",
        )
        assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_with_all_params(self, client: ModerationAPI) -> None:
        execute = client.actions.execute.execute(
            action_key="actionKey",
            author_ids=["string"],
            content_ids=["string"],
            duration=0,
            queue_id="queueId",
            value="value",
        )
        assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute(self, client: ModerationAPI) -> None:
        response = client.actions.execute.with_raw_response.execute(
            action_key="actionKey",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execute = response.parse()
        assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute(self, client: ModerationAPI) -> None:
        with client.actions.execute.with_streaming_response.execute(
            action_key="actionKey",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execute = response.parse()
            assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_by_id(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            execute = client.actions.execute.execute_by_id(
                action_id="actionId",
            )

        assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_by_id_with_all_params(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            execute = client.actions.execute.execute_by_id(
                action_id="actionId",
                author_ids=["string"],
                content_ids=["string"],
                queue_id="queueId",
                value="value",
            )

        assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_by_id(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.actions.execute.with_raw_response.execute_by_id(
                action_id="actionId",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execute = response.parse()
        assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_by_id(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            with client.actions.execute.with_streaming_response.execute_by_id(
                action_id="actionId",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                execute = response.parse()
                assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_execute_by_id(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            with pytest.raises(ValueError, match=r"Expected a non-empty value for `action_id` but received ''"):
                client.actions.execute.with_raw_response.execute_by_id(
                    action_id="",
                )


class TestAsyncExecute:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute(self, async_client: AsyncModerationAPI) -> None:
        execute = await async_client.actions.execute.execute(
            action_key="actionKey",
        )
        assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        execute = await async_client.actions.execute.execute(
            action_key="actionKey",
            author_ids=["string"],
            content_ids=["string"],
            duration=0,
            queue_id="queueId",
            value="value",
        )
        assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.actions.execute.with_raw_response.execute(
            action_key="actionKey",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execute = await response.parse()
        assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.actions.execute.with_streaming_response.execute(
            action_key="actionKey",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execute = await response.parse()
            assert_matches_type(ExecuteExecuteResponse, execute, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_by_id(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            execute = await async_client.actions.execute.execute_by_id(
                action_id="actionId",
            )

        assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_by_id_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            execute = await async_client.actions.execute.execute_by_id(
                action_id="actionId",
                author_ids=["string"],
                content_ids=["string"],
                queue_id="queueId",
                value="value",
            )

        assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_by_id(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.actions.execute.with_raw_response.execute_by_id(
                action_id="actionId",
            )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execute = await response.parse()
        assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_by_id(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.actions.execute.with_streaming_response.execute_by_id(
                action_id="actionId",
            ) as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                execute = await response.parse()
                assert_matches_type(ExecuteExecuteByIDResponse, execute, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_execute_by_id(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            with pytest.raises(ValueError, match=r"Expected a non-empty value for `action_id` but received ''"):
                await async_client.actions.execute.with_raw_response.execute_by_id(
                    action_id="",
                )
