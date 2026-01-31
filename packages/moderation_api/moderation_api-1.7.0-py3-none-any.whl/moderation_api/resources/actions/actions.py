# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal

import httpx

from ...types import action_list_params, action_create_params, action_update_params
from .execute import (
    ExecuteResource,
    AsyncExecuteResource,
    ExecuteResourceWithRawResponse,
    AsyncExecuteResourceWithRawResponse,
    ExecuteResourceWithStreamingResponse,
    AsyncExecuteResourceWithStreamingResponse,
)
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
from ...types.action_list_response import ActionListResponse
from ...types.action_create_response import ActionCreateResponse
from ...types.action_delete_response import ActionDeleteResponse
from ...types.action_update_response import ActionUpdateResponse
from ...types.action_retrieve_response import ActionRetrieveResponse

__all__ = ["ActionsResource", "AsyncActionsResource"]


class ActionsResource(SyncAPIResource):
    @cached_property
    def execute(self) -> ExecuteResource:
        return ExecuteResource(self._client)

    @cached_property
    def with_raw_response(self) -> ActionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return ActionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ActionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return ActionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        built_in: Optional[bool] | Omit = omit,
        description: Optional[str] | Omit = omit,
        filter_in_queue_ids: SequenceNotStr[str] | Omit = omit,
        free_text: bool | Omit = omit,
        key: Optional[str] | Omit = omit,
        position: Literal["ALL_QUEUES", "SOME_QUEUES", "HIDDEN"] | Omit = omit,
        possible_values: Iterable[action_create_params.PossibleValue] | Omit = omit,
        queue_behaviour: Literal["REMOVE", "ADD", "NO_CHANGE"] | Omit = omit,
        type: Optional[
            Literal[
                "AUTHOR_BLOCK",
                "AUTHOR_BLOCK_TEMP",
                "AUTHOR_UNBLOCK",
                "AUTHOR_DELETE",
                "AUTHOR_REPORT",
                "AUTHOR_WARN",
                "AUTHOR_CUSTOM",
                "ITEM_REJECT",
                "ITEM_ALLOW",
                "ITEM_CUSTOM",
            ]
        ]
        | Omit = omit,
        value_required: bool | Omit = omit,
        webhooks: Iterable[action_create_params.Webhook] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActionCreateResponse:
        """
        Create an action.

        Args:
          name: The name of the action.

          built_in: Whether the action is a built-in action or a custom one.

          description: The description of the action.

          filter_in_queue_ids: The IDs of the queues the action is available in.

          free_text: Whether the action allows any text to be entered as a value or if it must be one
              of the possible values.

          key: User defined key of the action.

          position: Show the action in all queues, selected queues or no queues (to use via API
              only).

          possible_values: The possible values of the action. The user will be prompted to select one of
              these values when executing the action.

          queue_behaviour: Whether the action resolves and removes the item, unresolves and re-add it to
              the queue, or does not change the resolve status.

          type: The type of the action.

          value_required: Whether the action requires a value to be executed.

          webhooks: The action's webhooks.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/actions",
            body=maybe_transform(
                {
                    "name": name,
                    "built_in": built_in,
                    "description": description,
                    "filter_in_queue_ids": filter_in_queue_ids,
                    "free_text": free_text,
                    "key": key,
                    "position": position,
                    "possible_values": possible_values,
                    "queue_behaviour": queue_behaviour,
                    "type": type,
                    "value_required": value_required,
                    "webhooks": webhooks,
                },
                action_create_params.ActionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionCreateResponse,
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
    ) -> ActionRetrieveResponse:
        """
        Get an action by ID.

        Args:
          id: The ID of the action to get.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/actions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionRetrieveResponse,
        )

    def update(
        self,
        id: str,
        *,
        built_in: Optional[bool] | Omit = omit,
        description: Optional[str] | Omit = omit,
        filter_in_queue_ids: SequenceNotStr[str] | Omit = omit,
        free_text: bool | Omit = omit,
        key: Optional[str] | Omit = omit,
        name: str | Omit = omit,
        position: Literal["ALL_QUEUES", "SOME_QUEUES", "HIDDEN"] | Omit = omit,
        possible_values: Iterable[action_update_params.PossibleValue] | Omit = omit,
        queue_behaviour: Literal["REMOVE", "ADD", "NO_CHANGE"] | Omit = omit,
        type: Optional[
            Literal[
                "AUTHOR_BLOCK",
                "AUTHOR_BLOCK_TEMP",
                "AUTHOR_UNBLOCK",
                "AUTHOR_DELETE",
                "AUTHOR_REPORT",
                "AUTHOR_WARN",
                "AUTHOR_CUSTOM",
                "ITEM_REJECT",
                "ITEM_ALLOW",
                "ITEM_CUSTOM",
            ]
        ]
        | Omit = omit,
        value_required: bool | Omit = omit,
        webhooks: Iterable[action_update_params.Webhook] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActionUpdateResponse:
        """
        Update an action.

        Args:
          id: The ID of the action to update.

          built_in: Whether the action is a built-in action or a custom one.

          description: The description of the action.

          filter_in_queue_ids: The IDs of the queues the action is available in.

          free_text: Whether the action allows any text to be entered as a value or if it must be one
              of the possible values.

          key: User defined key of the action.

          name: The name of the action.

          position: Show the action in all queues, selected queues or no queues (to use via API
              only).

          possible_values: The possible values of the action. The user will be prompted to select one of
              these values when executing the action.

          queue_behaviour: Whether the action resolves and removes the item, unresolves and re-add it to
              the queue, or does not change the resolve status.

          type: The type of the action.

          value_required: Whether the action requires a value to be executed.

          webhooks: The action's webhooks.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/actions/{id}",
            body=maybe_transform(
                {
                    "built_in": built_in,
                    "description": description,
                    "filter_in_queue_ids": filter_in_queue_ids,
                    "free_text": free_text,
                    "key": key,
                    "name": name,
                    "position": position,
                    "possible_values": possible_values,
                    "queue_behaviour": queue_behaviour,
                    "type": type,
                    "value_required": value_required,
                    "webhooks": webhooks,
                },
                action_update_params.ActionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionUpdateResponse,
        )

    def list(
        self,
        *,
        queue_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActionListResponse:
        """
        List all available moderation actions for the authenticated organization.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/actions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"queue_id": queue_id}, action_list_params.ActionListParams),
            ),
            cast_to=ActionListResponse,
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
    ) -> ActionDeleteResponse:
        """
        Delete an action and all of its webhooks.

        Args:
          id: The ID of the action to delete.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/actions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionDeleteResponse,
        )


class AsyncActionsResource(AsyncAPIResource):
    @cached_property
    def execute(self) -> AsyncExecuteResource:
        return AsyncExecuteResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncActionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/moderation-api/sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncActionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncActionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/moderation-api/sdk-python#with_streaming_response
        """
        return AsyncActionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        built_in: Optional[bool] | Omit = omit,
        description: Optional[str] | Omit = omit,
        filter_in_queue_ids: SequenceNotStr[str] | Omit = omit,
        free_text: bool | Omit = omit,
        key: Optional[str] | Omit = omit,
        position: Literal["ALL_QUEUES", "SOME_QUEUES", "HIDDEN"] | Omit = omit,
        possible_values: Iterable[action_create_params.PossibleValue] | Omit = omit,
        queue_behaviour: Literal["REMOVE", "ADD", "NO_CHANGE"] | Omit = omit,
        type: Optional[
            Literal[
                "AUTHOR_BLOCK",
                "AUTHOR_BLOCK_TEMP",
                "AUTHOR_UNBLOCK",
                "AUTHOR_DELETE",
                "AUTHOR_REPORT",
                "AUTHOR_WARN",
                "AUTHOR_CUSTOM",
                "ITEM_REJECT",
                "ITEM_ALLOW",
                "ITEM_CUSTOM",
            ]
        ]
        | Omit = omit,
        value_required: bool | Omit = omit,
        webhooks: Iterable[action_create_params.Webhook] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActionCreateResponse:
        """
        Create an action.

        Args:
          name: The name of the action.

          built_in: Whether the action is a built-in action or a custom one.

          description: The description of the action.

          filter_in_queue_ids: The IDs of the queues the action is available in.

          free_text: Whether the action allows any text to be entered as a value or if it must be one
              of the possible values.

          key: User defined key of the action.

          position: Show the action in all queues, selected queues or no queues (to use via API
              only).

          possible_values: The possible values of the action. The user will be prompted to select one of
              these values when executing the action.

          queue_behaviour: Whether the action resolves and removes the item, unresolves and re-add it to
              the queue, or does not change the resolve status.

          type: The type of the action.

          value_required: Whether the action requires a value to be executed.

          webhooks: The action's webhooks.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/actions",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "built_in": built_in,
                    "description": description,
                    "filter_in_queue_ids": filter_in_queue_ids,
                    "free_text": free_text,
                    "key": key,
                    "position": position,
                    "possible_values": possible_values,
                    "queue_behaviour": queue_behaviour,
                    "type": type,
                    "value_required": value_required,
                    "webhooks": webhooks,
                },
                action_create_params.ActionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionCreateResponse,
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
    ) -> ActionRetrieveResponse:
        """
        Get an action by ID.

        Args:
          id: The ID of the action to get.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/actions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionRetrieveResponse,
        )

    async def update(
        self,
        id: str,
        *,
        built_in: Optional[bool] | Omit = omit,
        description: Optional[str] | Omit = omit,
        filter_in_queue_ids: SequenceNotStr[str] | Omit = omit,
        free_text: bool | Omit = omit,
        key: Optional[str] | Omit = omit,
        name: str | Omit = omit,
        position: Literal["ALL_QUEUES", "SOME_QUEUES", "HIDDEN"] | Omit = omit,
        possible_values: Iterable[action_update_params.PossibleValue] | Omit = omit,
        queue_behaviour: Literal["REMOVE", "ADD", "NO_CHANGE"] | Omit = omit,
        type: Optional[
            Literal[
                "AUTHOR_BLOCK",
                "AUTHOR_BLOCK_TEMP",
                "AUTHOR_UNBLOCK",
                "AUTHOR_DELETE",
                "AUTHOR_REPORT",
                "AUTHOR_WARN",
                "AUTHOR_CUSTOM",
                "ITEM_REJECT",
                "ITEM_ALLOW",
                "ITEM_CUSTOM",
            ]
        ]
        | Omit = omit,
        value_required: bool | Omit = omit,
        webhooks: Iterable[action_update_params.Webhook] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActionUpdateResponse:
        """
        Update an action.

        Args:
          id: The ID of the action to update.

          built_in: Whether the action is a built-in action or a custom one.

          description: The description of the action.

          filter_in_queue_ids: The IDs of the queues the action is available in.

          free_text: Whether the action allows any text to be entered as a value or if it must be one
              of the possible values.

          key: User defined key of the action.

          name: The name of the action.

          position: Show the action in all queues, selected queues or no queues (to use via API
              only).

          possible_values: The possible values of the action. The user will be prompted to select one of
              these values when executing the action.

          queue_behaviour: Whether the action resolves and removes the item, unresolves and re-add it to
              the queue, or does not change the resolve status.

          type: The type of the action.

          value_required: Whether the action requires a value to be executed.

          webhooks: The action's webhooks.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/actions/{id}",
            body=await async_maybe_transform(
                {
                    "built_in": built_in,
                    "description": description,
                    "filter_in_queue_ids": filter_in_queue_ids,
                    "free_text": free_text,
                    "key": key,
                    "name": name,
                    "position": position,
                    "possible_values": possible_values,
                    "queue_behaviour": queue_behaviour,
                    "type": type,
                    "value_required": value_required,
                    "webhooks": webhooks,
                },
                action_update_params.ActionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionUpdateResponse,
        )

    async def list(
        self,
        *,
        queue_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ActionListResponse:
        """
        List all available moderation actions for the authenticated organization.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/actions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"queue_id": queue_id}, action_list_params.ActionListParams),
            ),
            cast_to=ActionListResponse,
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
    ) -> ActionDeleteResponse:
        """
        Delete an action and all of its webhooks.

        Args:
          id: The ID of the action to delete.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/actions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ActionDeleteResponse,
        )


class ActionsResourceWithRawResponse:
    def __init__(self, actions: ActionsResource) -> None:
        self._actions = actions

        self.create = to_raw_response_wrapper(
            actions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            actions.retrieve,
        )
        self.update = to_raw_response_wrapper(
            actions.update,
        )
        self.list = to_raw_response_wrapper(
            actions.list,
        )
        self.delete = to_raw_response_wrapper(
            actions.delete,
        )

    @cached_property
    def execute(self) -> ExecuteResourceWithRawResponse:
        return ExecuteResourceWithRawResponse(self._actions.execute)


class AsyncActionsResourceWithRawResponse:
    def __init__(self, actions: AsyncActionsResource) -> None:
        self._actions = actions

        self.create = async_to_raw_response_wrapper(
            actions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            actions.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            actions.update,
        )
        self.list = async_to_raw_response_wrapper(
            actions.list,
        )
        self.delete = async_to_raw_response_wrapper(
            actions.delete,
        )

    @cached_property
    def execute(self) -> AsyncExecuteResourceWithRawResponse:
        return AsyncExecuteResourceWithRawResponse(self._actions.execute)


class ActionsResourceWithStreamingResponse:
    def __init__(self, actions: ActionsResource) -> None:
        self._actions = actions

        self.create = to_streamed_response_wrapper(
            actions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            actions.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            actions.update,
        )
        self.list = to_streamed_response_wrapper(
            actions.list,
        )
        self.delete = to_streamed_response_wrapper(
            actions.delete,
        )

    @cached_property
    def execute(self) -> ExecuteResourceWithStreamingResponse:
        return ExecuteResourceWithStreamingResponse(self._actions.execute)


class AsyncActionsResourceWithStreamingResponse:
    def __init__(self, actions: AsyncActionsResource) -> None:
        self._actions = actions

        self.create = async_to_streamed_response_wrapper(
            actions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            actions.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            actions.update,
        )
        self.list = async_to_streamed_response_wrapper(
            actions.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            actions.delete,
        )

    @cached_property
    def execute(self) -> AsyncExecuteResourceWithStreamingResponse:
        return AsyncExecuteResourceWithStreamingResponse(self._actions.execute)
