from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class ProfileBase(BaseModel):
    name: str
    email: EmailStr
    budget_min: float = 0
    budget_max: float
    city: str
    district: Optional[str] = None
    qm_min: float = 0
    qm_max: Optional[float] = None
    zimmer_min: float = 1
    zimmer_max: Optional[float] = None
    stockwerk_min: Optional[int] = None
    stockwerk_max: Optional[int] = None
    balkon_required: bool = False
    einbaukueche_required: bool = False
    haustiere_erlaubt_required: bool = False
    barrierefrei_required: bool = False
    einzug_ab: Optional[datetime] = None
    active: bool = True


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    """Alle Felder optional, für Teil-Updates via PATCH."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    city: Optional[str] = None
    district: Optional[str] = None
    qm_min: Optional[float] = None
    qm_max: Optional[float] = None
    zimmer_min: Optional[float] = None
    zimmer_max: Optional[float] = None
    stockwerk_min: Optional[int] = None
    stockwerk_max: Optional[int] = None
    balkon_required: Optional[bool] = None
    einbaukueche_required: Optional[bool] = None
    haustiere_erlaubt_required: Optional[bool] = None
    barrierefrei_required: Optional[bool] = None
    einzug_ab: Optional[datetime] = None
    active: Optional[bool] = None


class ProfileOut(ProfileBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    url: str
    title: str
    city: Optional[str] = None
    district: Optional[str] = None
    price: Optional[float] = None
    qm: Optional[float] = None
    zimmer: Optional[float] = None
    stockwerk: Optional[int] = None
    balkon: Optional[bool] = None
    einbaukueche: Optional[bool] = None
    haustiere_erlaubt: Optional[bool] = None
    barrierefrei: Optional[bool] = None
    verfuegbar_ab: Optional[datetime] = None
    first_seen: datetime


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    score: float
    notified: bool
    created_at: datetime
    listing: ListingOut


class SourceCreate(BaseModel):
    """Ein vom Nutzer im Dashboard hinzugefügtes, generisches Portal."""
    key: str
    name: str
    search_url_template: str  # Platzhalter: {city}, {budget_max}, {zimmer_min}
    selector_card: str
    selector_link: str
    selector_title: Optional[str] = None
    selector_price: Optional[str] = None
    selector_qm: Optional[str] = None
    selector_zimmer: Optional[str] = None
    request_delay_seconds: float = 3.0
    enabled: bool = True


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    search_url_template: Optional[str] = None
    selector_card: Optional[str] = None
    selector_link: Optional[str] = None
    selector_title: Optional[str] = None
    selector_price: Optional[str] = None
    selector_qm: Optional[str] = None
    selector_zimmer: Optional[str] = None
    request_delay_seconds: Optional[float] = None


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    name: str
    type: str
    enabled: bool
    request_delay_seconds: float
    search_url_template: Optional[str] = None
    selector_card: Optional[str] = None
    selector_link: Optional[str] = None
    selector_title: Optional[str] = None
    selector_price: Optional[str] = None
    selector_qm: Optional[str] = None
    selector_zimmer: Optional[str] = None
    created_at: datetime


class ScanResult(BaseModel):
    profiles_scanned: int
    listings_found: int
    new_matches: int
