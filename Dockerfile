# syntax=docker/dockerfile:1.7

# ---------- builder ----------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt ./
RUN pip install --prefix=/install -r requirements.txt

# ---------- runtime ----------
FROM python:3.11-slim AS runtime

# CI 在上 tag 時傳入 (見 .github/workflows/release.yml)；本機 build 則顯示 dev
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/usr/local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
        tzdata \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home /app appuser

COPY --from=builder /install /usr/local

WORKDIR /app
COPY --chown=appuser:app . /app

RUN mkdir -p /app/data/raw /app/data/processed \
    && chown -R appuser:app /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/main.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
