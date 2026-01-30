# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from post_for_me import PostForMe, AsyncPostForMe
from tests.utils import assert_matches_type
from post_for_me.types import SocialAccountFeedListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSocialAccountFeeds:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: PostForMe) -> None:
        social_account_feed = client.social_account_feeds.list(
            social_account_id="social_account_id",
        )
        assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: PostForMe) -> None:
        social_account_feed = client.social_account_feeds.list(
            social_account_id="social_account_id",
            cursor="cursor",
            expand=["metrics"],
            external_post_id=["string"],
            limit=0,
            platform_post_id=["string"],
            social_post_id=["string"],
        )
        assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: PostForMe) -> None:
        response = client.social_account_feeds.with_raw_response.list(
            social_account_id="social_account_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_account_feed = response.parse()
        assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: PostForMe) -> None:
        with client.social_account_feeds.with_streaming_response.list(
            social_account_id="social_account_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_account_feed = response.parse()
            assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: PostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `social_account_id` but received ''"):
            client.social_account_feeds.with_raw_response.list(
                social_account_id="",
            )


class TestAsyncSocialAccountFeeds:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncPostForMe) -> None:
        social_account_feed = await async_client.social_account_feeds.list(
            social_account_id="social_account_id",
        )
        assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncPostForMe) -> None:
        social_account_feed = await async_client.social_account_feeds.list(
            social_account_id="social_account_id",
            cursor="cursor",
            expand=["metrics"],
            external_post_id=["string"],
            limit=0,
            platform_post_id=["string"],
            social_post_id=["string"],
        )
        assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncPostForMe) -> None:
        response = await async_client.social_account_feeds.with_raw_response.list(
            social_account_id="social_account_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_account_feed = await response.parse()
        assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncPostForMe) -> None:
        async with async_client.social_account_feeds.with_streaming_response.list(
            social_account_id="social_account_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_account_feed = await response.parse()
            assert_matches_type(SocialAccountFeedListResponse, social_account_feed, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncPostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `social_account_id` but received ''"):
            await async_client.social_account_feeds.with_raw_response.list(
                social_account_id="",
            )
