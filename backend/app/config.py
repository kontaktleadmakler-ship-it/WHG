"""Zentrale Konfiguration, geladen aus Umgebungsvariablen (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://immo:immo_secret@db:5432/immo_finder"
    secret_key: str = "change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_server: str = ""
    mail_port: int = 587

    vapid_public_key: str = ""
    vapid_private_key: str = ""

    scrape_interval_minutes: int = 30
    respect_robots_txt: bool = True
    scrape_min_delay_seconds: int = 3

    # E-Mail-Ingestion (bevorzugter, ToS-konformer Weg): zentrales Postfach,
    # in dem die offiziellen Suchauftrags-/Alert-Mails der Portale eingehen.
    imap_host: str = ""
    imap_port: int = 993
    imap_username: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"
    imap_poll_interval_minutes: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
