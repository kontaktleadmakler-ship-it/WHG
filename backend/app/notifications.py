"""Benachrichtigungssystem: E-Mail (SMTP) und Web-Push."""
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import settings
from app import models

try:
    from pywebpush import webpush, WebPushException
except ImportError:  # pywebpush optional, falls Push nicht konfiguriert ist
    webpush = None
    WebPushException = Exception


def _send_email(to_email: str, subject: str, body_html: str) -> bool:
    if not settings.mail_server:
        print("Mail-Server nicht konfiguriert - E-Mail wird nicht gesendet.")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            server.sendmail(settings.mail_from, [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"E-Mail-Versand fehlgeschlagen: {exc}")
        return False


def _send_push(subscription_json: str, title: str, body: str) -> bool:
    if webpush is None or not settings.vapid_private_key:
        print("Web-Push nicht konfiguriert - Push wird nicht gesendet.")
        return False
    try:
        webpush(
            subscription_info=json.loads(subscription_json),
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": "mailto:admin@example.com"},
        )
        return True
    except WebPushException as exc:
        print(f"Push-Versand fehlgeschlagen: {exc}")
        return False


def notify_user_of_match(
    db: Session,
    user: models.User,
    match: models.Match,
    listing: models.Listing,
    notification_settings: models.NotificationSettings | None,
) -> None:
    """Benachrichtigt einen Nutzer über ein neues Match, respektiert dessen Einstellungen."""
    if notification_settings is None:
        return  # kein Opt-in ohne explizite Einstellungen (DSGVO: keine Benachrichtigung ohne Einwilligung)

    subject = f"Neue Wohnung gefunden: {listing.title} ({match.score:.0f}% Match)"
    body_html = f"""
    <h2>{listing.title}</h2>
    <p>Match-Score: <strong>{match.score:.0f}%</strong></p>
    <p>Preis: {listing.price_total} € | Größe: {listing.size_sqm} m² | Zimmer: {listing.rooms}</p>
    <p>Ort: {listing.district or ''} {listing.city or ''}</p>
    <p><a href="{listing.url}">Zum Angebot auf {listing.portal}</a></p>
    <hr>
    <p style="font-size:12px;color:#888;">
      Du erhältst diese Nachricht, weil du bei ImmoFinder Benachrichtigungen für
      dieses Suchprofil aktiviert hast. Einstellungen kannst du jederzeit im
      Dashboard ändern oder Benachrichtigungen dort deaktivieren.
    </p>
    """

    if notification_settings.email_enabled:
        _send_email(user.email, subject, body_html)

    if notification_settings.push_enabled and notification_settings.push_subscription_json:
        _send_push(notification_settings.push_subscription_json, subject, f"Match-Score {match.score:.0f}%")
