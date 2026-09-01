"""Scraper für WG-Gesucht (www.wg-gesucht.de).

Hinweis: WG-Gesucht untersagt automatisiertes Auslesen in seinen AGB.
Für Alternativen prüfe, ob eine offizielle Schnittstelle angeboten wird,
bevor dieses Modul produktiv eingesetzt wird.
"""
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing

CITY_IDS = {
    "berlin": 8,
    "hamburg": 55,
    "muenchen": 90,
    "köln": 73,
    "koeln": 73,
}


class WGGesuchtScraper(BaseScraper):
    portal_name = "wg_gesucht"
    base_url = "https://www.wg-gesucht.de"

    def search(self, city: str, price_max: Optional[float] = None) -> List[RawListing]:
        city_id = CITY_IDS.get(city.lower())
        if city_id is None:
            print(f"[wg_gesucht] Unbekannte Stadt-ID für '{city}', überspringe.")
            return []

        search_url = f"{self.base_url}/wohnungen-in-{city.title()}.{city_id}.0.1.0.html"
        resp = self._throttled_get(search_url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[RawListing] = []

        for row in soup.select("table#table-list-container tr.listenansicht0, tr.listenansicht1"):
            try:
                listing = self._parse_row(row, city)
                if listing:
                    results.append(listing)
            except Exception as exc:
                print(f"[wg_gesucht] Parsefehler bei einer Zeile: {exc}")
        return results

    def _parse_row(self, row, city: str) -> Optional[RawListing]:
        link_el = row.select_one("a[href*='.html']")
        if not link_el:
            return None
        href = link_el["href"]
        url = href if href.startswith("http") else f"{self.base_url}/{href.lstrip('/')}"
        external_id_match = re.search(r"\.(\d+)\.html", url)
        external_id = external_id_match.group(1) if external_id_match else url

        title = link_el.get_text(strip=True) or "WG-Zimmer / Wohnung"

        price_el = row.select_one("td.column-price, .col-rent")
        price_total = self._parse_number(price_el.get_text() if price_el else None)

        size_el = row.select_one("td.column-size, .col-size")
        size_sqm = self._parse_number(size_el.get_text() if size_el else None)

        district_el = row.select_one("td.column-district, .col-district")
        district = district_el.get_text(strip=True) if district_el else None

        return RawListing(
            portal=self.portal_name,
            external_id=external_id,
            url=url,
            title=title,
            price_total=price_total,
            size_sqm=size_sqm,
            city=city.title(),
            district=district,
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
