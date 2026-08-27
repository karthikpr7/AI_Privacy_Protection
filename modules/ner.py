import spacy
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "privacy_ner_100k"
    / "best"
)


# =========================================================
# LOAD TRAINED MODEL
# =========================================================

print("=" * 70)
print("LOADING PRIVACY NER MODEL")
print("=" * 70)

print()
print("Model path:")
print(MODEL_PATH)

if not MODEL_PATH.exists():

    raise FileNotFoundError(
        f"Trained NER model not found:\n{MODEL_PATH}"
    )

nlp = spacy.load(
    MODEL_PATH
)

print()
print("100K NER model loaded successfully.")

print()
print("=" * 70)


# =========================================================
# NER DETECTION
# =========================================================

def detect_ner_pii(text):
    """
    Detect PII using the trained spaCy NER model.

    Returns a list of dictionaries containing:
        label
        value
        start
        end
        source
    """

    if not isinstance(
        text,
        str
    ) or not text.strip():

        return []

    doc = nlp(
        text
    )

    results = []

    for entity in doc.ents:

        results.append(
            {
                "label": entity.label_,
                "value": entity.text,
                "start": entity.start_char,
                "end": entity.end_char,
                "source": "ner"
            }
        )

    return results


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    sample_text = (
        "Contact Rahul Sharma at "
        "rahul.sharma@gmail.com. "
        "My phone number is +91 9876543210. "
        "My PAN is ABCDE1234F. "
        "My Aadhaar is 1234 5678 9012."
    )

    print()
    print("=" * 70)
    print("100K NER MODULE TEST")
    print("=" * 70)

    print()
    print("Input:")
    print(sample_text)

    print()
    print("NER DETECTIONS")
    print("-" * 70)

    results = detect_ner_pii(
        sample_text
    )

    if not results:

        print(
            "No entities detected."
        )

    else:

        for result in results:

            print(
                f"{result['label']:<20} "
                f"{result['value']:<30} "
                f"{result['source']:<10} "
                f"({result['start']}, {result['end']})"
            )

    print()
    print("=" * 70)
    print("100K NER MODULE TEST COMPLETED")
    print("=" * 70)