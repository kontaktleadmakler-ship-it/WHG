"""OPTIONALER Zusatzweg: periodisches Website-Scraping der Portale.

Empfohlen wird stattdessen der E-Mail-Ingestion-Weg
(app/email_ingestion/ingest_job.py), der auf den offiziellen Suchauftrags-
Alerts der Portale basiert und deren Nutzungsbedingungen respektiert.

Dieses Modul ruft aktiv Portal-Webseiten automatisiert ab. ImmoScout24,
Immonet und WG-Gesucht untersagen automatisiertes Auslesen in ihren AGB,
eBay Kleinanzeigen untersagt automatisierte Zugriffe ebenfalls. Es ist NICHT
Teil der Standard-Docker-Compose-Konfiguration und muss bewusst aktiviert
werden. Prüfe vor Nutzung die aktuellen Nutzungsbedingungen der Portale.

Start (falls bewusst gewünscht):
    python -m app.scrapers.scheduler
"""
from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import settings
from app.database import SessionLocal
from app import models
from app.listing_pipeline import upsert_listing, match_and_notify
from app.scrapers.immoscout24 import ImmoScout24Scraper
from app.scrapers.immonet import ImmonetScraper
from app.scrapers.wg_gesucht import WGGesuchtScraper
from app.scrapers.ebay_kleinanzeigen import EbayKleinanzeigenScraper

SCRAPERS = {
    "immoscout24": ImmoScout24Scraper(),
    "immonet": ImmonetScraper(),
    "wg_gesucht": WGGesuchtScraper(),
    "ebay_kleinanzeigen": EbayKleinanzeigenScraper(),
}


def run_scrape_cycle():
    db = SessionLocal()
    try:
        active_profiles = db.query(models.SearchProfile).filter(models.SearchProfile.is_active.is_(True)).all()
        if not active_profiles:
            print("Keine aktiven Suchprofile - überspringe Scrape-Zyklus.")
            return

        cities = {c for p in active_profiles for c in (p.cities or [])}
        if not cities:
            print("Keine Städte in Suchprofilen hinterlegt - überspringe.")
            return

        processed_listings = []
        for portal_name, scraper in SCRAPERS.items():
            for city in cities:
                relevant_profiles = [p for p in active_profiles if portal_name in (p.portals or [])]
                if not relevant_profiles:
                    continue
                price_max = max((p.price_max or 0) for p in relevant_profiles) or None
                try:
                    raw_listings = scraper.search(city=city, price_max=price_max)
                except Exception as exc:
                    print(f"[{portal_name}] Fehler beim Scrapen von {city}: {exc}")
                    continue
                for raw in raw_listings:
                    listing = upsert_listing(db, raw)
                    db.flush()
                    processed_listings.append(listing)
        db.commit()

        for listing in processed_listings:
            match_and_notify(db, listing, active_profiles)
        db.commit()
        print(f"Scrape-Zyklus abgeschlossen: {len(processed_listings)} Angebote verarbeitet.")
    finally:
        db.close()


def main():
    run_scrape_cycle()
    scheduler = BlockingScheduler(timezone="Europe/Berlin")
    scheduler.add_job(run_scrape_cycle, "interval", minutes=settings.scrape_interval_minutes)
    print(f"Scheduler gestartet, Intervall = {settings.scrape_interval_minutes} Minuten.")
    scheduler.start()


if __name__ == "__main__":
    main()
