# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, SequenceNotStr, not_given
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
from ...types.wordlist import word_add_params, word_remove_params
from ...types.wordlist.word_add_response import WordAddResponse
from ...types.wordlist.word_remove_response import WordRemoveResponse

__all__ = ["WordsResource", "AsyncWordsResource"]


class WordsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WordsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return WordsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WordsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return WordsResourceWithStreamingResponse(self)

    def add(
        self,
        id: str,
        *,
        words: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordAddResponse:
        """
        Add words to an existing wordlist

        Args:
          id: ID of the wordlist to add words to

          words: Array of words to add to the wordlist. Duplicate words will be ignored.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._post(
            f"/wordlist/{id}/words",
            body=maybe_transform({"words": words}, word_add_params.WordAddParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordAddResponse,
        )

    def remove(
        self,
        id: str,
        *,
        words: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordRemoveResponse:
        """
        Remove words from an existing wordlist

        Args:
          id: ID of the wordlist to remove words from

          words: Array of words to remove from the wordlist

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/wordlist/{id}/words",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"words": words}, word_remove_params.WordRemoveParams),
            ),
            cast_to=WordRemoveResponse,
        )


class AsyncWordsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWordsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWordsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWordsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AsyncWordsResourceWithStreamingResponse(self)

    async def add(
        self,
        id: str,
        *,
        words: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordAddResponse:
        """
        Add words to an existing wordlist

        Args:
          id: ID of the wordlist to add words to

          words: Array of words to add to the wordlist. Duplicate words will be ignored.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._post(
            f"/wordlist/{id}/words",
            body=await async_maybe_transform({"words": words}, word_add_params.WordAddParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WordAddResponse,
        )

    async def remove(
        self,
        id: str,
        *,
        words: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WordRemoveResponse:
        """
        Remove words from an existing wordlist

        Args:
          id: ID of the wordlist to remove words from

          words: Array of words to remove from the wordlist

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/wordlist/{id}/words",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"words": words}, word_remove_params.WordRemoveParams),
            ),
            cast_to=WordRemoveResponse,
        )


class WordsResourceWithRawResponse:
    def __init__(self, words: WordsResource) -> None:
        self._words = words

        self.add = to_raw_response_wrapper(
            words.add,
        )
        self.remove = to_raw_response_wrapper(
            words.remove,
        )


class AsyncWordsResourceWithRawResponse:
    def __init__(self, words: AsyncWordsResource) -> None:
        self._words = words

        self.add = async_to_raw_response_wrapper(
            words.add,
        )
        self.remove = async_to_raw_response_wrapper(
            words.remove,
        )


class WordsResourceWithStreamingResponse:
    def __init__(self, words: WordsResource) -> None:
        self._words = words

        self.add = to_streamed_response_wrapper(
            words.add,
        )
        self.remove = to_streamed_response_wrapper(
            words.remove,
        )


class AsyncWordsResourceWithStreamingResponse:
    def __init__(self, words: AsyncWordsResource) -> None:
        self._words = words

        self.add = async_to_streamed_response_wrapper(
            words.add,
        )
        self.remove = async_to_streamed_response_wrapper(
            words.remove,
        )
