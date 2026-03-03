# ╔══════════════════════════════════════════════════╗
# ║   SERENA DOWNLOADER BOT — Dockerfile             ║
# ║   Render Web Service · Docker compatible         ║
# ╚══════════════════════════════════════════════════╝
FROM python:3.11-slim

# System deps: ffmpeg for video processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY . .

# Create runtime dirs (also created in config.py but just in case)
RUN mkdir -p /tmp/serena_dl /tmp/serena_db /tmp/cookies /app/cookies

# Render sets PORT automatically; default 10000
EXPOSE 10000

CMD ["python", "-u", "bot.py"]
