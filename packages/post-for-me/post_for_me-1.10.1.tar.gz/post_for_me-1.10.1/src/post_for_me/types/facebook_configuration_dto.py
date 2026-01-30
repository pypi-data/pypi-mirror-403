# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["FacebookConfigurationDto", "Media", "MediaTag"]


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


class FacebookConfigurationDto(BaseModel):
    caption: Optional[object] = None
    """Overrides the `caption` from the post"""

    collaborators: Optional[List[List[object]]] = None
    """List of page ids to invite as collaborators for a Video Reel"""

    location: Optional[str] = None
    """Page id with a location that you want to tag the image or video with"""

    media: Optional[List[Media]] = None
    """Overrides the `media` from the post"""

    placement: Optional[Literal["reels", "stories", "timeline"]] = None
    """Facebook post placement"""
