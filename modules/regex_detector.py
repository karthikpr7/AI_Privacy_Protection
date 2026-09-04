import re


# ============================================================
# BASIC PATTERNS
# ============================================================

PATTERNS = {

    "PAN": re.compile(
        r"(?<![A-Z0-9])[A-Z]{5}[0-9]{4}[A-Z](?![A-Z0-9])",
        re.IGNORECASE
    ),

    "CREDITCARDNUMBER": re.compile(
        r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"
    ),

    "AADHAAR": re.compile(
        r"(?<!\d)\d{4}(?:[\s-]\d{4}){2}(?!\d)"
    ),

    "IFSC": re.compile(
        r"(?<![A-Z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Z0-9])",
        re.IGNORECASE
    ),
}


# ============================================================
# CONTEXT PATTERNS
# ============================================================

BANK_ACCOUNT_CONTEXT = re.compile(
    r"(?i)"
    r"(?:bank\s+account|account|a/c)"
    r"(?:\s+number|\s+no\.?|\s*#)?"
    r"\s*[:\-]?\s*"
    r"(\d{9,18})"
)


PASSPORT_CONTEXT = re.compile(
    r"(?i)"
    r"passport"
    r"\s*(?:number|no\.?)?"
    r"\s*[:\-]?\s*"
    r"([A-Z][0-9]{7})"
)


DRIVING_LICENSE_CONTEXT = re.compile(
    r"(?i)"
    r"(?:driving\s+license|driving\s+licence|dl)"
    r"\s*(?:number|no\.?)?"
    r"\s*[:\-]?\s*"
    r"([A-Z0-9]{2,4}\s?[A-Z0-9]{2,4}\s?[A-Z0-9]{4,14})"
)


VOTER_CONTEXT = re.compile(
    r"(?i)"
    r"(?:voter\s*id|voter)"
    r"\s*(?:number|no\.?)?"
    r"\s*[:\-]?\s*"
    r"([A-Z]{3}[0-9]{7})"
)


UPI_CONTEXT = re.compile(
    r"(?i)"
    r"(?:upi\s*(?:id|number)?|upi)"
    r"\s*[:\-]?\s*"
    r"([A-Za-z0-9._-]+@[A-Za-z][A-Za-z0-9._-]*)"
)


# Credit card specifically after "Credit Card Number".
# This lets us handle OCR mistakes without weakening
# the general credit-card detector.
CREDIT_CARD_CONTEXT = re.compile(
    r"(?i)"
    r"credit\s+card"
    r"\s*(?:number|no\.?)?"
    r"\s*[:\-]?\s*"
    r"([0-9O\s-]{13,25})"
)


# IFSC specifically after "IFSC Code".
IFSC_CONTEXT = re.compile(
    r"(?i)"
    r"ifsc"
    r"\s*(?:code|number|no\.?)?"
    r"\s*[:\-]?\s*"
    r"([A-Z0-9]{11})"
)


# ============================================================
# VALIDATION
# ============================================================

def digits_only(value):
    return re.sub(r"\D", "", str(value))


def luhn_check(number):

    digits = digits_only(number)

    if not digits:
        return False

    total = 0

    for index, digit in enumerate(reversed(digits)):

        value = int(digit)

        if index % 2 == 1:

            value *= 2

            if value > 9:
                value -= 9

        total += value

    return total % 10 == 0


def validate_card(value):

    digits = digits_only(value)

    if not 13 <= len(digits) <= 19:
        return False

    return luhn_check(digits)


def correct_ocr_card(value):

    """
    Correct common OCR mistakes in a credit-card value.

    This is used ONLY when the text occurs after
    'Credit Card Number'.

    Example:

    4111 1111 11114 1111
                  ^
                  extra OCR digit

    becomes:

    4111 1111 1111 1111
    """

    original = str(value).strip()

    # OCR often reads O as 0.
    normalized = original.replace("O", "0").replace("o", "0")

    digits = digits_only(normalized)

    # Already valid.
    if validate_card(digits):

        return format_card_like_original(
            digits,
            original
        )

    # --------------------------------------------------------
    # Try removing ONE OCR-inserted digit.
    # --------------------------------------------------------

    for index in range(len(digits)):

        candidate = (
            digits[:index]
            + digits[index + 1:]
        )

        if validate_card(candidate):

            return format_card_like_original(
                candidate,
                original
            )

    return None


def format_card_like_original(
    digits,
    original
):
    """
    Keep normal 4-digit grouping where possible.
    """

    if len(digits) == 16:

        return (
            digits[0:4]
            + " "
            + digits[4:8]
            + " "
            + digits[8:12]
            + " "
            + digits[12:16]
        )

    return digits


def validate_pan(value):

    return bool(
        re.fullmatch(
            r"[A-Z]{5}[0-9]{4}[A-Z]",
            str(value).strip().upper()
        )
    )


def validate_aadhaar(value):

    return len(
        digits_only(value)
    ) == 12


def validate_ifsc(value):

    return bool(
        re.fullmatch(
            r"[A-Z]{4}0[A-Z0-9]{6}",
            str(value).strip().upper()
        )
    )


def validate_passport(value):

    return bool(
        re.fullmatch(
            r"[A-Z][0-9]{7}",
            str(value).strip().upper()
        )
    )


def validate_voter_id(value):

    return bool(
        re.fullmatch(
            r"[A-Z]{3}[0-9]{7}",
            str(value).strip().upper()
        )
    )


# ============================================================
# OCR CORRECTION
# ============================================================

def correct_ocr_ifsc(value):

    """
    Correct O/0 confusion only in an IFSC candidate.

    Example:
    SBINO001234
    ->
    SBIN0001234
    """

    value = str(value).strip().upper()

    # IFSC has 11 characters.
    if len(value) != 11:
        return None

    characters = list(value)

    # First four positions are letters.
    # Fifth position must be zero.

    characters[4] = "0"

    corrected = "".join(characters)

    if validate_ifsc(corrected):
        return corrected

    return None


def correct_ocr_driving_license(value):

    """
    Correct common O/0 OCR confusion in a driving
    licence candidate.
    """

    value = str(value).strip().upper()

    corrected = value.replace("O", "0")

    # Normalize spaces.
    corrected = re.sub(
        r"\s+",
        " ",
        corrected
    )

    # Expected Indian DL-style structure.
    if re.fullmatch(
        r"[A-Z]{2}\s?\d{2}\s?\d{4,14}",
        corrected
    ):
        return corrected

    return None


# ============================================================
# DETECTOR
# ============================================================

def detect_regex_pii(text):

    if not isinstance(text, str) or not text.strip():
        return []

    detections = []

    # ========================================================
    # PAN
    # ========================================================

    for match in PATTERNS["PAN"].finditer(text):

        value = match.group(0)

        if validate_pan(value):

            detections.append({
                "label": "PAN",
                "value": value,
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })

    # ========================================================
    # AADHAAR
    # ========================================================

    for match in PATTERNS["AADHAAR"].finditer(text):

        value = match.group(0)

        if validate_aadhaar(value):

            detections.append({
                "label": "AADHAAR",
                "value": value,
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })

    # ========================================================
    # NORMAL CREDIT CARD DETECTION
    # ========================================================

    for match in PATTERNS["CREDITCARDNUMBER"].finditer(text):

        value = match.group(0).strip()

        if validate_card(value):

            detections.append({
                "label": "CREDITCARDNUMBER",
                "value": value,
                "start": match.start(),
                "end": match.start() + len(value),
                "source": "regex"
            })

    # ========================================================
    # CONTEXT CREDIT CARD
    # ========================================================

    for match in CREDIT_CARD_CONTEXT.finditer(text):

        original_value = match.group(1).strip()

        corrected_value = correct_ocr_card(
            original_value
        )

        if corrected_value:

            # Important:
            # Detection position covers the OCR value.
            detections.append({
                "label": "CREDITCARDNUMBER",
                "value": corrected_value,
                "ocr_value": original_value,
                "start": match.start(1),
                "end": match.end(1),
                "source": "regex"
            })

    # ========================================================
    # NORMAL IFSC
    # ========================================================

    for match in PATTERNS["IFSC"].finditer(text):

        value = match.group(0)

        if validate_ifsc(value):

            detections.append({
                "label": "IFSC",
                "value": value,
                "start": match.start(),
                "end": match.end(),
                "source": "regex"
            })

    # ========================================================
    # OCR IFSC
    # ========================================================

    for match in IFSC_CONTEXT.finditer(text):

        original_value = match.group(1)

        corrected_value = correct_ocr_ifsc(
            original_value
        )

        if corrected_value:

            detections.append({
                "label": "IFSC",
                "value": corrected_value,
                "ocr_value": original_value,
                "start": match.start(1),
                "end": match.end(1),
                "source": "regex"
            })

    # ========================================================
    # BANK ACCOUNT
    # ========================================================

    for match in BANK_ACCOUNT_CONTEXT.finditer(text):

        value = match.group(1)

        detections.append({
            "label": "BANK_ACCOUNT",
            "value": value,
            "start": match.start(1),
            "end": match.end(1),
            "source": "regex"
        })

    # ========================================================
    # PASSPORT
    # ========================================================

    for match in PASSPORT_CONTEXT.finditer(text):

        value = match.group(1).upper()

        if validate_passport(value):

            detections.append({
                "label": "PASSPORTNUM",
                "value": value,
                "start": match.start(1),
                "end": match.end(1),
                "source": "regex"
            })

    # ========================================================
    # DRIVING LICENCE
    # ========================================================

    for match in DRIVING_LICENSE_CONTEXT.finditer(text):

        original_value = match.group(1)

        corrected_value = correct_ocr_driving_license(
            original_value
        )

        if corrected_value:

            detections.append({
                "label": "DRIVERLICENSENUM",
                "value": corrected_value,
                "ocr_value": original_value,
                "start": match.start(1),
                "end": match.end(1),
                "source": "regex"
            })

    # ========================================================
    # VOTER ID
    # ========================================================

    for match in VOTER_CONTEXT.finditer(text):

        value = match.group(1).upper()

        if validate_voter_id(value):

            detections.append({
                "label": "VOTERID",
                "value": value,
                "start": match.start(1),
                "end": match.end(1),
                "source": "regex"
            })

    # ========================================================
    # UPI ID
    # ========================================================

    for match in UPI_CONTEXT.finditer(text):

        value = match.group(1)

        detections.append({
            "label": "UPIID",
            "value": value,
            "start": match.start(1),
            "end": match.end(1),
            "source": "regex"
        })

    # ========================================================
    # REMOVE OVERLAPS
    # ========================================================

    detections.sort(
        key=lambda item: (
            item["start"],
            -(item["end"] - item["start"])
        )
    )

    final_detections = []

    for detection in detections:

        overlaps = False

        for existing in final_detections:

            if (
                detection["start"] < existing["end"]
                and existing["start"] < detection["end"]
            ):
                overlaps = True
                break

        if not overlaps:

            final_detections.append(
                detection
            )

    final_detections.sort(
        key=lambda item: (
            item["start"],
            item["end"]
        )
    )

    return final_detections