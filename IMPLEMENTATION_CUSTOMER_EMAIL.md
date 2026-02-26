# Customer Email Export - Implementation Details

## Übersicht

Das neue Modul `customer_email_export` ermöglicht es Resellern, E-Mail-Adressen aller User über alle Kunden eines Tenants zu exportieren.

## Architektur

### 1. Provisioning API Client (`lib/provisioning.py`)

Ein dedizierter Client für die Dracoon Provisioning API:

```python
from lib.provisioning import ProvisioningClient

client = ProvisioningClient(base_url, service_token)
customers = await client.get_all_customers()
```

**Hauptfunktionen:**
- `get_customers()` - Holt Kunden (paginiert)
- `get_all_customers()` - Holt ALLE Kunden (automatische Pagination)
- `get_customer_users()` - Holt User eines Kunden (paginiert)
- `get_all_customer_users()` - Holt ALLE User eines Kunden
- `test_connection()` - Testet die Verbindung

### 2. Customer Email Export Modul (`modules/customer_email_export.py`)

Hauptmodul mit TUI für den E-Mail-Export:

**Workflow:**
1. Service Token aus `.env` laden oder abfragen
2. Verbindung zur Provisioning API testen
3. Alle Kunden laden
4. Für jeden Kunden alle User laden
5. E-Mail-Adressen sammeln
6. Ergebnisse anzeigen
7. Export als CSV anbieten

**Features:**
- Progress Bar während des Sammelns
- Fehlerbehandlung pro Kunden
- Statistiken (Gesamt-E-Mails, Anzahl Kunden, gesperrte User)
- CSV-Export mit Timestamp im Dateinamen

## Authentifizierung

### X-SDS-Service-Token

Anders als die normalen Module nutzt dieses Modul **NICHT** OAuth, sondern einen **Service Token**:

```
X-SDS-Service-Token: your_token_here
```

**Vorteile:**
- Nur ein Token nötig (kein Username/Password)
- Zugriff auf alle Kunden eines Tenants
- Keine OAuth-App-Konfiguration nötig

**Generierung:**
1. Als Reseller/Tenant Admin einloggen
2. Settings → Provisioning
3. Service Token generieren

## .env Konfiguration

Neue Zeile in `.env`:

```
DRACOON_SERVICE_TOKEN=your_service_token_here
```

## API Endpoints

Das Modul nutzt folgende Provisioning API Endpoints:

```
GET /api/v4/provisioning/customers
GET /api/v4/provisioning/customers/{id}
GET /api/v4/provisioning/customers/{id}/users
```

## CSV Export Format

Der Export enthält folgende Spalten:

| Spalte | Beschreibung |
|--------|--------------|
| Customer ID | Interne Kunden-ID |
| Customer Name | Firmenname des Kunden |
| User ID | Interne User-ID |
| First Name | Vorname |
| Last Name | Nachname |
| Email | E-Mail-Adresse |
| Username | Benutzername |
| Is Locked | Ja/Nein - Gesperrt |

## Fehlerbehandlung

- **Verbindungsfehler**: Klare Fehlermeldung mit Hinweis auf Token-Validität
- **Kunden-Fehler**: Pro-Kunde Fehlerbehandlung, andere Kunden werden weiter verarbeitet
- **Leere Ergebnisse**: Benutzerfreundliche Meldung wenn keine Daten gefunden

## Integration ins Hauptmenü

Das Modul ist als **Modul #4** im Hauptmenü integriert:

```python
{
    'id': 4,
    'name': 'Customer Email Export (Reseller)',
    'description': 'Export all email addresses from all customers (Multi-Tenant)',
    'module': customer_email_export,
    'requires_connection': False  # Nutzt Provisioning API
}
```

**Wichtig:** `requires_connection: False` bedeutet, dass keine Standard-OAuth-Verbindung benötigt wird.

## Verwendung

1. `.env` mit Service Token konfigurieren
2. Tool starten: `python3 dracoon-pyclient.py`
3. Modul #4 auswählen
4. Service Token wird automatisch aus `.env` geladen
5. Kunden werden durchlaufen
6. Ergebnis als CSV exportieren

## Erweiterungsmöglichkeiten

Mögliche zukünftige Features:

1. **Filter nach Kunden** - Nur bestimmte Kunden exportieren
2. **Filter nach User-Status** - Nur aktive/gesperrte User
3. **Mehr User-Attribute** - Rollen, letzte Anmeldung, etc.
4. **Direktes E-Mail-Versand** - Integration mit SMTP
5. **Gruppenzugehörigkeit** - Welcher User in welchen Gruppen

## Dependencies

Neue Abhängigkeit in `requirements.txt`:

```
httpx  # Für direkte HTTP-Requests an Provisioning API
```

## Testen

Test-Skript vorhanden: `test_provisioning.py`

```bash
# Credentials in test_provisioning.py eintragen
python3 test_provisioning.py
```

## Sicherheitshinweise

⚠️ **Service Token ist mächtig!**

- Zugriff auf ALLE Kunden des Tenants
- Sensible Daten (E-Mail-Adressen)
- NIEMALS in Git committen
- `.env` ist in `.gitignore`

## Troubleshooting

**"Connection failed"**
→ Service Token überprüfen, muss gültig sein

**"No customers found"**
→ Token hat keine Berechtigung oder keine Kunden vorhanden

**"Error loading users from X"**
→ Spezifischer Kunde hat ein Problem, wird übersprungen

**Import Error für httpx**
→ `pip install -r requirements.txt` ausführen
