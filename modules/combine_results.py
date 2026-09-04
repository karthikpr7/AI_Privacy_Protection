import re
from modules.ner import detect_ner_pii
from modules.regex_detector import detect_regex_pii


# ============================================================
# ONLY THESE LABELS ARE ALLOWED TO BE PRIVACY THREATS
# ============================================================

ALLOWED_SENSITIVE_LABELS = {
    "PAN",
    "AADHAAR",
    "PASSPORTNUM",
    "DRIVERLICENSENUM",
    "VOTERID",
    "VOTERIDNUM",
    "BANK_ACCOUNT",
    "BANKACCOUNT",
    "IFSC",
    "CREDITCARDNUMBER",
    "DEBITCARDNUMBER",
    "UPIID",
    "PASSWORD",
    "APIKEY",
    "API_KEY",
    "ACCESSTOKEN",
    "ACCESS_TOKEN",
    "SECRETKEY",
    "SECRET_KEY",
}


# ============================================================
# LABEL NORMALIZATION
# ============================================================

LABEL_ALIASES = {
    "BANKACCOUNT": "BANK_ACCOUNT",
    "DEBITCARDNUMBER": "CREDITCARDNUMBER",
    "VOTERIDNUM": "VOTERID",
    "API_KEY": "APIKEY",
    "ACCESS_TOKEN": "ACCESSTOKEN",
    "SECRET_KEY": "SECRETKEY",
}


def normalize_label(label):
    """
    Convert equivalent labels into one standard label.
    Unknown labels are returned unchanged.
    """
    label = str(label).strip().upper()
    return LABEL_ALIASES.get(label, label)


# ============================================================
# VALIDATE NER SENSITIVE VALUES
# ============================================================

def is_valid_ner_sensitive_value(label, value):
    """
    Extra validation for NER detections.

    The trained NER model is treated as a helper.
    Structured sensitive identifiers must also match
    their expected format.

    This prevents ordinary values such as:

        DOC2026
        EMP2026
        REF123456

    from being incorrectly classified as PASSPORTNUM.
    """

    if not value:
        return False

    value = str(value).strip()

    # --------------------------------------------------------
    # PAN
    # Example: ABCDE1234F
    # --------------------------------------------------------

    if label == "PAN":

        return bool(
            re.fullmatch(
                r"[A-Z]{5}[0-9]{4}[A-Z]",
                value.upper()
            )
        )

    # --------------------------------------------------------
    # AADHAAR
    # Example: 1234 5678 9012
    # --------------------------------------------------------

    if label == "AADHAAR":

        digits = re.sub(
            r"\D",
            "",
            value
        )

        return len(digits) == 12

    # --------------------------------------------------------
    # PASSPORT
    # Example: P1234567
    # --------------------------------------------------------

    if label == "PASSPORTNUM":

        return bool(
            re.fullmatch(
                r"[A-Z][0-9]{7}",
                value.upper()
            )
        )

    # --------------------------------------------------------
    # DRIVING LICENCE
    # --------------------------------------------------------

    if label == "DRIVERLICENSENUM":

        compact = re.sub(
            r"\s+",
            "",
            value.upper()
        )

        return (
            len(compact) >= 10
            and any(
                character.isalpha()
                for character in compact
            )
            and any(
                character.isdigit()
                for character in compact
            )
        )

    # --------------------------------------------------------
    # VOTER ID
    # Example: ABC1234567
    # --------------------------------------------------------

    if label == "VOTERID":

        return bool(
            re.fullmatch(
                r"[A-Z]{3}[0-9]{7}",
                value.upper()
            )
        )

    # --------------------------------------------------------
    # IFSC
    # Example: SBIN0001234
    # --------------------------------------------------------

    if label == "IFSC":

        compact = value.replace(
            " ",
            ""
        ).upper()

        return bool(
            re.fullmatch(
                r"[A-Z]{4}0[A-Z0-9]{6}",
                compact
            )
        )

    # --------------------------------------------------------
    # CREDIT / DEBIT CARD
    # --------------------------------------------------------

    if label in {
        "CREDITCARDNUMBER",
        "DEBITCARDNUMBER"
    }:

        digits = re.sub(
            r"\D",
            "",
            value
        )

        return len(digits) in {
            13,
            14,
            15,
            16,
            17,
            18,
            19
        }

    # --------------------------------------------------------
    # BANK ACCOUNT
    # --------------------------------------------------------

    if label in {
        "BANK_ACCOUNT",
        "BANKACCOUNT"
    }:

        digits = re.sub(
            r"\D",
            "",
            value
        )

        return 8 <= len(digits) <= 18

    # --------------------------------------------------------
    # UPI ID
    # --------------------------------------------------------

    if label in {
        "UPIID",
        "UPI_ID"
    }:

        return bool(
            re.fullmatch(
                r"[A-Za-z0-9._-]+@[A-Za-z0-9._-]+",
                value
            )
        )

    # --------------------------------------------------------
    # Password / API Key / Access Token / Secret Key
    #
    # These cannot reliably be validated using one simple
    # format, so allow approved NER predictions.
    # --------------------------------------------------------

    if label in {
        "PASSWORD",
        "APIKEY",
        "ACCESSTOKEN",
        "SECRETKEY"
    }:
        return True

    return False

# ============================================================
# OVERLAP CHECK
# ============================================================

def ranges_overlap(first, second):
    return (
        first["start"] < second["end"]
        and second["start"] < first["end"]
    )


# ============================================================
# FILTER NER RESULTS
# ============================================================

def filter_ner_results(ner_results):
    """
    NER is used only as a helper.

    Only approved sensitive labels are considered.

    Structured identifiers must also pass format
    validation to reduce false positives.
    """

    filtered = []

    for result in ner_results:

        label = normalize_label(
            result.get("label", "")
        )

        value = result.get(
            "value",
            ""
        )

        # ----------------------------------------------------
        # Only approved sensitive labels are allowed.
        # ----------------------------------------------------

        if label not in ALLOWED_SENSITIVE_LABELS:
            continue

        # ----------------------------------------------------
        # Validate the actual NER value.
        # ----------------------------------------------------

        if not is_valid_ner_sensitive_value(
            label,
            value
        ):
            continue

        filtered.append({
            **result,
            "label": label,
            "source": "ner"
        })

    return filtered


# ============================================================
# FILTER REGEX RESULTS
# ============================================================

def filter_regex_results(regex_results):
    """
    Regex detections are also restricted to the
    approved sensitive labels.
    """

    filtered = []

    for result in regex_results:

        label = normalize_label(result.get("label", ""))

        if label not in ALLOWED_SENSITIVE_LABELS:
            continue

        filtered.append({
            **result,
            "label": label,
            "source": "regex"
        })

    return filtered


# ============================================================
# COMBINE RESULTS
# ============================================================

def combine_results(ner_results, regex_results):

    # --------------------------------------------------------
    # First filter both sources.
    # --------------------------------------------------------

    filtered_regex = filter_regex_results(regex_results)
    filtered_ner = filter_ner_results(ner_results)

    # --------------------------------------------------------
    # REGEX HAS PRIORITY
    #
    # Regex patterns such as PAN, Aadhaar, card and IFSC
    # are validated formats.
    #
    # Therefore, if NER overlaps a regex detection,
    # keep the regex detection.
    # --------------------------------------------------------

    combined = list(filtered_regex)

    # --------------------------------------------------------
    # Add NER detections only when they don't overlap
    # an existing regex detection.
    # --------------------------------------------------------

    for ner_result in filtered_ner:

        overlap = any(
            ranges_overlap(ner_result, regex_result)
            for regex_result in combined
        )

        if overlap:
            continue

        combined.append(ner_result)

    # --------------------------------------------------------
    # Sort according to document position.
    # --------------------------------------------------------

    combined.sort(
        key=lambda item: (
            item["start"],
            item["end"]
        )
    )

    return combined


# ============================================================
# MAIN DETECTION FUNCTION
# ============================================================

def detect_pii(text):

    if not isinstance(text, str) or not text.strip():
        return []

    # Get NER detections.
    ner_results = detect_ner_pii(text)

    # Get regex detections.
    regex_results = detect_regex_pii(text)

    # Combine using strict privacy rules.
    return combine_results(
        ner_results,
        regex_results
    )