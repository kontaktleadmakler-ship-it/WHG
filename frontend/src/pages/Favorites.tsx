import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Favorite } from "../types";

export default function Favorites() {
  const [favorites, setFavorites] = useState<Favorite[]>([]);

  function load() {
    api.get("/favorites").then(({ data }) => setFavorites(data));
  }

  useEffect(load, []);

  async function remove(id: string) {
    await api.delete(`/favorites/${id}`);
    load();
  }

  return (
    <div>
      <h1>Favoriten</h1>
      {favorites.length === 0 ? (
        <p>Noch keine Favoriten gespeichert.</p>
      ) : (
        <div className="favorite-list">
          {favorites.map((f) => (
            <div key={f.id} className="favorite-row">
              <Link to={`/listing/${f.listing.id}`}>
                <strong>{f.listing.title}</strong>
                <span className="meta">
                  {" "}
                  · {f.listing.city} · {f.listing.price_total} € · {f.listing.size_sqm} m²
                </span>
              </Link>
              <button className="btn-danger" onClick={() => remove(f.id)}>
                Entfernen
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
