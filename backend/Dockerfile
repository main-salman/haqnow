FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and document processing
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

# Install Python dependencies (optimized for speed)
COPY requirements.txt requirements-rag.txt ./
# Use pre-built wheels and install in parallel where possible
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    pip install --no-cache-dir --prefer-binary sentence-transformers>=2.2.2,<3.0.0

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (can be overridden in Kubernetes)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

