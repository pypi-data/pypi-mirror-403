# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import APIStatusError, ModerationAPIError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import auth, queue, account, actions, authors, content, wordlist
    from .resources.auth import AuthResource, AsyncAuthResource
    from .resources.account import AccountResource, AsyncAccountResource
    from .resources.authors import AuthorsResource, AsyncAuthorsResource
    from .resources.content import ContentResource, AsyncContentResource
    from .resources.queue.queue import QueueResource, AsyncQueueResource
    from .resources.actions.actions import ActionsResource, AsyncActionsResource
    from .resources.wordlist.wordlist import WordlistResource, AsyncWordlistResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "ModerationAPI",
    "AsyncModerationAPI",
    "Client",
    "AsyncClient",
]


class ModerationAPI(SyncAPIClient):
    # client options
    secret_key: str

    def __init__(
        self,
        *,
        secret_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous ModerationAPI client instance.

        This automatically infers the `secret_key` argument from the `MODAPI_SECRET_KEY` environment variable if it is not provided.
        """
        if secret_key is None:
            secret_key = os.environ.get("MODAPI_SECRET_KEY")
        if secret_key is None:
            raise ModerationAPIError(
                "The secret_key client option must be set either by passing secret_key to the client or by setting the MODAPI_SECRET_KEY environment variable"
            )
        self.secret_key = secret_key

        if base_url is None:
            base_url = os.environ.get("MODERATION_API_BASE_URL")
        if base_url is None:
            base_url = f"https://api.moderationapi.com/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def authors(self) -> AuthorsResource:
        from .resources.authors import AuthorsResource

        return AuthorsResource(self)

    @cached_property
    def queue(self) -> QueueResource:
        from .resources.queue import QueueResource

        return QueueResource(self)

    @cached_property
    def actions(self) -> ActionsResource:
        from .resources.actions import ActionsResource

        return ActionsResource(self)

    @cached_property
    def content(self) -> ContentResource:
        from .resources.content import ContentResource

        return ContentResource(self)

    @cached_property
    def account(self) -> AccountResource:
        from .resources.account import AccountResource

        return AccountResource(self)

    @cached_property
    def auth(self) -> AuthResource:
        from .resources.auth import AuthResource

        return AuthResource(self)

    @cached_property
    def wordlist(self) -> WordlistResource:
        from .resources.wordlist import WordlistResource

        return WordlistResource(self)

    @cached_property
    def with_raw_response(self) -> ModerationAPIWithRawResponse:
        return ModerationAPIWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ModerationAPIWithStreamedResponse:
        return ModerationAPIWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        secret_key = self.secret_key
        return {"Authorization": f"Bearer {secret_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        secret_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            secret_key=secret_key or self.secret_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncModerationAPI(AsyncAPIClient):
    # client options
    secret_key: str

    def __init__(
        self,
        *,
        secret_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncModerationAPI client instance.

        This automatically infers the `secret_key` argument from the `MODAPI_SECRET_KEY` environment variable if it is not provided.
        """
        if secret_key is None:
            secret_key = os.environ.get("MODAPI_SECRET_KEY")
        if secret_key is None:
            raise ModerationAPIError(
                "The secret_key client option must be set either by passing secret_key to the client or by setting the MODAPI_SECRET_KEY environment variable"
            )
        self.secret_key = secret_key

        if base_url is None:
            base_url = os.environ.get("MODERATION_API_BASE_URL")
        if base_url is None:
            base_url = f"https://api.moderationapi.com/v1"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def authors(self) -> AsyncAuthorsResource:
        from .resources.authors import AsyncAuthorsResource

        return AsyncAuthorsResource(self)

    @cached_property
    def queue(self) -> AsyncQueueResource:
        from .resources.queue import AsyncQueueResource

        return AsyncQueueResource(self)

    @cached_property
    def actions(self) -> AsyncActionsResource:
        from .resources.actions import AsyncActionsResource

        return AsyncActionsResource(self)

    @cached_property
    def content(self) -> AsyncContentResource:
        from .resources.content import AsyncContentResource

        return AsyncContentResource(self)

    @cached_property
    def account(self) -> AsyncAccountResource:
        from .resources.account import AsyncAccountResource

        return AsyncAccountResource(self)

    @cached_property
    def auth(self) -> AsyncAuthResource:
        from .resources.auth import AsyncAuthResource

        return AsyncAuthResource(self)

    @cached_property
    def wordlist(self) -> AsyncWordlistResource:
        from .resources.wordlist import AsyncWordlistResource

        return AsyncWordlistResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncModerationAPIWithRawResponse:
        return AsyncModerationAPIWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncModerationAPIWithStreamedResponse:
        return AsyncModerationAPIWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        secret_key = self.secret_key
        return {"Authorization": f"Bearer {secret_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        secret_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            secret_key=secret_key or self.secret_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class ModerationAPIWithRawResponse:
    _client: ModerationAPI

    def __init__(self, client: ModerationAPI) -> None:
        self._client = client

    @cached_property
    def authors(self) -> authors.AuthorsResourceWithRawResponse:
        from .resources.authors import AuthorsResourceWithRawResponse

        return AuthorsResourceWithRawResponse(self._client.authors)

    @cached_property
    def queue(self) -> queue.QueueResourceWithRawResponse:
        from .resources.queue import QueueResourceWithRawResponse

        return QueueResourceWithRawResponse(self._client.queue)

    @cached_property
    def actions(self) -> actions.ActionsResourceWithRawResponse:
        from .resources.actions import ActionsResourceWithRawResponse

        return ActionsResourceWithRawResponse(self._client.actions)

    @cached_property
    def content(self) -> content.ContentResourceWithRawResponse:
        from .resources.content import ContentResourceWithRawResponse

        return ContentResourceWithRawResponse(self._client.content)

    @cached_property
    def account(self) -> account.AccountResourceWithRawResponse:
        from .resources.account import AccountResourceWithRawResponse

        return AccountResourceWithRawResponse(self._client.account)

    @cached_property
    def auth(self) -> auth.AuthResourceWithRawResponse:
        from .resources.auth import AuthResourceWithRawResponse

        return AuthResourceWithRawResponse(self._client.auth)

    @cached_property
    def wordlist(self) -> wordlist.WordlistResourceWithRawResponse:
        from .resources.wordlist import WordlistResourceWithRawResponse

        return WordlistResourceWithRawResponse(self._client.wordlist)


class AsyncModerationAPIWithRawResponse:
    _client: AsyncModerationAPI

    def __init__(self, client: AsyncModerationAPI) -> None:
        self._client = client

    @cached_property
    def authors(self) -> authors.AsyncAuthorsResourceWithRawResponse:
        from .resources.authors import AsyncAuthorsResourceWithRawResponse

        return AsyncAuthorsResourceWithRawResponse(self._client.authors)

    @cached_property
    def queue(self) -> queue.AsyncQueueResourceWithRawResponse:
        from .resources.queue import AsyncQueueResourceWithRawResponse

        return AsyncQueueResourceWithRawResponse(self._client.queue)

    @cached_property
    def actions(self) -> actions.AsyncActionsResourceWithRawResponse:
        from .resources.actions import AsyncActionsResourceWithRawResponse

        return AsyncActionsResourceWithRawResponse(self._client.actions)

    @cached_property
    def content(self) -> content.AsyncContentResourceWithRawResponse:
        from .resources.content import AsyncContentResourceWithRawResponse

        return AsyncContentResourceWithRawResponse(self._client.content)

    @cached_property
    def account(self) -> account.AsyncAccountResourceWithRawResponse:
        from .resources.account import AsyncAccountResourceWithRawResponse

        return AsyncAccountResourceWithRawResponse(self._client.account)

    @cached_property
    def auth(self) -> auth.AsyncAuthResourceWithRawResponse:
        from .resources.auth import AsyncAuthResourceWithRawResponse

        return AsyncAuthResourceWithRawResponse(self._client.auth)

    @cached_property
    def wordlist(self) -> wordlist.AsyncWordlistResourceWithRawResponse:
        from .resources.wordlist import AsyncWordlistResourceWithRawResponse

        return AsyncWordlistResourceWithRawResponse(self._client.wordlist)


class ModerationAPIWithStreamedResponse:
    _client: ModerationAPI

    def __init__(self, client: ModerationAPI) -> None:
        self._client = client

    @cached_property
    def authors(self) -> authors.AuthorsResourceWithStreamingResponse:
        from .resources.authors import AuthorsResourceWithStreamingResponse

        return AuthorsResourceWithStreamingResponse(self._client.authors)

    @cached_property
    def queue(self) -> queue.QueueResourceWithStreamingResponse:
        from .resources.queue import QueueResourceWithStreamingResponse

        return QueueResourceWithStreamingResponse(self._client.queue)

    @cached_property
    def actions(self) -> actions.ActionsResourceWithStreamingResponse:
        from .resources.actions import ActionsResourceWithStreamingResponse

        return ActionsResourceWithStreamingResponse(self._client.actions)

    @cached_property
    def content(self) -> content.ContentResourceWithStreamingResponse:
        from .resources.content import ContentResourceWithStreamingResponse

        return ContentResourceWithStreamingResponse(self._client.content)

    @cached_property
    def account(self) -> account.AccountResourceWithStreamingResponse:
        from .resources.account import AccountResourceWithStreamingResponse

        return AccountResourceWithStreamingResponse(self._client.account)

    @cached_property
    def auth(self) -> auth.AuthResourceWithStreamingResponse:
        from .resources.auth import AuthResourceWithStreamingResponse

        return AuthResourceWithStreamingResponse(self._client.auth)

    @cached_property
    def wordlist(self) -> wordlist.WordlistResourceWithStreamingResponse:
        from .resources.wordlist import WordlistResourceWithStreamingResponse

        return WordlistResourceWithStreamingResponse(self._client.wordlist)


class AsyncModerationAPIWithStreamedResponse:
    _client: AsyncModerationAPI

    def __init__(self, client: AsyncModerationAPI) -> None:
        self._client = client

    @cached_property
    def authors(self) -> authors.AsyncAuthorsResourceWithStreamingResponse:
        from .resources.authors import AsyncAuthorsResourceWithStreamingResponse

        return AsyncAuthorsResourceWithStreamingResponse(self._client.authors)

    @cached_property
    def queue(self) -> queue.AsyncQueueResourceWithStreamingResponse:
        from .resources.queue import AsyncQueueResourceWithStreamingResponse

        return AsyncQueueResourceWithStreamingResponse(self._client.queue)

    @cached_property
    def actions(self) -> actions.AsyncActionsResourceWithStreamingResponse:
        from .resources.actions import AsyncActionsResourceWithStreamingResponse

        return AsyncActionsResourceWithStreamingResponse(self._client.actions)

    @cached_property
    def content(self) -> content.AsyncContentResourceWithStreamingResponse:
        from .resources.content import AsyncContentResourceWithStreamingResponse

        return AsyncContentResourceWithStreamingResponse(self._client.content)

    @cached_property
    def account(self) -> account.AsyncAccountResourceWithStreamingResponse:
        from .resources.account import AsyncAccountResourceWithStreamingResponse

        return AsyncAccountResourceWithStreamingResponse(self._client.account)

    @cached_property
    def auth(self) -> auth.AsyncAuthResourceWithStreamingResponse:
        from .resources.auth import AsyncAuthResourceWithStreamingResponse

        return AsyncAuthResourceWithStreamingResponse(self._client.auth)

    @cached_property
    def wordlist(self) -> wordlist.AsyncWordlistResourceWithStreamingResponse:
        from .resources.wordlist import AsyncWordlistResourceWithStreamingResponse

        return AsyncWordlistResourceWithStreamingResponse(self._client.wordlist)


Client = ModerationAPI

AsyncClient = AsyncModerationAPI
