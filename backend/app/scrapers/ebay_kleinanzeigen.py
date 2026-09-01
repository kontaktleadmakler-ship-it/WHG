"""Scraper für eBay Kleinanzeigen (www.kleinanzeigen.de).

Hinweis: eBay Kleinanzeigen untersagt automatisierte Zugriffe in seinen
Nutzungsbedingungen. Für den produktiven Einsatz bitte AGB und robots.txt
prüfen; ggf. bietet die Plattform Alternativen (z.B. RSS-Feeds für
bestimmte Suchen) an, die vorzuziehen sind.
"""
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, RawListing


class EbayKleinanzeigenScraper(BaseScraper):
    portal_name = "ebay_kleinanzeigen"
    base_url = "https://www.kleinanzeigen.de"

    def search(self, city: str, price_max: Optional[float] = None) -> List[RawListing]:
        price_filter = f"anzeige:angebote/preis::{int(price_max)}/" if price_max else ""
        search_url = f"{self.base_url}/s-wohnung-mieten/{city.lower()}/{price_filter}c203"

        resp = self._throttled_get(search_url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results: List[RawListing] = []

        for card in soup.select("article.aditem"):
            try:
                results.append(self._parse_card(card, city))
            except Exception as exc:
                print(f"[ebay_kleinanzeigen] Parsefehler bei einer Karte: {exc}")
        return results

    def _parse_card(self, card, city: str) -> RawListing:
        external_id = card.get("data-adid", "")
        link_el = card.select_one("a.ellipsis")
        href = link_el["href"] if link_el else ""
        url = href if href.startswith("http") else f"{self.base_url}{href}"

        title = link_el.get_text(strip=True) if link_el else "Wohnungsanzeige"

        price_el = card.select_one(".aditem-main--middle--price-shipping--price")
        price_total = self._parse_number(price_el.get_text() if price_el else None)

        desc_el = card.select_one(".aditem-main--middle--description")
        description = desc_el.get_text(strip=True) if desc_el else None

        size_sqm, rooms = None, None
        tags_el = card.select_one(".aditem-main--middle--priceshipping, .aditem-main--top--right")
        if tags_el:
            text = tags_el.get_text(" ", strip=True)
            size_match = re.search(r"(\d+)\s?m²", text)
            rooms_match = re.search(r"(\d+([.,]\d+)?)\s?Zimmer", text)
            if size_match:
                size_sqm = float(size_match.group(1))
            if rooms_match:
                rooms = float(rooms_match.group(1).replace(",", "."))

        location_el = card.select_one(".aditem-main--top--left")
        location_text = location_el.get_text(strip=True) if location_el else city

        return RawListing(
            portal=self.portal_name,
            external_id=external_id or url,
            url=url,
            title=title,
            description=description,
            price_total=price_total,
            size_sqm=size_sqm,
            rooms=rooms,
            city=city.title(),
            district=location_text,
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
