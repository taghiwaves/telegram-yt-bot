# 🤖 YouTube Transkriptions-Bot – Deployment-Anleitung

## Was der Bot macht
- Du sendest einen YouTube-Link
- Der Bot lädt das Audio herunter (via yt-dlp)
- Whisper AI transkribiert das Audio zu Text
- Der Rohtext wird dir direkt in Telegram gesendet

---

## Schritt 1: Telegram Bot erstellen

1. Öffne Telegram und suche nach **@BotFather**
2. Sende `/newbot`
3. Gib deinem Bot einen Namen (z.B. `MeinTranskriptBot`)
4. Gib ihm einen Username (muss auf `bot` enden, z.B. `mein_transkript_bot`)
5. Du erhältst einen **Token** – z.B.:
   ```
   7412345678:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. Diesen Token sicher aufbewahren!

---

## Schritt 2: Lokal testen (optional)

### Voraussetzungen
- Python 3.10+
- ffmpeg installiert ([ffmpeg.org](https://ffmpeg.org/download.html))

### Installation
```bash
# Projektordner öffnen
cd telegram-yt-bot

# Abhängigkeiten installieren
pip install -r requirements.txt

# .env Datei erstellen
cp .env.example .env
# Dann .env öffnen und TELEGRAM_BOT_TOKEN eintragen

# Bot starten
python bot.py
```

---

## Schritt 3: Deployment auf Railway.app (kostenlos)

Railway bietet **500 Stunden/Monat kostenlos** – perfekt für einen Bot.

### 3.1 – Repository auf GitHub hochladen

1. Erstelle ein neues Repository auf [github.com](https://github.com)
2. Lade die Dateien hoch:
   - `bot.py`
   - `requirements.txt`
   - `Dockerfile`
   - `.env.example` (NICHT die echte `.env`!)

```bash
git init
git add bot.py requirements.txt Dockerfile .env.example
git commit -m "Initial commit"
git remote add origin https://github.com/DEIN_USERNAME/telegram-yt-bot.git
git push -u origin main
```

### 3.2 – Railway Projekt erstellen

1. Gehe zu [railway.app](https://railway.app) → mit GitHub einloggen
2. Klicke **"New Project"** → **"Deploy from GitHub repo"**
3. Wähle dein Repository aus
4. Railway erkennt das `Dockerfile` automatisch

### 3.3 – Umgebungsvariablen setzen

1. Im Railway-Dashboard: Klicke auf deinen Service
2. Gehe zu **"Variables"** (oben)
3. Klicke **"New Variable"** und füge hinzu:

| Variable | Wert |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Dein Token von BotFather |
| `WHISPER_MODEL` | `base` (oder `small` für mehr Genauigkeit) |

4. Klicke **"Deploy"** → Der Bot startet automatisch!

### 3.4 – Bot testen

1. Öffne Telegram → Suche nach deinem Bot-Username
2. Sende `/start`
3. Sende einen YouTube-Link, z.B.:
   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

---

## Alternative: Deployment auf Render.com

Falls Railway nicht funktioniert:

1. Gehe zu [render.com](https://render.com) → kostenloses Konto
2. **"New Web Service"** → GitHub Repo verbinden
3. Einstellungen:
   - **Runtime:** Docker
   - **Instance Type:** Free
4. Umgebungsvariablen unter **"Environment"** eintragen
5. **"Create Web Service"** klicken

---

## Bot-Befehle

| Befehl | Funktion |
|---|---|
| `/start` | Willkommensnachricht |
| `/help` | Hilfe & Anleitung |
| `/model` | Zeigt das aktuelle Whisper-Modell |

---

## Whisper Modelle – Übersicht

| Modell | Größe | Geschwindigkeit | Genauigkeit |
|---|---|---|---|
| `tiny` | 39 MB | ⚡⚡⚡ Sehr schnell | ⭐ |
| `base` | 74 MB | ⚡⚡ Schnell | ⭐⭐ ✅ Empfohlen |
| `small` | 244 MB | ⚡ Mittel | ⭐⭐⭐ |
| `medium` | 769 MB | 🐢 Langsam | ⭐⭐⭐⭐ |
| `large` | 1.5 GB | 🐢🐢 Sehr langsam | ⭐⭐⭐⭐⭐ |

> **Empfehlung für den Anfang:** `base` – gute Balance aus Geschwindigkeit und Genauigkeit.

---

## Fehlerbehebung

**Bot antwortet nicht:**
- Prüfe ob `TELEGRAM_BOT_TOKEN` korrekt gesetzt ist
- Schau in die Logs: Railway Dashboard → Logs

**"Download Error":**
- Das Video könnte privat, altersbeschränkt oder geografisch gesperrt sein

**Transkription sehr langsam:**
- Wechsle zu `WHISPER_MODEL=tiny` für schnellere Ergebnisse

---

## Projektstruktur

```
telegram-yt-bot/
├── bot.py              # Haupt-Bot-Code
├── requirements.txt    # Python-Abhängigkeiten
├── Dockerfile          # Container-Konfiguration
└── .env.example        # Beispiel für Umgebungsvariablen
```
