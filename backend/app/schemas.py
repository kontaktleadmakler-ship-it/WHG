"""Pydantic-Schemas für Request/Response-Validierung."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth / User ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    marketing_opt_in: bool = False
    accept_privacy_policy: bool = Field(
        ..., description="Muss True sein (DSGVO-Einwilligung zur Datenverarbeitung)."
    )


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Suchprofil ----------
class SearchProfileBase(BaseModel):
    name: str = "Mein Suchprofil"
    price_min: float = 0
    price_max: Optional[float] = None
    size_min_sqm: Optional[float] = None
    size_max_sqm: Optional[float] = None
    rooms_min: Optional[float] = None
    rooms_max: Optional[float] = None
    cities: List[str] = []
    districts: List[str] = []
    max_commute_minutes: Optional[int] = None
    must_have_features: List[str] = []
    nice_to_have_features: List[str] = []
    portals: List[str] = ["immoscout24", "immonet", "wg_gesucht", "ebay_kleinanzeigen"]
    is_active: bool = True


class SearchProfileCreate(SearchProfileBase):
    pass


class SearchProfileOut(SearchProfileBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Listing ----------
class ListingOut(BaseModel):
    id: str
    portal: str
    url: str
    title: str
    description: Optional[str]
    price_total: Optional[float]
    price_per_sqm: Optional[float]
    size_sqm: Optional[float]
    rooms: Optional[float]
    city: Optional[str]
    district: Optional[str]
    street: Optional[str]
    zip_code: Optional[str]
    features: List[str]
    image_urls: List[str]
    available_from: Optional[datetime]
    is_active: bool
    first_seen_at: datetime

    class Config:
        from_attributes = True


class MatchOut(BaseModel):
    id: str
    score: float
    listing: ListingOut
    notified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Favoriten ----------
class FavoriteCreate(BaseModel):
    listing_id: str
    note: Optional[str] = None


class FavoriteOut(BaseModel):
    id: str
    listing: ListingOut
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Benachrichtigungen ----------
class NotificationSettingsUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    min_score_for_notification: Optional[float] = None
    max_notifications_per_day: Optional[int] = None
    push_subscription_json: Optional[str] = None


class NotificationSettingsOut(BaseModel):
    email_enabled: bool
    push_enabled: bool
    min_score_for_notification: float
    max_notifications_per_day: int

    class Config:
        from_attributes = True


# ---------- Statistiken ----------
class PriceStatPoint(BaseModel):
    date: datetime
    avg_price_per_sqm: float
    listing_count: int


class MarketStats(BaseModel):
    city: str
    district: Optional[str]
    history: List[PriceStatPoint]
    current_avg_price_per_sqm: float
    current_listing_count: int
