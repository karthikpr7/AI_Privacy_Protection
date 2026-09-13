# PrivaSeal AI — Autonomous PII Privacy & Redaction Engine

PrivaSeal AI is an automated document privacy engine that detects, localizes, and redacts sensitive Personally Identifiable Information (PII) from vector PDFs and scanned image documents. Built with Flask, PyMuPDF, spaCy, and Tesseract OCR, the application runs inside an optimized Docker container designed for cloud deployment on platforms like Render.

---

## Key Capabilities

- **Multi-Format Processing:** Ingests native vector PDFs as well as scanned raster formats (`.png`, `.jpg`, `.jpeg`).
- **Precision Detection Engine:** Leverages spaCy Named Entity Recognition (NER) and targeted pattern matching to identify high-risk financial and identity credentials (PAN cards, Indian identity credentials, Bank Account numbers, Credit Cards).
- **Dual Masking Options:**
  - **Partial Mask:** Replaces sensitive digits with an auto-fitted asterisk format (`AB******4F`) that preserves typography, font scaling, and document baselines.
  - **Full Blackout:** Places solid vector redaction blocks over target bounding boxes.
- **Visual Scale Preservation:** Maps bounding boxes onto a 1:1 pixel/DPI coordinate system to eliminate aspect ratio distortion and font shifting.
- **Cyberpunk Dark UI:** High-contrast responsive interface styled with JetBrains Mono typography, status indicators, and mobile-first inspection viewports.

---

## Tech Stack

- **Backend:** Python 3.11, Flask, Gunicorn
- **Document & Image Processing:** PyMuPDF (`fitz`), Pillow, Tesseract OCR (`pytesseract`)
- **NLP & Parsing:** spaCy (`en_core_web_sm`), Regex Pattern Matchers
- **Frontend:** Vanilla JavaScript, HTML5 Canvas, PDF.js, Modern CSS3
- **Containerization & Hosting:** Docker, Render

---

## Architecture Overview

├── app.py                      # Flask routes, conversion, and lifecycle handling
├── Dockerfile                  # Production container setup (Tesseract, Linux fonts, Gunicorn)
├── requirements.txt            # Python dependencies
├── modules/
│   ├── privacy_engine.py       # PII identification via NER and regex
│   └── document_protector.py   # Baseline text rendering & canvas patching
├── static/
│   ├── css/style.css           # Cyberpunk-themed mobile-responsive stylesheet
│   └── js/app.js               # Canvas renderer, state manager, touch controls
└── templates/
└── index.html              # 3-step single-page application workflow


---

## Local Setup

### 1. Prerequisites
- Python 3.10+
- Tesseract OCR installed locally and added to system `PATH`
- Git

### 2. Installation
```powershell
# Clone the repository
git clone [https://github.com/karthikpr7/AI_Privacy_Protection.git](https://github.com/karthikpr7/AI_Privacy_Protection.git)
cd AI_Privacy_Protection

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Download spaCy small pipeline
python -m spacy download en_core_web_sm
3. Run the Development Server:
PowerShell:
python app.py

Open your browser at http://127.0.0.1:5000.

Production Deployment (Docker / Render)
The project includes a multi-stage Dockerfile pre-configured to install Tesseract binaries, system font packages (fonts-dejavu-core, fonts-liberation), and launch using Gunicorn on the port provided by the host environment:

Dockerfile
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 app:app"]

#Security & Privacy Notice
All file processing is performed server-side within the container boundary. Uploaded files and generated redacted assets are kept in ephemeral storage.