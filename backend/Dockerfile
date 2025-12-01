# Fast app image - uses pre-built base with all dependencies
# Build time: ~10 seconds (just copies code)
FROM ghcr.io/main-salman/backend-base:latest

WORKDIR /app

# Only copy application code (dependencies already in base)
COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
