"""IMAP-Client: liest Alert-/Suchauftrags-E-Mails der Immobilienportale aus
einem zentralen Postfach der Agentur.

Konzept (ToS-konform statt Scraping):
Für jedes Kundenprofil wird auf dem jeweiligen Portal ganz regulär über die
Portal-Oberfläche ein Suchauftrag/E-Mail-Alarm eingerichtet (Funktion, die
die Portale explizit für Nutzer/Makler anbieten). Die Portale senden dann
selbst neue Angebote per E-Mail an ein von der Agentur verwaltetes Postfach.
Dieses Modul holt diese E-Mails ab und übergibt sie an die passenden Parser
in parsers.py - es wird keine Portal-Website automatisiert abgerufen.
"""
import email
import imaplib
from dataclasses import dataclass
from email.header import decode_header
from typing import List

from app.config import settings


@dataclass
class InboxMessage:
    sender: str
    subject: str
    html_body: str
    text_body: str


def _decode(value) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    return "".join(
        (p.decode(enc or "utf-8", errors="ignore") if isinstance(p, bytes) else p) for p, enc in parts
    )


def fetch_unread_messages(mark_as_seen: bool = True) -> List[InboxMessage]:
    """Holt ungelesene Alert-Mails aus dem konfigurierten IMAP-Postfach."""
    if not settings.imap_host:
        print("IMAP nicht konfiguriert - überspringe E-Mail-Abruf.")
        return []

    messages: List[InboxMessage] = []
    with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
        imap.login(settings.imap_username, settings.imap_password)
        imap.select(settings.imap_folder or "INBOX")

        status, data = imap.search(None, "UNSEEN")
        if status != "OK":
            return []

        for num in data[0].split():
            fetch_mode = "(RFC822)" if mark_as_seen else "(BODY.PEEK[])"
            status, msg_data = imap.fetch(num, fetch_mode)
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            html_body, text_body = "", ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/html":
                        html_body += part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="ignore"
                        )
                    elif content_type == "text/plain":
                        text_body += part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="ignore"
                        )
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    decoded = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
                    if msg.get_content_type() == "text/html":
                        html_body = decoded
                    else:
                        text_body = decoded

            messages.append(
                InboxMessage(
                    sender=_decode(msg.get("From")),
                    subject=_decode(msg.get("Subject")),
                    html_body=html_body,
                    text_body=text_body,
                )
            )
    return messages
