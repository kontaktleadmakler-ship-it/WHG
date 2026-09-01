"""
Versand von Benachrichtigungen bei neuen Treffern.
Nutzt SMTP, falls konfiguriert; ansonsten wird nur geloggt (App-UI zeigt
Treffer ohnehin über /profiles/{id}/matches an).
"""
import logging
import smtplib
from email.mime.text import MIMEText

import config
from models import Profile, Listing

logger = logging.getLogger(__name__)


def _build_message(profile: Profile, listing: Listing, score: float) -> str:
    return (
        f"Neuer Treffer für dein Profil '{profile.name}' "
        f"(Übereinstimmung: {round(score * 100)}%)\n\n"
        f"{listing.title}\n"
        f"Ort: {listing.city}"
        + (f", {listing.district}" if listing.district else "")
        + f"\nMiete: {listing.price if listing.price is not None else 'unbekannt'} €\n"
        f"Größe: {listing.qm if listing.qm is not None else '?'} m², "
        f"{listing.zimmer if listing.zimmer is not None else '?'} Zimmer\n"
        f"Quelle: {listing.source}\n"
        f"Link: {listing.url}\n"
    )


def notify_match(profile: Profile, listing: Listing, score: float) -> bool:
    """Versucht eine Benachrichtigung zu versenden. Gibt True zurück bei Erfolg
    (inkl. reinem Log-Fallback), False nur bei einem echten Versandfehler."""
    body = _build_message(profile, listing, score)

    if not config.SMTP_HOST:
        logger.info("Kein SMTP konfiguriert – Treffer nur geloggt:\n%s", body)
        return True

    try:
        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = f"Neuer Wohnungstreffer: {listing.title}"
        msg["From"] = config.SMTP_FROM
        msg["To"] = profile.email

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            if config.SMTP_USER:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.SMTP_FROM, [profile.email], msg.as_string())
        logger.info("Benachrichtigung an %s versendet für Listing %s", profile.email, listing.id)
        return True
    except Exception as exc:
        logger.error("Benachrichtigung fehlgeschlagen für %s: %s", profile.email, exc)
        return False
