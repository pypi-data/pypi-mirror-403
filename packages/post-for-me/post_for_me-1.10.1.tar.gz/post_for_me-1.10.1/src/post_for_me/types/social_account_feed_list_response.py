# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .platform_post import PlatformPost

__all__ = ["SocialAccountFeedListResponse", "Meta"]


class Meta(BaseModel):
    cursor: str
    """Id representing the next page of items"""

    limit: float
    """Maximum number of items returned."""

    next: Optional[str] = None
    """URL to the next page of results, or null if none."""

    has_more: Optional[bool] = None
    """Indicates if there are more results or not"""


class SocialAccountFeedListResponse(BaseModel):
    data: List[PlatformPost]

    meta: Meta
