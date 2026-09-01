import { Link } from "react-router-dom";
import { MatchItem } from "../types";

function scoreColor(score: number): string {
  if (score >= 80) return "#1a9c53";
  if (score >= 60) return "#e0a020";
  return "#c9432b";
}

export default function MatchCard({ match }: { match: MatchItem }) {
  const { listing } = match;
  return (
    <Link to={`/listing/${listing.id}`} className="match-card">
      <div className="match-card-image">
        {listing.image_urls[0] ? (
          <img src={listing.image_urls[0]} alt={listing.title} />
        ) : (
          <div className="image-placeholder">Kein Bild</div>
        )}
        <span className="score-badge" style={{ backgroundColor: scoreColor(match.score) }}>
          {Math.round(match.score)}%
        </span>
      </div>
      <div className="match-card-body">
        <h3>{listing.title}</h3>
        <p className="meta">
          {listing.city} {listing.district ? `· ${listing.district}` : ""}
        </p>
        <p className="meta">
          {listing.price_total ? `${listing.price_total} €` : "Preis n/a"} ·{" "}
          {listing.size_sqm ? `${listing.size_sqm} m²` : ""} ·{" "}
          {listing.rooms ? `${listing.rooms} Zi.` : ""}
        </p>
        <span className="portal-tag">{listing.portal}</span>
      </div>
    </Link>
  );
}
