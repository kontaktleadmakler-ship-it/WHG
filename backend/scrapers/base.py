"""
Gemeinsames Interface für alle Portal-Scraper.

WICHTIGER HINWEIS ZUR RECHTSLAGE:
Die großen deutschen Immobilienportale (ImmoScout24, Immonet/Immowelt,
WG-Gesucht, eBay Kleinanzeigen) untersagen automatisiertes Auslesen ihrer
Inhalte in ihren Nutzungsbedingungen (Anti-Scraping-Klauseln, teils auch
technisch per Rate-Limiting, Captchas und IP-Sperren durchgesetzt).
Automatisiertes Scraping dieser Seiten kann Vertragsverstöße darstellen
und zu Accountsperren oder rechtlichen Schritten führen (vgl. u.a.
Rechtsprechung zum Scraping, z.B. LG/OLG-Entscheidungen zu § 4 UWG /
Hausrecht). Diese App liefert daher:

1. Einen MockScraper mit realistischen Testdaten (funktioniert immer,
   für Entwicklung/Demo).
2. Best-effort-Scraper-Gerüste für WG-Gesucht und ImmoScout24, die die
   HTML-Struktur der Seiten auslesen. Diese können jederzeit durch
   Layout-Änderungen brechen und sind NICHT für den Dauerbetrieb gegen
   die Live-Seiten gedacht, ohne vorher die jeweiligen Nutzungsbedingungen
   zu prüfen bzw. eine offizielle Schnittstelle zu nutzen (z.B. das
   ImmoScout24-Partnerprogramm/API für Makler, RSS-Feeds wo verfügbar).

Wer produktiv suchen will, sollte primär auf E-Mail-Suchagenten der
Portale selbst (die man dort einrichten kann) plus diese App als
Aggregator/Matching-Layer für die eigenen, eingesammelten Ergebnisse
setzen.
"""
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    source_name: str = "base"

    @abstractmethod
    def search(self, city: str, budget_max: float, zimmer_min: float | None = None) -> list[dict]:
        """
        Führt eine Suche aus und gibt eine Liste von Dicts zurück, deren Felder
        auf backend.models.Listing gemappt werden können:
        external_id, url, title, city, district, price, qm, zimmer, stockwerk,
        balkon, einbaukueche, haustiere_erlaubt, barrierefrei, verfuegbar_ab, raw_text
        """
        raise NotImplementedError
