"""
Liefert reproduzierbare Testdaten, ohne echte Portale anzufragen.
Nützlich zum Testen des Matching- und Benachrichtigungs-Flows, unabhängig
davon, ob die echten Scraper gerade wegen Layout-Änderungen funktionieren.
"""
import random
from datetime import datetime, timedelta
from .base import BaseScraper

_DISTRICTS = {
    "Berlin": ["Moabit", "Kreuzberg", "Neukölln", "Prenzlauer Berg", "Wedding", "Charlottenburg"],
    "Hamburg": ["Altona", "Eimsbüttel", "St. Pauli", "Winterhude"],
    "München": ["Schwabing", "Sendling", "Haidhausen", "Giesing"],
}


class MockScraper(BaseScraper):
    source_name = "demo-portal"

    def search(self, city: str, budget_max: float, zimmer_min: float | None = None) -> list[dict]:
        random.seed(f"{city}-{budget_max}-{datetime.now():%Y-%m-%d-%H}")
        districts = _DISTRICTS.get(city, [f"{city}-Mitte", f"{city}-Nord"])
        n = random.randint(4, 9)
        results = []
        for i in range(n):
            price = round(random.uniform(budget_max * 0.6, budget_max * 1.2), 2)
            qm = round(random.uniform(30, 110), 1)
            zimmer = random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4])
            results.append({
                "external_id": f"demo-{city}-{i}-{random.randint(1000,9999)}",
                "url": f"https://demo-portal.example/listing/{city.lower()}-{i}",
                "title": f"{zimmer}-Zimmer-Wohnung in {city}-{random.choice(districts)}",
                "city": city,
                "district": random.choice(districts),
                "price": price,
                "qm": qm,
                "zimmer": zimmer,
                "stockwerk": random.randint(0, 6),
                "balkon": random.choice([True, False]),
                "einbaukueche": random.choice([True, False]),
                "haustiere_erlaubt": random.choice([True, False, None]),
                "barrierefrei": random.choice([True, False, None]),
                "verfuegbar_ab": datetime.now() + timedelta(days=random.randint(0, 60)),
                "raw_text": "Automatisch generiertes Demo-Angebot für Testzwecke.",
            })
        return results
