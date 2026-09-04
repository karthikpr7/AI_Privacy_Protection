# ============================================================
# RISK ANALYZER
# ============================================================

# Only approved sensitive information contributes to risk.
RISK_WEIGHTS = {
    "PAN": 25,
    "AADHAAR": 25,
    "PASSPORTNUM": 20,
    "DRIVERLICENSENUM": 20,
    "VOTERID": 20,
    "BANK_ACCOUNT": 25,
    "BANKACCOUNT": 25,
    "IFSC": 15,
    "CREDITCARDNUMBER": 25,
    "DEBITCARDNUMBER": 25,
    "UPIID": 20,
    "PASSWORD": 30,
    "APIKEY": 30,
    "API_KEY": 30,
    "ACCESSTOKEN": 30,
    "ACCESS_TOKEN": 30,
    "SECRETKEY": 30,
    "SECRET_KEY": 30,
}


def normalize_label(label):
    """
    Convert equivalent labels into the labels
    used by the risk system.
    """

    label = str(label).strip().upper()

    aliases = {
        "BANKACCOUNT": "BANK_ACCOUNT",
        "VOTERIDNUM": "VOTERID",
        "DEBITCARDNUMBER": "CREDITCARDNUMBER",
        "API_KEY": "APIKEY",
        "ACCESS_TOKEN": "ACCESSTOKEN",
        "SECRET_KEY": "SECRETKEY",
    }

    return aliases.get(label, label)


def get_risk_level(score):
    """
    Convert numerical risk score into a risk level.
    """

    if score <= 25:
        return "LOW"

    if score <= 50:
        return "MEDIUM"

    if score <= 75:
        return "HIGH"

    return "CRITICAL"


def calculate_risk(detections):
    """
    Calculate privacy risk using only approved
    sensitive information.

    Unknown or unwanted labels contribute 0 risk.
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

        label = normalize_label(
            detection.get("label", "")
        )

        # Unknown labels have ZERO risk.
        weight = RISK_WEIGHTS.get(label, 0)

        weighted_total += weight

    # Keep score between 0 and 100.
    score = min(weighted_total, 100)

    level = get_risk_level(score)

    return {
        "score": score,
        "level": level,
        "total_detections": len(detections),
        "weighted_total": weighted_total,
    }