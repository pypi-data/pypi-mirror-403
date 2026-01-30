# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

import httpx

from ..types import (
    social_account_list_params,
    social_account_create_params,
    social_account_update_params,
    social_account_create_auth_url_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
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
from ..types.social_account import SocialAccount
from ..types.social_account_list_response import SocialAccountListResponse
from ..types.social_account_disconnect_response import SocialAccountDisconnectResponse
from ..types.social_account_create_auth_url_response import SocialAccountCreateAuthURLResponse

__all__ = ["SocialAccountsResource", "AsyncSocialAccountsResource"]


class SocialAccountsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SocialAccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#accessing-raw-response-data-eg-headers
        """
        return SocialAccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SocialAccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#with_streaming_response
        """
        return SocialAccountsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        access_token: str,
        access_token_expires_at: Union[str, datetime],
        platform: Literal[
            "facebook",
            "instagram",
            "x",
            "tiktok",
            "youtube",
            "pinterest",
            "linkedin",
            "bluesky",
            "threads",
            "tiktok_business",
        ],
        user_id: str,
        external_id: Optional[str] | Omit = omit,
        metadata: object | Omit = omit,
        refresh_token: Optional[str] | Omit = omit,
        refresh_token_expires_at: Union[str, datetime, None] | Omit = omit,
        username: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccount:
        """
        If a social account with the same platform and user_id already exists, it will
        be updated. If not, a new social account will be created.

        Args:
          access_token: The access token of the social account

          access_token_expires_at: The access token expiration date of the social account

          platform: The platform of the social account

          user_id: The user id of the social account

          external_id: The external id of the social account

          metadata: The metadata of the social account

          refresh_token: The refresh token of the social account

          refresh_token_expires_at: The refresh token expiration date of the social account

          username: The platform's username of the social account

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/social-accounts",
            body=maybe_transform(
                {
                    "access_token": access_token,
                    "access_token_expires_at": access_token_expires_at,
                    "platform": platform,
                    "user_id": user_id,
                    "external_id": external_id,
                    "metadata": metadata,
                    "refresh_token": refresh_token,
                    "refresh_token_expires_at": refresh_token_expires_at,
                    "username": username,
                },
                social_account_create_params.SocialAccountCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccount,
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
    ) -> SocialAccount:
        """
        Get social account by ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/v1/social-accounts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccount,
        )

    def update(
        self,
        id: str,
        *,
        external_id: str | Omit = omit,
        username: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccount:
        """
        Update social account

        Args:
          external_id: The platform's external id of the social account

          username: The platform's username of the social account

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._patch(
            f"/v1/social-accounts/{id}",
            body=maybe_transform(
                {
                    "external_id": external_id,
                    "username": username,
                },
                social_account_update_params.SocialAccountUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccount,
        )

    def list(
        self,
        *,
        id: SequenceNotStr[str] | Omit = omit,
        external_id: SequenceNotStr[str] | Omit = omit,
        limit: float | Omit = omit,
        offset: float | Omit = omit,
        platform: SequenceNotStr[str] | Omit = omit,
        username: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountListResponse:
        """
        Get a paginated result for social accounts based on the applied filters

        Args:
          id: Filter by id(s). Multiple values imply OR logic (e.g.,
              ?id=spc_xxxxxx&id=spc_yyyyyy).

          external_id: Filter by externalId(s). Multiple values imply OR logic (e.g.,
              ?externalId=test&externalId=test2).

          limit: Number of items to return

          offset: Number of items to skip

          platform: Filter by platform(s). Multiple values imply OR logic (e.g.,
              ?platform=x&platform=facebook).

          username: Filter by username(s). Multiple values imply OR logic (e.g.,
              ?username=test&username=test2).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/v1/social-accounts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "id": id,
                        "external_id": external_id,
                        "limit": limit,
                        "offset": offset,
                        "platform": platform,
                        "username": username,
                    },
                    social_account_list_params.SocialAccountListParams,
                ),
            ),
            cast_to=SocialAccountListResponse,
        )

    def create_auth_url(
        self,
        *,
        platform: str,
        external_id: str | Omit = omit,
        permissions: List[Literal["posts", "feeds"]] | Omit = omit,
        platform_data: social_account_create_auth_url_params.PlatformData | Omit = omit,
        redirect_url_override: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountCreateAuthURLResponse:
        """
        Generates a URL that initiates the authentication flow for a user's social media
        account. When visited, the user is redirected to the selected social platform's
        login/authorization page. Upon successful authentication, they are redirected
        back to your application

        Args:
          platform: The social account provider

          external_id: Your unique identifier for the social account

          permissions: List of permissions you want to allow. Will default to only post permissions.
              You must include the "feeds" permission to request an account feed and metrics

          platform_data: Additional data needed for the provider

          redirect_url_override: Override the default redirect URL for the OAuth flow. If provided, this URL will
              be used instead of our redirect URL. Make sure this URL is included in your
              app's authorized redirect urls. This override will not work when using our
              system credientals.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/v1/social-accounts/auth-url",
            body=maybe_transform(
                {
                    "platform": platform,
                    "external_id": external_id,
                    "permissions": permissions,
                    "platform_data": platform_data,
                    "redirect_url_override": redirect_url_override,
                },
                social_account_create_auth_url_params.SocialAccountCreateAuthURLParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccountCreateAuthURLResponse,
        )

    def disconnect(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountDisconnectResponse:
        """
        Disconnecting an account with remove all auth tokens and mark the account as
        disconnected. The record of the account will be kept and can be retrieved and
        reconnected by the owner of the account.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._post(
            f"/v1/social-accounts/{id}/disconnect",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccountDisconnectResponse,
        )


class AsyncSocialAccountsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSocialAccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSocialAccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSocialAccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#with_streaming_response
        """
        return AsyncSocialAccountsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        access_token: str,
        access_token_expires_at: Union[str, datetime],
        platform: Literal[
            "facebook",
            "instagram",
            "x",
            "tiktok",
            "youtube",
            "pinterest",
            "linkedin",
            "bluesky",
            "threads",
            "tiktok_business",
        ],
        user_id: str,
        external_id: Optional[str] | Omit = omit,
        metadata: object | Omit = omit,
        refresh_token: Optional[str] | Omit = omit,
        refresh_token_expires_at: Union[str, datetime, None] | Omit = omit,
        username: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccount:
        """
        If a social account with the same platform and user_id already exists, it will
        be updated. If not, a new social account will be created.

        Args:
          access_token: The access token of the social account

          access_token_expires_at: The access token expiration date of the social account

          platform: The platform of the social account

          user_id: The user id of the social account

          external_id: The external id of the social account

          metadata: The metadata of the social account

          refresh_token: The refresh token of the social account

          refresh_token_expires_at: The refresh token expiration date of the social account

          username: The platform's username of the social account

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/social-accounts",
            body=await async_maybe_transform(
                {
                    "access_token": access_token,
                    "access_token_expires_at": access_token_expires_at,
                    "platform": platform,
                    "user_id": user_id,
                    "external_id": external_id,
                    "metadata": metadata,
                    "refresh_token": refresh_token,
                    "refresh_token_expires_at": refresh_token_expires_at,
                    "username": username,
                },
                social_account_create_params.SocialAccountCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccount,
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
    ) -> SocialAccount:
        """
        Get social account by ID

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/v1/social-accounts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccount,
        )

    async def update(
        self,
        id: str,
        *,
        external_id: str | Omit = omit,
        username: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccount:
        """
        Update social account

        Args:
          external_id: The platform's external id of the social account

          username: The platform's username of the social account

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._patch(
            f"/v1/social-accounts/{id}",
            body=await async_maybe_transform(
                {
                    "external_id": external_id,
                    "username": username,
                },
                social_account_update_params.SocialAccountUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccount,
        )

    async def list(
        self,
        *,
        id: SequenceNotStr[str] | Omit = omit,
        external_id: SequenceNotStr[str] | Omit = omit,
        limit: float | Omit = omit,
        offset: float | Omit = omit,
        platform: SequenceNotStr[str] | Omit = omit,
        username: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountListResponse:
        """
        Get a paginated result for social accounts based on the applied filters

        Args:
          id: Filter by id(s). Multiple values imply OR logic (e.g.,
              ?id=spc_xxxxxx&id=spc_yyyyyy).

          external_id: Filter by externalId(s). Multiple values imply OR logic (e.g.,
              ?externalId=test&externalId=test2).

          limit: Number of items to return

          offset: Number of items to skip

          platform: Filter by platform(s). Multiple values imply OR logic (e.g.,
              ?platform=x&platform=facebook).

          username: Filter by username(s). Multiple values imply OR logic (e.g.,
              ?username=test&username=test2).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/v1/social-accounts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "id": id,
                        "external_id": external_id,
                        "limit": limit,
                        "offset": offset,
                        "platform": platform,
                        "username": username,
                    },
                    social_account_list_params.SocialAccountListParams,
                ),
            ),
            cast_to=SocialAccountListResponse,
        )

    async def create_auth_url(
        self,
        *,
        platform: str,
        external_id: str | Omit = omit,
        permissions: List[Literal["posts", "feeds"]] | Omit = omit,
        platform_data: social_account_create_auth_url_params.PlatformData | Omit = omit,
        redirect_url_override: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountCreateAuthURLResponse:
        """
        Generates a URL that initiates the authentication flow for a user's social media
        account. When visited, the user is redirected to the selected social platform's
        login/authorization page. Upon successful authentication, they are redirected
        back to your application

        Args:
          platform: The social account provider

          external_id: Your unique identifier for the social account

          permissions: List of permissions you want to allow. Will default to only post permissions.
              You must include the "feeds" permission to request an account feed and metrics

          platform_data: Additional data needed for the provider

          redirect_url_override: Override the default redirect URL for the OAuth flow. If provided, this URL will
              be used instead of our redirect URL. Make sure this URL is included in your
              app's authorized redirect urls. This override will not work when using our
              system credientals.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/v1/social-accounts/auth-url",
            body=await async_maybe_transform(
                {
                    "platform": platform,
                    "external_id": external_id,
                    "permissions": permissions,
                    "platform_data": platform_data,
                    "redirect_url_override": redirect_url_override,
                },
                social_account_create_auth_url_params.SocialAccountCreateAuthURLParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccountCreateAuthURLResponse,
        )

    async def disconnect(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountDisconnectResponse:
        """
        Disconnecting an account with remove all auth tokens and mark the account as
        disconnected. The record of the account will be kept and can be retrieved and
        reconnected by the owner of the account.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._post(
            f"/v1/social-accounts/{id}/disconnect",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SocialAccountDisconnectResponse,
        )


class SocialAccountsResourceWithRawResponse:
    def __init__(self, social_accounts: SocialAccountsResource) -> None:
        self._social_accounts = social_accounts

        self.create = to_raw_response_wrapper(
            social_accounts.create,
        )
        self.retrieve = to_raw_response_wrapper(
            social_accounts.retrieve,
        )
        self.update = to_raw_response_wrapper(
            social_accounts.update,
        )
        self.list = to_raw_response_wrapper(
            social_accounts.list,
        )
        self.create_auth_url = to_raw_response_wrapper(
            social_accounts.create_auth_url,
        )
        self.disconnect = to_raw_response_wrapper(
            social_accounts.disconnect,
        )


class AsyncSocialAccountsResourceWithRawResponse:
    def __init__(self, social_accounts: AsyncSocialAccountsResource) -> None:
        self._social_accounts = social_accounts

        self.create = async_to_raw_response_wrapper(
            social_accounts.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            social_accounts.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            social_accounts.update,
        )
        self.list = async_to_raw_response_wrapper(
            social_accounts.list,
        )
        self.create_auth_url = async_to_raw_response_wrapper(
            social_accounts.create_auth_url,
        )
        self.disconnect = async_to_raw_response_wrapper(
            social_accounts.disconnect,
        )


class SocialAccountsResourceWithStreamingResponse:
    def __init__(self, social_accounts: SocialAccountsResource) -> None:
        self._social_accounts = social_accounts

        self.create = to_streamed_response_wrapper(
            social_accounts.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            social_accounts.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            social_accounts.update,
        )
        self.list = to_streamed_response_wrapper(
            social_accounts.list,
        )
        self.create_auth_url = to_streamed_response_wrapper(
            social_accounts.create_auth_url,
        )
        self.disconnect = to_streamed_response_wrapper(
            social_accounts.disconnect,
        )


class AsyncSocialAccountsResourceWithStreamingResponse:
    def __init__(self, social_accounts: AsyncSocialAccountsResource) -> None:
        self._social_accounts = social_accounts

        self.create = async_to_streamed_response_wrapper(
            social_accounts.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            social_accounts.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            social_accounts.update,
        )
        self.list = async_to_streamed_response_wrapper(
            social_accounts.list,
        )
        self.create_auth_url = async_to_streamed_response_wrapper(
            social_accounts.create_auth_url,
        )
        self.disconnect = async_to_streamed_response_wrapper(
            social_accounts.disconnect,
        )
