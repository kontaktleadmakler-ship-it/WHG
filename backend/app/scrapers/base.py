"""Basisklasse für alle Portal-Scraper.

WICHTIGER HINWEIS ZUR RECHTSLAGE:
Immoscout24, Immonet und WG-Gesucht untersagen automatisiertes Auslesen
(Scraping) in ihren Allgemeinen Geschäftsbedingungen; einzelne Anbieter sind
in der Vergangenheit rechtlich gegen Scraper vorgegangen. eBay Kleinanzeigen
untersagt automatisierte Zugriffe ebenfalls in seinen Nutzungsbedingungen.
Wer dieses Modul einsetzt, ist selbst dafür verantwortlich, die aktuellen
Nutzungsbedingungen der jeweiligen Portale sowie robots.txt zu prüfen und
einzuhalten, offizielle APIs zu bevorzugen (Immoscout24 bietet z.B. ein
Partner-API-Programm) und Zugriffe verantwortungsvoll zu drosseln.
Diese Implementierung enthält daher standardmäßig eine robots.txt-Prüfung,
konservative Rate-Limits und respektiert HTTP-Fehlercodes (z.B. 429).

CSS-Selektoren auf Zielseiten ändern sich regelmäßig - die Parser-Methoden
müssen bei Layout-Änderungen der Portale angepasst werden.
"""
import time
import urllib.robotparser
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import requests

from app.config import settings

USER_AGENT = "ImmoFinderBot/1.0 (+privates Recherche-Tool; Kontakt: admin@example.com)"


@dataclass
class RawListing:
    portal: str
    external_id: str
    url: str
    title: str
    description: Optional[str] = None
    price_total: Optional[float] = None
    size_sqm: Optional[float] = None
    rooms: Optional[float] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    zip_code: Optional[str] = None
    features: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)
    available_from: Optional[datetime] = None


class BaseScraper(ABC):
    portal_name: str = "base"
    base_url: str = ""

    def __init__(self):
        self._robots_cache = {}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    # ---------- Verantwortungsvolles Crawling ----------
    def _allowed_by_robots(self, url: str) -> bool:
        if not settings.respect_robots_txt:
            return True
        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        if root not in self._robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{root}/robots.txt")
            try:
                rp.read()
            except Exception:
                # robots.txt nicht lesbar -> konservativ: nicht crawlen
                self._robots_cache[root] = None
                return False
            self._robots_cache[root] = rp
        rp = self._robots_cache[root]
        if rp is None:
            return False
        return rp.can_fetch(USER_AGENT, url)

    def _throttled_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        if not self._allowed_by_robots(url):
            print(f"[{self.portal_name}] robots.txt verbietet Zugriff auf {url} - übersprungen.")
            return None
        time.sleep(settings.scrape_min_delay_seconds)
        try:
            resp = self.session.get(url, timeout=15, **kwargs)
        except requests.RequestException as exc:
            print(f"[{self.portal_name}] Request-Fehler für {url}: {exc}")
            return None
        if resp.status_code == 429:
            print(f"[{self.portal_name}] Rate-Limit (429) erhalten, überspringe.")
            return None
        if resp.status_code >= 400:
            print(f"[{self.portal_name}] HTTP {resp.status_code} für {url}")
            return None
        return resp

    # ---------- von Subklassen zu implementieren ----------
    @abstractmethod
    def search(self, city: str, price_max: Optional[float] = None) -> List[RawListing]:
        """Sucht Angebote für eine Stadt und liefert eine Liste RawListing zurück."""
        raise NotImplementedError
