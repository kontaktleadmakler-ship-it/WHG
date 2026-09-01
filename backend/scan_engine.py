"""
Verbindet Scraper, Datenbank, Matching und Benachrichtigung.
"""
import logging
from sqlalchemy.orm import Session

from models import Profile, Listing, Match, Source
from scrapers import AVAILABLE_SCRAPERS, GenericScraper
from matching import calculate_match_score, MATCH_THRESHOLD
from notifications import notify_match

logger = logging.getLogger(__name__)


def _build_scraper(source: Source):
    """Erzeugt die passende Scraper-Instanz für eine aktivierte Source."""
    if source.type == "builtin":
        scraper_cls = AVAILABLE_SCRAPERS.get(source.key)
        if not scraper_cls:
            logger.warning("Unbekannte eingebaute Quelle: %s", source.key)
            return None
        return scraper_cls()
    if source.type == "custom":
        return GenericScraper(source)
    logger.warning("Unbekannter Quellentyp: %s (%s)", source.type, source.key)
    return None


def _upsert_listing(db: Session, source: str, data: dict) -> Listing:
    existing = (
        db.query(Listing)
        .filter(Listing.source == source, Listing.external_id == data["external_id"])
        .first()
    )
    if existing:
        for key, value in data.items():
            if key != "external_id":
                setattr(existing, key, value)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    listing = Listing(source=source, **data)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def scan_all_sources(db: Session) -> dict:
    """Durchsucht alle aktivierten Portale für alle aktiven Profile,
    speichert neue Angebote, führt Matching aus und benachrichtigt.
    Gibt eine Zusammenfassung zurück."""
    profiles = db.query(Profile).filter(Profile.active == True).all()  # noqa: E712
    if not profiles:
        return {"profiles_scanned": 0, "listings_found": 0, "new_matches": 0}

    cities = {p.city for p in profiles}
    listings_found = 0
    new_matches = 0

    enabled_sources = db.query(Source).filter(Source.enabled == True).all()  # noqa: E712
    if not enabled_sources:
        logger.warning("Keine Quelle im Dashboard aktiviert – Scan übersprungen.")
        return {"profiles_scanned": len(profiles), "listings_found": 0, "new_matches": 0}

    for source in enabled_sources:
        scraper = _build_scraper(source)
        if not scraper:
            continue

        for city in cities:
            city_profiles = [p for p in profiles if p.city == city]
            budget_max = max(p.budget_max for p in city_profiles)
            zimmer_min = min(
                (p.zimmer_min for p in city_profiles if p.zimmer_min), default=None
            )
            try:
                raw_results = scraper.search(city=city, budget_max=budget_max, zimmer_min=zimmer_min)
            except Exception as exc:
                logger.error("Scraper %s für %s fehlgeschlagen: %s", source.key, city, exc)
                continue

            listings_found += len(raw_results)
            for raw in raw_results:
                listing = _upsert_listing(db, scraper.source_name, raw)

                for profile in city_profiles:
                    score = calculate_match_score(profile, listing)
                    if score < MATCH_THRESHOLD:
                        continue

                    match = (
                        db.query(Match)
                        .filter(Match.profile_id == profile.id, Match.listing_id == listing.id)
                        .first()
                    )
                    if match:
                        continue  # bereits bekannt, keine doppelte Benachrichtigung

                    match = Match(profile_id=profile.id, listing_id=listing.id, score=score)
                    db.add(match)
                    db.commit()
                    db.refresh(match)

                    sent = notify_match(profile, listing, score)
                    match.notified = sent
                    db.add(match)
                    db.commit()

                    new_matches += 1

    return {
        "profiles_scanned": len(profiles),
        "listings_found": listings_found,
        "new_matches": new_matches,
    }
