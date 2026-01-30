# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable, Optional
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .platform_configurations_dto_param import PlatformConfigurationsDtoParam

__all__ = [
    "SocialPostCreateParams",
    "AccountConfiguration",
    "AccountConfigurationConfiguration",
    "AccountConfigurationConfigurationMedia",
    "AccountConfigurationConfigurationMediaTag",
    "AccountConfigurationConfigurationPoll",
    "Media",
    "MediaTag",
]


class SocialPostCreateParams(TypedDict, total=False):
    caption: Required[str]
    """Caption text for the post"""

    social_accounts: Required[SequenceNotStr[str]]
    """Array of social account IDs for posting"""

    account_configurations: Optional[Iterable[AccountConfiguration]]
    """Account-specific configurations for the post"""

    external_id: Optional[str]
    """Array of social account IDs for posting"""

    is_draft: Annotated[Optional[bool], PropertyInfo(alias="isDraft")]
    """If isDraft is set then the post will not be processed"""

    media: Optional[Iterable[Media]]
    """Array of media URLs associated with the post"""

    platform_configurations: Optional[PlatformConfigurationsDtoParam]
    """Platform-specific configurations for the post"""

    scheduled_at: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]
    """
    Scheduled date and time for the post, setting to null or undefined will post
    instantly
    """


class AccountConfigurationConfigurationMediaTag(TypedDict, total=False):
    id: Required[str]
    """Facebook User ID, Instagram Username or Instagram product id to tag"""

    platform: Required[Literal["facebook", "instagram"]]
    """The platform for the tags"""

    type: Required[Literal["user", "product"]]
    """
    The type of tag, user to tag accounts, product to tag products (only supported
    for instagram)
    """

    x: float
    """
    Percentage distance from left edge of the image, Not required for videos or
    stories
    """

    y: float
    """
    Percentage distance from top edge of the image, Not required for videos or
    stories
    """


class AccountConfigurationConfigurationMedia(TypedDict, total=False):
    url: Required[str]
    """Public URL of the media"""

    tags: Optional[Iterable[AccountConfigurationConfigurationMediaTag]]
    """List of tags to attach to the media"""

    thumbnail_timestamp_ms: Optional[object]
    """Timestamp in milliseconds of frame to use as thumbnail for the media"""

    thumbnail_url: Optional[object]
    """Public URL of the thumbnail for the media"""


class AccountConfigurationConfigurationPoll(TypedDict, total=False):
    """Poll options for the twitter"""

    duration_minutes: Required[float]
    """Duration of the poll in minutes"""

    options: Required[SequenceNotStr[str]]
    """The choices of the poll, requiring 2-4 options"""

    reply_settings: Literal["following", "mentionedUsers", "subscribers", "verified"]
    """Who can reply to the tweet"""


class AccountConfigurationConfiguration(TypedDict, total=False):
    """Configuration for the social account"""

    allow_comment: Optional[bool]
    """Allow comments on TikTok"""

    allow_duet: Optional[bool]
    """Allow duets on TikTok"""

    allow_stitch: Optional[bool]
    """Allow stitch on TikTok"""

    auto_add_music: Optional[bool]
    """Will automatically add music to photo posts on TikTok"""

    board_ids: Optional[SequenceNotStr[str]]
    """Pinterest board IDs"""

    caption: Optional[object]
    """Overrides the `caption` from the post"""

    collaborators: Optional[Iterable[Iterable[object]]]
    """
    List of page ids or users to invite as collaborators for a Video Reel (Instagram
    and Facebook)
    """

    community_id: str
    """Id of the twitter community to post to"""

    disclose_branded_content: Optional[bool]
    """Disclose branded content on TikTok"""

    disclose_your_brand: Optional[bool]
    """Disclose your brand on TikTok"""

    is_ai_generated: Optional[bool]
    """Flag content as AI generated on TikTok"""

    is_draft: Optional[bool]
    """
    Will create a draft upload to TikTok, posting will need to be completed from
    within the app
    """

    link: Optional[str]
    """Pinterest post link"""

    location: Optional[str]
    """
    Page id with a location that you want to tag the image or video with (Instagram
    and Facebook)
    """

    made_for_kids: Optional[bool]
    """If true will notify YouTube the video is intended for kids, defaults to false"""

    media: Optional[Iterable[AccountConfigurationConfigurationMedia]]
    """Overrides the `media` from the post"""

    placement: Optional[Literal["reels", "timeline", "stories"]]
    """Post placement for Facebook/Instagram/Threads"""

    poll: AccountConfigurationConfigurationPoll
    """Poll options for the twitter"""

    privacy_status: Optional[Literal["public", "private", "unlisted"]]
    """
    Sets the privacy status for TikTok (private, public), or YouTube (private,
    public, unlisted)
    """

    quote_tweet_id: str
    """Id of the tweet you want to quote"""

    reply_settings: Optional[Literal["following", "mentionedUsers", "subscribers", "verified"]]
    """Who can reply to the tweet"""

    share_to_feed: Optional[bool]
    """If false Instagram video posts will only be shown in the Reels tab"""

    title: Optional[str]
    """Overrides the `title` from the post"""

    trial_reel_type: Optional[Literal["manual", "performance"]]
    """Instagram trial reel type, when passed will be created as a trial reel.

    If manual the trial reel can be manually graduated in the native app. If
    perfomance the trial reel will be automatically graduated if the trial reel
    performs well.
    """


class AccountConfiguration(TypedDict, total=False):
    configuration: Required[AccountConfigurationConfiguration]
    """Configuration for the social account"""

    social_account_id: Required[str]
    """ID of the social account, you want to apply the configuration to"""


class MediaTag(TypedDict, total=False):
    id: Required[str]
    """Facebook User ID, Instagram Username or Instagram product id to tag"""

    platform: Required[Literal["facebook", "instagram"]]
    """The platform for the tags"""

    type: Required[Literal["user", "product"]]
    """
    The type of tag, user to tag accounts, product to tag products (only supported
    for instagram)
    """

    x: float
    """
    Percentage distance from left edge of the image, Not required for videos or
    stories
    """

    y: float
    """
    Percentage distance from top edge of the image, Not required for videos or
    stories
    """


class Media(TypedDict, total=False):
    url: Required[str]
    """Public URL of the media"""

    tags: Optional[Iterable[MediaTag]]
    """List of tags to attach to the media"""

    thumbnail_timestamp_ms: Optional[object]
    """Timestamp in milliseconds of frame to use as thumbnail for the media"""

    thumbnail_url: Optional[object]
    """Public URL of the thumbnail for the media"""
