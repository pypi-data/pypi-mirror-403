# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable
from typing_extensions import Literal, Required, TypedDict

__all__ = [
    "SocialAccountCreateAuthURLParams",
    "PlatformData",
    "PlatformDataBluesky",
    "PlatformDataFacebook",
    "PlatformDataInstagram",
    "PlatformDataLinkedin",
    "PlatformDataPinterest",
    "PlatformDataThreads",
    "PlatformDataTiktok",
    "PlatformDataTiktokBusiness",
    "PlatformDataYoutube",
]


class SocialAccountCreateAuthURLParams(TypedDict, total=False):
    platform: Required[str]
    """The social account provider"""

    external_id: str
    """Your unique identifier for the social account"""

    permissions: List[Literal["posts", "feeds"]]
    """List of permissions you want to allow.

    Will default to only post permissions. You must include the "feeds" permission
    to request an account feed and metrics
    """

    platform_data: PlatformData
    """Additional data needed for the provider"""

    redirect_url_override: str
    """Override the default redirect URL for the OAuth flow.

    If provided, this URL will be used instead of our redirect URL. Make sure this
    URL is included in your app's authorized redirect urls. This override will not
    work when using our system credientals.
    """


class PlatformDataBluesky(TypedDict, total=False):
    """Additional data needed for connecting bluesky accounts"""

    app_password: Required[str]
    """The app password of the account"""

    handle: Required[str]
    """The handle of the account"""


class PlatformDataFacebook(TypedDict, total=False):
    """Additional data for connecting facebook accounts"""

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default scopes: public_profile, pages_show_list, pages_read_engagement,
    pages_manage_posts, business_management
    """


class PlatformDataInstagram(TypedDict, total=False):
    """Additional data for connecting instagram accounts"""

    connection_type: Required[Literal["instagram", "facebook"]]
    """
    The type of connection; instagram for using login with instagram, facebook for
    using login with facebook.
    """

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default instagram scopes: instagram_business_basic,
    instagram_business_content_publish. Default facebook scopes: instagram_basic,
    instagram_content_publish, pages_show_list, public_profile, business_management
    """


class PlatformDataLinkedin(TypedDict, total=False):
    """Additional data for connecting linkedin accounts"""

    connection_type: Required[Literal["personal", "organization"]]
    """
    The type of connection; If using our provided credentials always use
    "organization". If using your own crednetials then only use "organization" if
    you are using the Community API
    """

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default personal scopes: openid, w_member_social, profile, email. Default
    organization scopes: r_basicprofile, w_member_social, r_organization_social,
    w_organization_social, rw_organization_admin
    """


class PlatformDataPinterest(TypedDict, total=False):
    """Additional data for connecting Pinterest accounts"""

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default scopes: boards:read, boards:write, pins:read, pins:write,
    user_accounts:read
    """


class PlatformDataThreads(TypedDict, total=False):
    """Additional data for connecting Threads accounts"""

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default scopes: threads_basic, threads_content_publish
    """


class PlatformDataTiktok(TypedDict, total=False):
    """Additional data for connecting TikTok accounts"""

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default scopes: user.info.basic, video.list, video.upload, video.publish
    """


class PlatformDataTiktokBusiness(TypedDict, total=False):
    """Additional data for connecting TikTok Business accounts"""

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default scopes: user.info.basic, user.info.username, user.info.stats,
    user.info.profile, user.account.type, user.insights, video.list, video.insights,
    comment.list, comment.list.manage, video.publish, video.upload, biz.spark.auth,
    discovery.search.words
    """


class PlatformDataYoutube(TypedDict, total=False):
    """Additional data for connecting YouTube accounts"""

    permission_overrides: Iterable[Iterable[object]]
    """Override the default permissions/scopes requested during OAuth.

    Default scopes: https://www.googleapis.com/auth/youtube.force-ssl,
    https://www.googleapis.com/auth/youtube.upload,
    https://www.googleapis.com/auth/youtube.readonly,
    https://www.googleapis.com/auth/userinfo.profile
    """


class PlatformData(TypedDict, total=False):
    """Additional data needed for the provider"""

    bluesky: PlatformDataBluesky
    """Additional data needed for connecting bluesky accounts"""

    facebook: PlatformDataFacebook
    """Additional data for connecting facebook accounts"""

    instagram: PlatformDataInstagram
    """Additional data for connecting instagram accounts"""

    linkedin: PlatformDataLinkedin
    """Additional data for connecting linkedin accounts"""

    pinterest: PlatformDataPinterest
    """Additional data for connecting Pinterest accounts"""

    threads: PlatformDataThreads
    """Additional data for connecting Threads accounts"""

    tiktok: PlatformDataTiktok
    """Additional data for connecting TikTok accounts"""

    tiktok_business: PlatformDataTiktokBusiness
    """Additional data for connecting TikTok Business accounts"""

    youtube: PlatformDataYoutube
    """Additional data for connecting YouTube accounts"""
