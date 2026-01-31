# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types import AuthCreateResponse, AuthRetrieveResponse

# pyright: reportDeprecated=false

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAuth:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            auth = client.auth.create()

        assert_matches_type(AuthCreateResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.auth.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth = response.parse()
        assert_matches_type(AuthCreateResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            with client.auth.with_streaming_response.create() as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                auth = response.parse()
                assert_matches_type(AuthCreateResponse, auth, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            auth = client.auth.retrieve()

        assert_matches_type(AuthRetrieveResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            response = client.auth.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth = response.parse()
        assert_matches_type(AuthRetrieveResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            with client.auth.with_streaming_response.retrieve() as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                auth = response.parse()
                assert_matches_type(AuthRetrieveResponse, auth, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAuth:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            auth = await async_client.auth.create()

        assert_matches_type(AuthCreateResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.auth.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth = await response.parse()
        assert_matches_type(AuthCreateResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.auth.with_streaming_response.create() as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                auth = await response.parse()
                assert_matches_type(AuthCreateResponse, auth, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            auth = await async_client.auth.retrieve()

        assert_matches_type(AuthRetrieveResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            response = await async_client.auth.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        auth = await response.parse()
        assert_matches_type(AuthRetrieveResponse, auth, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.warns(DeprecationWarning):
            async with async_client.auth.with_streaming_response.retrieve() as response:
                assert not response.is_closed
                assert response.http_request.headers.get("X-Stainless-Lang") == "python"

                auth = await response.parse()
                assert_matches_type(AuthRetrieveResponse, auth, path=["response"])

        assert cast(Any, response.is_closed) is True
