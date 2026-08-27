import re


# ============================================================
# Regular expressions
# ============================================================

PATTERNS = {

    # Email address
    "EMAIL": re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),

    # Indian mobile / telephone numbers
    "TELEPHONENUM": re.compile(
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
    ),

    # Indian PAN
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

"BANK_ACCOUNT": re.compile(
    r"(?<![\d+])\d{9,18}(?!\d)"
),

}


# ============================================================
# Validation helpers
# ============================================================

def digits_only(value):
    """Return only numeric characters."""
    return re.sub(r"\D", "", value)


def luhn_check(number):
    """
    Validate a card number using the Luhn algorithm.
    """

    digits = digits_only(number)

    if not 13 <= len(digits) <= 19:
        return False

    total = 0
    parity = len(digits) % 2

    for index, digit in enumerate(digits):

        value = int(digit)

        if index % 2 == parity:
            value *= 2

            if value > 9:
                value -= 9

        total += value

    return total % 10 == 0


def validate_card(value):
    """Return True when the card number passes Luhn validation."""
    return luhn_check(value)


def validate_pan(value):
    """Basic PAN format validation."""

    value = value.upper()

    return bool(
        re.fullmatch(
            r"[A-Z]{5}[0-9]{4}[A-Z]",
            value
        )
    )


def validate_aadhaar(value):
    """
    Basic Aadhaar structural validation.

    This checks the 12-digit structure but does not attempt
    to verify whether the number belongs to a real person.
    """

    digits = digits_only(value)

    return len(digits) == 12


def validate_ifsc(value):
    """Basic IFSC format validation."""

    return bool(
        re.fullmatch(
            r"[A-Z]{4}0[A-Z0-9]{6}",
            value.upper()
        )
    )

def overlaps_with_existing(result, results):
    """
    Check whether a detection overlaps an existing detection.
    """
    for existing in results:
        if (
            result["start"] < existing["end"]
            and result["end"] > existing["start"]
        ):
            return True

    return False

# ============================================================
# Main detector
# ============================================================

def detect_regex_pii(text):
    """
    Detect structured PII using regular expressions.

    Returns a list of dictionaries containing:
        label
        value
        start
        end
    """

    if not isinstance(text, str):
        return []

    results = []

    for label, pattern in PATTERNS.items():

        for match in pattern.finditer(text):

            # Get the matched value FIRST
            value = match.group()

            # ------------------------------------------------
            # Validate the matched value
            # ------------------------------------------------

            if label == "CREDITCARDNUMBER":

                if not validate_card(value):
                    continue

            elif label == "PAN":

                if not validate_pan(value):
                    continue

            elif label == "AADHAAR":

                if not validate_aadhaar(value):
                    continue

            elif label == "IFSC":

                if not validate_ifsc(value):
                    continue

            # ------------------------------------------------
            # Prevent bank account from duplicating phone
            # ------------------------------------------------

            if label == "BANK_ACCOUNT":

                if any(
                    existing["label"] == "TELEPHONENUM"
                    and existing["start"] <= match.start()
                    and existing["end"] >= match.end()
                    for existing in results
                ):
                    continue

            new_result = {
                "label": label,
                "value": value,
                "start": match.start(),
                "end": match.end()
            }

            # Prevent Aadhaar from overlapping a credit card.
            if label == "AADHAAR":
                if any(
                    existing["label"] == "CREDITCARDNUMBER"
                    and new_result["start"] < existing["end"]
                    and new_result["end"] > existing["start"]
                    for existing in results
                ):
                    continue

            results.append(new_result)

    # --------------------------------------------------------
    # Sort by position
    # --------------------------------------------------------

    results.sort(
        key=lambda item: (
            item["start"],
            item["end"]
        )
    )

    return results


# ============================================================
# Simple test
# ============================================================

if __name__ == "__main__":

    sample_text = """
    Email: test@example.com
    Phone: +91 9876543210
    PAN: ABCDE1234F
    Aadhaar: 1234 5678 9012
    IFSC: SBIN0001234
    Card: 4111 1111 1111 1111
    """

    print("=" * 70)
    print("REGEX PII DETECTOR TEST")
    print("=" * 70)

    results = detect_regex_pii(sample_text)

    for result in results:

        print(
            f"{result['label']:<20} "
            f"{result['value']:<25} "
            f"({result['start']}, {result['end']})"
        )