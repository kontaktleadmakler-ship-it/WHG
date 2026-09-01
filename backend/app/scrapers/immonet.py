"""Scraper für Immonet (www.immonet.de).

Hinweis: Immonet gehört zum selben Konzern wie ImmoScout24; die Nutzungs-
bedingungen untersagen ebenfalls automatisiertes Auslesen. Bitte AGB und
robots.txt vor produktivem Einsatz prüfen.
"""
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing


class ImmonetScraper(BaseScraper):
    portal_name = "immonet"
    base_url = "https://www.immonet.de"

    def search(self, city: str, price_max: Optional[float] = None) -> List[RawListing]:
        search_url = f"{self.base_url}/immobiliensuche/mietwohnungen/{city.lower()}"
        resp = self._throttled_get(search_url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[RawListing] = []

        for card in soup.select("div.result-list-entry, article.list-item"):
            try:
                results.append(self._parse_card(card))
            except Exception as exc:
                print(f"[immonet] Parsefehler bei einer Karte: {exc}")
        return results

    def _parse_card(self, card) -> RawListing:
        link_el = card.select_one("a[href*='/angebot/']")
        href = link_el["href"] if link_el else ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"
        external_id_match = re.search(r"/angebot/([\w-]+)", url)
        external_id = external_id_match.group(1) if external_id_match else url

        title_el = card.select_one("h2, .item-title")
        title = title_el.get_text(strip=True) if title_el else "Wohnung"

        price_el = card.select_one(".price, .item-price")
        price_total = self._parse_number(price_el.get_text() if price_el else None)

        size_el = card.select_one(".area, .item-area")
        size_sqm = self._parse_number(size_el.get_text() if size_el else None)

        rooms_el = card.select_one(".rooms, .item-rooms")
        rooms = self._parse_number(rooms_el.get_text() if rooms_el else None)

        location_el = card.select_one(".location, .item-region")
        location_text = location_el.get_text(strip=True) if location_el else ""

        return RawListing(
            portal=self.portal_name,
            external_id=external_id,
            url=url,
            title=title,
            price_total=price_total,
            size_sqm=size_sqm,
            rooms=rooms,
            city=location_text.split(",")[-1].strip() if location_text else None,
            district=location_text.split(",")[0].strip() if "," in location_text else None,
        )

    @staticmethod
    def _parse_number(text: Optional[str]) -> Optional[float]:
        if not text:
            return None
        cleaned = re.sub(r"[^\d,\.]", "", text).replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
