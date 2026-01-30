# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from post_for_me import PostForMe, AsyncPostForMe
from tests.utils import assert_matches_type
from post_for_me.types import (
    SocialPost,
    SocialPostListResponse,
    SocialPostDeleteResponse,
)
from post_for_me._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSocialPosts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: PostForMe) -> None:
        social_post = client.social_posts.create(
            caption="caption",
            social_accounts=["string"],
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: PostForMe) -> None:
        social_post = client.social_posts.create(
            caption="caption",
            social_accounts=["string"],
            account_configurations=[
                {
                    "configuration": {
                        "allow_comment": True,
                        "allow_duet": True,
                        "allow_stitch": True,
                        "auto_add_music": True,
                        "board_ids": ["string"],
                        "caption": {},
                        "collaborators": [[{}]],
                        "community_id": "community_id",
                        "disclose_branded_content": True,
                        "disclose_your_brand": True,
                        "is_ai_generated": True,
                        "is_draft": True,
                        "link": "link",
                        "location": "location",
                        "made_for_kids": True,
                        "media": [
                            {
                                "url": "url",
                                "tags": [
                                    {
                                        "id": "id",
                                        "platform": "facebook",
                                        "type": "user",
                                        "x": 0,
                                        "y": 0,
                                    }
                                ],
                                "thumbnail_timestamp_ms": {},
                                "thumbnail_url": {},
                            }
                        ],
                        "placement": "reels",
                        "poll": {
                            "duration_minutes": 0,
                            "options": ["string"],
                            "reply_settings": "following",
                        },
                        "privacy_status": "public",
                        "quote_tweet_id": "quote_tweet_id",
                        "reply_settings": "following",
                        "share_to_feed": True,
                        "title": "title",
                        "trial_reel_type": "manual",
                    },
                    "social_account_id": "social_account_id",
                }
            ],
            external_id="external_id",
            is_draft=True,
            media=[
                {
                    "url": "url",
                    "tags": [
                        {
                            "id": "id",
                            "platform": "facebook",
                            "type": "user",
                            "x": 0,
                            "y": 0,
                        }
                    ],
                    "thumbnail_timestamp_ms": {},
                    "thumbnail_url": {},
                }
            ],
            platform_configurations={
                "bluesky": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "facebook": {
                    "caption": {},
                    "collaborators": [[{}]],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "instagram": {
                    "caption": {},
                    "collaborators": ["string"],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                    "share_to_feed": True,
                    "trial_reel_type": "manual",
                },
                "linkedin": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "pinterest": {
                    "board_ids": ["string"],
                    "caption": {},
                    "link": "link",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "threads": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "tiktok": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "tiktok_business": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "x": {
                    "caption": {},
                    "community_id": "community_id",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "poll": {
                        "duration_minutes": 0,
                        "options": ["string"],
                        "reply_settings": "following",
                    },
                    "quote_tweet_id": "quote_tweet_id",
                    "reply_settings": "following",
                },
                "youtube": {
                    "caption": {},
                    "made_for_kids": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "public",
                    "title": "title",
                },
            },
            scheduled_at=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: PostForMe) -> None:
        response = client.social_posts.with_raw_response.create(
            caption="caption",
            social_accounts=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = response.parse()
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: PostForMe) -> None:
        with client.social_posts.with_streaming_response.create(
            caption="caption",
            social_accounts=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = response.parse()
            assert_matches_type(SocialPost, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: PostForMe) -> None:
        social_post = client.social_posts.retrieve(
            "id",
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: PostForMe) -> None:
        response = client.social_posts.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = response.parse()
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: PostForMe) -> None:
        with client.social_posts.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = response.parse()
            assert_matches_type(SocialPost, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: PostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.social_posts.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: PostForMe) -> None:
        social_post = client.social_posts.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: PostForMe) -> None:
        social_post = client.social_posts.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
            account_configurations=[
                {
                    "configuration": {
                        "allow_comment": True,
                        "allow_duet": True,
                        "allow_stitch": True,
                        "auto_add_music": True,
                        "board_ids": ["string"],
                        "caption": {},
                        "collaborators": [[{}]],
                        "community_id": "community_id",
                        "disclose_branded_content": True,
                        "disclose_your_brand": True,
                        "is_ai_generated": True,
                        "is_draft": True,
                        "link": "link",
                        "location": "location",
                        "made_for_kids": True,
                        "media": [
                            {
                                "url": "url",
                                "tags": [
                                    {
                                        "id": "id",
                                        "platform": "facebook",
                                        "type": "user",
                                        "x": 0,
                                        "y": 0,
                                    }
                                ],
                                "thumbnail_timestamp_ms": {},
                                "thumbnail_url": {},
                            }
                        ],
                        "placement": "reels",
                        "poll": {
                            "duration_minutes": 0,
                            "options": ["string"],
                            "reply_settings": "following",
                        },
                        "privacy_status": "public",
                        "quote_tweet_id": "quote_tweet_id",
                        "reply_settings": "following",
                        "share_to_feed": True,
                        "title": "title",
                        "trial_reel_type": "manual",
                    },
                    "social_account_id": "social_account_id",
                }
            ],
            external_id="external_id",
            is_draft=True,
            media=[
                {
                    "url": "url",
                    "tags": [
                        {
                            "id": "id",
                            "platform": "facebook",
                            "type": "user",
                            "x": 0,
                            "y": 0,
                        }
                    ],
                    "thumbnail_timestamp_ms": {},
                    "thumbnail_url": {},
                }
            ],
            platform_configurations={
                "bluesky": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "facebook": {
                    "caption": {},
                    "collaborators": [[{}]],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "instagram": {
                    "caption": {},
                    "collaborators": ["string"],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                    "share_to_feed": True,
                    "trial_reel_type": "manual",
                },
                "linkedin": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "pinterest": {
                    "board_ids": ["string"],
                    "caption": {},
                    "link": "link",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "threads": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "tiktok": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "tiktok_business": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "x": {
                    "caption": {},
                    "community_id": "community_id",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "poll": {
                        "duration_minutes": 0,
                        "options": ["string"],
                        "reply_settings": "following",
                    },
                    "quote_tweet_id": "quote_tweet_id",
                    "reply_settings": "following",
                },
                "youtube": {
                    "caption": {},
                    "made_for_kids": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "public",
                    "title": "title",
                },
            },
            scheduled_at=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: PostForMe) -> None:
        response = client.social_posts.with_raw_response.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = response.parse()
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: PostForMe) -> None:
        with client.social_posts.with_streaming_response.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = response.parse()
            assert_matches_type(SocialPost, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: PostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.social_posts.with_raw_response.update(
                id="",
                caption="caption",
                social_accounts=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: PostForMe) -> None:
        social_post = client.social_posts.list()
        assert_matches_type(SocialPostListResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: PostForMe) -> None:
        social_post = client.social_posts.list(
            external_id=["string"],
            limit=0,
            offset=0,
            platform=["bluesky"],
            social_account_id=["string"],
            status=["draft"],
        )
        assert_matches_type(SocialPostListResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: PostForMe) -> None:
        response = client.social_posts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = response.parse()
        assert_matches_type(SocialPostListResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: PostForMe) -> None:
        with client.social_posts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = response.parse()
            assert_matches_type(SocialPostListResponse, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: PostForMe) -> None:
        social_post = client.social_posts.delete(
            "id",
        )
        assert_matches_type(SocialPostDeleteResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: PostForMe) -> None:
        response = client.social_posts.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = response.parse()
        assert_matches_type(SocialPostDeleteResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: PostForMe) -> None:
        with client.social_posts.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = response.parse()
            assert_matches_type(SocialPostDeleteResponse, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: PostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.social_posts.with_raw_response.delete(
                "",
            )


class TestAsyncSocialPosts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.create(
            caption="caption",
            social_accounts=["string"],
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.create(
            caption="caption",
            social_accounts=["string"],
            account_configurations=[
                {
                    "configuration": {
                        "allow_comment": True,
                        "allow_duet": True,
                        "allow_stitch": True,
                        "auto_add_music": True,
                        "board_ids": ["string"],
                        "caption": {},
                        "collaborators": [[{}]],
                        "community_id": "community_id",
                        "disclose_branded_content": True,
                        "disclose_your_brand": True,
                        "is_ai_generated": True,
                        "is_draft": True,
                        "link": "link",
                        "location": "location",
                        "made_for_kids": True,
                        "media": [
                            {
                                "url": "url",
                                "tags": [
                                    {
                                        "id": "id",
                                        "platform": "facebook",
                                        "type": "user",
                                        "x": 0,
                                        "y": 0,
                                    }
                                ],
                                "thumbnail_timestamp_ms": {},
                                "thumbnail_url": {},
                            }
                        ],
                        "placement": "reels",
                        "poll": {
                            "duration_minutes": 0,
                            "options": ["string"],
                            "reply_settings": "following",
                        },
                        "privacy_status": "public",
                        "quote_tweet_id": "quote_tweet_id",
                        "reply_settings": "following",
                        "share_to_feed": True,
                        "title": "title",
                        "trial_reel_type": "manual",
                    },
                    "social_account_id": "social_account_id",
                }
            ],
            external_id="external_id",
            is_draft=True,
            media=[
                {
                    "url": "url",
                    "tags": [
                        {
                            "id": "id",
                            "platform": "facebook",
                            "type": "user",
                            "x": 0,
                            "y": 0,
                        }
                    ],
                    "thumbnail_timestamp_ms": {},
                    "thumbnail_url": {},
                }
            ],
            platform_configurations={
                "bluesky": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "facebook": {
                    "caption": {},
                    "collaborators": [[{}]],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "instagram": {
                    "caption": {},
                    "collaborators": ["string"],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                    "share_to_feed": True,
                    "trial_reel_type": "manual",
                },
                "linkedin": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "pinterest": {
                    "board_ids": ["string"],
                    "caption": {},
                    "link": "link",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "threads": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "tiktok": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "tiktok_business": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "x": {
                    "caption": {},
                    "community_id": "community_id",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "poll": {
                        "duration_minutes": 0,
                        "options": ["string"],
                        "reply_settings": "following",
                    },
                    "quote_tweet_id": "quote_tweet_id",
                    "reply_settings": "following",
                },
                "youtube": {
                    "caption": {},
                    "made_for_kids": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "public",
                    "title": "title",
                },
            },
            scheduled_at=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncPostForMe) -> None:
        response = await async_client.social_posts.with_raw_response.create(
            caption="caption",
            social_accounts=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = await response.parse()
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncPostForMe) -> None:
        async with async_client.social_posts.with_streaming_response.create(
            caption="caption",
            social_accounts=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = await response.parse()
            assert_matches_type(SocialPost, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.retrieve(
            "id",
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncPostForMe) -> None:
        response = await async_client.social_posts.with_raw_response.retrieve(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = await response.parse()
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncPostForMe) -> None:
        async with async_client.social_posts.with_streaming_response.retrieve(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = await response.parse()
            assert_matches_type(SocialPost, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncPostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.social_posts.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
            account_configurations=[
                {
                    "configuration": {
                        "allow_comment": True,
                        "allow_duet": True,
                        "allow_stitch": True,
                        "auto_add_music": True,
                        "board_ids": ["string"],
                        "caption": {},
                        "collaborators": [[{}]],
                        "community_id": "community_id",
                        "disclose_branded_content": True,
                        "disclose_your_brand": True,
                        "is_ai_generated": True,
                        "is_draft": True,
                        "link": "link",
                        "location": "location",
                        "made_for_kids": True,
                        "media": [
                            {
                                "url": "url",
                                "tags": [
                                    {
                                        "id": "id",
                                        "platform": "facebook",
                                        "type": "user",
                                        "x": 0,
                                        "y": 0,
                                    }
                                ],
                                "thumbnail_timestamp_ms": {},
                                "thumbnail_url": {},
                            }
                        ],
                        "placement": "reels",
                        "poll": {
                            "duration_minutes": 0,
                            "options": ["string"],
                            "reply_settings": "following",
                        },
                        "privacy_status": "public",
                        "quote_tweet_id": "quote_tweet_id",
                        "reply_settings": "following",
                        "share_to_feed": True,
                        "title": "title",
                        "trial_reel_type": "manual",
                    },
                    "social_account_id": "social_account_id",
                }
            ],
            external_id="external_id",
            is_draft=True,
            media=[
                {
                    "url": "url",
                    "tags": [
                        {
                            "id": "id",
                            "platform": "facebook",
                            "type": "user",
                            "x": 0,
                            "y": 0,
                        }
                    ],
                    "thumbnail_timestamp_ms": {},
                    "thumbnail_url": {},
                }
            ],
            platform_configurations={
                "bluesky": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "facebook": {
                    "caption": {},
                    "collaborators": [[{}]],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "instagram": {
                    "caption": {},
                    "collaborators": ["string"],
                    "location": "location",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                    "share_to_feed": True,
                    "trial_reel_type": "manual",
                },
                "linkedin": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "pinterest": {
                    "board_ids": ["string"],
                    "caption": {},
                    "link": "link",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                },
                "threads": {
                    "caption": {},
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "placement": "reels",
                },
                "tiktok": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "tiktok_business": {
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "auto_add_music": True,
                    "caption": {},
                    "disclose_branded_content": True,
                    "disclose_your_brand": True,
                    "is_ai_generated": True,
                    "is_draft": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "privacy_status",
                    "title": "title",
                },
                "x": {
                    "caption": {},
                    "community_id": "community_id",
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "poll": {
                        "duration_minutes": 0,
                        "options": ["string"],
                        "reply_settings": "following",
                    },
                    "quote_tweet_id": "quote_tweet_id",
                    "reply_settings": "following",
                },
                "youtube": {
                    "caption": {},
                    "made_for_kids": True,
                    "media": [
                        {
                            "url": "url",
                            "tags": [
                                {
                                    "id": "id",
                                    "platform": "facebook",
                                    "type": "user",
                                    "x": 0,
                                    "y": 0,
                                }
                            ],
                            "thumbnail_timestamp_ms": {},
                            "thumbnail_url": {},
                        }
                    ],
                    "privacy_status": "public",
                    "title": "title",
                },
            },
            scheduled_at=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncPostForMe) -> None:
        response = await async_client.social_posts.with_raw_response.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = await response.parse()
        assert_matches_type(SocialPost, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncPostForMe) -> None:
        async with async_client.social_posts.with_streaming_response.update(
            id="id",
            caption="caption",
            social_accounts=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = await response.parse()
            assert_matches_type(SocialPost, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncPostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.social_posts.with_raw_response.update(
                id="",
                caption="caption",
                social_accounts=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.list()
        assert_matches_type(SocialPostListResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.list(
            external_id=["string"],
            limit=0,
            offset=0,
            platform=["bluesky"],
            social_account_id=["string"],
            status=["draft"],
        )
        assert_matches_type(SocialPostListResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncPostForMe) -> None:
        response = await async_client.social_posts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = await response.parse()
        assert_matches_type(SocialPostListResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncPostForMe) -> None:
        async with async_client.social_posts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = await response.parse()
            assert_matches_type(SocialPostListResponse, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncPostForMe) -> None:
        social_post = await async_client.social_posts.delete(
            "id",
        )
        assert_matches_type(SocialPostDeleteResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncPostForMe) -> None:
        response = await async_client.social_posts.with_raw_response.delete(
            "id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        social_post = await response.parse()
        assert_matches_type(SocialPostDeleteResponse, social_post, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncPostForMe) -> None:
        async with async_client.social_posts.with_streaming_response.delete(
            "id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            social_post = await response.parse()
            assert_matches_type(SocialPostDeleteResponse, social_post, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncPostForMe) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.social_posts.with_raw_response.delete(
                "",
            )
