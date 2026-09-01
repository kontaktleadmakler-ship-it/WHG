import { useEffect, useState } from "react";
import { api } from "../api/client";
import { NotificationSettings } from "../types";

export default function NotificationSettingsPage() {
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get("/notifications/settings").then(({ data }) => setSettings(data));
  }, []);

  async function save() {
    if (!settings) return;
    await api.put("/notifications/settings", settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  if (!settings) return <p>Lade Einstellungen…</p>;

  return (
    <div>
      <h1>Benachrichtigungseinstellungen</h1>
      <div className="profile-form">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.email_enabled}
            onChange={(e) => setSettings({ ...settings, email_enabled: e.target.checked })}
          />
          E-Mail-Benachrichtigungen aktiv
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={settings.push_enabled}
            onChange={(e) => setSettings({ ...settings, push_enabled: e.target.checked })}
          />
          Push-Benachrichtigungen aktiv (Browser)
        </label>

        <label>Mindest-Score für Benachrichtigung (%)</label>
        <input
          type="number"
          min={0}
          max={100}
          value={settings.min_score_for_notification}
          onChange={(e) =>
            setSettings({ ...settings, min_score_for_notification: Number(e.target.value) })
          }
        />

        <label>Max. Benachrichtigungen pro Tag</label>
        <input
          type="number"
          min={1}
          value={settings.max_notifications_per_day}
          onChange={(e) =>
            setSettings({ ...settings, max_notifications_per_day: Number(e.target.value) })
          }
        />

        <button className="btn-primary" onClick={save}>
          Speichern
        </button>
        {saved && <span className="success-text">Gespeichert ✓</span>}
      </div>

      <p className="dsgvo-note">
        Hinweis (DSGVO): Du kannst Benachrichtigungen jederzeit deaktivieren. Deine Suchprofile
        und Kontodaten kannst du in den Kontoeinstellungen vollständig löschen lassen.
      </p>
    </div>
  );
}
