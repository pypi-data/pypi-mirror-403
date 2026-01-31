# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from ..types import author_list_params, author_create_params, author_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.author_list_response import AuthorListResponse
from ..types.author_create_response import AuthorCreateResponse
from ..types.author_delete_response import AuthorDeleteResponse
from ..types.author_update_response import AuthorUpdateResponse
from ..types.author_retrieve_response import AuthorRetrieveResponse

__all__ = ["AuthorsResource", "AsyncAuthorsResource"]


class AuthorsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AuthorsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AuthorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AuthorsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AuthorsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        external_id: str,
        email: Optional[str] | Omit = omit,
        external_link: Optional[str] | Omit = omit,
        first_seen: float | Omit = omit,
        last_seen: float | Omit = omit,
        manual_trust_level: Optional[float] | Omit = omit,
        metadata: author_create_params.Metadata | Omit = omit,
        name: Optional[str] | Omit = omit,
        profile_picture: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorCreateResponse:
        """Create a new author.

        Typically not needed as authors are created automatically
        when content is moderated.

        Args:
          external_id: External ID of the user, typically the ID of the author in your database.

          email: Author email address

          external_link: URL of the author's external profile

          first_seen: Timestamp when author first appeared

          last_seen: Timestamp of last activity

          metadata: Additional metadata provided by your system. We recommend including any relevant
              information that may assist in the moderation process.

          name: Author name or identifier

          profile_picture: URL of the author's profile picture

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/authors",
            body=maybe_transform(
                {
                    "external_id": external_id,
                    "email": email,
                    "external_link": external_link,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "manual_trust_level": manual_trust_level,
                    "metadata": metadata,
                    "name": name,
                    "profile_picture": profile_picture,
                },
                author_create_params.AuthorCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorCreateResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorRetrieveResponse:
        """
        Get detailed information about a specific author including historical data and
        analysis

        Args:
          id: Either external ID or the ID assigned by moderation API.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/authors/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        email: Optional[str] | Omit = omit,
        external_link: Optional[str] | Omit = omit,
        first_seen: float | Omit = omit,
        last_seen: float | Omit = omit,
        manual_trust_level: Optional[float] | Omit = omit,
        metadata: author_update_params.Metadata | Omit = omit,
        name: Optional[str] | Omit = omit,
        profile_picture: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorUpdateResponse:
        """
        Update the details of a specific author

        Args:
          id: Either external ID or the ID assigned by moderation API.

          email: Author email address

          external_link: URL of the author's external profile

          first_seen: Timestamp when author first appeared

          last_seen: Timestamp of last activity

          metadata: Additional metadata provided by your system. We recommend including any relevant
              information that may assist in the moderation process.

          name: Author name or identifier

          profile_picture: URL of the author's profile picture

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/authors/{id}",
            body=maybe_transform(
                {
                    "email": email,
                    "external_link": external_link,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "manual_trust_level": manual_trust_level,
                    "metadata": metadata,
                    "name": name,
                    "profile_picture": profile_picture,
                },
                author_update_params.AuthorUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorUpdateResponse,
        )

    def list(
        self,
        *,
        content_types: str | Omit = omit,
        last_active_date: str | Omit = omit,
        member_since_date: str | Omit = omit,
        page_number: float | Omit = omit,
        page_size: float | Omit = omit,
        sort_by: Literal[
            "trustLevel",
            "violationCount",
            "reportCount",
            "memberSince",
            "lastActive",
            "contentCount",
            "flaggedContentRatio",
            "averageSentiment",
        ]
        | Omit = omit,
        sort_direction: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorListResponse:
        """
        Get a paginated list of authors with their activity metrics and reputation

        Args:
          page_number: Page number to fetch

          page_size: Number of authors per page

          sort_direction: Sort direction

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/authors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "content_types": content_types,
                        "last_active_date": last_active_date,
                        "member_since_date": member_since_date,
                        "page_number": page_number,
                        "page_size": page_size,
                        "sort_by": sort_by,
                        "sort_direction": sort_direction,
                    },
                    author_list_params.AuthorListParams,
                ),
            ),
            cast_to=AuthorListResponse,
        )

    def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorDeleteResponse:
        """
        Delete a specific author

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/authors/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorDeleteResponse,
        )


class AsyncAuthorsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAuthorsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAuthorsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAuthorsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AsyncAuthorsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        external_id: str,
        email: Optional[str] | Omit = omit,
        external_link: Optional[str] | Omit = omit,
        first_seen: float | Omit = omit,
        last_seen: float | Omit = omit,
        manual_trust_level: Optional[float] | Omit = omit,
        metadata: author_create_params.Metadata | Omit = omit,
        name: Optional[str] | Omit = omit,
        profile_picture: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorCreateResponse:
        """Create a new author.

        Typically not needed as authors are created automatically
        when content is moderated.

        Args:
          external_id: External ID of the user, typically the ID of the author in your database.

          email: Author email address

          external_link: URL of the author's external profile

          first_seen: Timestamp when author first appeared

          last_seen: Timestamp of last activity

          metadata: Additional metadata provided by your system. We recommend including any relevant
              information that may assist in the moderation process.

          name: Author name or identifier

          profile_picture: URL of the author's profile picture

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/authors",
            body=await async_maybe_transform(
                {
                    "external_id": external_id,
                    "email": email,
                    "external_link": external_link,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "manual_trust_level": manual_trust_level,
                    "metadata": metadata,
                    "name": name,
                    "profile_picture": profile_picture,
                },
                author_create_params.AuthorCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorCreateResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorRetrieveResponse:
        """
        Get detailed information about a specific author including historical data and
        analysis

        Args:
          id: Either external ID or the ID assigned by moderation API.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/authors/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        email: Optional[str] | Omit = omit,
        external_link: Optional[str] | Omit = omit,
        first_seen: float | Omit = omit,
        last_seen: float | Omit = omit,
        manual_trust_level: Optional[float] | Omit = omit,
        metadata: author_update_params.Metadata | Omit = omit,
        name: Optional[str] | Omit = omit,
        profile_picture: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorUpdateResponse:
        """
        Update the details of a specific author

        Args:
          id: Either external ID or the ID assigned by moderation API.

          email: Author email address

          external_link: URL of the author's external profile

          first_seen: Timestamp when author first appeared

          last_seen: Timestamp of last activity

          metadata: Additional metadata provided by your system. We recommend including any relevant
              information that may assist in the moderation process.

          name: Author name or identifier

          profile_picture: URL of the author's profile picture

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/authors/{id}",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "external_link": external_link,
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                    "manual_trust_level": manual_trust_level,
                    "metadata": metadata,
                    "name": name,
                    "profile_picture": profile_picture,
                },
                author_update_params.AuthorUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorUpdateResponse,
        )

    async def list(
        self,
        *,
        content_types: str | Omit = omit,
        last_active_date: str | Omit = omit,
        member_since_date: str | Omit = omit,
        page_number: float | Omit = omit,
        page_size: float | Omit = omit,
        sort_by: Literal[
            "trustLevel",
            "violationCount",
            "reportCount",
            "memberSince",
            "lastActive",
            "contentCount",
            "flaggedContentRatio",
            "averageSentiment",
        ]
        | Omit = omit,
        sort_direction: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorListResponse:
        """
        Get a paginated list of authors with their activity metrics and reputation

        Args:
          page_number: Page number to fetch

          page_size: Number of authors per page

          sort_direction: Sort direction

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/authors",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "content_types": content_types,
                        "last_active_date": last_active_date,
                        "member_since_date": member_since_date,
                        "page_number": page_number,
                        "page_size": page_size,
                        "sort_by": sort_by,
                        "sort_direction": sort_direction,
                    },
                    author_list_params.AuthorListParams,
                ),
            ),
            cast_to=AuthorListResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AuthorDeleteResponse:
        """
        Delete a specific author

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/authors/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AuthorDeleteResponse,
        )


class AuthorsResourceWithRawResponse:
    def __init__(self, authors: AuthorsResource) -> None:
        self._authors = authors

        self.create = to_raw_response_wrapper(
            authors.create,
        )
        self.retrieve = to_raw_response_wrapper(
            authors.retrieve,
        )
        self.update = to_raw_response_wrapper(
            authors.update,
        )
        self.list = to_raw_response_wrapper(
            authors.list,
        )
        self.delete = to_raw_response_wrapper(
            authors.delete,
        )


class AsyncAuthorsResourceWithRawResponse:
    def __init__(self, authors: AsyncAuthorsResource) -> None:
        self._authors = authors

        self.create = async_to_raw_response_wrapper(
            authors.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            authors.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            authors.update,
        )
        self.list = async_to_raw_response_wrapper(
            authors.list,
        )
        self.delete = async_to_raw_response_wrapper(
            authors.delete,
        )


class AuthorsResourceWithStreamingResponse:
    def __init__(self, authors: AuthorsResource) -> None:
        self._authors = authors

        self.create = to_streamed_response_wrapper(
            authors.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            authors.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            authors.update,
        )
        self.list = to_streamed_response_wrapper(
            authors.list,
        )
        self.delete = to_streamed_response_wrapper(
            authors.delete,
        )


class AsyncAuthorsResourceWithStreamingResponse:
    def __init__(self, authors: AsyncAuthorsResource) -> None:
        self._authors = authors

        self.create = async_to_streamed_response_wrapper(
            authors.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            authors.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            authors.update,
        )
        self.list = async_to_streamed_response_wrapper(
            authors.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            authors.delete,
        )
