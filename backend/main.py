"""
Wohnungssuche-App – FastAPI-Backend.

Start (Entwicklung):
    uvicorn main:app --reload --port 8000

API-Doku danach unter http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

import config
from database import get_db, init_db, SessionLocal
from models import Profile, Match, Source
from schemas import (
    ProfileCreate, ProfileUpdate, ProfileOut, MatchOut, ScanResult,
    SourceCreate, SourceUpdate, SourceOut,
)
from scan_engine import scan_all_sources
from scrapers import BUILTIN_SOURCE_META

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _scheduled_scan_job():
    db = SessionLocal()
    try:
        result = scan_all_sources(db)
        logger.info("Automatischer Scan abgeschlossen: %s", result)
    finally:
        db.close()


def _seed_builtin_sources():
    """Legt die eingebauten Portale einmalig in der Source-Tabelle an,
    falls noch nicht vorhanden, damit sie im Dashboard erscheinen."""
    db = SessionLocal()
    try:
        for key, meta in BUILTIN_SOURCE_META.items():
            existing = db.query(Source).filter(Source.key == key).first()
            if existing:
                continue
            db.add(Source(
                key=key,
                name=meta["name"],
                type="builtin",
                enabled=meta["enabled_default"],
            ))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _seed_builtin_sources()
    scheduler.add_job(
        _scheduled_scan_job,
        "interval",
        minutes=config.SCAN_INTERVAL_MINUTES,
        id="periodic_scan",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler gestartet: Scan alle %s Minuten. Aktive Portale im Dashboard prüfen.",
        config.SCAN_INTERVAL_MINUTES,
    )
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Wohnungssuche API",
    description="Profilverwaltung, Matching und Benachrichtigungen für die Wohnungssuche.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # für mobile Clients / lokale Entwicklung offen; in Produktion einschränken
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Profile (CRUD) ----------

@app.post("/profiles", response_model=ProfileOut)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    profile = Profile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/profiles", response_model=list[ProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return db.query(Profile).order_by(Profile.created_at.desc()).all()


@app.get("/profiles/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil nicht gefunden")
    return profile


@app.patch("/profiles/{profile_id}", response_model=ProfileOut)
def update_profile(profile_id: int, payload: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil nicht gefunden")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil nicht gefunden")
    db.delete(profile)
    db.commit()
    return None


# ---------- Treffer ----------

@app.get("/profiles/{profile_id}/matches", response_model=list[MatchOut])
def get_matches(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil nicht gefunden")
    return (
        db.query(Match)
        .filter(Match.profile_id == profile_id)
        .order_by(Match.score.desc())
        .all()
    )


# ---------- Portale (Sources) ----------

@app.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.type.desc(), Source.name).all()


@app.post("/sources", response_model=SourceOut)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    if db.query(Source).filter(Source.key == payload.key).first():
        raise HTTPException(status_code=409, detail="Ein Portal mit diesem Key existiert bereits")
    source = Source(type="custom", **payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.patch("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Portal nicht gefunden")
    updates = payload.model_dump(exclude_unset=True)
    if source.type == "builtin":
        # Eingebaute Portale: nur an/aus schaltbar, keine Selektoren editierbar
        updates = {k: v for k, v in updates.items() if k == "enabled"}
    for key, value in updates.items():
        setattr(source, key, value)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.delete("/sources/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Portal nicht gefunden")
    if source.type == "builtin":
        raise HTTPException(status_code=400, detail="Eingebaute Portale können nur deaktiviert, nicht gelöscht werden")
    db.delete(source)
    db.commit()
    return None


# ---------- Scan manuell auslösen ----------

@app.post("/scan", response_model=ScanResult)
def trigger_scan(db: Session = Depends(get_db)):
    return scan_all_sources(db)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    enabled = [s.key for s in db.query(Source).filter(Source.enabled == True).all()]  # noqa: E712
    return {
        "status": "ok",
        "enabled_sources": enabled,
        "scan_interval_minutes": config.SCAN_INTERVAL_MINUTES,
    }


# ---------- Frontend ausliefern ----------

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
