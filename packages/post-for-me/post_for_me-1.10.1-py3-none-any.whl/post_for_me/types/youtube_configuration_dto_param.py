# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["YoutubeConfigurationDtoParam", "Media", "MediaTag"]


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


class YoutubeConfigurationDtoParam(TypedDict, total=False):
    caption: Optional[object]
    """Overrides the `caption` from the post"""

    made_for_kids: Optional[bool]
    """If true will notify YouTube the video is intended for kids, defaults to false"""

    media: Optional[Iterable[Media]]
    """Overrides the `media` from the post"""

    privacy_status: Optional[Literal["public", "private", "unlisted"]]
    """Sets the privacy status of the video, will default to public"""

    title: Optional[str]
    """Overrides the `title` from the post"""
