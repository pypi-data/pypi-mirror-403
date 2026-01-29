"""Models for the checkin/recent API endpoint."""

from pydantic import BaseModel, ConfigDict

from .common import Checkins, Meta, Notifications, Pagination


class CheckinRecentResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    is_offset_checkin_id: bool
    offset: int
    limit: int
    index: str
    time: float
    checkins: Checkins
    pagination: Pagination


class CheckinRecent(BaseModel):
    model_config = ConfigDict(frozen=True)
    meta: Meta
    notifications: Notifications
    response: CheckinRecentResponse
