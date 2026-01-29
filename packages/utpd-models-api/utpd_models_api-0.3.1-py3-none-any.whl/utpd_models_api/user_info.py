"""Models for the user/info API endpoint."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from .common import Meta, Notifications, UserContact


class Stats(BaseModel):
    model_config = ConfigDict(frozen=True)
    total_badges: int
    total_friends: int
    total_checkins: int
    total_beers: int
    total_created_beers: int
    total_followings: int
    total_photos: int


class Badge(BaseModel):
    model_config = ConfigDict(frozen=True)
    badges_to_facebook: int
    badges_to_twitter: int


class Checkin(BaseModel):
    model_config = ConfigDict(frozen=True)
    checkin_to_facebook: int
    checkin_to_twitter: int
    checkin_to_foursquare: int


class Navigation(BaseModel):
    model_config = ConfigDict(frozen=True)
    default_to_checkin: int


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)
    badge: Badge
    checkin: Checkin
    navigation: Navigation
    email_address: str


class Subscribe(BaseModel):
    model_config = ConfigDict(frozen=True)
    is_subscribed: int
    subscribe_type: str


class UserInfoUser(BaseModel):
    """Extended user model for user/info endpoint with additional fields."""

    model_config = ConfigDict(frozen=True)
    uid: int
    id: int
    user_name: str
    is_anonymous: int
    first_name: str
    last_name: str
    user_avatar: str
    user_avatar_hd: str
    user_cover_photo: str
    user_cover_photo_offset: int
    is_private: int
    rating_bump: int
    location: str
    url: str
    bio: str
    is_supporter: int
    is_moderator: int
    relationship: str
    block_status: str
    mute_status: str
    untappd_url: str
    account_type: str
    stats: Stats
    contact: UserContact | Any | None = None
    date_joined: str
    settings: Settings | Any | None = None
    wish_list_subscribe_status: bool | None = None
    subscribe: Subscribe | None = None


class UserInfoResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    user: UserInfoUser


class UserInfo(BaseModel):
    model_config = ConfigDict(frozen=True)
    meta: Meta
    notifications: Notifications
    response: UserInfoResponse
