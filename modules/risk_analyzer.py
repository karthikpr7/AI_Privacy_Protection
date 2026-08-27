# ============================================================
# Risk Analyzer
# ============================================================

# Project-defined risk weights.
# These are not official privacy standards.

RISK_WEIGHTS = {

    # Lower-risk contextual information
    "GIVENNAME": 5,
    "SURNAME": 5,
    "TITLE": 5,
    "AGE": 5,
    "GENDER": 5,
    "SEX": 5,

    # Moderate-risk contact/location information
    "EMAIL": 10,
    "TELEPHONENUM": 10,
    "CITY": 8,
    "STREET": 10,
    "BUILDINGNUM": 10,
    "ZIPCODE": 8,

    # Higher-risk identification information
    "DATE": 8,
    "DRIVERLICENSENUM": 20,
    "PASSPORTNUM": 20,
    "IDCARDNUM": 20,
    "TAXNUM": 20,
    "SOCIALNUM": 20,

    # Critical financial / highly sensitive identifiers
    "PAN": 25,
    "AADHAAR": 25,
    "BANK_ACCOUNT": 25,
    "CREDITCARDNUMBER": 25,
    "IFSC": 15,
}


# ============================================================
# Risk levels
# ============================================================

def get_risk_level(score):
    """
    Convert a 0-100 risk score into a project-defined level.
    """

    if score <= 25:
        return "LOW"

    if score <= 50:
        return "MEDIUM"

    if score <= 75:
        return "HIGH"

    return "CRITICAL"


# ============================================================
# Calculate risk
# ============================================================

def calculate_risk(detections):
    """
    Calculate a risk score from detected PII.

    The raw sum of entity weights is capped at 100.

    Parameters
    ----------
    detections : list
        List of PII detection dictionaries.

    Returns
    -------
    dict
        Risk score, risk level, and supporting information.
    """

    if not detections:
        return {
            "score": 0,
            "level": "LOW",
            "total_detections": 0,
            "weighted_total": 0,
        }

    weighted_total = 0

    for detection in detections:

        label = detection.get("label")

        weight = RISK_WEIGHTS.get(
            label,
            5
        )

        weighted_total += weight

    # Keep the final score within 0-100.
    score = min(
        weighted_total,
        100
    )

    level = get_risk_level(score)

    return {
        "score": score,
        "level": level,
        "total_detections": len(detections),
        "weighted_total": weighted_total,
    }


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    sample_detections = [

        {
            "label": "GIVENNAME",
            "value": "Rahul Sharma",
            "start": 0,
            "end": 12,
        },

        {
            "label": "EMAIL",
            "value": "rahul@gmail.com",
            "start": 20,
            "end": 36,
        },

        {
            "label": "PAN",
            "value": "ABCDE1234F",
            "start": 45,
            "end": 55,
        },
    ]

    result = calculate_risk(
        sample_detections
    )

    print("=" * 70)
    print("RISK ANALYZER TEST")
    print("=" * 70)

    print()
    print("Detections:")
    print(
        result["total_detections"]
    )

    print(
        "Weighted total:",
        result["weighted_total"]
    )

    print(
        "Risk score:",
        result["score"],
        "/ 100"
    )

    print(
        "Risk level:",
        result["level"]
    )

    print()
    print("=" * 70)
    print("RISK ANALYZER TEST COMPLETED")
    print("=" * 70)