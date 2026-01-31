# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types.wordlist import WordAddResponse, WordRemoveResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestWords:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add(self, client: ModerationAPI) -> None:
        word = client.wordlist.words.add(
            id="id",
            words=["string"],
        )
        assert_matches_type(WordAddResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add(self, client: ModerationAPI) -> None:
        response = client.wordlist.words.with_raw_response.add(
            id="id",
            words=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        word = response.parse()
        assert_matches_type(WordAddResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add(self, client: ModerationAPI) -> None:
        with client.wordlist.words.with_streaming_response.add(
            id="id",
            words=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            word = response.parse()
            assert_matches_type(WordAddResponse, word, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_add(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.wordlist.words.with_raw_response.add(
                id="",
                words=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_remove(self, client: ModerationAPI) -> None:
        word = client.wordlist.words.remove(
            id="id",
            words=["string"],
        )
        assert_matches_type(WordRemoveResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_remove(self, client: ModerationAPI) -> None:
        response = client.wordlist.words.with_raw_response.remove(
            id="id",
            words=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        word = response.parse()
        assert_matches_type(WordRemoveResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_remove(self, client: ModerationAPI) -> None:
        with client.wordlist.words.with_streaming_response.remove(
            id="id",
            words=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            word = response.parse()
            assert_matches_type(WordRemoveResponse, word, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_remove(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.wordlist.words.with_raw_response.remove(
                id="",
                words=["string"],
            )


class TestAsyncWords:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add(self, async_client: AsyncModerationAPI) -> None:
        word = await async_client.wordlist.words.add(
            id="id",
            words=["string"],
        )
        assert_matches_type(WordAddResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.wordlist.words.with_raw_response.add(
            id="id",
            words=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        word = await response.parse()
        assert_matches_type(WordAddResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.wordlist.words.with_streaming_response.add(
            id="id",
            words=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            word = await response.parse()
            assert_matches_type(WordAddResponse, word, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_add(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.wordlist.words.with_raw_response.add(
                id="",
                words=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_remove(self, async_client: AsyncModerationAPI) -> None:
        word = await async_client.wordlist.words.remove(
            id="id",
            words=["string"],
        )
        assert_matches_type(WordRemoveResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_remove(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.wordlist.words.with_raw_response.remove(
            id="id",
            words=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        word = await response.parse()
        assert_matches_type(WordRemoveResponse, word, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_remove(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.wordlist.words.with_streaming_response.remove(
            id="id",
            words=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            word = await response.parse()
            assert_matches_type(WordRemoveResponse, word, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_remove(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.wordlist.words.with_raw_response.remove(
                id="",
                words=["string"],
            )
