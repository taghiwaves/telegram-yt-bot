FROM python:3.11-slim

# FFmpeg installieren (wird von Whisper + yt-dlp benötigt)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir setuptools wheel
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

COPY bot.py .

CMD ["python", "bot.py"]
