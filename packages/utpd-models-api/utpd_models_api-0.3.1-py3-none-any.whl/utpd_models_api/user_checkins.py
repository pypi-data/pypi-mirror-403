"""Models for the user/checkins API endpoint."""

from pydantic import BaseModel, ConfigDict

from .common import Checkins, Meta, Notifications, Pagination


class UserCheckinsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    pagination: Pagination
    checkins: Checkins


class UserCheckins(BaseModel):
    model_config = ConfigDict(frozen=True)
    meta: Meta
    notifications: Notifications
    response: UserCheckinsResponse
