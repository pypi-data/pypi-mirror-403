# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["TiktokConfigurationParam", "Media", "MediaTag"]


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


class TiktokConfigurationParam(TypedDict, total=False):
    allow_comment: Optional[bool]
    """Allow comments on TikTok"""

    allow_duet: Optional[bool]
    """Allow duets on TikTok"""

    allow_stitch: Optional[bool]
    """Allow stitch on TikTok"""

    auto_add_music: Optional[bool]
    """Will automatically add music to photo posts"""

    caption: Optional[object]
    """Overrides the `caption` from the post"""

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

    media: Optional[Iterable[Media]]
    """Overrides the `media` from the post"""

    privacy_status: Optional[str]
    """Sets the privacy status for TikTok (private, public)"""

    title: Optional[str]
    """Overrides the `title` from the post"""
