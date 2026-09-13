import os
import re
import spacy
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

MODEL_DIR = "models/model-best"
nlp = spacy.load(MODEL_DIR) if os.path.exists(MODEL_DIR) else spacy.load("en_core_web_sm")

# STRICT HIGH-SENSITIVITY PATTERNS
PATTERNS = {
    "CREDIT_CARD": re.compile(r'\b(?:\d{4}[-\s]){3}\d{4}\b|\b\d{16}\b'),
    "AADHAAR": re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b'),
    "PAN": re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', re.IGNORECASE),
    "BANK_ACC": re.compile(r'\b[0-9]{9,18}\b')
}

def extract_entities_from_text(text: str, page_num: int = 1):
    results = []

    # 1. Custom spaCy Predictions
    doc = nlp(text)
    for ent in doc.ents:
        val = ent.text.strip().strip(",.:;-")
        if ent.label_ == "PAN" and re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', val, re.I):
            results.append({"label": "PAN", "value": val, "page": page_num, "source": "spacy_ner"})
        elif ent.label_ == "BANK_ACC" and val.isdigit() and 9 <= len(val) <= 18:
            results.append({"label": "BANK_ACC", "value": val, "page": page_num, "source": "spacy_ner"})

    # 2. Pattern Matching in strict priority
    for label in ["CREDIT_CARD", "AADHAAR", "PAN", "BANK_ACC"]:
        pattern = PATTERNS[label]
        for match in pattern.finditer(text):
            val = match.group(0).strip()

            if any(val in r['value'] or r['value'] in val for r in results):
                continue

            if label == "BANK_ACC":
                prefix = text[max(0, match.start() - 15):match.start()].lower()
                if any(kw in prefix for kw in ["dl", "license", "licence", "ka", "mh", "dl-", "id:"]):
                    continue

            results.append({
                "label": label,
                "value": val,
                "page": page_num,
                "source": "pattern_matcher"
            })

    return results

def process_document(pdf_path: str):
    doc = fitz.open(pdf_path)
    all_detections = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1
        text = page.get_text("text")

        # Scanned Image Page: Run OCR to extract text
        if len(text.strip()) < 30:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img)

        detections = extract_entities_from_text(text, page_num=page_num)
        all_detections.extend(detections)

    doc.close()
    return all_detections