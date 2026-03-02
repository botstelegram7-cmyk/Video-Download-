FROM python:3.11-slim-bookworm

LABEL maintainer="@Xioqui_Xan & @TechnicalSerena"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg wget curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/cookies /app/data /tmp/downloads /tmp/cookies

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV DOWNLOAD_DIR=/tmp/downloads
ENV DATABASE_PATH=/app/data/bot.db

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

EXPOSE 8080

CMD ["python", "/app/bot.py"]
