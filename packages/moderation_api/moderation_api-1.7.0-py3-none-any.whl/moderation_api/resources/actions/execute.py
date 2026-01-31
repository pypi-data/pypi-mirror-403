# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import typing_extensions

import httpx

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
from ...types.actions import execute_execute_params, execute_execute_by_id_params
from ...types.actions.execute_execute_response import ExecuteExecuteResponse
from ...types.actions.execute_execute_by_id_response import ExecuteExecuteByIDResponse

__all__ = ["ExecuteResource", "AsyncExecuteResource"]


class ExecuteResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExecuteResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return ExecuteResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExecuteResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return ExecuteResourceWithStreamingResponse(self)

    def execute(
        self,
        *,
        action_key: str,
        author_ids: SequenceNotStr[str] | Omit = omit,
        content_ids: SequenceNotStr[str] | Omit = omit,
        duration: float | Omit = omit,
        queue_id: str | Omit = omit,
        value: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExecuteExecuteResponse:
        """
        Execute a moderation action on one or more content items.

        Args:
          action_key: ID or key of the action to execute

          author_ids: IDs of the authors to apply the action to. Provide this or contentIds.

          content_ids: IDs of the content items to apply the action to. Provide this or authorIds.

          duration: Optional duration in milliseconds for actions with timeouts

          queue_id: Optional queue ID if the action is queue-specific

          value: Optional value to provide with the action

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/actions/execute",
            body=maybe_transform(
                {
                    "action_key": action_key,
                    "author_ids": author_ids,
                    "content_ids": content_ids,
                    "duration": duration,
                    "queue_id": queue_id,
                    "value": value,
                },
                execute_execute_params.ExecuteExecuteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExecuteExecuteResponse,
        )

    @typing_extensions.deprecated("deprecated")
    def execute_by_id(
        self,
        action_id: str,
        *,
        author_ids: SequenceNotStr[str] | Omit = omit,
        content_ids: SequenceNotStr[str] | Omit = omit,
        queue_id: str | Omit = omit,
        value: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExecuteExecuteByIDResponse:
        """
        Execute an action on a set of content items in a queue.

        Args:
          action_id: The ID or key of the action to execute.

          author_ids: IDs of the authors to apply the action to

          content_ids: The IDs of the content items to perform the action on.

          queue_id: The ID of the queue the action was performed from if any.

          value: The value of the action. Useful to set a reason for the action etc.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not action_id:
            raise ValueError(f"Expected a non-empty value for `action_id` but received {action_id!r}")
        return self._post(
            f"/actions/{action_id}/execute",
            body=maybe_transform(
                {
                    "author_ids": author_ids,
                    "content_ids": content_ids,
                    "queue_id": queue_id,
                    "value": value,
                },
                execute_execute_by_id_params.ExecuteExecuteByIDParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExecuteExecuteByIDResponse,
        )


class AsyncExecuteResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExecuteResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncExecuteResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExecuteResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AsyncExecuteResourceWithStreamingResponse(self)

    async def execute(
        self,
        *,
        action_key: str,
        author_ids: SequenceNotStr[str] | Omit = omit,
        content_ids: SequenceNotStr[str] | Omit = omit,
        duration: float | Omit = omit,
        queue_id: str | Omit = omit,
        value: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExecuteExecuteResponse:
        """
        Execute a moderation action on one or more content items.

        Args:
          action_key: ID or key of the action to execute

          author_ids: IDs of the authors to apply the action to. Provide this or contentIds.

          content_ids: IDs of the content items to apply the action to. Provide this or authorIds.

          duration: Optional duration in milliseconds for actions with timeouts

          queue_id: Optional queue ID if the action is queue-specific

          value: Optional value to provide with the action

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/actions/execute",
            body=await async_maybe_transform(
                {
                    "action_key": action_key,
                    "author_ids": author_ids,
                    "content_ids": content_ids,
                    "duration": duration,
                    "queue_id": queue_id,
                    "value": value,
                },
                execute_execute_params.ExecuteExecuteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExecuteExecuteResponse,
        )

    @typing_extensions.deprecated("deprecated")
    async def execute_by_id(
        self,
        action_id: str,
        *,
        author_ids: SequenceNotStr[str] | Omit = omit,
        content_ids: SequenceNotStr[str] | Omit = omit,
        queue_id: str | Omit = omit,
        value: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExecuteExecuteByIDResponse:
        """
        Execute an action on a set of content items in a queue.

        Args:
          action_id: The ID or key of the action to execute.

          author_ids: IDs of the authors to apply the action to

          content_ids: The IDs of the content items to perform the action on.

          queue_id: The ID of the queue the action was performed from if any.

          value: The value of the action. Useful to set a reason for the action etc.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not action_id:
            raise ValueError(f"Expected a non-empty value for `action_id` but received {action_id!r}")
        return await self._post(
            f"/actions/{action_id}/execute",
            body=await async_maybe_transform(
                {
                    "author_ids": author_ids,
                    "content_ids": content_ids,
                    "queue_id": queue_id,
                    "value": value,
                },
                execute_execute_by_id_params.ExecuteExecuteByIDParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExecuteExecuteByIDResponse,
        )


class ExecuteResourceWithRawResponse:
    def __init__(self, execute: ExecuteResource) -> None:
        self._execute = execute

        self.execute = to_raw_response_wrapper(
            execute.execute,
        )
        self.execute_by_id = (  # pyright: ignore[reportDeprecated]
            to_raw_response_wrapper(
                execute.execute_by_id,  # pyright: ignore[reportDeprecated],
            )
        )


class AsyncExecuteResourceWithRawResponse:
    def __init__(self, execute: AsyncExecuteResource) -> None:
        self._execute = execute

        self.execute = async_to_raw_response_wrapper(
            execute.execute,
        )
        self.execute_by_id = (  # pyright: ignore[reportDeprecated]
            async_to_raw_response_wrapper(
                execute.execute_by_id,  # pyright: ignore[reportDeprecated],
            )
        )


class ExecuteResourceWithStreamingResponse:
    def __init__(self, execute: ExecuteResource) -> None:
        self._execute = execute

        self.execute = to_streamed_response_wrapper(
            execute.execute,
        )
        self.execute_by_id = (  # pyright: ignore[reportDeprecated]
            to_streamed_response_wrapper(
                execute.execute_by_id,  # pyright: ignore[reportDeprecated],
            )
        )


class AsyncExecuteResourceWithStreamingResponse:
    def __init__(self, execute: AsyncExecuteResource) -> None:
        self._execute = execute

        self.execute = async_to_streamed_response_wrapper(
            execute.execute,
        )
        self.execute_by_id = (  # pyright: ignore[reportDeprecated]
            async_to_streamed_response_wrapper(
                execute.execute_by_id,  # pyright: ignore[reportDeprecated],
            )
        )
