# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types import QueueGetStatsResponse, QueueRetrieveResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestQueue:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ModerationAPI) -> None:
        queue = client.queue.retrieve(
            "id",
        )
        assert_matches_type(QueueRetrieveResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ModerationAPI) -> None:
        response = client.queue.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        queue = response.parse()
        assert_matches_type(QueueRetrieveResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ModerationAPI) -> None:
        with client.queue.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            queue = response.parse()
            assert_matches_type(QueueRetrieveResponse, queue, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.queue.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_stats(self, client: ModerationAPI) -> None:
        queue = client.queue.get_stats(
            id="id",
        )
        assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_stats_with_all_params(self, client: ModerationAPI) -> None:
        queue = client.queue.get_stats(
            id="id",
            within_days="withinDays",
        )
        assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_stats(self, client: ModerationAPI) -> None:
        response = client.queue.with_raw_response.get_stats(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        queue = response.parse()
        assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_stats(self, client: ModerationAPI) -> None:
        with client.queue.with_streaming_response.get_stats(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            queue = response.parse()
            assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_stats(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.queue.with_raw_response.get_stats(
                id="",
            )


class TestAsyncQueue:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncModerationAPI) -> None:
        queue = await async_client.queue.retrieve(
            "id",
        )
        assert_matches_type(QueueRetrieveResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.queue.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        queue = await response.parse()
        assert_matches_type(QueueRetrieveResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.queue.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            queue = await response.parse()
            assert_matches_type(QueueRetrieveResponse, queue, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.queue.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_stats(self, async_client: AsyncModerationAPI) -> None:
        queue = await async_client.queue.get_stats(
            id="id",
        )
        assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_stats_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        queue = await async_client.queue.get_stats(
            id="id",
            within_days="withinDays",
        )
        assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_stats(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.queue.with_raw_response.get_stats(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        queue = await response.parse()
        assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_stats(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.queue.with_streaming_response.get_stats(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            queue = await response.parse()
            assert_matches_type(QueueGetStatsResponse, queue, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_stats(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.queue.with_raw_response.get_stats(
                id="",
            )
