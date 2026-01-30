# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["PinterestConfigurationDtoParam", "Media", "MediaTag"]


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


class PinterestConfigurationDtoParam(TypedDict, total=False):
    board_ids: Optional[SequenceNotStr[str]]
    """Pinterest board IDs"""

    caption: Optional[object]
    """Overrides the `caption` from the post"""

    link: Optional[str]
    """Pinterest post link"""

    media: Optional[Iterable[Media]]
    """Overrides the `media` from the post"""
