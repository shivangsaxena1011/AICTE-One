# AICTE ONE - Enterprise Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data assets
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Set environment defaults
ENV HOST=0.0.0.0 \
    PORT=8000 \
    DATABASE_URL=sqlite:///./aicte_governance.db

# Run FastAPI production server
CMD ["python", "backend/main.py"]
