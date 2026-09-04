# modules/masking.py


# =========================================================
# ENTITIES THAT SHOULD REMAIN VISIBLE
# =========================================================

DO_NOT_MASK = {
    "GIVENNAME",
    "SURNAME",
}


# =========================================================
# MASK EMAIL
# =========================================================

def mask_email(value):

    if "@" not in value:
        return value

    username, domain = value.split(
        "@",
        1
    )

    if len(username) <= 2:

        masked_username = (
            username[0]
            + "*"
            * (len(username) - 1)
        )

    else:

        masked_username = (
            username[0]
            + "*"
            * (len(username) - 2)
            + username[-1]
        )

    return (
        masked_username
        + "@"
        + domain
    )


# =========================================================
# MASK DIGIT-BASED PII
# =========================================================

def mask_digits(
    value,
    keep_last=4
):

    # Count actual digits
    digit_count = sum(
        char.isdigit()
        for char in value
    )

    if digit_count <= keep_last:
        return value

    digits_to_mask = (
        digit_count - keep_last
    )

    current_digit = 0

    result = ""

    for char in value:

        if char.isdigit():

            current_digit += 1

            if current_digit <= digits_to_mask:

                result += "*"

            else:

                result += char

        else:

            # Keep spaces, +, -, etc.
            result += char

    return result


# =========================================================
# MASK PAN
# =========================================================

def mask_pan(value):

    characters = list(value)

    # Keep first 3 and last 2 characters
    # Example:
    # ABCDE1234F
    # ABC*****4F

    if len(characters) <= 5:
        return "*" * len(characters)

    return (
        value[:3]
        + "*" * (len(value) - 5)
        + value[-2:]
    )


# =========================================================
# MASK GENERIC ALPHANUMERIC IDENTIFIER
# =========================================================

def mask_identifier(
    value,
    keep_last=4
):

    positions = [
        index
        for index, char in enumerate(value)
        if char.isalnum()
    ]

    if len(positions) <= keep_last:
        return "*" * len(value)

    mask_count = (
        len(positions)
        - keep_last
    )

    result = list(value)

    for index in positions[:mask_count]:

        result[index] = "*"

    return "".join(result)


# =========================================================
# MASK VALUE
# =========================================================

def mask_value(
    value,
    label
):

    if not value:
        return value

    label = label.upper()

    # -----------------------------------------------------
    # Names remain visible
    # -----------------------------------------------------

    if label in DO_NOT_MASK:
        return value

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    if label == "EMAIL":

        return mask_email(
            value
        )

    # -----------------------------------------------------
    # Phone
    # -----------------------------------------------------

    if label == "TELEPHONENUM":

        # Keep country code visible.
        # Example:
        # +91 9876543210
        # becomes
        # +91 *******3210

        if value.startswith("+"):

            parts = value.split(
                " ",
                1
            )

            if len(parts) == 2:

                country_code = parts[0]
                phone_number = parts[1]

                masked_number = mask_digits(
                    phone_number,
                    keep_last=4
                )

                return (
                    country_code
                    + masked_number
                )

    # -----------------------------------------------------
    # Credit card
    # -----------------------------------------------------

    if label == "CREDITCARDNUMBER":

        return mask_digits(
            value,
            keep_last=4
        )

    # -----------------------------------------------------
    # PAN
    # -----------------------------------------------------

    if label == "PAN":

        def mask_pan(value):
            """
            Partially mask PAN.

            Example:
                ABCDE1234F
                ABC*****4F
            """

            if len(value) < 6:
                return "*" * len(value)

            return (
                value[:3]
                + "*" * (len(value) - 5)
                + value[-2:]
            )

        return mask_pan(value)

        # -----------------------------------------------------
    # Aadhaar and other identifiers
    # -----------------------------------------------------

    if label in {
        "AADHAAR",
        "PASSPORTNUM",
        "DRIVERLICENSENUM",
        "IDCARDNUM",
        "SOCIALNUM",
        "TAXNUM",
        "BANK_ACCOUNT",
        "BANKACCOUNT",
        "IFSC",
        "VOTERID",
        "VOTERIDNUM",
    }:

        return mask_identifier(
            value,
            keep_last=4
        )


    # -----------------------------------------------------
    # UPI ID
    # -----------------------------------------------------

    if label in {
        "UPIID",
        "UPI_ID",
    }:

        if "@" in value:

            username, provider = value.split(
                "@",
                1
            )

            # Keep exactly 15 stars for UPI username
            masked_username = "*" * 15

            # Keep the last 5 characters of provider
            # and replace the first 3 characters.
            #
            # Example:
            # okicici
            # ***icici

            if len(provider) > 5:

                masked_provider = (
                    "***"
                    + provider[-5:]
                )

            else:

                masked_provider = (
                    "***"
                    + provider
                )

            return (
                masked_username
                + "@"
                + masked_provider
            )

        return "*" * 15


# =========================================================
# MASK DETECTIONS
# =========================================================

def mask_detections(
    text,
    detections
):

    if not isinstance(
        text,
        str
    ):

        return text

    if not detections:
        return text

    masked_text = text

    # -----------------------------------------------------
    # Right-to-left replacement
    # -----------------------------------------------------

    sorted_detections = sorted(
        detections,
        key=lambda item: item.get(
            "start",
            0
        ),
        reverse=True
    )

    for detection in sorted_detections:

        label = detection.get(
            "label",
            ""
        )

        start = detection.get(
            "start"
        )

        end = detection.get(
            "end"
        )

        if start is None or end is None:
            continue

        if start < 0 or end <= start:
            continue

        if end > len(masked_text):
            continue

        # -------------------------------------------------
        # Don't mask names
        # -------------------------------------------------

        if label.upper() in DO_NOT_MASK:
            continue

        # -------------------------------------------------
        # Always use the actual substring
        # from the current text
        # -------------------------------------------------

        original_value = masked_text[
            start:end
        ]

        if not original_value:
            continue

        replacement = mask_value(
            original_value,
            label
        )

        masked_text = (
            masked_text[:start]
            + replacement
            + masked_text[end:]
        )

    return masked_text

# =========================================================
# MASK TEXT USING DETECTED VALUES
# =========================================================

def mask_text_by_values(
    text,
    detections
):

    if not isinstance(
        text,
        str
    ):
        return text

    if not detections:
        return text

    masked_text = text

    # Process longer values first
    # This helps with values containing spaces.
    sorted_detections = sorted(
        detections,
        key=lambda item: len(
            str(
                item.get(
                    "value",
                    ""
                )
            )
        ),
        reverse=True
    )

    for detection in sorted_detections:

        label = detection.get(
            "label",
            ""
        )

        value = detection.get(
            "value",
            ""
        )

        if not value:
            continue

        # Do not mask unwanted entities
        if label.upper() in DO_NOT_MASK:
            continue

        # Generate the project's existing
        # masking format
        masked_value = mask_value(
            value,
            label
        )

        if masked_value == value:
            continue

        # Replace the detected value
        # wherever it occurs in the extracted text
        masked_text = masked_text.replace(
            value,
            masked_value
        )

    return masked_text

# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    sample_text = (
        "Name: Rahul Sharma\n"
        "Email: rahul@gmail.com\n"
        "Phone: +91 9876543210\n"
        "PAN: ABCDE1234F\n"
        "Aadhaar: 1234 5678 9012\n"
        "Card: 4111 1111 1111 1111"
    )

    # IMPORTANT:
    # These positions are calculated automatically
    # so the test cannot contain incorrect indexes.

    detections = []

    test_values = [
        ("GIVENNAME", "Rahul Sharma"),
        ("EMAIL", "rahul@gmail.com"),
        ("TELEPHONENUM", "+91 9876543210"),
        ("PAN", "ABCDE1234F"),
        ("AADHAAR", "1234 5678 9012"),
        ("CREDITCARDNUMBER", "4111 1111 1111 1111"),
    ]

    for label, value in test_values:

        start = sample_text.find(
            value
        )

        if start != -1:

            detections.append(
                {
                    "label": label,
                    "value": value,
                    "start": start,
                    "end": start + len(value)
                }
            )

    print("=" * 70)
    print("PARTIAL MASKING TEST")
    print("=" * 70)

    print()
    print("ORIGINAL:")
    print(sample_text)

    print()
    print("MASKED:")

    print(
        mask_detections(
            sample_text,
            detections
        )
    )

    print()
    print("=" * 70)
    print("MASKING TEST COMPLETED")
    print("=" * 70)