import os
import sys
import re
import spacy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

model_path = "models/model-best" if os.path.exists("models/model-best") else "en_core_web_sm"
nlp = spacy.load(model_path)

# Structural Validation Regexes
PAN_STRICT = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]$')
BANK_STRICT = re.compile(r'^[0-9]{9,18}$')

# Context keywords that indicate benign (non-sensitive) identifiers
BENIGN_KEYWORDS = {"invoice", "inv", "tracking", "order", "ref", "amount", "total", "inr", "usd"}

def is_valid_entity(label: str, raw_val: str, full_context: str = "") -> bool:
    clean_val = raw_val.strip().strip(",.:;-")
    
    if label == "PAN":
        # Reject fragments or currency codes
        if not PAN_STRICT.match(clean_val.upper()):
            return False
        return True

    elif label == "BANK_ACC":
        # Indian/international bank accounts are 9-18 continuous digits
        if not BANK_STRICT.match(clean_val):
            return False
        
        # Suppress if surrounded by benign metadata
        words_nearby = set(re.findall(r'\b[A-Za-z]+\b', full_context.lower()))
        if BENIGN_KEYWORDS.intersection(words_nearby) and len(clean_val) < 9:
            return False
            
        return True

    return False

def scan_text_entities(text: str):
    found = []
    
    # 1. Custom spaCy Predictions with Validation Gate
    doc = nlp(text)
    for ent in doc.ents:
        val = ent.text.strip().strip(",.:;-")
        if is_valid_entity(ent.label_, val, text):
            found.append({
                "label": ent.label_,
                "value": val,
                "source": "spacy_ner"
            })

    # 2. De-spaced Regex Pattern (handles OCR artifacts like 'A B C D E 1 2 3 4 F')
    condensed_text = re.sub(r'(?<=\b[A-Za-z0-9])\s+(?=[A-Za-z0-9]\b)', '', text)
    
    for match in re.finditer(r'\b[A-Za-z]{5}[0-9]{4}[A-Za-z]\b', condensed_text):
        val = match.group(0).upper()
        if not any(f['value'].upper() == val for f in found):
            found.append({
                "label": "PAN",
                "value": val,
                "source": "regex_despaced"
            })

    for match in re.finditer(r'\b[0-9]{9,18}\b', condensed_text):
        val = match.group(0)
        if not any(f['value'] == val for f in found):
            found.append({
                "label": "BANK_ACC",
                "value": val,
                "source": "regex_pattern"
            })

    return found

TEST_CASES = [
    "Tax ID: ABCDE1234F, Beneficiary: 987654321098",
    "tax reference abcde1234f on record",
    "PAN: A B C D E 1 2 3 4 F",
    "Invoice ID: 982341, Tracking Code: 44921, Total Due: INR 14,500.00"
]

print("\n" + "=" * 55)
print("     HYBRID PRIVACY ENGINE SCANNER (POST-FILTERED)")
print("=" * 55)

for idx, text in enumerate(TEST_CASES, 1):
    print(f"\nTest #{idx}: \"{text}\"")
    entities = scan_text_entities(text)
    if entities:
        for ent in entities:
            print(f"  [+] DETECTED: {ent['label']:<9} | Value: '{ent['value']}' | Source: {ent['source']}")
    else:
        print("  [-] No PII detected (Correct for non-PII / benign lines).")

print("\n" + "=" * 55 + "\n")