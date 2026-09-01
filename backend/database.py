"""
Datenbank-Setup. Standardmäßig SQLite-Datei im Projektordner.
Für Produktivbetrieb kann DATABASE_URL z.B. auf PostgreSQL zeigen.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wohnungssuche.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Modelle importieren, damit sie bei Base registriert sind, bevor Tabellen erzeugt werden
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
