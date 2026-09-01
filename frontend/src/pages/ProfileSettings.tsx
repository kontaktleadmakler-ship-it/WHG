import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import { SearchProfile } from "../types";

const ALL_PORTALS = ["immoscout24", "immonet", "wg_gesucht", "ebay_kleinanzeigen"];

const emptyProfile: Omit<SearchProfile, "id" | "created_at"> = {
  name: "Mein Suchprofil",
  price_min: 0,
  price_max: 1200,
  size_min_sqm: 40,
  size_max_sqm: undefined,
  rooms_min: 2,
  rooms_max: undefined,
  cities: [],
  districts: [],
  must_have_features: [],
  nice_to_have_features: [],
  portals: ALL_PORTALS,
  is_active: true,
};

export default function ProfileSettings() {
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [form, setForm] = useState(emptyProfile);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [citiesInput, setCitiesInput] = useState("");
  const [mustHaveInput, setMustHaveInput] = useState("");

  function load() {
    api.get("/profiles").then(({ data }) => setProfiles(data));
  }

  useEffect(load, []);

  function startEdit(p: SearchProfile) {
    setEditingId(p.id);
    setForm(p);
    setCitiesInput(p.cities.join(", "));
    setMustHaveInput(p.must_have_features.join(", "));
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyProfile);
    setCitiesInput("");
    setMustHaveInput("");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const payload = {
      ...form,
      cities: citiesInput.split(",").map((c) => c.trim()).filter(Boolean),
      must_have_features: mustHaveInput.split(",").map((c) => c.trim()).filter(Boolean),
    };
    if (editingId) {
      await api.put(`/profiles/${editingId}`, payload);
    } else {
      await api.post("/profiles", payload);
    }
    resetForm();
    load();
  }

  async function handleDelete(id: string) {
    await api.delete(`/profiles/${id}`);
    load();
  }

  function togglePortal(portal: string) {
    setForm((f) => ({
      ...f,
      portals: f.portals.includes(portal)
        ? f.portals.filter((p) => p !== portal)
        : [...f.portals, portal],
    }));
  }

  return (
    <div>
      <h1>Suchprofile</h1>

      <div className="profile-list">
        {profiles.map((p) => (
          <div key={p.id} className="profile-row">
            <div>
              <strong>{p.name}</strong>
              <span className="meta">
                {" "}
                · {p.cities.join(", ") || "keine Stadt"} · bis {p.price_max ?? "∞"} €
              </span>
            </div>
            <div>
              <button className="btn-secondary" onClick={() => startEdit(p)}>
                Bearbeiten
              </button>
              <button className="btn-danger" onClick={() => handleDelete(p.id)}>
                Löschen
              </button>
            </div>
          </div>
        ))}
      </div>

      <h2>{editingId ? "Suchprofil bearbeiten" : "Neues Suchprofil"}</h2>
      <form className="profile-form" onSubmit={handleSubmit}>
        <label>Name</label>
        <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />

        <div className="form-row">
          <div>
            <label>Budget min. (€)</label>
            <input
              type="number"
              value={form.price_min}
              onChange={(e) => setForm({ ...form, price_min: Number(e.target.value) })}
            />
          </div>
          <div>
            <label>Budget max. (€)</label>
            <input
              type="number"
              value={form.price_max ?? ""}
              onChange={(e) => setForm({ ...form, price_max: Number(e.target.value) })}
            />
          </div>
        </div>

        <div className="form-row">
          <div>
            <label>Größe min. (m²)</label>
            <input
              type="number"
              value={form.size_min_sqm ?? ""}
              onChange={(e) => setForm({ ...form, size_min_sqm: Number(e.target.value) })}
            />
          </div>
          <div>
            <label>Zimmer min.</label>
            <input
              type="number"
              value={form.rooms_min ?? ""}
              onChange={(e) => setForm({ ...form, rooms_min: Number(e.target.value) })}
            />
          </div>
        </div>

        <label>Städte (kommagetrennt)</label>
        <input value={citiesInput} onChange={(e) => setCitiesInput(e.target.value)} placeholder="Berlin, Leipzig" />

        <label>Ausstattung / Must-Haves (kommagetrennt)</label>
        <input
          value={mustHaveInput}
          onChange={(e) => setMustHaveInput(e.target.value)}
          placeholder="Balkon, Einbauküche, Aufzug"
        />

        <label>Portale durchsuchen</label>
        <div className="portal-checkboxes">
          {ALL_PORTALS.map((portal) => (
            <label key={portal} className="checkbox-label">
              <input
                type="checkbox"
                checked={form.portals.includes(portal)}
                onChange={() => togglePortal(portal)}
              />
              {portal}
            </label>
          ))}
        </div>

        <div className="form-actions">
          <button className="btn-primary" type="submit">
            {editingId ? "Speichern" : "Anlegen"}
          </button>
          {editingId && (
            <button type="button" className="btn-secondary" onClick={resetForm}>
              Abbrechen
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
