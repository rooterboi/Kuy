# ============================================================
#  Music Bot - Render.com uchun Dockerfile (FFmpeg + yt-dlp)
# ============================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Tizim paketlari: ffmpeg (audio/video), git, curl (healthcheck), build-essential (kerak bo'lsa wheel build)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg git curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN mkdir -p data tmp logs

# Render PORT o'zgaruvchisini o'zi beradi (health-check server shu portda ishlaydi)
ENV PORT=10000
EXPOSE 10000

HEALTHCHECK --interval=60s --timeout=5s --start-period=30s \
    CMD curl -fs http://localhost:${PORT}/health || exit 1

CMD ["python", "bot.py"]
