"""
SQLAlchemy-Modelle für die Wohnungssuche-App.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from database import Base


class Profile(Base):
    """Ein Suchprofil mit den Kriterien eines Nutzers."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)  # Ziel für Benachrichtigungen

    # Kernkriterien
    budget_min = Column(Float, default=0)
    budget_max = Column(Float, nullable=False)
    city = Column(String, nullable=False)          # z.B. "Berlin"
    district = Column(String, nullable=True)        # optional, z.B. "Moabit"
    qm_min = Column(Float, default=0)
    qm_max = Column(Float, nullable=True)
    zimmer_min = Column(Float, default=1)
    zimmer_max = Column(Float, nullable=True)

    # Zusatzkriterien
    stockwerk_min = Column(Integer, nullable=True)
    stockwerk_max = Column(Integer, nullable=True)
    balkon_required = Column(Boolean, default=False)
    einbaukueche_required = Column(Boolean, default=False)
    haustiere_erlaubt_required = Column(Boolean, default=False)
    barrierefrei_required = Column(Boolean, default=False)
    einzug_ab = Column(DateTime, nullable=True)     # frühestes Einzugsdatum

    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    matches = relationship("Match", back_populates="profile")


class Listing(Base):
    """Ein gescraptes Wohnungsangebot."""
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)   # z.B. "wg-gesucht", "immoscout24"
    external_id = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)

    title = Column(String, nullable=False)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    price = Column(Float, nullable=True)       # Warmmiete/Kaltmiete je nach Quelle
    qm = Column(Float, nullable=True)
    zimmer = Column(Float, nullable=True)
    stockwerk = Column(Integer, nullable=True)
    balkon = Column(Boolean, nullable=True)
    einbaukueche = Column(Boolean, nullable=True)
    haustiere_erlaubt = Column(Boolean, nullable=True)
    barrierefrei = Column(Boolean, nullable=True)
    verfuegbar_ab = Column(DateTime, nullable=True)

    raw_text = Column(Text, nullable=True)     # unstrukturierter Beschreibungstext
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    matches = relationship("Match", back_populates="listing")


class Source(Base):
    """Ein durchsuchbares Portal: eingebaut (Code-Scraper) oder vom Nutzer
    über das Dashboard als generische CSS-Selektor-Quelle hinzugefügt."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)          # Anzeigename im Dashboard
    type = Column(String, nullable=False)           # "builtin" oder "custom"
    enabled = Column(Boolean, default=False)
    request_delay_seconds = Column(Float, default=3.0)

    # Nur für type == "custom": generischer CSS-Selektor-Scraper
    search_url_template = Column(Text, nullable=True)   # z.B. https://x.de/suche?stadt={city}&preis_bis={budget_max}
    selector_card = Column(String, nullable=True)
    selector_link = Column(String, nullable=True)
    selector_title = Column(String, nullable=True)
    selector_price = Column(String, nullable=True)
    selector_qm = Column(String, nullable=True)
    selector_zimmer = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Match(Base):
    """Verknüpfung Profil <-> Angebot mit Score, verhindert doppelte Benachrichtigungen."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    score = Column(Float, nullable=False)      # 0.0 - 1.0
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="matches")
    listing = relationship("Listing", back_populates="matches")
