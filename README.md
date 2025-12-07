# Dracoon Pyclient

Python-Tool für die Dracoon API mit Console-Interface.

## Module

- **User zu Gruppe hinzufügen** - Massenoperation zum Hinzufügen von Usern zu Gruppen
- **Room Admin Report** - Zeigt an wo ein User letzter Raum Admin ist. Raum kann dann direkt gelöscht werden.

## Installation

```bash
git clone https://github.com/ewald1976/dracoon-pyclient.git
cd dracoon-pyclient

# Virtual Environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Dependencies
pip3 install -r requirements.txt
```

## Konfiguration

### OAuth-App in Dracoon erstellen

1. Einstellungen → Sicherheit → OAuth Apps → "Neue OAuth-App erstellen"
2. Grant Type: `password`
3. Redirect URI: `http://localhost`
4. Client-ID und Client-Secret notieren

### .env Datei

```bash
cp .env.example .env
nano .env  # Credentials eintragen
```

**Erforderliche Berechtigungen:**
- Group Admin (für User-zu-Gruppe)
- User Manager (für Room Admin Report)

## Verwendung

```bash
python3 dracoon-pyclient.py
```

## Häufige Fehler

**401 Unauthorized** - Zugangsdaten in `.env` prüfen, OAuth Grant Type muss `password` sein

**403 Forbidden** - Benutzer hat nicht die erforderlichen Berechtigungen

**ModuleNotFoundError** - `pip3 install -r requirements.txt` ausführen

## Disclaimer

Dieses Tool wurde privat entwickelt und hat **keinen offiziellen Bezug zur Firma Dracoon**. Die Nutzung erfolgt auf eigene Verantwortung. Der Entwickler übernimmt keine Haftung für eventuelle Schäden, die durch die Verwendung dieses Tools entstehen.

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

## Autor

[@ewald1976](https://github.com/ewald1976)
