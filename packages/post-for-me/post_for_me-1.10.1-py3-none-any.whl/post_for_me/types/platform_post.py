# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "PlatformPost",
    "Metrics",
    "MetricsTikTokBusinessMetricsDto",
    "MetricsTikTokBusinessMetricsDtoAudienceCity",
    "MetricsTikTokBusinessMetricsDtoAudienceCountry",
    "MetricsTikTokBusinessMetricsDtoAudienceGender",
    "MetricsTikTokBusinessMetricsDtoAudienceType",
    "MetricsTikTokBusinessMetricsDtoEngagementLike",
    "MetricsTikTokBusinessMetricsDtoImpressionSource",
    "MetricsTikTokBusinessMetricsDtoVideoViewRetention",
    "MetricsTikTokPostMetricsDto",
    "MetricsInstagramPostMetricsDto",
    "MetricsYouTubePostMetricsDto",
]


class MetricsTikTokBusinessMetricsDtoAudienceCity(BaseModel):
    city_name: str
    """City name"""

    percentage: float
    """Percentage of audience from this city"""


class MetricsTikTokBusinessMetricsDtoAudienceCountry(BaseModel):
    country: str
    """Country name"""

    percentage: float
    """Percentage of audience from this country"""


class MetricsTikTokBusinessMetricsDtoAudienceGender(BaseModel):
    gender: str
    """Gender category"""

    percentage: float
    """Percentage of audience of this gender"""


class MetricsTikTokBusinessMetricsDtoAudienceType(BaseModel):
    percentage: float
    """Percentage of audience of this type"""

    type: str
    """Type of audience"""


class MetricsTikTokBusinessMetricsDtoEngagementLike(BaseModel):
    percentage: float
    """Percentage value for the metric"""

    second: str
    """Time in seconds for the metric"""


class MetricsTikTokBusinessMetricsDtoImpressionSource(BaseModel):
    impression_source: str
    """Name of the impression source"""

    percentage: float
    """Percentage of impressions from this source"""


class MetricsTikTokBusinessMetricsDtoVideoViewRetention(BaseModel):
    percentage: float
    """Percentage value for the metric"""

    second: str
    """Time in seconds for the metric"""


class MetricsTikTokBusinessMetricsDto(BaseModel):
    address_clicks: float
    """Number of address clicks"""

    app_download_clicks: float
    """Number of app download clicks"""

    audience_cities: List[MetricsTikTokBusinessMetricsDtoAudienceCity]
    """Audience cities breakdown"""

    audience_countries: List[MetricsTikTokBusinessMetricsDtoAudienceCountry]
    """Audience countries breakdown"""

    audience_genders: List[MetricsTikTokBusinessMetricsDtoAudienceGender]
    """Audience genders breakdown"""

    audience_types: List[MetricsTikTokBusinessMetricsDtoAudienceType]
    """Audience types breakdown"""

    average_time_watched: float
    """Average time watched in seconds"""

    comments: float
    """Number of comments on the post"""

    email_clicks: float
    """Number of email clicks"""

    engagement_likes: List[MetricsTikTokBusinessMetricsDtoEngagementLike]
    """Engagement likes data by percentage and time"""

    favorites: float
    """Number of favorites on the post"""

    full_video_watched_rate: float
    """Rate of full video watches as a percentage"""

    impression_sources: List[MetricsTikTokBusinessMetricsDtoImpressionSource]
    """Impression sources breakdown"""

    lead_submissions: float
    """Number of lead submissions"""

    likes: float
    """Number of likes on the post"""

    new_followers: float
    """Number of new followers gained from the post"""

    phone_number_clicks: float
    """Number of phone number clicks"""

    profile_views: float
    """Number of profile views generated"""

    reach: float
    """Total reach of the post"""

    shares: float
    """Number of shares on the post"""

    total_time_watched: float
    """Total time watched in seconds"""

    video_view_retention: List[MetricsTikTokBusinessMetricsDtoVideoViewRetention]
    """Video view retention data by percentage and time"""

    video_views: float
    """Total number of video views"""

    website_clicks: float
    """Number of website clicks"""


class MetricsTikTokPostMetricsDto(BaseModel):
    comment_count: float
    """Number of comments on the video"""

    like_count: float
    """Number of likes on the video"""

    share_count: float
    """Number of shares of the video"""

    view_count: float
    """Number of views on the video"""


class MetricsInstagramPostMetricsDto(BaseModel):
    comments: Optional[float] = None
    """Number of comments on the post"""

    follows: Optional[float] = None
    """Number of new follows from this post"""

    ig_reels_avg_watch_time: Optional[float] = None
    """Average watch time for Reels (in milliseconds)"""

    ig_reels_video_view_total_time: Optional[float] = None
    """Total watch time for Reels (in milliseconds)"""

    likes: Optional[float] = None
    """Number of likes on the post"""

    navigation: Optional[float] = None
    """Navigation actions taken on the media"""

    profile_activity: Optional[float] = None
    """Profile activity generated from this post"""

    profile_visits: Optional[float] = None
    """Number of profile visits from this post"""

    reach: Optional[float] = None
    """Total number of unique accounts that have seen the media"""

    replies: Optional[float] = None
    """Number of replies to the story (story media only)"""

    saved: Optional[float] = None
    """Total number of unique accounts that have saved the media"""

    shares: Optional[float] = None
    """Total number of shares of the media"""

    total_interactions: Optional[float] = None
    """Total interactions on the post"""

    views: Optional[float] = None
    """Number of views on the post"""


class MetricsYouTubePostMetricsDto(BaseModel):
    comments: float
    """Number of comments on the video"""

    dislikes: float
    """Number of dislikes on the video"""

    likes: float
    """Number of likes on the video"""

    views: float
    """Number of views on the video"""

    annotation_clickable_impressions: Optional[float] = FieldInfo(alias="annotationClickableImpressions", default=None)
    """Number of clickable annotation impressions"""

    annotation_clicks: Optional[float] = FieldInfo(alias="annotationClicks", default=None)
    """Number of annotation clicks"""

    annotation_click_through_rate: Optional[float] = FieldInfo(alias="annotationClickThroughRate", default=None)
    """Annotation click-through rate"""

    annotation_closable_impressions: Optional[float] = FieldInfo(alias="annotationClosableImpressions", default=None)
    """Number of closable annotation impressions"""

    annotation_close_rate: Optional[float] = FieldInfo(alias="annotationCloseRate", default=None)
    """Annotation close rate"""

    annotation_closes: Optional[float] = FieldInfo(alias="annotationCloses", default=None)
    """Number of annotation closes"""

    annotation_impressions: Optional[float] = FieldInfo(alias="annotationImpressions", default=None)
    """Number of annotation impressions"""

    average_view_duration: Optional[float] = FieldInfo(alias="averageViewDuration", default=None)
    """Average view duration in seconds"""

    average_view_percentage: Optional[float] = FieldInfo(alias="averageViewPercentage", default=None)
    """Average percentage of the video watched"""

    card_click_rate: Optional[float] = FieldInfo(alias="cardClickRate", default=None)
    """Card click-through rate"""

    card_clicks: Optional[float] = FieldInfo(alias="cardClicks", default=None)
    """Number of card clicks"""

    card_impressions: Optional[float] = FieldInfo(alias="cardImpressions", default=None)
    """Number of card impressions"""

    card_teaser_click_rate: Optional[float] = FieldInfo(alias="cardTeaserClickRate", default=None)
    """Card teaser click-through rate"""

    card_teaser_clicks: Optional[float] = FieldInfo(alias="cardTeaserClicks", default=None)
    """Number of card teaser clicks"""

    card_teaser_impressions: Optional[float] = FieldInfo(alias="cardTeaserImpressions", default=None)
    """Number of card teaser impressions"""

    engaged_views: Optional[float] = FieldInfo(alias="engagedViews", default=None)
    """Number of engaged views"""

    estimated_minutes_watched: Optional[float] = FieldInfo(alias="estimatedMinutesWatched", default=None)
    """Estimated minutes watched"""

    estimated_red_minutes_watched: Optional[float] = FieldInfo(alias="estimatedRedMinutesWatched", default=None)
    """Estimated minutes watched by YouTube Premium (Red) members"""

    red_views: Optional[float] = FieldInfo(alias="redViews", default=None)
    """Number of views from YouTube Premium (Red) members"""

    shares: Optional[float] = None
    """Number of shares"""

    subscribers_gained: Optional[float] = FieldInfo(alias="subscribersGained", default=None)
    """Subscribers gained"""

    subscribers_lost: Optional[float] = FieldInfo(alias="subscribersLost", default=None)
    """Subscribers lost"""

    videos_added_to_playlists: Optional[float] = FieldInfo(alias="videosAddedToPlaylists", default=None)
    """Number of times the video was added to playlists"""

    videos_removed_from_playlists: Optional[float] = FieldInfo(alias="videosRemovedFromPlaylists", default=None)
    """Number of times the video was removed from playlists"""


Metrics: TypeAlias = Union[
    MetricsTikTokBusinessMetricsDto,
    MetricsTikTokPostMetricsDto,
    MetricsInstagramPostMetricsDto,
    MetricsYouTubePostMetricsDto,
]


class PlatformPost(BaseModel):
    caption: str
    """Caption or text content of the post"""

    media: List[List[object]]
    """Array of media items attached to the post"""

    platform: str
    """Social media platform name"""

    platform_account_id: str
    """Platform-specific account ID"""

    platform_post_id: str
    """Platform-specific post ID"""

    platform_url: str
    """URL to the post on the platform"""

    social_account_id: str
    """ID of the social account"""

    external_account_id: Optional[str] = None
    """External account ID from the platform"""

    external_post_id: Optional[str] = None
    """External post ID from the platform"""

    metrics: Optional[Metrics] = None
    """Post metrics and analytics data"""

    posted_at: Optional[datetime] = None
    """Date the post was published"""

    social_post_id: Optional[str] = None
    """ID of the social post"""

    social_post_result_id: Optional[str] = None
    """ID of the social post result"""
