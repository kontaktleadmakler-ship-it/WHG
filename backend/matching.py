"""
Matching-Algorithmus: bewertet, wie gut ein Listing zu einem Profil passt.
Score zwischen 0.0 (kein Match) und 1.0 (perfekter Match).

Hartausschluss-Kriterien (K.O.) führen sofort zu Score 0.0, weiche Kriterien
fließen gewichtet in den Score ein.
"""
from models import Profile, Listing

# Gewichte für weiche Kriterien (Summe = 1.0)
WEIGHTS = {
    "budget": 0.30,
    "qm": 0.20,
    "zimmer": 0.20,
    "district": 0.10,
    "stockwerk": 0.05,
    "balkon": 0.05,
    "einbaukueche": 0.05,
    "einzug": 0.05,
}

MATCH_THRESHOLD = 0.6  # ab diesem Score gilt ein Listing als "Treffer"


def _range_score(value, min_val, max_val):
    """1.0 wenn value im [min_val, max_val] liegt, sonst linear abfallend."""
    if value is None:
        return 0.5  # unbekannt -> neutral werten statt hart auszuschließen
    if min_val is not None and value < min_val:
        diff = (min_val - value) / max(min_val, 1)
        return max(0.0, 1.0 - diff)
    if max_val is not None and value > max_val:
        diff = (value - max_val) / max(max_val, 1)
        return max(0.0, 1.0 - diff)
    return 1.0


def calculate_match_score(profile: Profile, listing: Listing) -> float:
    # --- Harte K.O.-Kriterien ---
    if listing.city and profile.city and listing.city.lower() != profile.city.lower():
        return 0.0

    if profile.haustiere_erlaubt_required and listing.haustiere_erlaubt is False:
        return 0.0

    if profile.barrierefrei_required and listing.barrierefrei is False:
        return 0.0

    if listing.price is not None and listing.price > profile.budget_max * 1.15:
        # mehr als 15% über Budget: kein sinnvoller Treffer mehr
        return 0.0

    # --- Weiche Kriterien ---
    scores = {}
    scores["budget"] = _range_score(listing.price, profile.budget_min, profile.budget_max)
    scores["qm"] = _range_score(listing.qm, profile.qm_min, profile.qm_max)
    scores["zimmer"] = _range_score(listing.zimmer, profile.zimmer_min, profile.zimmer_max)

    if profile.district and listing.district:
        scores["district"] = 1.0 if profile.district.lower() in listing.district.lower() else 0.6
    else:
        scores["district"] = 0.8  # keine Bezirksangabe -> leicht positiv neutral

    scores["stockwerk"] = _range_score(
        listing.stockwerk, profile.stockwerk_min, profile.stockwerk_max
    )

    if profile.balkon_required:
        scores["balkon"] = 1.0 if listing.balkon else 0.0
    else:
        scores["balkon"] = 1.0

    if profile.einbaukueche_required:
        scores["einbaukueche"] = 1.0 if listing.einbaukueche else 0.0
    else:
        scores["einbaukueche"] = 1.0

    if profile.einzug_ab and listing.verfuegbar_ab:
        scores["einzug"] = 1.0 if listing.verfuegbar_ab <= profile.einzug_ab else 0.5
    else:
        scores["einzug"] = 0.8

    total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    return round(total, 3)


def find_matches_for_profile(profile: Profile, listings: list[Listing]):
    """Gibt Liste von (listing, score) zurück, sortiert nach Score absteigend,
    nur Treffer über MATCH_THRESHOLD."""
    results = []
    for listing in listings:
        score = calculate_match_score(profile, listing)
        if score >= MATCH_THRESHOLD:
            results.append((listing, score))
    results.sort(key=lambda x: x[1], reverse=True)
    return results
