"""
Generischer Scraper für vom Nutzer über das Dashboard hinzugefügte Portale.
Statt fest programmierter Selektoren (wie bei wggesucht.py/immoscout24.py)
werden Such-URL und CSS-Selektoren aus der Datenbank (models.Source) gelesen.

Verantwortung liegt beim Nutzer: nur Portale hinzufügen, deren Nutzungs-
bedingungen automatisiertes Auslesen erlauben bzw. für die eine private,
geringfügige Nutzung geprüft wurde. Siehe Hinweis in scrapers/base.py.
"""
import time
import logging
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WohnungssucheBot/1.0; +private-use)"
}


class GenericScraper(BaseScraper):
    """Wird pro Aufruf mit einer models.Source-Konfiguration instanziiert."""

    def __init__(self, source):
        self.source_name = source.key
        self.url_template = source.search_url_template
        self.selector_card = source.selector_card
        self.selector_link = source.selector_link
        self.selector_title = source.selector_title
        self.selector_price = source.selector_price
        self.selector_qm = source.selector_qm
        self.selector_zimmer = source.selector_zimmer
        self.request_delay_seconds = source.request_delay_seconds or 3.0

    def search(self, city: str, budget_max: float, zimmer_min: float | None = None) -> list[dict]:
        if not self.url_template or not self.selector_card or not self.selector_link:
            logger.warning("Quelle %s unvollständig konfiguriert – übersprungen.", self.source_name)
            return []

        url = self.url_template.format(
            city=city, budget_max=int(budget_max), zimmer_min=zimmer_min or ""
        )
        results: list[dict] = []
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Generische Quelle %s: Anfrage an %s fehlgeschlagen: %s", self.source_name, url, exc)
            return results

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(self.selector_card)

        for card in cards:
            try:
                link_tag = card.select_one(self.selector_link)
                if not link_tag or not link_tag.get("href"):
                    continue
                href = link_tag["href"]
                url_full = href if href.startswith("http") else requests.compat.urljoin(url, href)
                external_id = href.rstrip("/").split("/")[-1] or url_full

                title = self._text(card, self.selector_title) or link_tag.get_text(strip=True) or "Unbekanntes Angebot"
                price = self._parse_number(self._text(card, self.selector_price))
                qm = self._parse_number(self._text(card, self.selector_qm))
                zimmer = self._parse_number(self._text(card, self.selector_zimmer))

                results.append({
                    "external_id": external_id,
                    "url": url_full,
                    "title": title,
                    "city": city,
                    "district": None,
                    "price": price,
                    "qm": qm,
                    "zimmer": zimmer,
                    "stockwerk": None,
                    "balkon": None,
                    "einbaukueche": None,
                    "haustiere_erlaubt": None,
                    "barrierefrei": None,
                    "verfuegbar_ab": None,
                    "raw_text": card.get_text(" ", strip=True)[:500],
                })
            except Exception as exc:
                logger.debug("Generische Quelle %s: Karte übersprungen: %s", self.source_name, exc)
                continue

        time.sleep(self.request_delay_seconds)
        return results

    @staticmethod
    def _text(card, selector: str | None) -> str:
        if not selector:
            return ""
        tag = card.select_one(selector)
        return tag.get_text(strip=True) if tag else ""

    @staticmethod
    def _parse_number(text: str) -> float | None:
        if not text:
            return None
        digits = "".join(ch for ch in text if ch.isdigit() or ch == ",")
        digits = digits.replace(",", ".")
        try:
            return float(digits)
        except ValueError:
            return None
