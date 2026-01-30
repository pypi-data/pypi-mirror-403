# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["SocialAccountListParams"]


class SocialAccountListParams(TypedDict, total=False):
    id: SequenceNotStr[str]
    """Filter by id(s).

    Multiple values imply OR logic (e.g., ?id=spc_xxxxxx&id=spc_yyyyyy).
    """

    external_id: SequenceNotStr[str]
    """Filter by externalId(s).

    Multiple values imply OR logic (e.g., ?externalId=test&externalId=test2).
    """

    limit: float
    """Number of items to return"""

    offset: float
    """Number of items to skip"""

    platform: SequenceNotStr[str]
    """Filter by platform(s).

    Multiple values imply OR logic (e.g., ?platform=x&platform=facebook).
    """

    username: SequenceNotStr[str]
    """Filter by username(s).

    Multiple values imply OR logic (e.g., ?username=test&username=test2).
    """
