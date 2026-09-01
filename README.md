# Wohnungssuche-App

Profilbasierte Wohnungssuche mit automatischem Abgleich neuer Angebote und
Benachrichtigung bei Treffern.

## Architektur

```
backend/
  main.py          FastAPI-App, alle REST-Endpunkte, Scheduler-Start
  models.py        SQLAlchemy-Modelle: Profile, Listing, Match
  schemas.py        Pydantic-Schemas für die API
  database.py       SQLite-Setup (per DATABASE_URL austauschbar)
  matching.py       Bewertungsalgorithmus (Score 0.0–1.0)
  notifications.py  E-Mail-Versand bei Treffern (SMTP, optional)
  scan_engine.py     Verbindet Scraper + Matching + Benachrichtigung
  config.py          Zentrale Konfiguration aus .env
  scrapers/
    base.py           Gemeinsames Interface
    mock_scraper.py    Demo-Datenquelle (immer funktionsfähig)
    wggesucht.py        Best-effort-Scraper WG-Gesucht
    immoscout24.py      Best-effort-Scraper ImmoScout24
frontend/
  index.html         Einfache Oberfläche zur Profilverwaltung & Trefferanzeige
```

Die API dient gleichzeitig als Backend für die mitgelieferte Web-UI und für
mobile Clients (z.B. eine native App oder ein Shortcut, das dieselben
Endpunkte nutzt).

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Werte nach Bedarf anpassen
cd backend
uvicorn main:app --reload --port 8000
```

Danach:
- Weboberfläche: http://localhost:8000/
- API-Dokumentation (Swagger): http://localhost:8000/docs

## Nutzung

1. Im UI (oder per `POST /profiles`) ein Suchprofil anlegen: Budget, Stadt,
   m², Zimmer, Stockwerk, Balkon, Einbauküche, Haustiere, Barrierefreiheit,
   Einzugsdatum.
2. Der Scheduler durchsucht die in `ENABLED_SCRAPERS` aktivierten Quellen
   automatisch alle `SCAN_INTERVAL_MINUTES` Minuten (Standard: 30). Manuell
   auslösen geht über den Button „Jetzt durchsuchen“ oder `POST /scan`.
3. Neue Angebote werden gespeichert und gegen alle aktiven Profile bewertet
   (`matching.py`). Ab einem Score von 0.6 gilt es als Treffer.
4. Bei neuem Treffer wird versucht, eine E-Mail zu senden (falls SMTP in
   `.env` konfiguriert ist); ohne SMTP-Konfiguration werden Treffer geloggt
   und erscheinen sofort im UI unter dem jeweiligen Profil.

## Portale verwalten (Dashboard)

Im Dashboard gibt es unter „Portale verwalten“ eine Liste aller Quellen mit
Ein/Aus-Schaltern sowie ein Formular zum Hinzufügen eigener Portale. Das
läuft komplett über die Datenbank (Tabelle `sources`), nicht mehr über `.env`:

- **Eingebaute Portale** (Demo, WG-Gesucht, ImmoScout24) lassen sich nur
  an-/ausschalten, nicht bearbeiten oder löschen.
- **Eigene Portale** werden über eine Such-URL-Vorlage plus CSS-Selektoren
  definiert (kein Code nötig):
  - Such-URL-Vorlage mit Platzhaltern `{city}`, `{budget_max}`, `{zimmer_min}`,
    z.B. `https://beispiel.de/suche?stadt={city}&preis_bis={budget_max}`
  - Selektor für die Angebots-Karte (Container-Element pro Treffer)
  - Selektor für den Link zum Angebot
  - optional: Selektoren für Titel, Preis, m², Zimmer
  - Selektoren am besten mit den Browser-Entwicklertools (Rechtsklick →
    „Untersuchen“) auf der jeweiligen Portalseite ermitteln.

Diese generische Quelle (`backend/scrapers/generic.py`) übernimmt dieselbe
Matching- und Benachrichtigungslogik wie die eingebauten Scraper. Die
gleichen API-Endpunkte (`GET/POST/PATCH/DELETE /sources`) stehen auch für
mobile Clients zur Verfügung.

## Wichtiger Hinweis zu den Portal-Scrapern

Standardmäßig ist nur das **Demo-Portal** aktiv. Es liefert realistische
Testdaten, damit die gesamte Kette – Profilanlage, Matching, Benachrichtigung,
UI, Portalverwaltung – sofort ohne weiteres Setup ausprobiert werden kann.

Für die echten Portale gilt:

- **ImmoScout24, Immonet/Immowelt, WG-Gesucht und eBay Kleinanzeigen
  untersagen automatisiertes Auslesen in ihren Nutzungsbedingungen** und
  setzen dies technisch durch (Bot-Erkennung, Rate-Limits, Captchas,
  teils IP-Sperren). Automatisiertes Scraping dieser Seiten kann gegen die
  AGB verstoßen und zu Accountsperren oder Abmahnungen führen.
- Die mitgelieferten Scraper-Gerüste (`wggesucht.py`, `immoscout24.py`)
  zeigen, wie man technisch an die Aufgabe herangeht (HTTP-Request,
  HTML-Parsing, Mapping auf das gemeinsame Datenformat), sind aber bewusst
  als **Platzhalter mit Beispiel-Selektoren** gehalten. Sie werden mit
  hoher Wahrscheinlichkeit angepasst werden müssen, da sich das HTML-Layout
  der Seiten regelmäßig ändert, und funktionieren gegen aktive
  Bot-Erkennung teils gar nicht ohne Headless-Browser (z.B. Playwright) und
  IP-Rotation.
- **Empfohlene, unproblematische Alternative:** Auf den Portalen selbst
  E-Mail-Suchagenten/Alerts einrichten (das bieten alle genannten Seiten
  offiziell an) und diese App als Aggregator nutzen, der die eingehenden
  Angebote (z.B. per E-Mail-Parsing oder manuellem Import über `POST
  /scan`-ähnliche Endpunkte) sammelt, bewertet und in einer gemeinsamen
  Oberfläche darstellt. Für ImmoScout24 gibt es zudem ein offizielles
  Partner-/Makler-API-Programm, das für professionelle Nutzung infrage
  kommt.
- Wer die Scraper dennoch gegen die Live-Seiten einsetzen möchte, sollte
  vorher selbst die aktuellen Nutzungsbedingungen prüfen, niedrige
  Abruffrequenzen einhalten (siehe `request_delay_seconds`) und robots.txt
  respektieren.

## Matching-Algorithmus

`matching.py` prüft zunächst harte Ausschlusskriterien (Stadt, Budget deutlich
überschritten, Pflicht-Haustiere/Barrierefreiheit nicht erfüllt → Score 0).
Danach fließen Budget, m², Zimmer, Stadtteil, Stockwerk, Balkon, Einbauküche
und Einzugsdatum gewichtet in einen Score zwischen 0 und 1 ein. Ab 0.6 gilt
ein Angebot als Treffer und wird gespeichert bzw. gemeldet.

## Datenbank

Standardmäßig SQLite (`wohnungssuche.db`, wird beim ersten Start automatisch
angelegt). Für Mehrbenutzer-/Produktivbetrieb `DATABASE_URL` in `.env` auf
z.B. PostgreSQL umstellen — der Code ist über SQLAlchemy datenbankagnostisch.

## API-Endpunkte (Auswahl)

| Methode | Pfad                        | Zweck                          |
|---------|-----------------------------|---------------------------------|
| POST    | /profiles                   | Profil anlegen                  |
| GET     | /profiles                   | Alle Profile auflisten          |
| GET     | /profiles/{id}               | Einzelnes Profil abrufen        |
| PATCH   | /profiles/{id}               | Profil teilweise aktualisieren  |
| DELETE  | /profiles/{id}               | Profil löschen                  |
| GET     | /profiles/{id}/matches       | Treffer eines Profils           |
| POST    | /scan                        | Suche über alle Quellen anstoßen|
| GET     | /health                      | Status/Konfiguration prüfen     |
| GET     | /sources                     | Alle Portale auflisten          |
| POST    | /sources                     | Eigenes Portal hinzufügen       |
| PATCH   | /sources/{id}                 | Portal an/aus schalten, editieren|
| DELETE  | /sources/{id}                 | Eigenes Portal löschen          |

Vollständige, interaktive Doku unter `/docs` (Swagger UI), automatisch aus
den Pydantic-Schemas generiert — direkt nutzbar für die Anbindung mobiler
Clients.
