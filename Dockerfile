# ╔══════════════════════════════════════════╗
# ║   🐳  D O C K E R F I L E               ║
# ║   SerenaDownloaderBot                   ║
# ╚══════════════════════════════════════════╝

FROM python:3.11-slim-bookworm

# ── Labels ──
LABEL maintainer="@Xioqui_Xan & @TechnicalSerena"
LABEL description="Serena Universal Downloader Bot"

# ── System Dependencies ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    curl \
    ca-certificates \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Working Directory ──
WORKDIR /app

# ── Python Dependencies ──
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Create directories ──
RUN mkdir -p /app/cookies /app/data /tmp/downloads

# ── Copy Source ──
COPY . .

# ── Environment Defaults ──
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOWNLOAD_DIR=/tmp/downloads
ENV DATABASE_PATH=/app/data/bot.db

# ── Health check ──
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# ── Expose Port ──
EXPOSE 8080

# ── Entry Point ──
CMD ["python", "bot.py"]
