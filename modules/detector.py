from modules.combine_results import detect_pii
from modules.risk_analyzer import calculate_risk
from modules.masking import mask_detections
from modules.report_generator import generate_report

def analyze_text(text, document_name="Text Input"):
    """
    Complete privacy analysis.

    Pipeline:
        Text
        ↓
        NER + Regex
        ↓
        Deduplication
        ↓
        Risk analysis
        ↓
        Partial masking
    """

    if not isinstance(text, str) or not text.strip():

        return {
            "detections": [],
            "risk": {
                "score": 0,
                "level": "LOW",
                "total_detections": 0,
                "weighted_total": 0,
            },
            "masked_text": text if isinstance(text, str) else "",
        }

    # -------------------------------------------------------
    # 1. Detect PII
    # -------------------------------------------------------

    detections = detect_pii(text)

    # -------------------------------------------------------
    # 2. Calculate risk
    # -------------------------------------------------------

    risk = calculate_risk(detections)

    # -------------------------------------------------------
    # 3. Partially mask detected PII
    # -------------------------------------------------------

    masked_text = mask_detections(
        text,
        detections
    )

    report = generate_report(
    {
        "detections": detections,
        "risk": risk,
        "masked_text": masked_text
    },
    document_name=document_name
)

    return {
        "detections": detections,
        "risk": risk,
        "masked_text": masked_text,
        "report": report,
    }


if __name__ == "__main__":

    sample_text = (
        "Contact Rahul Sharma at "
        "rahul.sharma@gmail.com. "
        "My phone number is +91 9876543210. "
        "My PAN is ABCDE1234F. "
        "My Aadhaar is 1234 5678 9012. "
        "My card number is 4111 1111 1111 1111."
    )

    print("=" * 70)
    print("COMPLETE PRIVACY ANALYSIS TEST")
    print("=" * 70)

    print()
    print("ORIGINAL TEXT")
    print("-" * 70)
    print(sample_text)

    result = analyze_text(sample_text)

    print()
    print("DETECTED PII")
    print("-" * 70)

    for detection in result["detections"]:

        print(
            f"{detection['label']:<20} "
            f"{detection['value']:<30} "
            f"{detection['source']:<10}"
        )

    print()
    print("RISK ANALYSIS")
    print("-" * 70)

    print(
        "Score:",
        result["risk"]["score"],
        "/ 100"
    )

    print(
        "Level:",
        result["risk"]["level"]
    )

    print(
        "Total detections:",
        result["risk"]["total_detections"]
    )

    print()
    print("PARTIALLY MASKED TEXT")
    print("-" * 70)
    print(result["masked_text"])

    print()
    print("PRIVACY REPORT")
    print("-" * 70)
    print(result["report"])

    print()
    print("=" * 70)
    print("COMPLETE PRIVACY ANALYSIS COMPLETED")
    print("=" * 70)