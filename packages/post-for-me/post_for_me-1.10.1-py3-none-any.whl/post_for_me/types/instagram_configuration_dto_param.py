# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["InstagramConfigurationDtoParam", "Media", "MediaTag"]


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


class InstagramConfigurationDtoParam(TypedDict, total=False):
    caption: Optional[object]
    """Overrides the `caption` from the post"""

    collaborators: Optional[SequenceNotStr[str]]
    """Instagram usernames to be tagged as a collaborator"""

    location: Optional[str]
    """Page id with a location that you want to tag the image or video with"""

    media: Optional[Iterable[Media]]
    """Overrides the `media` from the post"""

    placement: Optional[Literal["reels", "stories", "timeline"]]
    """Instagram post placement"""

    share_to_feed: Optional[bool]
    """If false video posts will only be shown in the Reels tab"""

    trial_reel_type: Optional[Literal["manual", "performance"]]
    """Instagram trial reel type, when passed will be created as a trial reel.

    If manual the trial reel can be manually graduated in the native app. If
    perfomance the trial reel will be automatically graduated if the trial reel
    performs well.
    """
