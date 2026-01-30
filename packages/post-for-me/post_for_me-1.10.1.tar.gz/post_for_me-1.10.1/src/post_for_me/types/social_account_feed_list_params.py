# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal, TypedDict

from .._types import SequenceNotStr

__all__ = ["SocialAccountFeedListParams"]


class SocialAccountFeedListParams(TypedDict, total=False):
    cursor: str
    """Cursor identifying next page of results"""

    expand: List[Literal["metrics"]]
    """Expand additional data in the response.

    Currently supports: "metrics" to include post analytics data.
    """

    external_post_id: SequenceNotStr[str]
    """Filter by Post for Me Social Postexternal ID.

    Multiple values imply OR logic (e.g.,
    ?external_post_id=xxxxxx&external_post_id=yyyyyy).
    """

    limit: float
    """
    Number of items to return; Note: some platforms will have different max limits,
    in the case the provided limit is over the platform's limit we will return the
    max allowed by the platform.
    """

    platform_post_id: SequenceNotStr[str]
    """Filter by the platform's id(s).

    Multiple values imply OR logic (e.g.,
    ?social_post_id=spr_xxxxxx&social_post_id=spr_yyyyyy).
    """

    social_post_id: SequenceNotStr[str]
    """Filter by Post for Me Social Post id(s).

    Multiple values imply OR logic (e.g.,
    ?social_post_id=sp_xxxxxx&social_post_id=sp_yyyyyy).
    """
