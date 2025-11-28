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
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    libmysqlclient-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (can be overridden in Kubernetes)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

