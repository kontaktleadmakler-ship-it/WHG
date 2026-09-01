# ImmoFinder – Wohnungssuche-Assistent (deutscher Wohnungsmarkt)

Vollständige Webanwendung: Scraping mehrerer Immobilienportale, Score-basiertes
Matching gegen individuelle Suchprofile, Benachrichtigungen (E-Mail/Push) und
ein React/TypeScript-Dashboard mit Statistiken und Favoriten.

## Architektur

```
immo-finder/
├── docker-compose.yml
├── backend/                # FastAPI + PostgreSQL
│   └── app/
│       ├── main.py         # FastAPI-App, Router-Registrierung
│       ├── models.py       # SQLAlchemy-Modelle
│       ├── schemas.py      # Pydantic-Schemas
│       ├── auth.py         # JWT-Login
│       ├── matching.py     # Score-Algorithmus (0-100)
│       ├── notifications.py# E-Mail (SMTP) + Web-Push
│       ├── routers/        # /api/auth, /profiles, /listings, /favorites, /notifications, /stats
│       └── scrapers/       # Immoscout24, Immonet, WG-Gesucht, eBay Kleinanzeigen + Scheduler
└── frontend/                # React + TypeScript (Vite)
    └── src/
        ├── pages/           # Login, Register, Dashboard, ProfileSettings, ListingDetail,
        │                     Favorites, Statistics, NotificationSettings
        ├── components/       # Layout, MatchCard
        └── api/client.ts     # Axios-Client mit JWT-Interceptor
```

## Starten (Docker)

```bash
cp backend/.env.example backend/.env   # Zugangsdaten eintragen (SMTP, VAPID-Keys, SECRET_KEY)
docker compose up --build
```

- Backend/API: http://localhost:8000/docs (automatische OpenAPI-Doku)
- Frontend: http://localhost:3000
- Der `scraper-worker`-Container läuft periodisch (`SCRAPE_INTERVAL_MINUTES`) und
  matcht neue Angebote automatisch gegen alle aktiven Suchprofile.

## Score-Algorithmus (Kurzfassung)

Gewichtung: Preis 35 %, Größe 20 %, Lage 20 %, Zimmeranzahl 10 %,
Muss-Ausstattung 10 %, Wunsch-Ausstattung 5 %. Fehlende Muss-Kriterien halbieren
den Gesamtscore. Details in `backend/app/matching.py`.

## Datenbeschaffung: E-Mail-Ingestion (Standardweg, empfohlen für Makler/Agenturen)

ImmoScout24, Immonet und WG-Gesucht untersagen automatisiertes Auslesen
(Scraping) in ihren Nutzungsbedingungen; eBay Kleinanzeigen untersagt
automatisierte Zugriffe ebenfalls. Für den gewerblichen Einsatz (Suche für
mehrere Kunden) ist deshalb der **Standardweg dieser App die offizielle
Suchauftrags-/E-Mail-Alarm-Funktion** der Portale statt Website-Scraping:

1. Lege ein zentrales Postfach für deine Agentur an (z. B. `alerts@deine-domain.de`).
2. Richte für jedes Kundenprofil auf jedem gewünschten Portal ganz regulär über
   die Portal-Oberfläche einen Suchauftrag/E-Mail-Alarm ein (Preis, Lage,
   Größe etc. entsprechend dem jeweiligen Kundenprofil), Zieladresse = das
   Agentur-Postfach. Das ist eine von den Portalen selbst bereitgestellte,
   ToS-konforme Funktion.
3. Trage die IMAP-Zugangsdaten dieses Postfachs in `backend/.env` ein
   (`IMAP_HOST`, `IMAP_USERNAME`, `IMAP_PASSWORD`, …).
4. Der Service `email-ingestion-worker` (siehe `docker-compose.yml`) liest
   neue Alert-Mails, extrahiert die enthaltenen Angebote
   (`backend/app/email_ingestion/parsers.py`) und speist sie in dieselbe
   Matching-/Benachrichtigungs-Pipeline ein wie zuvor.
5. Für ImmoScout24 lohnt sich zusätzlich das Partner-/Makler-API-Programm für
   professionelle Nutzer – bei Bedarf lässt sich ein weiterer Ingestion-Pfad
   analog zu `email_ingestion/` ergänzen, sobald ein API-Zugang vorliegt.

**Hinweis zu den E-Mail-Parsern:** Alert-Mail-Layouts unterscheiden sich je
Portal und können sich ändern. Die Parser in `parsers.py` sind bewusst
tolerant geschrieben (Regex + Link-Muster), sollten aber anhand echter
Beispiel-Mails deines Postfachs verifiziert/angepasst werden.

### Optional, standardmäßig deaktiviert: Website-Scraping

`backend/app/scrapers/` enthält zusätzlich einen struktureller Referenz-
Scraper pro Portal (robots.txt-Prüfung, Rate-Limiting). Dieser Weg **verstößt
gegen die Nutzungsbedingungen der Portale** und ist im Docker-Compose-Setup
über ein Profil ausgeblendet (`docker compose --profile scraping up
scraper-worker`). Aktiviere ihn nur, wenn du die aktuellen AGB geprüft hast
und das Risiko bewusst trägst – für den gewerblichen Einsatz raten wir davon
ab und empfehlen den E-Mail-Ingestion-Weg oder offizielle APIs.

## DSGVO-Hinweise (Umsetzungsstand)

- Registrierung erfordert explizite Einwilligung (`accept_privacy_policy`),
  Zeitstempel wird gespeichert (`consent_given_at`).
- Marketing-Kommunikation ist Opt-in (`marketing_opt_in`), nicht vorausgewählt.
- Benachrichtigungen werden nur verschickt, wenn der Nutzer sie aktiv aktiviert.
- Recht auf Löschung: `DELETE /api/auth/me` löscht Konto und alle verknüpften
  Daten (Suchprofile, Favoriten, Matches) per Cascade.
- Für den produktiven Betrieb zusätzlich nötig: Auftragsverarbeitungsverträge
  mit Hosting-/Mail-Anbietern, vollständige Datenschutzerklärung, Cookie-Banner
  (falls Tracking eingesetzt wird), Verzeichnis von Verarbeitungstätigkeiten.

## Nicht enthalten / nächste Schritte für Produktivbetrieb

- Alembic-Migrationsskripte (aktuell `Base.metadata.create_all` beim Start)
- Rate-Limiting/Captcha-Handling bei Bot-Schutz der Zielportale (Selenium-Fallback
  ist vorbereitet, aber nicht für alle Portale ausprogrammiert)
- E-Mail-Verifizierung nach Registrierung
- Automatisierte Tests (pytest/vitest)
