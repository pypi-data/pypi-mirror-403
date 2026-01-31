# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types import (
    AuthorListResponse,
    AuthorCreateResponse,
    AuthorDeleteResponse,
    AuthorUpdateResponse,
    AuthorRetrieveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAuthors:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ModerationAPI) -> None:
        author = client.authors.create(
            external_id="external_id",
        )
        assert_matches_type(AuthorCreateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: ModerationAPI) -> None:
        author = client.authors.create(
            external_id="external_id",
            email="dev@stainless.com",
            external_link="https://example.com",
            first_seen=0,
            last_seen=0,
            manual_trust_level=-1,
            metadata={
                "email_verified": True,
                "identity_verified": True,
                "is_paying_customer": True,
                "phone_verified": True,
            },
            name="name",
            profile_picture="https://example.com",
        )
        assert_matches_type(AuthorCreateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ModerationAPI) -> None:
        response = client.authors.with_raw_response.create(
            external_id="external_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = response.parse()
        assert_matches_type(AuthorCreateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ModerationAPI) -> None:
        with client.authors.with_streaming_response.create(
            external_id="external_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = response.parse()
            assert_matches_type(AuthorCreateResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ModerationAPI) -> None:
        author = client.authors.retrieve(
            "id",
        )
        assert_matches_type(AuthorRetrieveResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ModerationAPI) -> None:
        response = client.authors.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = response.parse()
        assert_matches_type(AuthorRetrieveResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ModerationAPI) -> None:
        with client.authors.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = response.parse()
            assert_matches_type(AuthorRetrieveResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.authors.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: ModerationAPI) -> None:
        author = client.authors.update(
            id="id",
        )
        assert_matches_type(AuthorUpdateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: ModerationAPI) -> None:
        author = client.authors.update(
            id="id",
            email="dev@stainless.com",
            external_link="https://example.com",
            first_seen=0,
            last_seen=0,
            manual_trust_level=-1,
            metadata={
                "email_verified": True,
                "identity_verified": True,
                "is_paying_customer": True,
                "phone_verified": True,
            },
            name="name",
            profile_picture="https://example.com",
        )
        assert_matches_type(AuthorUpdateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: ModerationAPI) -> None:
        response = client.authors.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = response.parse()
        assert_matches_type(AuthorUpdateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: ModerationAPI) -> None:
        with client.authors.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = response.parse()
            assert_matches_type(AuthorUpdateResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.authors.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ModerationAPI) -> None:
        author = client.authors.list()
        assert_matches_type(AuthorListResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ModerationAPI) -> None:
        author = client.authors.list(
            content_types="contentTypes",
            last_active_date="lastActiveDate",
            member_since_date="memberSinceDate",
            page_number=0,
            page_size=0,
            sort_by="trustLevel",
            sort_direction="asc",
        )
        assert_matches_type(AuthorListResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ModerationAPI) -> None:
        response = client.authors.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = response.parse()
        assert_matches_type(AuthorListResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ModerationAPI) -> None:
        with client.authors.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = response.parse()
            assert_matches_type(AuthorListResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: ModerationAPI) -> None:
        author = client.authors.delete(
            "id",
        )
        assert_matches_type(AuthorDeleteResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: ModerationAPI) -> None:
        response = client.authors.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = response.parse()
        assert_matches_type(AuthorDeleteResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: ModerationAPI) -> None:
        with client.authors.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = response.parse()
            assert_matches_type(AuthorDeleteResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.authors.with_raw_response.delete(
                "",
            )


class TestAsyncAuthors:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.create(
            external_id="external_id",
        )
        assert_matches_type(AuthorCreateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.create(
            external_id="external_id",
            email="dev@stainless.com",
            external_link="https://example.com",
            first_seen=0,
            last_seen=0,
            manual_trust_level=-1,
            metadata={
                "email_verified": True,
                "identity_verified": True,
                "is_paying_customer": True,
                "phone_verified": True,
            },
            name="name",
            profile_picture="https://example.com",
        )
        assert_matches_type(AuthorCreateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.authors.with_raw_response.create(
            external_id="external_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = await response.parse()
        assert_matches_type(AuthorCreateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.authors.with_streaming_response.create(
            external_id="external_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = await response.parse()
            assert_matches_type(AuthorCreateResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.retrieve(
            "id",
        )
        assert_matches_type(AuthorRetrieveResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.authors.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = await response.parse()
        assert_matches_type(AuthorRetrieveResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.authors.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = await response.parse()
            assert_matches_type(AuthorRetrieveResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.authors.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.update(
            id="id",
        )
        assert_matches_type(AuthorUpdateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.update(
            id="id",
            email="dev@stainless.com",
            external_link="https://example.com",
            first_seen=0,
            last_seen=0,
            manual_trust_level=-1,
            metadata={
                "email_verified": True,
                "identity_verified": True,
                "is_paying_customer": True,
                "phone_verified": True,
            },
            name="name",
            profile_picture="https://example.com",
        )
        assert_matches_type(AuthorUpdateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.authors.with_raw_response.update(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = await response.parse()
        assert_matches_type(AuthorUpdateResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.authors.with_streaming_response.update(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = await response.parse()
            assert_matches_type(AuthorUpdateResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.authors.with_raw_response.update(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.list()
        assert_matches_type(AuthorListResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.list(
            content_types="contentTypes",
            last_active_date="lastActiveDate",
            member_since_date="memberSinceDate",
            page_number=0,
            page_size=0,
            sort_by="trustLevel",
            sort_direction="asc",
        )
        assert_matches_type(AuthorListResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.authors.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = await response.parse()
        assert_matches_type(AuthorListResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.authors.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = await response.parse()
            assert_matches_type(AuthorListResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncModerationAPI) -> None:
        author = await async_client.authors.delete(
            "id",
        )
        assert_matches_type(AuthorDeleteResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.authors.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        author = await response.parse()
        assert_matches_type(AuthorDeleteResponse, author, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.authors.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            author = await response.parse()
            assert_matches_type(AuthorDeleteResponse, author, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.authors.with_raw_response.delete(
                "",
            )
