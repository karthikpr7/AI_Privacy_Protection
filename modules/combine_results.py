from modules.ner import detect_ner_pii
from modules.regex_detector import detect_regex_pii


def ranges_overlap(first, second):
    """Return True if two entity spans overlap."""

    return (
        first["start"] < second["end"]
        and second["start"] < first["end"]
    )

def is_contextual_false_positive(result):
    """
    Remove obvious NER false positives where the detected
    text contains a privacy-field keyword.
    """

    value = result["value"].strip().lower()

    false_positive_words = {
        "aadhaar",
        "pan",
        "email",
        "phone",
        "telephone",
        "mobile",
        "address",
        "account",
        "passport",
        "credit",
        "card",
        "ifsc",
        "bank",
    }

    words = value.split()

    # Exact match
    if value in false_positive_words:
        return True

    # Detect phrases such as:
    # "My Aadhaar"
    # "My email"
    # "Phone number"
    # "Bank account"
    if any(
        word in false_positive_words
        for word in words
    ):
        return True

    return False

def combine_results(ner_results, regex_results):
    """
    Combine NER and Regex detections.

    Regex detections have priority when both detectors
    identify overlapping text.
    """

    combined = []

    # -----------------------------------------------------
    # Add Regex results first
    # -----------------------------------------------------

    for result in regex_results:

        combined.append(
            {
                **result,
                "source": "regex"
            }
        )

    # -----------------------------------------------------
    # Add NER results when they do not overlap
    # -----------------------------------------------------

    for result in ner_results:

        if is_contextual_false_positive(result):
            continue

        overlap = any(
            ranges_overlap(result, existing)
            for existing in combined
        )

        if not overlap:
            combined.append(
                {
                    **result,
                    "source": "ner"
                }
            )

    # -----------------------------------------------------
    # Sort by position in text
    # -----------------------------------------------------

    combined.sort(
        key=lambda item: (
            item["start"],
            item["end"]
        )
    )

    return combined


def detect_pii(text):
    """
    Run both NER and Regex detection and return
    the deduplicated final PII results.
    """

    if not isinstance(text, str) or not text.strip():
        return []

    ner_results = detect_ner_pii(text)

    regex_results = detect_regex_pii(text)

    return combine_results(
        ner_results,
        regex_results
    )


if __name__ == "__main__":

    sample_text = (
        "Contact Rahul Sharma at "
        "rahul.sharma@gmail.com. "
        "My phone number is +91 9876543210. "
        "My PAN is ABCDE1234F."
    )

    print("=" * 70)
    print("COMBINED NER + REGEX TEST")
    print("=" * 70)

    print()
    print("Text:")
    print(sample_text)

    print()
    print("Detected PII:")
    print("-" * 70)

    results = detect_pii(sample_text)

    for result in results:

        print(
            f"{result['label']:<20} "
            f"{result['value']:<30} "
            f"{result['source']:<10} "
            f"({result['start']}, {result['end']})"
        )

    print()
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)