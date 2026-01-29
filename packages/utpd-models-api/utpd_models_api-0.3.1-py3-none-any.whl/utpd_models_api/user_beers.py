"""Models for the user/beers API endpoint."""

from functools import total_ordering

from pydantic import BaseModel, ConfigDict, Field

from .common import Beer, Brewery, Meta, Notifications, Pagination


class Dates(BaseModel):
    model_config = ConfigDict(frozen=True)
    first_checkin_date: str
    start_date: bool | str
    end_date: bool | str
    tz_offset: str = Field(..., alias="tzOffset")


@total_ordering
class UserBeer(Beer):
    """Extended Beer model with additional fields from user/beers endpoint."""

    beer_ibu: int | None = None
    beer_description: str | None = None
    created_at: str | None = None
    rating_score: float | None = None
    rating_count: int | None = None

    def __eq__(self, other: object) -> bool:
        """Beer ID is unique, so we can use it."""
        return self.bid == other.bid if isinstance(other, UserBeer) else NotImplemented

    def __lt__(self, other: object) -> bool:
        """Beer ID is unique, so we can use it for ordering."""
        return self.bid < other.bid if isinstance(other, UserBeer) else NotImplemented

    def __hash__(self) -> int:
        """Beer ID is unique, so we can use it as a hash."""
        return hash(self.bid)


class UserBeerItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    first_checkin_id: int
    first_created_at: str
    recent_checkin_id: int
    recent_created_at: str
    recent_created_at_timezone: int
    rating_score: float
    user_auth_rating_score: float
    first_had: str
    count: int
    beer: UserBeer
    brewery: Brewery


class Beers(BaseModel):
    model_config = ConfigDict(frozen=True)
    count: int
    items: list[UserBeerItem]
    sort_english: str
    sort_name: str


class UserBeersResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    total_count: int
    dates: Dates
    is_search: bool
    sort: bool | str
    type_id: bool
    country_id: bool
    brewery_id: bool
    rating_score: bool
    region_id: bool
    container_id: bool
    is_multi_type: bool
    beers: Beers
    sort_key: str
    sort_name: str
    pagination: Pagination


class UserBeers(BaseModel):
    model_config = ConfigDict(frozen=True)
    meta: Meta
    notifications: Notifications
    response: UserBeersResponse
