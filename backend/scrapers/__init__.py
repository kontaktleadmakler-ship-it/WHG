from .mock_scraper import MockScraper
from .wggesucht import WGGesuchtScraper
from .immoscout24 import ImmoScout24Scraper
from .generic import GenericScraper

# Zentrale Registry der eingebauten (code-basierten) Scraper. "demo" ist
# standardmäßig aktiv, damit die App ohne Konfiguration sofort lauffähig ist.
AVAILABLE_SCRAPERS = {
    "demo": MockScraper,
    "wg-gesucht": WGGesuchtScraper,
    "immoscout24": ImmoScout24Scraper,
}

# Anzeigenamen + Standard-Aktivierung für die Erstbefüllung der Source-Tabelle.
BUILTIN_SOURCE_META = {
    "demo": {"name": "Demo-Portal (Testdaten)", "enabled_default": True},
    "wg-gesucht": {"name": "WG-Gesucht", "enabled_default": False},
    "immoscout24": {"name": "ImmoScout24", "enabled_default": False},
}

__all__ = [
    "AVAILABLE_SCRAPERS", "BUILTIN_SOURCE_META",
    "MockScraper", "WGGesuchtScraper", "ImmoScout24Scraper", "GenericScraper",
]
