# Multi-stage build for faster rebuilds
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    tesseract-ocr-rus \
    tesseract-ocr-chi-sim \
    tesseract-ocr-jpn \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    pkg-config \
    libmariadb-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Dependencies stage (cached unless requirements change)
FROM base AS dependencies
COPY requirements.txt requirements-rag.txt ./
# Install dependencies with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary -r requirements.txt && \
    pip install --prefer-binary sentence-transformers>=2.2.2,<3.0.0

# Application stage (only rebuilds when code changes)
FROM dependencies AS app
COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
