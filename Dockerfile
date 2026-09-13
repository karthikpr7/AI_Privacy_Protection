FROM python:3.11-slim

# Install system libraries, Tesseract OCR engine, and Linux system fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download small spaCy language model
RUN python -m spacy download en_core_web_sm

# Copy application files
COPY . .

# Match directory names with app.py
RUN mkdir -p uploads processed

EXPOSE 10000

# Run via Gunicorn binding to Render's injected PORT
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 app:app"]