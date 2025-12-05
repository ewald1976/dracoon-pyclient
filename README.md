# Dracoon Pyclient

Python-Tool für die Dracoon API mit Console-Interface.

## Aktuelles Modul: User-zu-Gruppe Manager

Fügt Benutzer zu Gruppen hinzu - einzeln, gefiltert oder als Massenoperation.

## Installation

# Dracoon Pyclient

Python-Tool für die Dracoon API mit Console-Interface.

## Aktuelles Modul: User-zu-Gruppe Manager

Fügt Benutzer zu Gruppen hinzu - einzeln, gefiltert oder als Massenoperation.

## Installation

```bash
git clone https://github.com/ewald1976/dracoon-pyclient.git
cd dracoon-pyclient

# Virtual Environment erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate

# Abhängigkeiten installieren
pip3 install -r requirements.txt
```

### Debian Trixie

Sollten Sie Debian Trixie verwenden, sind folgende Pakete erforderlich:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git
```

## Konfiguration

### OAuth-App in Dracoon erstellen

1. Einstellungen → Sicherheit → OAuth Apps → "Neue OAuth-App erstellen"
2. Konfiguration:
   - Grant Type: `password`
   - Redirect URI: `http://localhost`
   - Scopes: `user:read`, `group:read`, `group:write`
3. Client-ID und Client-Secret notieren

### .env Datei anlegen

```bash
cp .env.example .env
```

In `.env` eintragen:

```bash
DRACOON_BASE_URL=https://ihre-instanz.dracoon.com
DRACOON_CLIENT_ID=ihre_client_id
DRACOON_CLIENT_SECRET=ihr_client_secret
DRACOON_USERNAME=ihr_benutzername
DRACOON_PASSWORD=ihr_passwort
```

## Verwendung

```bash
python3 dracoon-pyclient.py
```

Das Tool führt durch den Prozess:
1. Gruppe auswählen
2. Benutzer auswählen (alle / nur neue / manuell)
3. Bestätigen

## Häufige Fehler

**401 Unauthorized:** Zugangsdaten in `.env` prüfen

**403 Forbidden:** Benutzerrechte prüfen (Admin oder User-Manager erforderlich)

**ModuleNotFoundError:** `pip3 install -r requirements.txt`

## Hinweis

Das Projekt befindet sich in der Entwicklung und wird um weitere Module erweitert.

## Lizenz

MIT License

## Autor

Elmar Leirich ([@ewald1976](https://github.com/ewald1976))

## Konfiguration

### OAuth-App in Dracoon erstellen

1. Einstellungen → Sicherheit → OAuth Apps → "Neue OAuth-App erstellen"
2. Konfiguration:
   - Grant Type: `password`
   - Redirect URI: `http://localhost`
   - Berechtigungen: User-Manager, Group Manager
3. Client-ID und Client-Secret notieren

### .env Datei anlegen

```bash
cp .env.example .env
```

In `.env` eintragen:

```bash
DRACOON_BASE_URL=https://ihre-instanz.dracoon.com
DRACOON_CLIENT_ID=ihre_client_id
DRACOON_CLIENT_SECRET=ihr_client_secret
DRACOON_USERNAME=ihr_benutzername
DRACOON_PASSWORD=ihr_passwort
```

## Verwendung

```bash
python3 dracoon-pyclient.py
```

Das Tool führt durch den Prozess:
1. Gruppe auswählen
2. Benutzer auswählen (alle / nur neue / manuell)
3. Bestätigen

## Häufige Fehler

**401 Unauthorized:** Zugangsdaten in `.env` prüfen

**403 Forbidden:** Benutzerrechte prüfen (Admin oder User-Manager erforderlich)

**ModuleNotFoundError:** `pip3 install -r requirements.txt`

## Hinweis

Das Projekt befindet sich in der Entwicklung und wird um weitere Module erweitert.

## Lizenz

MIT License

## Autor

Elmar Leirich ([@ewald1976](https://github.com/ewald1976))