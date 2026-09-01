"""Parser für die Alert-/Suchauftrags-E-Mails der einzelnen Portale.

Diese Parser lesen ausschließlich E-Mails, die die Portale selbst über ihre
offiziellen Suchauftrags-/Benachrichtigungsfunktion verschicken. Da sich das
E-Mail-Layout je Portal und über die Zeit ändern kann, sind die Parser
bewusst tolerant (mehrere Fallback-Selektoren/Regex) gebaut. Wenn ein Portal
sein Alert-Mail-Template ändert, hier nachjustieren - dazu am besten eine
Beispiel-Mail als .html/.eml speichern und die Selektoren/Regex daran
anpassen.
"""
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from app.email_ingestion.imap_client import InboxMessage
from app.scrapers.base import RawListing  # gleiche Zielstruktur wie Website-Scraper


def _parse_number(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    cleaned = re.sub(r"[^\d,\.]", "", text).replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_by_domain(sender: str) -> Optional[str]:
    sender = sender.lower()
    if "immobilienscout24" in sender or "immoscout" in sender:
        return "immoscout24"
    if "immonet" in sender:
        return "immonet"
    if "wg-gesucht" in sender:
        return "wg_gesucht"
    if "kleinanzeigen" in sender or "ebay-kleinanzeigen" in sender:
        return "ebay_kleinanzeigen"
    return None


def parse_message(msg: InboxMessage) -> List[RawListing]:
    portal = _extract_by_domain(msg.sender)
    if portal is None:
        return []  # unbekannter Absender, z.B. eine andere Mail im Postfach - ignorieren

    if not msg.html_body:
        return []

    soup = BeautifulSoup(msg.html_body, "html.parser")
    parser_fn = {
        "immoscout24": _parse_immoscout24_mail,
        "immonet": _parse_immonet_mail,
        "wg_gesucht": _parse_wg_gesucht_mail,
        "ebay_kleinanzeigen": _parse_kleinanzeigen_mail,
    }[portal]
    return parser_fn(soup)


def _extract_listing_links(soup: BeautifulSoup, url_pattern: str) -> List[str]:
    links = set()
    for a in soup.find_all("a", href=True):
        if re.search(url_pattern, a["href"]):
            links.add(a["href"])
    return list(links)


def _parse_immoscout24_mail(soup: BeautifulSoup) -> List[RawListing]:
    results = []
    for link in _extract_listing_links(soup, r"/expose/\d+"):
        external_id_match = re.search(r"/expose/(\d+)", link)
        external_id = external_id_match.group(1) if external_id_match else link
        # der umgebende Block der jeweiligen Anzeige (Tabellenzeile/Container um den Link)
        anchor = soup.find("a", href=link)
        container = anchor.find_parent(["tr", "table", "div"]) if anchor else None
        text = container.get_text(" ", strip=True) if container else ""

        price_match = re.search(r"([\d.,]+)\s?€", text)
        size_match = re.search(r"([\d.,]+)\s?m²", text)
        rooms_match = re.search(r"([\d.,]+)\s?Zi", text)
        title = anchor.get_text(strip=True) if anchor else "Wohnung (ImmoScout24-Alert)"

        results.append(
            RawListing(
                portal="immoscout24",
                external_id=external_id,
                url=link,
                title=title,
                price_total=_parse_number(price_match.group(1) if price_match else None),
                size_sqm=_parse_number(size_match.group(1) if size_match else None),
                rooms=_parse_number(rooms_match.group(1) if rooms_match else None),
            )
        )
    return results


def _parse_immonet_mail(soup: BeautifulSoup) -> List[RawListing]:
    results = []
    for link in _extract_listing_links(soup, r"/angebot/[\w-]+"):
        external_id_match = re.search(r"/angebot/([\w-]+)", link)
        external_id = external_id_match.group(1) if external_id_match else link
        anchor = soup.find("a", href=link)
        container = anchor.find_parent(["tr", "table", "div"]) if anchor else None
        text = container.get_text(" ", strip=True) if container else ""

        price_match = re.search(r"([\d.,]+)\s?€", text)
        size_match = re.search(r"([\d.,]+)\s?m²", text)
        title = anchor.get_text(strip=True) if anchor else "Wohnung (Immonet-Alert)"

        results.append(
            RawListing(
                portal="immonet",
                external_id=external_id,
                url=link,
                title=title,
                price_total=_parse_number(price_match.group(1) if price_match else None),
                size_sqm=_parse_number(size_match.group(1) if size_match else None),
            )
        )
    return results


def _parse_wg_gesucht_mail(soup: BeautifulSoup) -> List[RawListing]:
    results = []
    for link in _extract_listing_links(soup, r"\.\d+\.html"):
        external_id_match = re.search(r"\.(\d+)\.html", link)
        external_id = external_id_match.group(1) if external_id_match else link
        anchor = soup.find("a", href=link)
        container = anchor.find_parent(["tr", "table", "div"]) if anchor else None
        text = container.get_text(" ", strip=True) if container else ""

        price_match = re.search(r"([\d.,]+)\s?€", text)
        size_match = re.search(r"([\d.,]+)\s?m²", text)
        title = anchor.get_text(strip=True) if anchor else "Wohnung/WG-Zimmer (WG-Gesucht-Alert)"

        results.append(
            RawListing(
                portal="wg_gesucht",
                external_id=external_id,
                url=link,
                title=title,
                price_total=_parse_number(price_match.group(1) if price_match else None),
                size_sqm=_parse_number(size_match.group(1) if size_match else None),
            )
        )
    return results


def _parse_kleinanzeigen_mail(soup: BeautifulSoup) -> List[RawListing]:
    results = []
    for link in _extract_listing_links(soup, r"/s-anzeige/"):
        anchor = soup.find("a", href=link)
        container = anchor.find_parent(["tr", "table", "div"]) if anchor else None
        text = container.get_text(" ", strip=True) if container else ""

        price_match = re.search(r"([\d.,]+)\s?€", text)
        size_match = re.search(r"([\d.,]+)\s?m²", text)
        rooms_match = re.search(r"([\d.,]+)\s?Zimmer", text)
        title = anchor.get_text(strip=True) if anchor else "Wohnungsanzeige (Kleinanzeigen-Alert)"

        results.append(
            RawListing(
                portal="ebay_kleinanzeigen",
                external_id=link,
                url=link,
                title=title,
                price_total=_parse_number(price_match.group(1) if price_match else None),
                size_sqm=_parse_number(size_match.group(1) if size_match else None),
                rooms=_parse_number(rooms_match.group(1) if rooms_match else None),
            )
        )
    return results
