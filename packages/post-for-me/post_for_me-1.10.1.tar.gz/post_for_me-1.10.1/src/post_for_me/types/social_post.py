# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel
from .social_account import SocialAccount
from .platform_configurations_dto import PlatformConfigurationsDto

__all__ = [
    "SocialPost",
    "AccountConfiguration",
    "AccountConfigurationConfiguration",
    "AccountConfigurationConfigurationMedia",
    "AccountConfigurationConfigurationMediaTag",
    "AccountConfigurationConfigurationPoll",
    "Media",
    "MediaTag",
]


class AccountConfigurationConfigurationMediaTag(BaseModel):
    id: str
    """Facebook User ID, Instagram Username or Instagram product id to tag"""

    platform: Literal["facebook", "instagram"]
    """The platform for the tags"""

    type: Literal["user", "product"]
    """
    The type of tag, user to tag accounts, product to tag products (only supported
    for instagram)
    """

    x: Optional[float] = None
    """
    Percentage distance from left edge of the image, Not required for videos or
    stories
    """

    y: Optional[float] = None
    """
    Percentage distance from top edge of the image, Not required for videos or
    stories
    """


class AccountConfigurationConfigurationMedia(BaseModel):
    url: str
    """Public URL of the media"""

    tags: Optional[List[AccountConfigurationConfigurationMediaTag]] = None
    """List of tags to attach to the media"""

    thumbnail_timestamp_ms: Optional[object] = None
    """Timestamp in milliseconds of frame to use as thumbnail for the media"""

    thumbnail_url: Optional[object] = None
    """Public URL of the thumbnail for the media"""


class AccountConfigurationConfigurationPoll(BaseModel):
    """Poll options for the twitter"""

    duration_minutes: float
    """Duration of the poll in minutes"""

    options: List[str]
    """The choices of the poll, requiring 2-4 options"""

    reply_settings: Optional[Literal["following", "mentionedUsers", "subscribers", "verified"]] = None
    """Who can reply to the tweet"""


class AccountConfigurationConfiguration(BaseModel):
    """Configuration for the social account"""

    allow_comment: Optional[bool] = None
    """Allow comments on TikTok"""

    allow_duet: Optional[bool] = None
    """Allow duets on TikTok"""

    allow_stitch: Optional[bool] = None
    """Allow stitch on TikTok"""

    auto_add_music: Optional[bool] = None
    """Will automatically add music to photo posts on TikTok"""

    board_ids: Optional[List[str]] = None
    """Pinterest board IDs"""

    caption: Optional[object] = None
    """Overrides the `caption` from the post"""

    collaborators: Optional[List[List[object]]] = None
    """
    List of page ids or users to invite as collaborators for a Video Reel (Instagram
    and Facebook)
    """

    community_id: Optional[str] = None
    """Id of the twitter community to post to"""

    disclose_branded_content: Optional[bool] = None
    """Disclose branded content on TikTok"""

    disclose_your_brand: Optional[bool] = None
    """Disclose your brand on TikTok"""

    is_ai_generated: Optional[bool] = None
    """Flag content as AI generated on TikTok"""

    is_draft: Optional[bool] = None
    """
    Will create a draft upload to TikTok, posting will need to be completed from
    within the app
    """

    link: Optional[str] = None
    """Pinterest post link"""

    location: Optional[str] = None
    """
    Page id with a location that you want to tag the image or video with (Instagram
    and Facebook)
    """

    made_for_kids: Optional[bool] = None
    """If true will notify YouTube the video is intended for kids, defaults to false"""

    media: Optional[List[AccountConfigurationConfigurationMedia]] = None
    """Overrides the `media` from the post"""

    placement: Optional[Literal["reels", "timeline", "stories"]] = None
    """Post placement for Facebook/Instagram/Threads"""

    poll: Optional[AccountConfigurationConfigurationPoll] = None
    """Poll options for the twitter"""

    privacy_status: Optional[Literal["public", "private", "unlisted"]] = None
    """
    Sets the privacy status for TikTok (private, public), or YouTube (private,
    public, unlisted)
    """

    quote_tweet_id: Optional[str] = None
    """Id of the tweet you want to quote"""

    reply_settings: Optional[Literal["following", "mentionedUsers", "subscribers", "verified"]] = None
    """Who can reply to the tweet"""

    share_to_feed: Optional[bool] = None
    """If false Instagram video posts will only be shown in the Reels tab"""

    title: Optional[str] = None
    """Overrides the `title` from the post"""

    trial_reel_type: Optional[Literal["manual", "performance"]] = None
    """Instagram trial reel type, when passed will be created as a trial reel.

    If manual the trial reel can be manually graduated in the native app. If
    perfomance the trial reel will be automatically graduated if the trial reel
    performs well.
    """


class AccountConfiguration(BaseModel):
    configuration: AccountConfigurationConfiguration
    """Configuration for the social account"""

    social_account_id: str
    """ID of the social account, you want to apply the configuration to"""


class MediaTag(BaseModel):
    id: str
    """Facebook User ID, Instagram Username or Instagram product id to tag"""

    platform: Literal["facebook", "instagram"]
    """The platform for the tags"""

    type: Literal["user", "product"]
    """
    The type of tag, user to tag accounts, product to tag products (only supported
    for instagram)
    """

    x: Optional[float] = None
    """
    Percentage distance from left edge of the image, Not required for videos or
    stories
    """

    y: Optional[float] = None
    """
    Percentage distance from top edge of the image, Not required for videos or
    stories
    """


class Media(BaseModel):
    url: str
    """Public URL of the media"""

    tags: Optional[List[MediaTag]] = None
    """List of tags to attach to the media"""

    thumbnail_timestamp_ms: Optional[object] = None
    """Timestamp in milliseconds of frame to use as thumbnail for the media"""

    thumbnail_url: Optional[object] = None
    """Public URL of the thumbnail for the media"""


class SocialPost(BaseModel):
    id: str
    """Unique identifier of the post"""

    account_configurations: Optional[List[AccountConfiguration]] = None
    """Account-specific configurations for the post"""

    caption: str
    """Caption text for the post"""

    created_at: str
    """Timestamp when the post was created"""

    external_id: Optional[str] = None
    """Provided unique identifier of the post"""

    media: Optional[List[Media]] = None
    """Array of media URLs associated with the post"""

    platform_configurations: Optional[PlatformConfigurationsDto] = None
    """Platform-specific configurations for the post"""

    scheduled_at: Optional[str] = None
    """Scheduled date and time for the post"""

    social_accounts: List[SocialAccount]
    """Array of social account IDs for posting"""

    status: Literal["draft", "scheduled", "processing", "processed"]
    """Current status of the post: draft, processed, scheduled, or processing"""

    updated_at: str
    """Timestamp when the post was last updated"""
