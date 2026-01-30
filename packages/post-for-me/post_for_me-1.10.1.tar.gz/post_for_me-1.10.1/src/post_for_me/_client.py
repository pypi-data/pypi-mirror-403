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
from ._exceptions import APIStatusError, PostForMeError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import media, social_posts, social_accounts, social_post_results, social_account_feeds
    from .resources.media import MediaResource, AsyncMediaResource
    from .resources.social_posts import SocialPostsResource, AsyncSocialPostsResource
    from .resources.social_accounts import SocialAccountsResource, AsyncSocialAccountsResource
    from .resources.social_post_results import SocialPostResultsResource, AsyncSocialPostResultsResource
    from .resources.social_account_feeds import SocialAccountFeedsResource, AsyncSocialAccountFeedsResource

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "PostForMe",
    "AsyncPostForMe",
    "Client",
    "AsyncClient",
]


class PostForMe(SyncAPIClient):
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
        """Construct a new synchronous PostForMe client instance.

        This automatically infers the `api_key` argument from the `POST_FOR_ME_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("POST_FOR_ME_API_KEY")
        if api_key is None:
            raise PostForMeError(
                "The api_key client option must be set either by passing api_key to the client or by setting the POST_FOR_ME_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("POST_FOR_ME_BASE_URL")
        if base_url is None:
            base_url = f"https://api.postforme.dev"

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
    def media(self) -> MediaResource:
        from .resources.media import MediaResource

        return MediaResource(self)

    @cached_property
    def social_posts(self) -> SocialPostsResource:
        from .resources.social_posts import SocialPostsResource

        return SocialPostsResource(self)

    @cached_property
    def social_post_results(self) -> SocialPostResultsResource:
        from .resources.social_post_results import SocialPostResultsResource

        return SocialPostResultsResource(self)

    @cached_property
    def social_accounts(self) -> SocialAccountsResource:
        from .resources.social_accounts import SocialAccountsResource

        return SocialAccountsResource(self)

    @cached_property
    def social_account_feeds(self) -> SocialAccountFeedsResource:
        from .resources.social_account_feeds import SocialAccountFeedsResource

        return SocialAccountFeedsResource(self)

    @cached_property
    def with_raw_response(self) -> PostForMeWithRawResponse:
        return PostForMeWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PostForMeWithStreamedResponse:
        return PostForMeWithStreamedResponse(self)

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


class AsyncPostForMe(AsyncAPIClient):
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
        """Construct a new async AsyncPostForMe client instance.

        This automatically infers the `api_key` argument from the `POST_FOR_ME_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("POST_FOR_ME_API_KEY")
        if api_key is None:
            raise PostForMeError(
                "The api_key client option must be set either by passing api_key to the client or by setting the POST_FOR_ME_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("POST_FOR_ME_BASE_URL")
        if base_url is None:
            base_url = f"https://api.postforme.dev"

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
    def media(self) -> AsyncMediaResource:
        from .resources.media import AsyncMediaResource

        return AsyncMediaResource(self)

    @cached_property
    def social_posts(self) -> AsyncSocialPostsResource:
        from .resources.social_posts import AsyncSocialPostsResource

        return AsyncSocialPostsResource(self)

    @cached_property
    def social_post_results(self) -> AsyncSocialPostResultsResource:
        from .resources.social_post_results import AsyncSocialPostResultsResource

        return AsyncSocialPostResultsResource(self)

    @cached_property
    def social_accounts(self) -> AsyncSocialAccountsResource:
        from .resources.social_accounts import AsyncSocialAccountsResource

        return AsyncSocialAccountsResource(self)

    @cached_property
    def social_account_feeds(self) -> AsyncSocialAccountFeedsResource:
        from .resources.social_account_feeds import AsyncSocialAccountFeedsResource

        return AsyncSocialAccountFeedsResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncPostForMeWithRawResponse:
        return AsyncPostForMeWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPostForMeWithStreamedResponse:
        return AsyncPostForMeWithStreamedResponse(self)

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


class PostForMeWithRawResponse:
    _client: PostForMe

    def __init__(self, client: PostForMe) -> None:
        self._client = client

    @cached_property
    def media(self) -> media.MediaResourceWithRawResponse:
        from .resources.media import MediaResourceWithRawResponse

        return MediaResourceWithRawResponse(self._client.media)

    @cached_property
    def social_posts(self) -> social_posts.SocialPostsResourceWithRawResponse:
        from .resources.social_posts import SocialPostsResourceWithRawResponse

        return SocialPostsResourceWithRawResponse(self._client.social_posts)

    @cached_property
    def social_post_results(self) -> social_post_results.SocialPostResultsResourceWithRawResponse:
        from .resources.social_post_results import SocialPostResultsResourceWithRawResponse

        return SocialPostResultsResourceWithRawResponse(self._client.social_post_results)

    @cached_property
    def social_accounts(self) -> social_accounts.SocialAccountsResourceWithRawResponse:
        from .resources.social_accounts import SocialAccountsResourceWithRawResponse

        return SocialAccountsResourceWithRawResponse(self._client.social_accounts)

    @cached_property
    def social_account_feeds(self) -> social_account_feeds.SocialAccountFeedsResourceWithRawResponse:
        from .resources.social_account_feeds import SocialAccountFeedsResourceWithRawResponse

        return SocialAccountFeedsResourceWithRawResponse(self._client.social_account_feeds)


class AsyncPostForMeWithRawResponse:
    _client: AsyncPostForMe

    def __init__(self, client: AsyncPostForMe) -> None:
        self._client = client

    @cached_property
    def media(self) -> media.AsyncMediaResourceWithRawResponse:
        from .resources.media import AsyncMediaResourceWithRawResponse

        return AsyncMediaResourceWithRawResponse(self._client.media)

    @cached_property
    def social_posts(self) -> social_posts.AsyncSocialPostsResourceWithRawResponse:
        from .resources.social_posts import AsyncSocialPostsResourceWithRawResponse

        return AsyncSocialPostsResourceWithRawResponse(self._client.social_posts)

    @cached_property
    def social_post_results(self) -> social_post_results.AsyncSocialPostResultsResourceWithRawResponse:
        from .resources.social_post_results import AsyncSocialPostResultsResourceWithRawResponse

        return AsyncSocialPostResultsResourceWithRawResponse(self._client.social_post_results)

    @cached_property
    def social_accounts(self) -> social_accounts.AsyncSocialAccountsResourceWithRawResponse:
        from .resources.social_accounts import AsyncSocialAccountsResourceWithRawResponse

        return AsyncSocialAccountsResourceWithRawResponse(self._client.social_accounts)

    @cached_property
    def social_account_feeds(self) -> social_account_feeds.AsyncSocialAccountFeedsResourceWithRawResponse:
        from .resources.social_account_feeds import AsyncSocialAccountFeedsResourceWithRawResponse

        return AsyncSocialAccountFeedsResourceWithRawResponse(self._client.social_account_feeds)


class PostForMeWithStreamedResponse:
    _client: PostForMe

    def __init__(self, client: PostForMe) -> None:
        self._client = client

    @cached_property
    def media(self) -> media.MediaResourceWithStreamingResponse:
        from .resources.media import MediaResourceWithStreamingResponse

        return MediaResourceWithStreamingResponse(self._client.media)

    @cached_property
    def social_posts(self) -> social_posts.SocialPostsResourceWithStreamingResponse:
        from .resources.social_posts import SocialPostsResourceWithStreamingResponse

        return SocialPostsResourceWithStreamingResponse(self._client.social_posts)

    @cached_property
    def social_post_results(self) -> social_post_results.SocialPostResultsResourceWithStreamingResponse:
        from .resources.social_post_results import SocialPostResultsResourceWithStreamingResponse

        return SocialPostResultsResourceWithStreamingResponse(self._client.social_post_results)

    @cached_property
    def social_accounts(self) -> social_accounts.SocialAccountsResourceWithStreamingResponse:
        from .resources.social_accounts import SocialAccountsResourceWithStreamingResponse

        return SocialAccountsResourceWithStreamingResponse(self._client.social_accounts)

    @cached_property
    def social_account_feeds(self) -> social_account_feeds.SocialAccountFeedsResourceWithStreamingResponse:
        from .resources.social_account_feeds import SocialAccountFeedsResourceWithStreamingResponse

        return SocialAccountFeedsResourceWithStreamingResponse(self._client.social_account_feeds)


class AsyncPostForMeWithStreamedResponse:
    _client: AsyncPostForMe

    def __init__(self, client: AsyncPostForMe) -> None:
        self._client = client

    @cached_property
    def media(self) -> media.AsyncMediaResourceWithStreamingResponse:
        from .resources.media import AsyncMediaResourceWithStreamingResponse

        return AsyncMediaResourceWithStreamingResponse(self._client.media)

    @cached_property
    def social_posts(self) -> social_posts.AsyncSocialPostsResourceWithStreamingResponse:
        from .resources.social_posts import AsyncSocialPostsResourceWithStreamingResponse

        return AsyncSocialPostsResourceWithStreamingResponse(self._client.social_posts)

    @cached_property
    def social_post_results(self) -> social_post_results.AsyncSocialPostResultsResourceWithStreamingResponse:
        from .resources.social_post_results import AsyncSocialPostResultsResourceWithStreamingResponse

        return AsyncSocialPostResultsResourceWithStreamingResponse(self._client.social_post_results)

    @cached_property
    def social_accounts(self) -> social_accounts.AsyncSocialAccountsResourceWithStreamingResponse:
        from .resources.social_accounts import AsyncSocialAccountsResourceWithStreamingResponse

        return AsyncSocialAccountsResourceWithStreamingResponse(self._client.social_accounts)

    @cached_property
    def social_account_feeds(self) -> social_account_feeds.AsyncSocialAccountFeedsResourceWithStreamingResponse:
        from .resources.social_account_feeds import AsyncSocialAccountFeedsResourceWithStreamingResponse

        return AsyncSocialAccountFeedsResourceWithStreamingResponse(self._client.social_account_feeds)


Client = PostForMe

AsyncClient = AsyncPostForMe
