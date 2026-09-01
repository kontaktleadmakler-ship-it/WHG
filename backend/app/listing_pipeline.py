"""Gemeinsame Pipeline: Angebot speichern/aktualisieren -> Matching -> Benachrichtigung.

Wird sowohl von der E-Mail-Ingestion (empfohlener Weg) als auch optional vom
Website-Scraping-Scheduler genutzt, damit Matching-Logik und Benachrichtigungs-
Regeln an genau einer Stelle gepflegt werden.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.matching import calculate_match_score
from app.notifications import notify_user_of_match
from app.scrapers.base import RawListing


def upsert_listing(db: Session, raw: RawListing) -> models.Listing:
    existing = (
        db.query(models.Listing)
        .filter(models.Listing.portal == raw.portal, models.Listing.external_id == raw.external_id)
        .first()
    )
    if existing:
        existing.last_seen_at = datetime.utcnow()
        existing.is_active = True
        existing.price_total = raw.price_total or existing.price_total
        existing.size_sqm = raw.size_sqm or existing.size_sqm
        existing.rooms = raw.rooms or existing.rooms
        db.add(existing)
        return existing

    listing = models.Listing(
        portal=raw.portal,
        external_id=raw.external_id,
        url=raw.url,
        title=raw.title,
        description=raw.description,
        price_total=raw.price_total,
        price_per_sqm=(raw.price_total / raw.size_sqm) if raw.price_total and raw.size_sqm else None,
        size_sqm=raw.size_sqm,
        rooms=raw.rooms,
        city=raw.city,
        district=raw.district,
        street=raw.street,
        zip_code=raw.zip_code,
        features=raw.features,
        image_urls=raw.image_urls,
        available_from=raw.available_from,
    )
    db.add(listing)
    db.flush()
    return listing


def match_and_notify(db: Session, listing: models.Listing, active_profiles: list[models.SearchProfile]) -> None:
    for profile in active_profiles:
        if profile.portals and listing.portal not in profile.portals:
            continue
        result = calculate_match_score(profile, listing)
        existing_match = (
            db.query(models.Match)
            .filter(models.Match.profile_id == profile.id, models.Match.listing_id == listing.id)
            .first()
        )
        if existing_match:
            existing_match.score = result.total
            existing_match.score_breakdown = result.as_json()
            match = existing_match
        else:
            match = models.Match(
                profile_id=profile.id,
                listing_id=listing.id,
                score=result.total,
                score_breakdown=result.as_json(),
            )
            db.add(match)
        db.flush()

        settings_row = (
            db.query(models.NotificationSettings)
            .filter(models.NotificationSettings.user_id == profile.user_id)
            .first()
        )
        min_score = settings_row.min_score_for_notification if settings_row else 70.0
        if not match.notified and result.total >= min_score:
            user = db.query(models.User).filter(models.User.id == profile.user_id).first()
            notify_user_of_match(db, user, match, listing, settings_row)
            match.notified = True
