import { useEffect, useState } from "react";
import { api } from "../api/client";
import { MatchItem, SearchProfile } from "../types";
import MatchCard from "../components/MatchCard";

export default function Dashboard() {
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [profileId, setProfileId] = useState<string>("");
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState("score");
  const [order, setOrder] = useState("desc");
  const [city, setCity] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/profiles").then(({ data }) => setProfiles(data));
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .get("/listings/matches", {
        params: {
          profile_id: profileId || undefined,
          min_score: minScore,
          sort_by: sortBy,
          order,
          city: city || undefined,
          max_price: maxPrice || undefined,
        },
      })
      .then(({ data }) => setMatches(data))
      .finally(() => setLoading(false));
  }, [profileId, minScore, sortBy, order, city, maxPrice]);

  return (
    <div>
      <h1>Gefundene Wohnungen</h1>

      <div className="filter-bar">
        <select value={profileId} onChange={(e) => setProfileId(e.target.value)}>
          <option value="">Alle Suchprofile</option>
          {profiles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Min. Score %"
          value={minScore}
          onChange={(e) => setMinScore(Number(e.target.value))}
        />

        <input placeholder="Stadt filtern" value={city} onChange={(e) => setCity(e.target.value)} />

        <input
          type="number"
          placeholder="Max. Preis €"
          value={maxPrice}
          onChange={(e) => setMaxPrice(e.target.value)}
        />

        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="score">Match-Score</option>
          <option value="price">Preis</option>
          <option value="size">Größe</option>
          <option value="date">Neueste zuerst</option>
        </select>

        <select value={order} onChange={(e) => setOrder(e.target.value)}>
          <option value="desc">Absteigend</option>
          <option value="asc">Aufsteigend</option>
        </select>
      </div>

      {loading ? (
        <p>Lade Angebote…</p>
      ) : matches.length === 0 ? (
        <p>Keine Treffer. Passe dein Suchprofil an oder warte auf den nächsten Scrape-Zyklus.</p>
      ) : (
        <div className="match-grid">
          {matches.map((m) => (
            <MatchCard key={m.id} match={m} />
          ))}
        </div>
      )}
    </div>
  );
}
