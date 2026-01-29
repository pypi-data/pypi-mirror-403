"""Models for the user/friends API endpoint."""

from pydantic import BaseModel, ConfigDict

from .common import Meta, Notifications, Pagination, UserBase


class MutualFriends(BaseModel):
    model_config = ConfigDict(frozen=True)
    count: int
    items: list


class FriendItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    friendship_hash: str
    created_at: str
    mutual_friends: MutualFriends
    user: UserBase


class UserFriendsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    found: int
    count: int
    items: list[FriendItem]
    pagination: Pagination


class UserFriends(BaseModel):
    model_config = ConfigDict(frozen=True)
    meta: Meta
    notifications: Notifications
    response: UserFriendsResponse
