import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { Listing } from "../types";

export default function ListingDetail() {
  const { id } = useParams();
  const [listing, setListing] = useState<Listing | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get(`/listings/${id}`).then(({ data }) => setListing(data));
  }, [id]);

  async function addToFavorites() {
    if (!listing) return;
    await api.post("/favorites", { listing_id: listing.id });
    setSaved(true);
  }

  if (!listing) return <p>Lade Details…</p>;

  return (
    <div className="listing-detail">
      <div className="gallery">
        {listing.image_urls.length > 0 ? (
          listing.image_urls.map((src) => <img key={src} src={src} alt={listing.title} />)
        ) : (
          <div className="image-placeholder large">Keine Bilder verfügbar</div>
        )}
      </div>

      <h1>{listing.title}</h1>
      <p className="meta">
        {listing.street ? `${listing.street}, ` : ""}
        {listing.zip_code} {listing.city} {listing.district ? `(${listing.district})` : ""}
      </p>

      <div className="fact-grid">
        <div>
          <span className="label">Miete</span>
          <span className="value">{listing.price_total ? `${listing.price_total} €` : "n/a"}</span>
        </div>
        <div>
          <span className="label">Größe</span>
          <span className="value">{listing.size_sqm ? `${listing.size_sqm} m²` : "n/a"}</span>
        </div>
        <div>
          <span className="label">Zimmer</span>
          <span className="value">{listing.rooms ?? "n/a"}</span>
        </div>
        <div>
          <span className="label">Portal</span>
          <span className="value">{listing.portal}</span>
        </div>
      </div>

      {listing.features.length > 0 && (
        <>
          <h3>Ausstattung</h3>
          <ul className="feature-list">
            {listing.features.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </>
      )}

      {listing.description && (
        <>
          <h3>Beschreibung</h3>
          <p>{listing.description}</p>
        </>
      )}

      <div className="form-actions">
        <a className="btn-primary" href={listing.url} target="_blank" rel="noreferrer">
          Original-Anzeige öffnen
        </a>
        <button className="btn-secondary" onClick={addToFavorites} disabled={saved}>
          {saved ? "Gespeichert ✓" : "Zu Favoriten hinzufügen"}
        </button>
      </div>
    </div>
  );
}
