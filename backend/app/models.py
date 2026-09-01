"""SQLAlchemy-Modelle: Nutzer, Suchprofile, Wohnungsangebote, Favoriten, Benachrichtigungen."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class PortalEnum(str, enum.Enum):
    immoscout24 = "immoscout24"
    immonet = "immonet"
    wg_gesucht = "wg_gesucht"
    ebay_kleinanzeigen = "ebay_kleinanzeigen"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # DSGVO: expliziter Consent-Zeitstempel für Datenverarbeitung / Benachrichtigungen
    consent_given_at = Column(DateTime, nullable=True)
    marketing_opt_in = Column(Boolean, default=False)

    profiles = relationship("SearchProfile", back_populates="owner", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    notification_settings = relationship(
        "NotificationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class SearchProfile(Base):
    """Ein Suchprofil = ein Satz von Kriterien, gegen den Angebote gematcht werden."""
    __tablename__ = "search_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, default="Mein Suchprofil")

    price_min = Column(Float, default=0)
    price_max = Column(Float, nullable=True)
    size_min_sqm = Column(Float, nullable=True)
    size_max_sqm = Column(Float, nullable=True)
    rooms_min = Column(Float, nullable=True)
    rooms_max = Column(Float, nullable=True)

    cities = Column(ARRAY(String), default=list)          # z.B. ["Berlin", "Leipzig"]
    districts = Column(ARRAY(String), default=list)        # z.B. ["Kreuzberg", "Neukölln"]
    max_commute_minutes = Column(Integer, nullable=True)

    must_have_features = Column(ARRAY(String), default=list)   # z.B. ["Balkon", "EBK", "Aufzug"]
    nice_to_have_features = Column(ARRAY(String), default=list)

    portals = Column(ARRAY(String), default=list)  # welche Portale durchsucht werden sollen
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="profiles")
    matches = relationship("Match", back_populates="profile", cascade="all, delete-orphan")


class Listing(Base):
    """Ein gescraptes Wohnungsangebot (normalisiert über alle Portale)."""
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("portal", "external_id", name="uq_portal_external_id"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    portal = Column(Enum(PortalEnum), nullable=False)
    external_id = Column(String, nullable=False)  # ID/URL-Slug auf dem Quellportal
    url = Column(String, nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    price_total = Column(Float, nullable=True)
    price_per_sqm = Column(Float, nullable=True)
    size_sqm = Column(Float, nullable=True)
    rooms = Column(Float, nullable=True)

    city = Column(String, nullable=True, index=True)
    district = Column(String, nullable=True, index=True)
    street = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    features = Column(ARRAY(String), default=list)
    image_urls = Column(ARRAY(String), default=list)

    available_from = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)  # false, wenn Angebot offline/vermietet
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("Match", back_populates="listing", cascade="all, delete-orphan")


class Match(Base):
    """Score-basiertes Matching zwischen Suchprofil und Angebot."""
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("profile_id", "listing_id", name="uq_profile_listing"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("search_profiles.id"), nullable=False)
    listing_id = Column(UUID(as_uuid=False), ForeignKey("listings.id"), nullable=False)

    score = Column(Float, nullable=False)          # 0-100
    score_breakdown = Column(Text, nullable=True)   # JSON-String mit Teilscores
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("SearchProfile", back_populates="matches")
    listing = relationship("Listing", back_populates="matches")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "listing_id", name="uq_user_listing_fav"),)

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    listing_id = Column(UUID(as_uuid=False), ForeignKey("listings.id"), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    listing = relationship("Listing")


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), unique=True, nullable=False)

    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)
    min_score_for_notification = Column(Float, default=70.0)
    max_notifications_per_day = Column(Integer, default=10)
    push_subscription_json = Column(Text, nullable=True)  # Web-Push-Subscription-Objekt

    user = relationship("User", back_populates="notification_settings")


class PriceHistory(Base):
    """Für Statistiken: Preisentwicklung pro Stadt/Bezirk über Zeit."""
    __tablename__ = "price_history"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    city = Column(String, index=True, nullable=False)
    district = Column(String, index=True, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    avg_price_per_sqm = Column(Float, nullable=False)
    listing_count = Column(Integer, nullable=False)
