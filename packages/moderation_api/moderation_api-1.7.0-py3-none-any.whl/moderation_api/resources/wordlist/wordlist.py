# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .words import (
    WordsResource,
    AsyncWordsResource,
    WordsResourceWithRawResponse,
    AsyncWordsResourceWithRawResponse,
    WordsResourceWithStreamingResponse,
    AsyncWordsResourceWithStreamingResponse,
)
from ...types import wordlist_update_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.wordlist_list_response import WordlistListResponse
from ...types.wordlist_update_response import WordlistUpdateResponse
from ...types.wordlist_retrieve_response import WordlistRetrieveResponse
from ...types.wordlist_get_embedding_status_response import WordlistGetEmbeddingStatusResponse

__all__ = ["WordlistResource", "AsyncWordlistResource"]


class WordlistResource(SyncAPIResource):
    @cached_property
    def words(self) -> WordsResource:
        return WordsResource(self._client)

    @cached_property
    def with_raw_response(self) -> WordlistResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return WordlistResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WordlistResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return WordlistResourceWithStreamingResponse(self)

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
    ) -> WordlistRetrieveResponse:
        """
        Get a specific wordlist by ID

        Args:
          id: ID of the wordlist to get

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/wordlist/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        description: str | Omit = omit,
        key: str | Omit = omit,
        name: str | Omit = omit,
        strict: bool | Omit = omit,
        words: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordlistUpdateResponse:
        """
        Update a wordlist

        Args:
          id: ID of the wordlist to update

          description: New description for the wordlist

          key: New key for the wordlist

          name: New name for the wordlist

          strict: Deprecated. Now using threshold in project settings.

          words: New words for the wordlist. Replace the existing words with these new ones.
              Duplicate words will be ignored.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/wordlist/{id}",
            body=maybe_transform(
                {
                    "description": description,
                    "key": key,
                    "name": name,
                    "strict": strict,
                    "words": words,
                },
                wordlist_update_params.WordlistUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistUpdateResponse,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordlistListResponse:
        """List all wordlists for the authenticated organization"""
        return self._get(
            "/wordlist",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistListResponse,
        )

    def get_embedding_status(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordlistGetEmbeddingStatusResponse:
        """
        Get the current embedding progress status for a wordlist

        Args:
          id: ID of the wordlist to check embedding status for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/wordlist/{id}/embedding-status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistGetEmbeddingStatusResponse,
        )


class AsyncWordlistResource(AsyncAPIResource):
    @cached_property
    def words(self) -> AsyncWordsResource:
        return AsyncWordsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncWordlistResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWordlistResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWordlistResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AsyncWordlistResourceWithStreamingResponse(self)

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
    ) -> WordlistRetrieveResponse:
        """
        Get a specific wordlist by ID

        Args:
          id: ID of the wordlist to get

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/wordlist/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        description: str | Omit = omit,
        key: str | Omit = omit,
        name: str | Omit = omit,
        strict: bool | Omit = omit,
        words: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordlistUpdateResponse:
        """
        Update a wordlist

        Args:
          id: ID of the wordlist to update

          description: New description for the wordlist

          key: New key for the wordlist

          name: New name for the wordlist

          strict: Deprecated. Now using threshold in project settings.

          words: New words for the wordlist. Replace the existing words with these new ones.
              Duplicate words will be ignored.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/wordlist/{id}",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "key": key,
                    "name": name,
                    "strict": strict,
                    "words": words,
                },
                wordlist_update_params.WordlistUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistUpdateResponse,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordlistListResponse:
        """List all wordlists for the authenticated organization"""
        return await self._get(
            "/wordlist",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistListResponse,
        )

    async def get_embedding_status(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordlistGetEmbeddingStatusResponse:
        """
        Get the current embedding progress status for a wordlist

        Args:
          id: ID of the wordlist to check embedding status for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/wordlist/{id}/embedding-status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordlistGetEmbeddingStatusResponse,
        )


class WordlistResourceWithRawResponse:
    def __init__(self, wordlist: WordlistResource) -> None:
        self._wordlist = wordlist

        self.retrieve = to_raw_response_wrapper(
            wordlist.retrieve,
        )
        self.update = to_raw_response_wrapper(
            wordlist.update,
        )
        self.list = to_raw_response_wrapper(
            wordlist.list,
        )
        self.get_embedding_status = to_raw_response_wrapper(
            wordlist.get_embedding_status,
        )

    @cached_property
    def words(self) -> WordsResourceWithRawResponse:
        return WordsResourceWithRawResponse(self._wordlist.words)


class AsyncWordlistResourceWithRawResponse:
    def __init__(self, wordlist: AsyncWordlistResource) -> None:
        self._wordlist = wordlist

        self.retrieve = async_to_raw_response_wrapper(
            wordlist.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            wordlist.update,
        )
        self.list = async_to_raw_response_wrapper(
            wordlist.list,
        )
        self.get_embedding_status = async_to_raw_response_wrapper(
            wordlist.get_embedding_status,
        )

    @cached_property
    def words(self) -> AsyncWordsResourceWithRawResponse:
        return AsyncWordsResourceWithRawResponse(self._wordlist.words)


class WordlistResourceWithStreamingResponse:
    def __init__(self, wordlist: WordlistResource) -> None:
        self._wordlist = wordlist

        self.retrieve = to_streamed_response_wrapper(
            wordlist.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            wordlist.update,
        )
        self.list = to_streamed_response_wrapper(
            wordlist.list,
        )
        self.get_embedding_status = to_streamed_response_wrapper(
            wordlist.get_embedding_status,
        )

    @cached_property
    def words(self) -> WordsResourceWithStreamingResponse:
        return WordsResourceWithStreamingResponse(self._wordlist.words)


class AsyncWordlistResourceWithStreamingResponse:
    def __init__(self, wordlist: AsyncWordlistResource) -> None:
        self._wordlist = wordlist

        self.retrieve = async_to_streamed_response_wrapper(
            wordlist.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            wordlist.update,
        )
        self.list = async_to_streamed_response_wrapper(
            wordlist.list,
        )
        self.get_embedding_status = async_to_streamed_response_wrapper(
            wordlist.get_embedding_status,
        )

    @cached_property
    def words(self) -> AsyncWordsResourceWithStreamingResponse:
        return AsyncWordsResourceWithStreamingResponse(self._wordlist.words)
