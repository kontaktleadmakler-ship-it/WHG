import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { api } from "../api/client";
import { MarketStats } from "../types";

export default function Statistics() {
  const [city, setCity] = useState("Berlin");
  const [stats, setStats] = useState<MarketStats | null>(null);
  const [density, setDensity] = useState<{ city: string; count: number }[]>([]);

  useEffect(() => {
    api.get("/stats/market", { params: { city } }).then(({ data }) => setStats(data));
  }, [city]);

  useEffect(() => {
    api.get("/stats/density").then(({ data }) => setDensity(data));
  }, []);

  return (
    <div>
      <h1>Marktstatistiken</h1>

      <div className="filter-bar">
        <label>Stadt:</label>
        <input value={city} onChange={(e) => setCity(e.target.value)} />
      </div>

      {stats && (
        <>
          <h3>
            Preisentwicklung – {stats.city} (aktuell {stats.current_avg_price_per_sqm} €/m²,{" "}
            {stats.current_listing_count} Angebote)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={(d) => new Date(d).toLocaleDateString("de-DE")} />
              <YAxis unit=" €/m²" />
              <Tooltip labelFormatter={(d) => new Date(d).toLocaleDateString("de-DE")} />
              <Line type="monotone" dataKey="avg_price_per_sqm" stroke="#2563eb" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </>
      )}

      <h3>Angebotsdichte nach Stadt</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={density}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="city" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#1a9c53" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
