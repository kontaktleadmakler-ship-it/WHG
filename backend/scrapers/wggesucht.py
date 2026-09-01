"""
Best-effort-Scraper für WG-Gesucht.de.

ACHTUNG: WG-Gesucht untersagt automatisiertes Auslesen in den AGB und setzt
Rate-Limiting/Captchas ein. Dieses Modul ist ein Gerüst für Nutzer, die die
Rechtslage für ihren Fall selbst geprüft haben (z.B. rein private, geringe
Abruffrequenz) bzw. es gegen eigene/erlaubte Datenquellen austauschen wollen.
Die CSS-Selektoren MÜSSEN gegen die aktuelle Live-Seite verifiziert werden,
sie ändern sich erfahrungsgemäß regelmäßig.
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


class WGGesuchtScraper(BaseScraper):
    source_name = "wg-gesucht"
    BASE_URL = "https://www.wg-gesucht.de"

    def __init__(self, request_delay_seconds: float = 3.0):
        self.request_delay_seconds = request_delay_seconds

    def search(self, city: str, budget_max: float, zimmer_min: float | None = None) -> list[dict]:
        # WG-Gesucht verwendet Stadt-spezifische IDs in der Such-URL, die man
        # normalerweise über die eigene Auswahl auf der Seite ermitteln muss.
        # Hier als einfache Volltext-Query gehalten; bei Bedarf anpassen.
        search_url = f"{self.BASE_URL}/{city.lower()}.html"
        results: list[dict] = []
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("WG-Gesucht Anfrage fehlgeschlagen (%s): %s", search_url, exc)
            return results

        soup = BeautifulSoup(resp.text, "lxml")
        # Platzhalter-Selektor: passt zum Zeitpunkt der Erstellung ungefähr auf
        # die Listing-Karten. MUSS bei Nutzung gegen die Live-Seite geprüft werden.
        cards = soup.select("div.wgg_card, div[id^='liste-details-ad-']")

        for card in cards:
            try:
                link_tag = card.select_one("a[href*='.html']")
                if not link_tag:
                    continue
                href = link_tag.get("href", "")
                url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                external_id = href.strip("/").split("/")[-1].split(".")[0]

                title_tag = card.select_one("h3, .headline")
                title = title_tag.get_text(strip=True) if title_tag else "Unbekanntes Angebot"

                price_tag = card.select_one(".col-xs-3, .price")
                price = self._parse_price(price_tag.get_text(strip=True)) if price_tag else None

                results.append({
                    "external_id": external_id or url,
                    "url": url,
                    "title": title,
                    "city": city,
                    "district": None,
                    "price": price,
                    "qm": None,
                    "zimmer": None,
                    "stockwerk": None,
                    "balkon": None,
                    "einbaukueche": None,
                    "haustiere_erlaubt": None,
                    "barrierefrei": None,
                    "verfuegbar_ab": None,
                    "raw_text": card.get_text(" ", strip=True)[:500],
                })
            except Exception as exc:  # einzelne kaputte Karte soll nicht alles stoppen
                logger.debug("Konnte Karte nicht parsen: %s", exc)
                continue

        time.sleep(self.request_delay_seconds)  # fair bleiben, Server nicht überlasten
        return results

    @staticmethod
    def _parse_price(text: str) -> float | None:
        digits = "".join(ch for ch in text if ch.isdigit() or ch == ",")
        digits = digits.replace(",", ".")
        try:
            return float(digits)
        except ValueError:
            return None
