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

### Windows

Für Windows steht eine ausführbare Version zur Verfügung. Wenn ein .env File für die Konfiguraion verwendet wird, muss sich dieses im selben Verzeichnis befinden wie die EXE-Datei.

## Häufige Fehler

**401 Unauthorized** - Zugangsdaten in `.env` prüfen, OAuth Grant Type muss `password` sein

**403 Forbidden** - Benutzer hat nicht die erforderlichen Berechtigungen

**ModuleNotFoundError** - `pip3 install -r requirements.txt` ausführen

## Disclaimer 

Dieses Tool wurde privat entwickelt und hat **keinen offiziellen Bezug zur Firma Dracoon**. Die Nutzung erfolgt auf eigene Verantwortung. Der Entwickler übernimmt keine Haftung für eventuelle Schäden, die durch die Verwendung dieses Tools entstehen.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

### Verwendete Bibliotheken

Dieses Projekt nutzt das offizielle [DRACOON Python SDK](https://github.com/unbekanntes-pferd/dracoon-python-api), welches unter der Apache License 2.0 lizenziert ist.

#### DRACOON Python SDK
- **Repository:** https://github.com/unbekanntes-pferd/dracoon-python-api
- **Lizenz:** Apache License 2.0
- **Copyright:** © DRACOON Contributors

Weitere verwendete Bibliotheken:
- **Rich** - MIT License
- **python-dotenv** - BSD-3-Clause License

Eine vollständige Liste aller Abhängigkeiten findest du in `requirements.txt`.

## Autor

[@ewald1976](https://github.com/ewald1976)
