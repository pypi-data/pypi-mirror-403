# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.queue import item_list_params, item_resolve_params, item_unresolve_params
from ..._base_client import make_request_options
from ...types.queue.item_list_response import ItemListResponse
from ...types.queue.item_resolve_response import ItemResolveResponse
from ...types.queue.item_unresolve_response import ItemUnresolveResponse

__all__ = ["ItemsResource", "AsyncItemsResource"]


class ItemsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return ItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return ItemsResourceWithStreamingResponse(self)

    def list(
        self,
        id: str,
        *,
        after_date: str | Omit = omit,
        author_id: str | Omit = omit,
        before_date: str | Omit = omit,
        conversation_ids: str | Omit = omit,
        filtered_action_ids: str | Omit = omit,
        include_resolved: str | Omit = omit,
        labels: str | Omit = omit,
        page_number: float | Omit = omit,
        page_size: float | Omit = omit,
        sort_direction: Literal["asc", "desc"] | Omit = omit,
        sort_field: Literal["createdAt", "severity", "reviewedAt"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ItemListResponse:
        """
        Get paginated list of items in a moderation queue with filtering options

        Args:
          id: The queue ID

          page_number: Page number to fetch

          page_size: Number of items per page

          sort_direction: Sort direction

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/queue/{id}/items",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after_date": after_date,
                        "author_id": author_id,
                        "before_date": before_date,
                        "conversation_ids": conversation_ids,
                        "filtered_action_ids": filtered_action_ids,
                        "include_resolved": include_resolved,
                        "labels": labels,
                        "page_number": page_number,
                        "page_size": page_size,
                        "sort_direction": sort_direction,
                        "sort_field": sort_field,
                    },
                    item_list_params.ItemListParams,
                ),
            ),
            cast_to=ItemListResponse,
        )

    def resolve(
        self,
        item_id: str,
        *,
        id: str,
        comment: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ItemResolveResponse:
        """
        Mark a queue item as resolved with a specific moderation action

        Args:
          id: The queue ID

          item_id: The item ID to resolve

          comment: Optional comment

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        if not item_id:
            raise ValueError(f"Expected a non-empty value for `item_id` but received {item_id!r}")
        return self._post(
            f"/queue/{id}/items/{item_id}/resolve",
            body=maybe_transform({"comment": comment}, item_resolve_params.ItemResolveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ItemResolveResponse,
        )

    def unresolve(
        self,
        item_id: str,
        *,
        id: str,
        comment: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ItemUnresolveResponse:
        """
        Mark a previously resolved queue item as unresolved/pending

        Args:
          id: The queue ID

          item_id: The item ID to unresolve

          comment: Optional reason for unresolving the item

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        if not item_id:
            raise ValueError(f"Expected a non-empty value for `item_id` but received {item_id!r}")
        return self._post(
            f"/queue/{id}/items/{item_id}/unresolve",
            body=maybe_transform({"comment": comment}, item_unresolve_params.ItemUnresolveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ItemUnresolveResponse,
        )


class AsyncItemsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AsyncItemsResourceWithStreamingResponse(self)

    async def list(
        self,
        id: str,
        *,
        after_date: str | Omit = omit,
        author_id: str | Omit = omit,
        before_date: str | Omit = omit,
        conversation_ids: str | Omit = omit,
        filtered_action_ids: str | Omit = omit,
        include_resolved: str | Omit = omit,
        labels: str | Omit = omit,
        page_number: float | Omit = omit,
        page_size: float | Omit = omit,
        sort_direction: Literal["asc", "desc"] | Omit = omit,
        sort_field: Literal["createdAt", "severity", "reviewedAt"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ItemListResponse:
        """
        Get paginated list of items in a moderation queue with filtering options

        Args:
          id: The queue ID

          page_number: Page number to fetch

          page_size: Number of items per page

          sort_direction: Sort direction

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/queue/{id}/items",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after_date": after_date,
                        "author_id": author_id,
                        "before_date": before_date,
                        "conversation_ids": conversation_ids,
                        "filtered_action_ids": filtered_action_ids,
                        "include_resolved": include_resolved,
                        "labels": labels,
                        "page_number": page_number,
                        "page_size": page_size,
                        "sort_direction": sort_direction,
                        "sort_field": sort_field,
                    },
                    item_list_params.ItemListParams,
                ),
            ),
            cast_to=ItemListResponse,
        )

    async def resolve(
        self,
        item_id: str,
        *,
        id: str,
        comment: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ItemResolveResponse:
        """
        Mark a queue item as resolved with a specific moderation action

        Args:
          id: The queue ID

          item_id: The item ID to resolve

          comment: Optional comment

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        if not item_id:
            raise ValueError(f"Expected a non-empty value for `item_id` but received {item_id!r}")
        return await self._post(
            f"/queue/{id}/items/{item_id}/resolve",
            body=await async_maybe_transform({"comment": comment}, item_resolve_params.ItemResolveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ItemResolveResponse,
        )

    async def unresolve(
        self,
        item_id: str,
        *,
        id: str,
        comment: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ItemUnresolveResponse:
        """
        Mark a previously resolved queue item as unresolved/pending

        Args:
          id: The queue ID

          item_id: The item ID to unresolve

          comment: Optional reason for unresolving the item

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        if not item_id:
            raise ValueError(f"Expected a non-empty value for `item_id` but received {item_id!r}")
        return await self._post(
            f"/queue/{id}/items/{item_id}/unresolve",
            body=await async_maybe_transform({"comment": comment}, item_unresolve_params.ItemUnresolveParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ItemUnresolveResponse,
        )


class ItemsResourceWithRawResponse:
    def __init__(self, items: ItemsResource) -> None:
        self._items = items

        self.list = to_raw_response_wrapper(
            items.list,
        )
        self.resolve = to_raw_response_wrapper(
            items.resolve,
        )
        self.unresolve = to_raw_response_wrapper(
            items.unresolve,
        )


class AsyncItemsResourceWithRawResponse:
    def __init__(self, items: AsyncItemsResource) -> None:
        self._items = items

        self.list = async_to_raw_response_wrapper(
            items.list,
        )
        self.resolve = async_to_raw_response_wrapper(
            items.resolve,
        )
        self.unresolve = async_to_raw_response_wrapper(
            items.unresolve,
        )


class ItemsResourceWithStreamingResponse:
    def __init__(self, items: ItemsResource) -> None:
        self._items = items

        self.list = to_streamed_response_wrapper(
            items.list,
        )
        self.resolve = to_streamed_response_wrapper(
            items.resolve,
        )
        self.unresolve = to_streamed_response_wrapper(
            items.unresolve,
        )


class AsyncItemsResourceWithStreamingResponse:
    def __init__(self, items: AsyncItemsResource) -> None:
        self._items = items

        self.list = async_to_streamed_response_wrapper(
            items.list,
        )
        self.resolve = async_to_streamed_response_wrapper(
            items.resolve,
        )
        self.unresolve = async_to_streamed_response_wrapper(
            items.unresolve,
        )
