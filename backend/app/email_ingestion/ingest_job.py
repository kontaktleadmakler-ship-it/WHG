"""Hintergrund-Job (empfohlener Standardweg): liest Alert-Mails der Portale
aus dem Agentur-Postfach, extrahiert Angebote und stößt Matching +
Benachrichtigungen an.

Start (Docker-Service "email-ingestion-worker"):
    python -m app.email_ingestion.ingest_job

Voraussetzung: Für jedes Kundenprofil wurde auf den gewünschten Portalen ganz
regulär über die Portal-Oberfläche ein Suchauftrag/E-Mail-Alarm eingerichtet,
der an die in .env konfigurierte IMAP-Adresse sendet (siehe README).
"""
from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import settings
from app.database import SessionLocal
from app import models
from app.email_ingestion.imap_client import fetch_unread_messages
from app.email_ingestion.parsers import parse_message
from app.listing_pipeline import upsert_listing, match_and_notify


def run_ingest_cycle():
    messages = fetch_unread_messages()
    if not messages:
        print("Keine neuen Alert-Mails.")
        return

    db = SessionLocal()
    try:
        active_profiles = (
            db.query(models.SearchProfile).filter(models.SearchProfile.is_active.is_(True)).all()
        )
        processed = 0
        for msg in messages:
            raw_listings = parse_message(msg)
            for raw in raw_listings:
                listing = upsert_listing(db, raw)
                db.flush()
                match_and_notify(db, listing, active_profiles)
                processed += 1
        db.commit()
        print(f"E-Mail-Ingestion abgeschlossen: {processed} Angebote aus {len(messages)} Mails verarbeitet.")
    finally:
        db.close()


def main():
    run_ingest_cycle()
    scheduler = BlockingScheduler(timezone="Europe/Berlin")
    scheduler.add_job(run_ingest_cycle, "interval", minutes=settings.imap_poll_interval_minutes)
    print(f"E-Mail-Ingestion gestartet, Intervall = {settings.imap_poll_interval_minutes} Minuten.")
    scheduler.start()


if __name__ == "__main__":
    main()
