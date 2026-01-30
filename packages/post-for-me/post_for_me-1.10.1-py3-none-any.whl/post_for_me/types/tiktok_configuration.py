# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["TiktokConfiguration", "Media", "MediaTag"]


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


class TiktokConfiguration(BaseModel):
    allow_comment: Optional[bool] = None
    """Allow comments on TikTok"""

    allow_duet: Optional[bool] = None
    """Allow duets on TikTok"""

    allow_stitch: Optional[bool] = None
    """Allow stitch on TikTok"""

    auto_add_music: Optional[bool] = None
    """Will automatically add music to photo posts"""

    caption: Optional[object] = None
    """Overrides the `caption` from the post"""

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

    media: Optional[List[Media]] = None
    """Overrides the `media` from the post"""

    privacy_status: Optional[str] = None
    """Sets the privacy status for TikTok (private, public)"""

    title: Optional[str] = None
    """Overrides the `title` from the post"""
