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
from ._exceptions import APIStatusError, BountylabError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import raw_repos, raw_users, user_emails, search_repos, search_users
    from .resources.raw_repos import RawReposResource, AsyncRawReposResource
    from .resources.raw_users import RawUsersResource, AsyncRawUsersResource
    from .resources.user_emails import UserEmailsResource, AsyncUserEmailsResource
    from .resources.search_repos import SearchReposResource, AsyncSearchReposResource
    from .resources.search_users import SearchUsersResource, AsyncSearchUsersResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Bountylab",
    "AsyncBountylab",
    "Client",
    "AsyncClient",
]


class Bountylab(SyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
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
        """Construct a new synchronous Bountylab client instance.

        This automatically infers the `api_key` argument from the `BOUNTYLAB_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("BOUNTYLAB_API_KEY")
        if api_key is None:
            raise BountylabError(
                "The api_key client option must be set either by passing api_key to the client or by setting the BOUNTYLAB_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("BOUNTYLAB_BASE_URL")
        if base_url is None:
            base_url = f"https://api.bountylab.io/v2"

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
    def raw_users(self) -> RawUsersResource:
        from .resources.raw_users import RawUsersResource

        return RawUsersResource(self)

    @cached_property
    def raw_repos(self) -> RawReposResource:
        from .resources.raw_repos import RawReposResource

        return RawReposResource(self)

    @cached_property
    def user_emails(self) -> UserEmailsResource:
        from .resources.user_emails import UserEmailsResource

        return UserEmailsResource(self)

    @cached_property
    def search_users(self) -> SearchUsersResource:
        from .resources.search_users import SearchUsersResource

        return SearchUsersResource(self)

    @cached_property
    def search_repos(self) -> SearchReposResource:
        from .resources.search_repos import SearchReposResource

        return SearchReposResource(self)

    @cached_property
    def with_raw_response(self) -> BountylabWithRawResponse:
        return BountylabWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BountylabWithStreamedResponse:
        return BountylabWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

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
        api_key: str | None = None,
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
            api_key=api_key or self.api_key,
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


class AsyncBountylab(AsyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
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
        """Construct a new async AsyncBountylab client instance.

        This automatically infers the `api_key` argument from the `BOUNTYLAB_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("BOUNTYLAB_API_KEY")
        if api_key is None:
            raise BountylabError(
                "The api_key client option must be set either by passing api_key to the client or by setting the BOUNTYLAB_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("BOUNTYLAB_BASE_URL")
        if base_url is None:
            base_url = f"https://api.bountylab.io/v2"

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
    def raw_users(self) -> AsyncRawUsersResource:
        from .resources.raw_users import AsyncRawUsersResource

        return AsyncRawUsersResource(self)

    @cached_property
    def raw_repos(self) -> AsyncRawReposResource:
        from .resources.raw_repos import AsyncRawReposResource

        return AsyncRawReposResource(self)

    @cached_property
    def user_emails(self) -> AsyncUserEmailsResource:
        from .resources.user_emails import AsyncUserEmailsResource

        return AsyncUserEmailsResource(self)

    @cached_property
    def search_users(self) -> AsyncSearchUsersResource:
        from .resources.search_users import AsyncSearchUsersResource

        return AsyncSearchUsersResource(self)

    @cached_property
    def search_repos(self) -> AsyncSearchReposResource:
        from .resources.search_repos import AsyncSearchReposResource

        return AsyncSearchReposResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncBountylabWithRawResponse:
        return AsyncBountylabWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBountylabWithStreamedResponse:
        return AsyncBountylabWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

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
        api_key: str | None = None,
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
            api_key=api_key or self.api_key,
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


class BountylabWithRawResponse:
    _client: Bountylab

    def __init__(self, client: Bountylab) -> None:
        self._client = client

    @cached_property
    def raw_users(self) -> raw_users.RawUsersResourceWithRawResponse:
        from .resources.raw_users import RawUsersResourceWithRawResponse

        return RawUsersResourceWithRawResponse(self._client.raw_users)

    @cached_property
    def raw_repos(self) -> raw_repos.RawReposResourceWithRawResponse:
        from .resources.raw_repos import RawReposResourceWithRawResponse

        return RawReposResourceWithRawResponse(self._client.raw_repos)

    @cached_property
    def user_emails(self) -> user_emails.UserEmailsResourceWithRawResponse:
        from .resources.user_emails import UserEmailsResourceWithRawResponse

        return UserEmailsResourceWithRawResponse(self._client.user_emails)

    @cached_property
    def search_users(self) -> search_users.SearchUsersResourceWithRawResponse:
        from .resources.search_users import SearchUsersResourceWithRawResponse

        return SearchUsersResourceWithRawResponse(self._client.search_users)

    @cached_property
    def search_repos(self) -> search_repos.SearchReposResourceWithRawResponse:
        from .resources.search_repos import SearchReposResourceWithRawResponse

        return SearchReposResourceWithRawResponse(self._client.search_repos)


class AsyncBountylabWithRawResponse:
    _client: AsyncBountylab

    def __init__(self, client: AsyncBountylab) -> None:
        self._client = client

    @cached_property
    def raw_users(self) -> raw_users.AsyncRawUsersResourceWithRawResponse:
        from .resources.raw_users import AsyncRawUsersResourceWithRawResponse

        return AsyncRawUsersResourceWithRawResponse(self._client.raw_users)

    @cached_property
    def raw_repos(self) -> raw_repos.AsyncRawReposResourceWithRawResponse:
        from .resources.raw_repos import AsyncRawReposResourceWithRawResponse

        return AsyncRawReposResourceWithRawResponse(self._client.raw_repos)

    @cached_property
    def user_emails(self) -> user_emails.AsyncUserEmailsResourceWithRawResponse:
        from .resources.user_emails import AsyncUserEmailsResourceWithRawResponse

        return AsyncUserEmailsResourceWithRawResponse(self._client.user_emails)

    @cached_property
    def search_users(self) -> search_users.AsyncSearchUsersResourceWithRawResponse:
        from .resources.search_users import AsyncSearchUsersResourceWithRawResponse

        return AsyncSearchUsersResourceWithRawResponse(self._client.search_users)

    @cached_property
    def search_repos(self) -> search_repos.AsyncSearchReposResourceWithRawResponse:
        from .resources.search_repos import AsyncSearchReposResourceWithRawResponse

        return AsyncSearchReposResourceWithRawResponse(self._client.search_repos)


class BountylabWithStreamedResponse:
    _client: Bountylab

    def __init__(self, client: Bountylab) -> None:
        self._client = client

    @cached_property
    def raw_users(self) -> raw_users.RawUsersResourceWithStreamingResponse:
        from .resources.raw_users import RawUsersResourceWithStreamingResponse

        return RawUsersResourceWithStreamingResponse(self._client.raw_users)

    @cached_property
    def raw_repos(self) -> raw_repos.RawReposResourceWithStreamingResponse:
        from .resources.raw_repos import RawReposResourceWithStreamingResponse

        return RawReposResourceWithStreamingResponse(self._client.raw_repos)

    @cached_property
    def user_emails(self) -> user_emails.UserEmailsResourceWithStreamingResponse:
        from .resources.user_emails import UserEmailsResourceWithStreamingResponse

        return UserEmailsResourceWithStreamingResponse(self._client.user_emails)

    @cached_property
    def search_users(self) -> search_users.SearchUsersResourceWithStreamingResponse:
        from .resources.search_users import SearchUsersResourceWithStreamingResponse

        return SearchUsersResourceWithStreamingResponse(self._client.search_users)

    @cached_property
    def search_repos(self) -> search_repos.SearchReposResourceWithStreamingResponse:
        from .resources.search_repos import SearchReposResourceWithStreamingResponse

        return SearchReposResourceWithStreamingResponse(self._client.search_repos)


class AsyncBountylabWithStreamedResponse:
    _client: AsyncBountylab

    def __init__(self, client: AsyncBountylab) -> None:
        self._client = client

    @cached_property
    def raw_users(self) -> raw_users.AsyncRawUsersResourceWithStreamingResponse:
        from .resources.raw_users import AsyncRawUsersResourceWithStreamingResponse

        return AsyncRawUsersResourceWithStreamingResponse(self._client.raw_users)

    @cached_property
    def raw_repos(self) -> raw_repos.AsyncRawReposResourceWithStreamingResponse:
        from .resources.raw_repos import AsyncRawReposResourceWithStreamingResponse

        return AsyncRawReposResourceWithStreamingResponse(self._client.raw_repos)

    @cached_property
    def user_emails(self) -> user_emails.AsyncUserEmailsResourceWithStreamingResponse:
        from .resources.user_emails import AsyncUserEmailsResourceWithStreamingResponse

        return AsyncUserEmailsResourceWithStreamingResponse(self._client.user_emails)

    @cached_property
    def search_users(self) -> search_users.AsyncSearchUsersResourceWithStreamingResponse:
        from .resources.search_users import AsyncSearchUsersResourceWithStreamingResponse

        return AsyncSearchUsersResourceWithStreamingResponse(self._client.search_users)

    @cached_property
    def search_repos(self) -> search_repos.AsyncSearchReposResourceWithStreamingResponse:
        from .resources.search_repos import AsyncSearchReposResourceWithStreamingResponse

        return AsyncSearchReposResourceWithStreamingResponse(self._client.search_repos)


Client = Bountylab

AsyncClient = AsyncBountylab
