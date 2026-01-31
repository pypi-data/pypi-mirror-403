# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from tests.utils import assert_matches_type
from moderation_api import ModerationAPI, AsyncModerationAPI
from moderation_api.types.queue import (
    ItemListResponse,
    ItemResolveResponse,
    ItemUnresolveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestItems:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ModerationAPI) -> None:
        item = client.queue.items.list(
            id="id",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ModerationAPI) -> None:
        item = client.queue.items.list(
            id="id",
            after_date="afterDate",
            author_id="authorId",
            before_date="beforeDate",
            conversation_ids="conversationIds",
            filtered_action_ids="filteredActionIds",
            include_resolved="includeResolved",
            labels="labels",
            page_number=0,
            page_size=0,
            sort_direction="asc",
            sort_field="createdAt",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ModerationAPI) -> None:
        response = client.queue.items.with_raw_response.list(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ModerationAPI) -> None:
        with client.queue.items.with_streaming_response.list(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemListResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.queue.items.with_raw_response.list(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_resolve(self, client: ModerationAPI) -> None:
        item = client.queue.items.resolve(
            item_id="itemId",
            id="id",
        )
        assert_matches_type(ItemResolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_resolve_with_all_params(self, client: ModerationAPI) -> None:
        item = client.queue.items.resolve(
            item_id="itemId",
            id="id",
            comment="comment",
        )
        assert_matches_type(ItemResolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_resolve(self, client: ModerationAPI) -> None:
        response = client.queue.items.with_raw_response.resolve(
            item_id="itemId",
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemResolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_resolve(self, client: ModerationAPI) -> None:
        with client.queue.items.with_streaming_response.resolve(
            item_id="itemId",
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemResolveResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_resolve(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.queue.items.with_raw_response.resolve(
                item_id="itemId",
                id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            client.queue.items.with_raw_response.resolve(
                item_id="",
                id="id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_unresolve(self, client: ModerationAPI) -> None:
        item = client.queue.items.unresolve(
            item_id="itemId",
            id="id",
        )
        assert_matches_type(ItemUnresolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_unresolve_with_all_params(self, client: ModerationAPI) -> None:
        item = client.queue.items.unresolve(
            item_id="itemId",
            id="id",
            comment="comment",
        )
        assert_matches_type(ItemUnresolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_unresolve(self, client: ModerationAPI) -> None:
        response = client.queue.items.with_raw_response.unresolve(
            item_id="itemId",
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemUnresolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_unresolve(self, client: ModerationAPI) -> None:
        with client.queue.items.with_streaming_response.unresolve(
            item_id="itemId",
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemUnresolveResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_unresolve(self, client: ModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.queue.items.with_raw_response.unresolve(
                item_id="itemId",
                id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            client.queue.items.with_raw_response.unresolve(
                item_id="",
                id="id",
            )


class TestAsyncItems:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncModerationAPI) -> None:
        item = await async_client.queue.items.list(
            id="id",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        item = await async_client.queue.items.list(
            id="id",
            after_date="afterDate",
            author_id="authorId",
            before_date="beforeDate",
            conversation_ids="conversationIds",
            filtered_action_ids="filteredActionIds",
            include_resolved="includeResolved",
            labels="labels",
            page_number=0,
            page_size=0,
            sort_direction="asc",
            sort_field="createdAt",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.queue.items.with_raw_response.list(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.queue.items.with_streaming_response.list(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemListResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.queue.items.with_raw_response.list(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_resolve(self, async_client: AsyncModerationAPI) -> None:
        item = await async_client.queue.items.resolve(
            item_id="itemId",
            id="id",
        )
        assert_matches_type(ItemResolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_resolve_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        item = await async_client.queue.items.resolve(
            item_id="itemId",
            id="id",
            comment="comment",
        )
        assert_matches_type(ItemResolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_resolve(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.queue.items.with_raw_response.resolve(
            item_id="itemId",
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemResolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_resolve(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.queue.items.with_streaming_response.resolve(
            item_id="itemId",
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemResolveResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_resolve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.queue.items.with_raw_response.resolve(
                item_id="itemId",
                id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            await async_client.queue.items.with_raw_response.resolve(
                item_id="",
                id="id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_unresolve(self, async_client: AsyncModerationAPI) -> None:
        item = await async_client.queue.items.unresolve(
            item_id="itemId",
            id="id",
        )
        assert_matches_type(ItemUnresolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_unresolve_with_all_params(self, async_client: AsyncModerationAPI) -> None:
        item = await async_client.queue.items.unresolve(
            item_id="itemId",
            id="id",
            comment="comment",
        )
        assert_matches_type(ItemUnresolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_unresolve(self, async_client: AsyncModerationAPI) -> None:
        response = await async_client.queue.items.with_raw_response.unresolve(
            item_id="itemId",
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemUnresolveResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_unresolve(self, async_client: AsyncModerationAPI) -> None:
        async with async_client.queue.items.with_streaming_response.unresolve(
            item_id="itemId",
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemUnresolveResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_unresolve(self, async_client: AsyncModerationAPI) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.queue.items.with_raw_response.unresolve(
                item_id="itemId",
                id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `item_id` but received ''"):
            await async_client.queue.items.with_raw_response.unresolve(
                item_id="",
                id="id",
            )
