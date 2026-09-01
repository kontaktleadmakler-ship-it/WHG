"""Scraper für ImmoScout24 (www.immobilienscout24.de).

Hinweis: ImmoScout24 untersagt automatisiertes Scraping in seinen AGB und
setzt aktive Bot-Erkennung ein. Für den produktiven Einsatz wird dringend
empfohlen, das offizielle ImmoScout24-Partner-API-Programm zu nutzen
(https://www.immobilienscout24.de/geschaeftskunden/) statt HTML zu parsen.
Der folgende Code dient als struktureller Referenzparser und muss bei
Layout-Änderungen der Zielseite angepasst werden.
"""
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing


class ImmoScout24Scraper(BaseScraper):
    portal_name = "immoscout24"
    base_url = "https://www.immobilienscout24.de"

    def search(self, city: str, price_max: Optional[float] = None) -> List[RawListing]:
        search_url = (
            f"{self.base_url}/Suche/de/{city.lower()}/wohnung-mieten"
        )
        params = {}
        if price_max:
            params["price"] = f"-{int(price_max)}"

        resp = self._throttled_get(search_url, params=params)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[RawListing] = []

        for card in soup.select("article[data-item='result']"):
            try:
                results.append(self._parse_card(card))
            except Exception as exc:
                print(f"[immoscout24] Parsefehler bei einer Karte: {exc}")
        return results

    def _parse_card(self, card) -> RawListing:
        link_el = card.select_one("a[href*='/expose/']")
        href = link_el["href"] if link_el else ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"
        external_id_match = re.search(r"/expose/(\d+)", url)
        external_id = external_id_match.group(1) if external_id_match else url

        title_el = card.select_one("h2, [data-testid='title']")
        title = title_el.get_text(strip=True) if title_el else "Wohnung"

        price_el = card.select_one("[data-testid='price'], .price")
        price_total = self._parse_number(price_el.get_text() if price_el else None)

        size_el = card.select_one("[data-testid='area'], .area")
        size_sqm = self._parse_number(size_el.get_text() if size_el else None)

        rooms_el = card.select_one("[data-testid='rooms'], .rooms")
        rooms = self._parse_number(rooms_el.get_text() if rooms_el else None)

        address_el = card.select_one("[data-testid='address'], .address")
        address_text = address_el.get_text(strip=True) if address_el else ""
        city_name, district, zip_code = self._split_address(address_text)

        return RawListing(
            portal=self.portal_name,
            external_id=external_id,
            url=url,
            title=title,
            price_total=price_total,
            size_sqm=size_sqm,
            rooms=rooms,
            city=city_name,
            district=district,
            zip_code=zip_code,
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

    @staticmethod
    def _split_address(text: str):
        # Erwartetes Format z.B. "10115 Berlin, Mitte"
        match = re.match(r"(\d{5})\s+([^,]+)(?:,\s*(.+))?", text)
        if not match:
            return None, None, None
        zip_code, city_name, district = match.groups()
        return city_name, district, zip_code
