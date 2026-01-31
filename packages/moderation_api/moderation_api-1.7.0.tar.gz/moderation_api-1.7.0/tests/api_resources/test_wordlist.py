# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types import (
    WordlistListResponse,
    WordlistUpdateResponse,
    WordlistRetrieveResponse,
    WordlistGetEmbeddingStatusResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestWordlist:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ModerationAPI) -> None:
        wordlist = client.wordlist.retrieve(
            "id",
        )
        assert_matches_type(WordlistRetrieveResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ModerationAPI) -> None:
        response = client.wordlist.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = response.parse()
        assert_matches_type(WordlistRetrieveResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ModerationAPI) -> None:
        with client.wordlist.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = response.parse()
            assert_matches_type(WordlistRetrieveResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.wordlist.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: ModerationAPI) -> None:
        wordlist = client.wordlist.update(
            id="id",
        )
        assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: ModerationAPI) -> None:
        wordlist = client.wordlist.update(
            id="id",
            description="description",
            key="key",
            name="name",
            strict=True,
            words=["string"],
        )
        assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: ModerationAPI) -> None:
        response = client.wordlist.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = response.parse()
        assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: ModerationAPI) -> None:
        with client.wordlist.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = response.parse()
            assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.wordlist.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ModerationAPI) -> None:
        wordlist = client.wordlist.list()
        assert_matches_type(WordlistListResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ModerationAPI) -> None:
        response = client.wordlist.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = response.parse()
        assert_matches_type(WordlistListResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ModerationAPI) -> None:
        with client.wordlist.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = response.parse()
            assert_matches_type(WordlistListResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_embedding_status(self, client: ModerationAPI) -> None:
        wordlist = client.wordlist.get_embedding_status(
            "id",
        )
        assert_matches_type(WordlistGetEmbeddingStatusResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_embedding_status(self, client: ModerationAPI) -> None:
        response = client.wordlist.with_raw_response.get_embedding_status(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = response.parse()
        assert_matches_type(WordlistGetEmbeddingStatusResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_embedding_status(self, client: ModerationAPI) -> None:
        with client.wordlist.with_streaming_response.get_embedding_status(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = response.parse()
            assert_matches_type(WordlistGetEmbeddingStatusResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_embedding_status(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.wordlist.with_raw_response.get_embedding_status(
                "",
            )


class TestAsyncWordlist:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncModerationAPI) -> None:
        wordlist = await async_client.wordlist.retrieve(
            "id",
        )
        assert_matches_type(WordlistRetrieveResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.wordlist.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = await response.parse()
        assert_matches_type(WordlistRetrieveResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.wordlist.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = await response.parse()
            assert_matches_type(WordlistRetrieveResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.wordlist.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncModerationAPI) -> None:
        wordlist = await async_client.wordlist.update(
            id="id",
        )
        assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        wordlist = await async_client.wordlist.update(
            id="id",
            description="description",
            key="key",
            name="name",
            strict=True,
            words=["string"],
        )
        assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.wordlist.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = await response.parse()
        assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.wordlist.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = await response.parse()
            assert_matches_type(WordlistUpdateResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.wordlist.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncModerationAPI) -> None:
        wordlist = await async_client.wordlist.list()
        assert_matches_type(WordlistListResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.wordlist.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = await response.parse()
        assert_matches_type(WordlistListResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.wordlist.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = await response.parse()
            assert_matches_type(WordlistListResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_embedding_status(self, async_client: AsyncModerationAPI) -> None:
        wordlist = await async_client.wordlist.get_embedding_status(
            "id",
        )
        assert_matches_type(WordlistGetEmbeddingStatusResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_embedding_status(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.wordlist.with_raw_response.get_embedding_status(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        wordlist = await response.parse()
        assert_matches_type(WordlistGetEmbeddingStatusResponse, wordlist, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_embedding_status(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.wordlist.with_streaming_response.get_embedding_status(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            wordlist = await response.parse()
            assert_matches_type(WordlistGetEmbeddingStatusResponse, wordlist, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_embedding_status(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.wordlist.with_raw_response.get_embedding_status(
                "",
            )
