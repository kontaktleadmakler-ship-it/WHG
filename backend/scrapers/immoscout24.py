"""
Best-effort-Scraper für ImmobilienScout24.

ACHTUNG: ImmoScout24 untersagt automatisiertes Auslesen in den AGB und
setzt aktiv technische Anti-Scraping-Maßnahmen ein (u.a. Bot-Erkennung,
teils JavaScript-Rendering nötig). Ein einfacher requests+BeautifulSoup-
Ansatz wie hier funktioniert oft nur eingeschränkt oder gar nicht.
Für Dauerbetrieb bitte prüfen, ob die offizielle ImmoScout24-API
(Partner-/Makler-Zugang) für den eigenen Anwendungsfall infrage kommt.
Dieses Modul ist bewusst als austauschbares Gerüst gehalten.
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


class ImmoScout24Scraper(BaseScraper):
    source_name = "immoscout24"
    BASE_URL = "https://www.immobilienscout24.de"

    def __init__(self, request_delay_seconds: float = 3.0):
        self.request_delay_seconds = request_delay_seconds

    def search(self, city: str, budget_max: float, zimmer_min: float | None = None) -> list[dict]:
        search_url = (
            f"{self.BASE_URL}/Suche/de/wohnung-mieten"
            f"?price=-{int(budget_max)}&numberofrooms={zimmer_min or ''}&query={city}"
        )
        results: list[dict] = []
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("ImmoScout24 Anfrage fehlgeschlagen (%s): %s", search_url, exc)
            return results

        soup = BeautifulSoup(resp.text, "lxml")
        # Platzhalter-Selektor, MUSS gegen die Live-Seite verifiziert werden.
        cards = soup.select("article[data-item='result'], div.result-list-entry")

        for card in cards:
            try:
                link_tag = card.select_one("a[href*='/expose/']")
                if not link_tag:
                    continue
                href = link_tag.get("href", "")
                url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                external_id = href.rstrip("/").split("/")[-1]

                title = link_tag.get_text(strip=True) or "Unbekanntes Angebot"

                price_tag = card.select_one("[data-is='result-list-entry-price']")
                price = self._parse_number(price_tag.get_text(strip=True)) if price_tag else None

                qm_tag = card.select_one("[data-is='result-list-entry-area']")
                qm = self._parse_number(qm_tag.get_text(strip=True)) if qm_tag else None

                zimmer_tag = card.select_one("[data-is='result-list-entry-rooms']")
                zimmer = self._parse_number(zimmer_tag.get_text(strip=True)) if zimmer_tag else None

                results.append({
                    "external_id": external_id or url,
                    "url": url,
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
                logger.debug("Konnte Karte nicht parsen: %s", exc)
                continue

        time.sleep(self.request_delay_seconds)
        return results

    @staticmethod
    def _parse_number(text: str) -> float | None:
        digits = "".join(ch for ch in text if ch.isdigit() or ch == ",")
        digits = digits.replace(",", ".")
        try:
            return float(digits)
        except ValueError:
            return None
