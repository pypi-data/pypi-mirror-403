# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["FacebookConfigurationDtoParam", "Media", "MediaTag"]


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


class FacebookConfigurationDtoParam(TypedDict, total=False):
    caption: Optional[object]
    """Overrides the `caption` from the post"""

    collaborators: Optional[Iterable[Iterable[object]]]
    """List of page ids to invite as collaborators for a Video Reel"""

    location: Optional[str]
    """Page id with a location that you want to tag the image or video with"""

    media: Optional[Iterable[Media]]
    """Overrides the `media` from the post"""

    placement: Optional[Literal["reels", "stories", "timeline"]]
    """Facebook post placement"""
