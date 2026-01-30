# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal

import httpx

from ..types import social_account_feed_list_params
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
from ..types.social_account_feed_list_response import SocialAccountFeedListResponse

__all__ = ["SocialAccountFeedsResource", "AsyncSocialAccountFeedsResource"]


class SocialAccountFeedsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SocialAccountFeedsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#accessing-raw-response-data-eg-headers
        """
        return SocialAccountFeedsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SocialAccountFeedsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#with_streaming_response
        """
        return SocialAccountFeedsResourceWithStreamingResponse(self)

    def list(
        self,
        social_account_id: str,
        *,
        cursor: str | Omit = omit,
        expand: List[Literal["metrics"]] | Omit = omit,
        external_post_id: SequenceNotStr[str] | Omit = omit,
        limit: float | Omit = omit,
        platform_post_id: SequenceNotStr[str] | Omit = omit,
        social_post_id: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountFeedListResponse:
        """
        Get a paginated result for the social account based on the applied filters

        Args:
          cursor: Cursor identifying next page of results

          expand: Expand additional data in the response. Currently supports: "metrics" to include
              post analytics data.

          external_post_id: Filter by Post for Me Social Postexternal ID. Multiple values imply OR logic
              (e.g., ?external_post_id=xxxxxx&external_post_id=yyyyyy).

          limit: Number of items to return; Note: some platforms will have different max limits,
              in the case the provided limit is over the platform's limit we will return the
              max allowed by the platform.

          platform_post_id: Filter by the platform's id(s). Multiple values imply OR logic (e.g.,
              ?social_post_id=spr_xxxxxx&social_post_id=spr_yyyyyy).

          social_post_id: Filter by Post for Me Social Post id(s). Multiple values imply OR logic (e.g.,
              ?social_post_id=sp_xxxxxx&social_post_id=sp_yyyyyy).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not social_account_id:
            raise ValueError(f"Expected a non-empty value for `social_account_id` but received {social_account_id!r}")
        return self._get(
            f"/v1/social-account-feeds/{social_account_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "expand": expand,
                        "external_post_id": external_post_id,
                        "limit": limit,
                        "platform_post_id": platform_post_id,
                        "social_post_id": social_post_id,
                    },
                    social_account_feed_list_params.SocialAccountFeedListParams,
                ),
            ),
            cast_to=SocialAccountFeedListResponse,
        )


class AsyncSocialAccountFeedsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSocialAccountFeedsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSocialAccountFeedsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSocialAccountFeedsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/DayMoonDevelopment/post-for-me-python#with_streaming_response
        """
        return AsyncSocialAccountFeedsResourceWithStreamingResponse(self)

    async def list(
        self,
        social_account_id: str,
        *,
        cursor: str | Omit = omit,
        expand: List[Literal["metrics"]] | Omit = omit,
        external_post_id: SequenceNotStr[str] | Omit = omit,
        limit: float | Omit = omit,
        platform_post_id: SequenceNotStr[str] | Omit = omit,
        social_post_id: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SocialAccountFeedListResponse:
        """
        Get a paginated result for the social account based on the applied filters

        Args:
          cursor: Cursor identifying next page of results

          expand: Expand additional data in the response. Currently supports: "metrics" to include
              post analytics data.

          external_post_id: Filter by Post for Me Social Postexternal ID. Multiple values imply OR logic
              (e.g., ?external_post_id=xxxxxx&external_post_id=yyyyyy).

          limit: Number of items to return; Note: some platforms will have different max limits,
              in the case the provided limit is over the platform's limit we will return the
              max allowed by the platform.

          platform_post_id: Filter by the platform's id(s). Multiple values imply OR logic (e.g.,
              ?social_post_id=spr_xxxxxx&social_post_id=spr_yyyyyy).

          social_post_id: Filter by Post for Me Social Post id(s). Multiple values imply OR logic (e.g.,
              ?social_post_id=sp_xxxxxx&social_post_id=sp_yyyyyy).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not social_account_id:
            raise ValueError(f"Expected a non-empty value for `social_account_id` but received {social_account_id!r}")
        return await self._get(
            f"/v1/social-account-feeds/{social_account_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "cursor": cursor,
                        "expand": expand,
                        "external_post_id": external_post_id,
                        "limit": limit,
                        "platform_post_id": platform_post_id,
                        "social_post_id": social_post_id,
                    },
                    social_account_feed_list_params.SocialAccountFeedListParams,
                ),
            ),
            cast_to=SocialAccountFeedListResponse,
        )


class SocialAccountFeedsResourceWithRawResponse:
    def __init__(self, social_account_feeds: SocialAccountFeedsResource) -> None:
        self._social_account_feeds = social_account_feeds

        self.list = to_raw_response_wrapper(
            social_account_feeds.list,
        )


class AsyncSocialAccountFeedsResourceWithRawResponse:
    def __init__(self, social_account_feeds: AsyncSocialAccountFeedsResource) -> None:
        self._social_account_feeds = social_account_feeds

        self.list = async_to_raw_response_wrapper(
            social_account_feeds.list,
        )


class SocialAccountFeedsResourceWithStreamingResponse:
    def __init__(self, social_account_feeds: SocialAccountFeedsResource) -> None:
        self._social_account_feeds = social_account_feeds

        self.list = to_streamed_response_wrapper(
            social_account_feeds.list,
        )


class AsyncSocialAccountFeedsResourceWithStreamingResponse:
    def __init__(self, social_account_feeds: AsyncSocialAccountFeedsResource) -> None:
        self._social_account_feeds = social_account_feeds

        self.list = async_to_streamed_response_wrapper(
            social_account_feeds.list,
        )
