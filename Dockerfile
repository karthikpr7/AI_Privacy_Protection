FROM python:3.11-slim

# Install Tesseract OCR and required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency file first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create required runtime directories
RUN mkdir -p uploads outputs/protected outputs/reports

# Render provides the PORT environment variable.
# Gunicorn listens on 0.0.0.0:10000 by default through Render,
# so use the PORT variable explicitly.
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} app:app