# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types import ContentSubmitResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestContent:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit(self, client: ModerationAPI) -> None:
        content = client.content.submit(
            content={
                "text": "x",
                "type": "text",
            },
        )
        assert_matches_type(ContentSubmitResponse, content, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_with_all_params(self, client: ModerationAPI) -> None:
        content = client.content.submit(
            content={
                "text": "x",
                "type": "text",
            },
            author_id="authorId",
            channel="channel",
            content_id="contentId",
            conversation_id="conversationId",
            do_not_store=True,
            metadata={"foo": "bar"},
            meta_type="profile",
            policies=[
                {
                    "id": "toxicity",
                    "flag": True,
                    "threshold": 0,
                }
            ],
            timestamp=0,
        )
        assert_matches_type(ContentSubmitResponse, content, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit(self, client: ModerationAPI) -> None:
        response = client.content.with_raw_response.submit(
            content={
                "text": "x",
                "type": "text",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        content = response.parse()
        assert_matches_type(ContentSubmitResponse, content, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit(self, client: ModerationAPI) -> None:
        with client.content.with_streaming_response.submit(
            content={
                "text": "x",
                "type": "text",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            content = response.parse()
            assert_matches_type(ContentSubmitResponse, content, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncContent:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit(self, async_client: AsyncModerationAPI) -> None:
        content = await async_client.content.submit(
            content={
                "text": "x",
                "type": "text",
            },
        )
        assert_matches_type(ContentSubmitResponse, content, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        content = await async_client.content.submit(
            content={
                "text": "x",
                "type": "text",
            },
            author_id="authorId",
            channel="channel",
            content_id="contentId",
            conversation_id="conversationId",
            do_not_store=True,
            metadata={"foo": "bar"},
            meta_type="profile",
            policies=[
                {
                    "id": "toxicity",
                    "flag": True,
                    "threshold": 0,
                }
            ],
            timestamp=0,
        )
        assert_matches_type(ContentSubmitResponse, content, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.content.with_raw_response.submit(
            content={
                "text": "x",
                "type": "text",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        content = await response.parse()
        assert_matches_type(ContentSubmitResponse, content, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.content.with_streaming_response.submit(
            content={
                "text": "x",
                "type": "text",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            content = await response.parse()
            assert_matches_type(ContentSubmitResponse, content, path=["response"])

        assert cast(Any, response.is_closed) is True
