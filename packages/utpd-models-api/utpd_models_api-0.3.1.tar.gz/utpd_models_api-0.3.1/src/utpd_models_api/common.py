"""Common Pydantic models shared across Untappd API responses.

These models are extracted from multiple endpoint responses to avoid duplication
and provide a single place to fix edge cases when the API returns unexpected data.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict

# === API Envelope Models ===


class ResponseTime(BaseModel):
    model_config = ConfigDict(frozen=True)
    time: float
    measure: str


class InitTime(BaseModel):
    model_config = ConfigDict(frozen=True)
    time: int
    measure: str


class Meta(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: int
    response_time: ResponseTime
    init_time: InitTime


class UnreadCount(BaseModel):
    model_config = ConfigDict(frozen=True)
    comments: int
    toasts: int
    friends: int
    messages: int
    venues: int
    veunes: int  # API typo, kept for compatibility
    others: int
    news: int


class Notifications(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: str
    unread_count: UnreadCount


class Pagination(BaseModel):
    """Pagination info - fields vary by endpoint."""

    model_config = ConfigDict(frozen=True)
    next_url: str
    since_url: str | None = None
    max_id: int | bool | str | None = None
    offset: int | None = None


# === User Models ===


class UserContact(BaseModel):
    """User's linked social accounts."""

    model_config = ConfigDict(frozen=True)
    foursquare: str | None = None


class BreweryDetails(BaseModel):
    model_config = ConfigDict(frozen=True)
    brewery_id: int


class VenueDetails(BaseModel):
    model_config = ConfigDict(frozen=True)
    venue_id: int


class UserBase(BaseModel):
    """Base user model with common fields across endpoints."""

    model_config = ConfigDict(frozen=True)
    uid: int
    user_name: str
    first_name: str
    last_name: str
    location: str
    bio: str
    user_avatar: str
    relationship: str | None = None
    is_supporter: int | None = None
    is_private: int | None = None
    url: str | None = None
    public_toasts: int | None = None
    contact: UserContact | list[Any] | None = None
    account_type: str | None = None
    venue_details: list[Any] | VenueDetails | None = None
    brewery_details: list[Any] | BreweryDetails | None = None
    user_link: str | None = None


# === Beer Models ===


class Beer(BaseModel):
    """Beer info - fields vary slightly by endpoint."""

    model_config = ConfigDict(frozen=True)
    bid: int
    beer_name: str
    beer_label: str
    beer_style: str
    beer_abv: float
    beer_active: int | None = None
    has_had: bool | None = None
    beer_label_hd: str | None = None
    beer_slug: str | None = None
    beer_ibu: int | None = None
    beer_description: str | None = None
    created_at: str | None = None
    rating_score: float | None = None
    rating_count: int | None = None


# === Brewery Models ===


class BreweryContact(BaseModel):
    """Brewery contact info."""

    model_config = ConfigDict(frozen=True)
    twitter: str | None = None
    facebook: str | None = None
    instagram: str | None = None
    url: str | None = None


class BreweryLocation(BaseModel):
    model_config = ConfigDict(frozen=True)
    brewery_city: str
    brewery_state: str
    lat: float
    lng: float


class Brewery(BaseModel):
    model_config = ConfigDict(frozen=True)
    brewery_id: int
    brewery_name: str
    brewery_slug: str | None = None
    brewery_page_url: str
    brewery_type: str | Any | None = None
    brewery_label: str
    country_name: str
    contact: BreweryContact | list[Any] | None = None
    location: BreweryLocation
    brewery_active: int


# === Venue Models ===


class VenueCategoryItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    category_key: str
    category_name_en: str
    category_name: str
    category_id: str
    is_primary: bool


class VenueCategories(BaseModel):
    model_config = ConfigDict(frozen=True)
    count: int
    items: list[VenueCategoryItem]


class VenueLocation(BaseModel):
    model_config = ConfigDict(frozen=True)
    venue_address: str
    venue_city: str
    venue_state: str
    venue_country: str
    lat: float
    lng: float


class VenueContact(BaseModel):
    model_config = ConfigDict(frozen=True)
    twitter: str | None = None
    venue_url: str | None = None


class Foursquare(BaseModel):
    model_config = ConfigDict(frozen=True)
    foursquare_id: str
    foursquare_url: str


class VenueIcon(BaseModel):
    model_config = ConfigDict(frozen=True)
    sm: str
    md: str
    lg: str


class Venue(BaseModel):
    model_config = ConfigDict(frozen=True)
    venue_id: int
    venue_name: str
    venue_slug: str
    primary_category_en: str | None = None
    primary_category: str | None = None
    parent_category_id: str | None = None
    categories: VenueCategories
    location: VenueLocation
    contact: VenueContact | list[Any] | None = None
    foursquare: Foursquare
    venue_icon: VenueIcon
    is_verified: bool
    spotlights: list[Any] | None = None
    has_beer: bool | None = None
    has_food: bool | None = None
    has_wine: bool | None = None
    has_spirits: bool | None = None


# === Checkin-related Models ===


class Photo(BaseModel):
    model_config = ConfigDict(frozen=True)
    photo_img_sm: str
    photo_img_md: str
    photo_img_lg: str
    photo_img_og: str


class MediaItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    photo_id: int
    photo: Photo


class Media(BaseModel):
    model_config = ConfigDict(frozen=True)
    count: int
    items: list[MediaItem]


class Source(BaseModel):
    model_config = ConfigDict(frozen=True)
    app_name: str
    app_website: str


class BadgeImage(VenueIcon):
    pass


class BadgeItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    badge_id: int
    user_badge_id: int
    badge_name: str
    badge_description: str
    created_at: str
    badge_image: BadgeImage


class Badges(BaseModel):
    model_config = ConfigDict(frozen=True)
    count: int
    items: list[BadgeItem]
    retro_status: bool | None = None


class CommentItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    user: UserBase
    checkin_id: int | None = None
    comment_id: int | None = None
    comment_owner: bool | None = None
    comment_editor: bool | None = None
    comment: str | None = None
    created_at: str | None = None
    comment_source: str | None = None


class Comments(BaseModel):
    model_config = ConfigDict(frozen=True)
    total_count: int
    count: int
    items: list[CommentItem | Any]


class ToastItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    uid: int
    user: UserBase
    like_id: int
    like_owner: bool
    created_at: str


class Toasts(BaseModel):
    model_config = ConfigDict(frozen=True)
    total_count: int
    count: int
    auth_toast: bool | None = None
    items: list[ToastItem]


class CheckinItem(BaseModel):
    """A single checkin entry."""

    model_config = ConfigDict(frozen=True)
    checkin_id: int
    created_at: str
    rating_score: float
    checkin_comment: str
    user: UserBase
    beer: Beer
    brewery: Brewery
    venue: Venue | list[Any] | None = None
    comments: Comments
    toasts: Toasts
    media: Media
    source: Source
    badges: Badges


class Checkins(BaseModel):
    model_config = ConfigDict(frozen=True)
    count: int
    items: list[CheckinItem]
