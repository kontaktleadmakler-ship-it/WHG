"""
Zentrale Konfiguration. Werte können per .env überschrieben werden
(siehe .env.example).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Welche Portale durchsucht werden, wird jetzt über das Dashboard
# (Tabelle "sources") verwaltet, nicht mehr über diese Datei.

# Intervall für die automatische Suche, in Minuten
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "30"))

# SMTP für E-Mail-Benachrichtigungen (optional, sonst nur In-App/Log)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "wohnungssuche@example.com")
