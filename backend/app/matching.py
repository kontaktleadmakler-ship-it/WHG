"""Score-basierter Matching-Algorithmus zwischen Suchprofilen und Angeboten.

Der Score (0-100) setzt sich aus gewichteten Teilkriterien zusammen. Jedes
Kriterium liefert 0.0-1.0, multipliziert mit seinem Gewicht.
"""
import json
from dataclasses import dataclass, field
from typing import Dict, Optional

from app import models

WEIGHTS = {
    "price": 0.35,
    "size": 0.20,
    "rooms": 0.10,
    "location": 0.20,
    "must_have_features": 0.10,
    "nice_to_have_features": 0.05,
}


@dataclass
class ScoreResult:
    total: float
    breakdown: Dict[str, float] = field(default_factory=dict)

    def as_json(self) -> str:
        return json.dumps(self.breakdown, ensure_ascii=False)


def _score_price(profile: models.SearchProfile, listing: models.Listing) -> float:
    if listing.price_total is None:
        return 0.5  # neutral, wenn unbekannt
    if listing.price_total < profile.price_min:
        return 1.0
    if profile.price_max is None:
        return 1.0
    if listing.price_total <= profile.price_max:
        # linear höherer Score, je weiter unter dem Maximalbudget
        spanne = max(profile.price_max - profile.price_min, 1)
        return round(1.0 - (listing.price_total - profile.price_min) / spanne * 0.3, 3)
    # über Budget -> Score sinkt schnell mit Überschreitung
    overshoot = (listing.price_total - profile.price_max) / profile.price_max
    return max(0.0, 1.0 - overshoot * 2)


def _score_range(value: Optional[float], vmin: Optional[float], vmax: Optional[float]) -> float:
    if value is None:
        return 0.5
    if vmin is not None and value < vmin:
        deficit = (vmin - value) / max(vmin, 1)
        return max(0.0, 1.0 - deficit)
    if vmax is not None and value > vmax:
        excess = (value - vmax) / max(vmax, 1)
        return max(0.0, 1.0 - excess)
    return 1.0


def _score_location(profile: models.SearchProfile, listing: models.Listing) -> float:
    if not profile.cities:
        return 1.0
    if listing.city and listing.city.lower() in [c.lower() for c in profile.cities]:
        if not profile.districts:
            return 1.0
        if listing.district and listing.district.lower() in [d.lower() for d in profile.districts]:
            return 1.0
        return 0.7  # richtige Stadt, falscher Bezirk
    return 0.1  # falsche Stadt


def _score_features(wanted: list, present: list) -> float:
    if not wanted:
        return 1.0
    present_lower = {f.lower() for f in (present or [])}
    hits = sum(1 for w in wanted if w.lower() in present_lower)
    return hits / len(wanted)


def calculate_match_score(profile: models.SearchProfile, listing: models.Listing) -> ScoreResult:
    breakdown = {
        "price": _score_price(profile, listing),
        "size": _score_range(listing.size_sqm, profile.size_min_sqm, profile.size_max_sqm),
        "rooms": _score_range(listing.rooms, profile.rooms_min, profile.rooms_max),
        "location": _score_location(profile, listing),
        "must_have_features": _score_features(profile.must_have_features, listing.features),
        "nice_to_have_features": _score_features(profile.nice_to_have_features, listing.features),
    }

    total = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS) * 100

    # Hartes Ausschlusskriterium: fehlende Must-Have-Features drücken den Score stark
    if profile.must_have_features and breakdown["must_have_features"] < 1.0:
        total *= 0.5

    return ScoreResult(total=round(total, 1), breakdown=breakdown)
