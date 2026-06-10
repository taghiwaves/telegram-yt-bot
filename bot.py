import os
import re
import asyncio
import tempfile
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import yt_dlp
import whisper

# Logging einrichten
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Whisper-Modell laden (beim ersten Start wird es heruntergeladen)
# Modelle: tiny, base, small, medium, large (größer = genauer, aber langsamer)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
model = None


def load_whisper_model():
    global model
    if model is None:
        logger.info(f"Lade Whisper-Modell: {WHISPER_MODEL}")
        model = whisper.load_model(WHISPER_MODEL)
        logger.info("Whisper-Modell geladen.")
    return model


def is_youtube_url(url: str) -> bool:
    pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
    return bool(re.match(pattern, url))


def download_audio(url: str, output_path: str) -> str:
    """Lädt das Audio eines YouTube-Videos herunter."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path + "/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info["id"]
        title = info.get("title", "Unbekannt")
        audio_file = os.path.join(output_path, f"{video_id}.mp3")
        return audio_file, title


def transcribe_audio(audio_path: str) -> str:
    """Transkribiert eine Audiodatei mit Whisper."""
    whisper_model = load_whisper_model()
    result = whisper_model.transcribe(audio_path)
    return result["text"].strip()


# ─── Telegram-Handler ────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Willkommen beim YouTube Transkriptions-Bot!*\n\n"
        "Sende mir einfach einen YouTube-Link und ich extrahiere den Text aus dem Video.\n\n"
        "📌 *Befehle:*\n"
        "/start – Diese Nachricht\n"
        "/help – Hilfe & Info\n"
        "/model – Aktuelles Whisper-Modell anzeigen",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *So benutzt du den Bot:*\n\n"
        "1. Kopiere einen YouTube-Link\n"
        "2. Sende ihn in diesen Chat\n"
        "3. Warte kurz – der Bot lädt das Audio herunter und transkribiert es\n"
        "4. Du erhältst den vollständigen Rohtext\n\n"
        "⚠️ *Hinweise:*\n"
        "• Lange Videos dauern entsprechend länger\n"
        "• Der Bot funktioniert am besten mit klar gesprochenem Audio\n"
        "• Unterstützte Sprachen: alle (Whisper erkennt automatisch)\n\n"
        f"🤖 Aktuelles Modell: `{WHISPER_MODEL}`",
        parse_mode="Markdown",
    )


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 Aktuell verwendetes Whisper-Modell: `{WHISPER_MODEL}`\n\n"
        "Verfügbare Modelle (über Umgebungsvariable `WHISPER_MODEL`):\n"
        "• `tiny` – Sehr schnell, weniger genau\n"
        "• `base` – Gute Balance ✅ (Standard)\n"
        "• `small` – Genauer, etwas langsamer\n"
        "• `medium` – Sehr genau\n"
        "• `large` – Beste Qualität, langsam",
        parse_mode="Markdown",
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_youtube_url(url):
        await update.message.reply_text(
            "❌ Das ist kein gültiger YouTube-Link.\n"
            "Bitte sende einen Link im Format:\n"
            "`https://www.youtube.com/watch?v=...`\n"
            "oder `https://youtu.be/...`",
            parse_mode="Markdown",
        )
        return

    status_msg = await update.message.reply_text(
        "⏳ *Schritt 1/3:* Link erkannt, lade Audio herunter..."
        , parse_mode="Markdown"
    )

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Audio herunterladen
            await status_msg.edit_text(
                "⏳ *Schritt 1/3:* Audio wird heruntergeladen...",
                parse_mode="Markdown",
            )
            audio_path, title = await asyncio.to_thread(download_audio, url, tmpdir)

            await status_msg.edit_text(
                f"✅ *Schritt 1/3:* Audio heruntergeladen\n"
                f"🎬 Video: _{title}_\n\n"
                f"⏳ *Schritt 2/3:* Transkribiere mit Whisper ({WHISPER_MODEL})...",
                parse_mode="Markdown",
            )

            # Transkribieren
            text = await asyncio.to_thread(transcribe_audio, audio_path)

            await status_msg.edit_text(
                f"✅ *Schritt 2/3:* Transkription abgeschlossen\n\n"
                f"⏳ *Schritt 3/3:* Sende Text...",
                parse_mode="Markdown",
            )

        # Text senden (Telegram-Limit: 4096 Zeichen pro Nachricht)
        header = f"📄 *Transkript: {title}*\n\n"
        full_text = header + text

        chunk_size = 4000
        if len(full_text) <= chunk_size:
            await update.message.reply_text(full_text, parse_mode="Markdown")
        else:
            # Ersten Teil mit Header
            await update.message.reply_text(full_text[:chunk_size], parse_mode="Markdown")
            # Rest in Blöcken senden
            for i in range(chunk_size, len(full_text), chunk_size):
                await update.message.reply_text(
                    full_text[i : i + chunk_size], parse_mode="Markdown"
                )

        await status_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download-Fehler: {e}")
        await status_msg.edit_text(
            "❌ *Fehler beim Herunterladen.*\n\n"
            "Mögliche Ursachen:\n"
            "• Video ist privat oder altersbeschränkt\n"
            "• Video existiert nicht mehr\n"
            "• Geografische Einschränkung",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Unbekannter Fehler: {e}")
        await status_msg.edit_text(
            f"❌ *Ein Fehler ist aufgetreten:*\n`{str(e)}`",
            parse_mode="Markdown",
        )


# ─── Bot starten ─────────────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN ist nicht gesetzt!")

    # Whisper beim Start vorladen
    load_whisper_model()

    app = Application.builder().token(token).build()

    # Befehle registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    logger.info("✅ Bot läuft...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
