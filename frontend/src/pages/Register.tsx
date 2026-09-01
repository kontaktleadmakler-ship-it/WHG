import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);
  const [marketingOptIn, setMarketingOptIn] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!acceptPrivacy) {
      setError("Bitte akzeptiere die Datenschutzerklärung, um fortzufahren.");
      return;
    }
    try {
      await api.post("/auth/register", {
        email,
        password,
        full_name: fullName,
        accept_privacy_policy: acceptPrivacy,
        marketing_opt_in: marketingOptIn,
      });
      navigate("/login");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registrierung fehlgeschlagen.");
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit}>
        <h1>Konto erstellen</h1>
        {error && <div className="error-box">{error}</div>}
        <label>Name</label>
        <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <label>E-Mail</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label>Passwort (mind. 8 Zeichen)</label>
        <input
          type="password"
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={acceptPrivacy}
            onChange={(e) => setAcceptPrivacy(e.target.checked)}
          />
          Ich akzeptiere die Datenschutzerklärung (Verarbeitung meiner Daten gemäß DSGVO).
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={marketingOptIn}
            onChange={(e) => setMarketingOptIn(e.target.checked)}
          />
          Ich möchte optional Produkt-News per E-Mail erhalten (jederzeit widerrufbar).
        </label>
        <button className="btn-primary" type="submit">
          Registrieren
        </button>
        <p className="switch-auth">
          Bereits registriert? <Link to="/login">Zum Login</Link>
        </p>
      </form>
    </div>
  );
}
