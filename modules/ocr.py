# modules/ocr.py

import os
import re

import fitz
import pytesseract

from PIL import Image


# =========================================================
# SUPPORTED FILE TYPES
# =========================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}


# =========================================================
# EXTRACT TEXT FROM FILE
# =========================================================

def extract_text_from_file(file_path):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    # =====================================================
    # IMAGE
    # =====================================================

    if extension in {
        ".png",
        ".jpg",
        ".jpeg"
    }:

        image = Image.open(
            file_path
        ).convert(
            "RGB"
        )

        return pytesseract.image_to_string(
            image
        )

    # =====================================================
    # PDF
    # =====================================================

    if extension == ".pdf":

        document = fitz.open(
            file_path
        )

        text_parts = []

        for page in document:

            page_text = page.get_text(
                "text"
            )

            if page_text.strip():

                text_parts.append(
                    page_text
                )

        document.close()

        return "\n".join(
            text_parts
        )


# =========================================================
# EXTRACT DOCUMENT DATA
# =========================================================

def extract_document_data(file_path):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    # =====================================================
    # IMAGE
    # =====================================================

    if extension in {
        ".png",
        ".jpg",
        ".jpeg"
    }:

        image = Image.open(
            file_path
        ).convert(
            "RGB"
        )

        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        words = []

        total = len(
            ocr_data["text"]
        )

        for i in range(total):

            text = str(
                ocr_data["text"][i]
            ).strip()

            if not text:
                continue

            try:

                confidence = float(
                    ocr_data["conf"][i]
                )

            except Exception:

                confidence = -1

            words.append({

                "text":
                    text,

                "left":
                    int(
                        ocr_data["left"][i]
                    ),

                "top":
                    int(
                        ocr_data["top"][i]
                    ),

                "width":
                    int(
                        ocr_data["width"][i]
                    ),

                "height":
                    int(
                        ocr_data["height"][i]
                    ),

                "conf":
                    confidence,
            })

        page_text = " ".join(

            word["text"]

            for word in words
        )

        return {

            "type":
                "image",

            "path":
                file_path,

            "text":
                page_text,

            "words":
                words,

            "width":
                image.width,

            "height":
                image.height,
        }

    # =====================================================
    # PDF
    # =====================================================

    if extension == ".pdf":

        document = fitz.open(
            file_path
        )

        pages = []

        for page_number, page in enumerate(
            document
        ):

            page_text = page.get_text(
                "text"
            )

            if page_text.strip():

                page_words = []

                for word in page.get_text(
                    "words"
                ):

                    page_words.append({

                        "text":
                            word[4],

                        "x0":
                            word[0],

                        "y0":
                            word[1],

                        "x1":
                            word[2],

                        "y1":
                            word[3],

                        "block":
                            word[5],

                        "line":
                            word[6],

                        "word":
                            word[7],
                    })

                pages.append({

                    "page_number":
                        page_number,

                    "type":
                        "text",

                    "text":
                        page_text,

                    "words":
                        page_words,
                })

            else:

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(
                        2,
                        2
                    )
                )

                image = Image.frombytes(
                    "RGB",
                    [
                        pix.width,
                        pix.height
                    ],
                    pix.samples
                )

                ocr_data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT
                )

                page_words = []

                for i in range(
                    len(
                        ocr_data["text"]
                    )
                ):

                    text = str(
                        ocr_data["text"][i]
                    ).strip()

                    if not text:
                        continue

                    page_words.append({

                        "text":
                            text,

                        "left":
                            int(
                                ocr_data["left"][i]
                            ),

                        "top":
                            int(
                                ocr_data["top"][i]
                            ),

                        "width":
                            int(
                                ocr_data["width"][i]
                            ),

                        "height":
                            int(
                                ocr_data["height"][i]
                            ),

                        "conf":
                            float(
                                ocr_data["conf"][i]
                            ),
                    })

                page_text = " ".join(

                    word["text"]

                    for word in page_words
                )

                pages.append({

                    "page_number":
                        page_number,

                    "type":
                        "ocr",

                    "text":
                        page_text,

                    "words":
                        page_words,

                    "scale":
                        2,
                })

        document.close()

        full_text = "\n".join(

            page["text"]

            for page in pages
        )

        return {

            "type":
                "pdf",

            "path":
                file_path,

            "text":
                full_text,

            "pages":
                pages,
        }


# =========================================================
# NORMALIZE SENSITIVE OCR VALUE
# =========================================================

def normalize_sensitive_ocr_value(
    value,
    label
):

    if not value:
        return value

    value = str(
        value
    ).strip()

    label = str(
        label
    ).upper().strip()

    # =====================================================
    # PAN
    # =====================================================

    if label == "PAN":

        return re.sub(
            r"[^A-Z0-9]",
            "",
            value.upper()
        )

    # =====================================================
    # AADHAAR
    # =====================================================

    if label == "AADHAAR":

        return re.sub(
            r"\D",
            "",
            value
        )

    # =====================================================
    # PASSPORT
    # =====================================================

    if label == "PASSPORTNUM":

        return re.sub(
            r"[^A-Z0-9]",
            "",
            value.upper()
        )

    # =====================================================
    # DRIVING LICENCE
    # =====================================================

    if label == "DRIVERLICENSENUM":

        value = re.sub(
            r"[^A-Z0-9-]",
            "",
            value.upper()
        )

        if len(value) > 1:

            value = (
                value[0]
                + value[1:].replace(
                    "O",
                    "0"
                )
            )

        return value

    # =====================================================
    # VOTER ID
    # =====================================================

    if label in {
        "VOTERID",
        "VOTERIDNUM"
    }:

        return re.sub(
            r"[^A-Z0-9]",
            "",
            value.upper()
        )

    # =====================================================
    # BANK ACCOUNT
    # =====================================================

    if label in {
        "BANK_ACCOUNT",
        "BANKACCOUNT"
    }:

        return re.sub(
            r"\D",
            "",
            value
        )

    # =====================================================
    # IFSC
    # =====================================================

    if label == "IFSC":

        value = re.sub(
            r"[^A-Z0-9]",
            "",
            value.upper()
        )

        if len(value) == 11:

            if value[4] == "O":

                value = (
                    value[:4]
                    + "0"
                    + value[5:]
                )

        return value

    # =====================================================
    # CREDIT / DEBIT CARD
    # =====================================================

    if label in {
        "CREDITCARDNUMBER",
        "DEBITCARDNUMBER"
    }:

        return re.sub(
            r"\D",
            "",
            value
        )

    # =====================================================
    # UPI
    # =====================================================

    if label in {
        "UPIID",
        "UPI_ID"
    }:

        return re.sub(
            r"\s+",
            "",
            value
        )

    return value


# =========================================================
# VALIDATE UPI
# =========================================================

def is_valid_upi(
    value
):

    if not value:
        return False

    value = str(
        value
    ).strip()

    return bool(
        re.fullmatch(
            r"[A-Za-z0-9._-]+@[A-Za-z0-9._-]+",
            value
        )
    )


# =========================================================
# CORRECT OCR VALUE WORD
# =========================================================

def correct_value_word(
    word
):
    """
    Correct OCR bounding box when Tesseract combines
    ':' or '>' with the sensitive value.

    Example:

        :NUMBERKA0120180012345

    becomes a value-only bounding box.
    """

    corrected = dict(
        word
    )

    raw_text = str(
        word.get(
            "text",
            ""
        )
    ).strip()

    if not raw_text:
        return corrected

    # -----------------------------------------------------
    # Separator combined with value.
    # -----------------------------------------------------

    if not raw_text.startswith(
        (
            ":",
            ">"
        )
    ):
        return corrected

    left = int(
        word.get(
            "left",
            0
        )
    )

    width = int(
        word.get(
            "width",
            0
        )
    )

    height = int(
        word.get(
            "height",
            0
        )
    )

    if width <= 0:
        return corrected

    # -----------------------------------------------------
    # Estimate separator width.
    # -----------------------------------------------------

    separator_width = max(
        3,
        min(
            6,
            int(
                height * 0.30
            )
        )
    )

    corrected[
        "left"
    ] = (
        left
        + separator_width
    )

    corrected[
        "width"
    ] = max(
        1,
        width
        - separator_width
    )

    return corrected


# =========================================================
# DETECT SENSITIVE FIELDS FROM OCR
# =========================================================

def detect_sensitive_fields_from_ocr(
    document_data
):
    """
    Detect ONLY approved high-risk sensitive information.

    Explicitly ignored:

        Name
        DOB
        Phone
        Email
        Address
        City
        State
        Country
        IP
        MAC
        Website
        Employee ID
        Reference Number
        Normal dates
        Normal numbers
        Unknown entities
    """

    if not document_data:
        return []

    if document_data.get(
        "type"
    ) != "image":

        return []

    words = document_data.get(
        "words",
        []
    )

    if not words:
        return []

    # =====================================================
    # APPROVED SENSITIVE FIELD LABELS
    # =====================================================

    field_labels = {

        "pan number":
            "PAN",

        "aadhaar number":
            "AADHAAR",

        "passport number":
            "PASSPORTNUM",

        "driving license number":
            "DRIVERLICENSENUM",

        "driving licence number":
            "DRIVERLICENSENUM",

        "voter id number":
            "VOTERID",

        "bank account number":
            "BANK_ACCOUNT",

        "ifsc code":
            "IFSC",

        "credit card number":
            "CREDITCARDNUMBER",

        "debit card number":
            "DEBITCARDNUMBER",

        "upi id":
            "UPIID",
    }

    # =====================================================
    # NORMALIZE OCR WORDS
    # =====================================================

    normalized_words = []

    for original_word in words:

        text = str(
            original_word.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        word = {

            "text":
                text,

            "lower":
                text.lower(),

            "left":
                int(
                    original_word.get(
                        "left",
                        0
                    )
                ),

            "top":
                int(
                    original_word.get(
                        "top",
                        0
                    )
                ),

            "width":
                int(
                    original_word.get(
                        "width",
                        0
                    )
                ),

            "height":
                int(
                    original_word.get(
                        "height",
                        0
                    )
                ),
        }

        word["right"] = (
            word["left"]
            + word["width"]
        )

        word["bottom"] = (
            word["top"]
            + word["height"]
        )

        normalized_words.append(
            word
        )

    detections = []

    # =====================================================
    # FIND APPROVED FIELD LABELS
    # =====================================================

    for index in range(
        len(
            normalized_words
        )
    ):

        for length in range(
            1,
            5
        ):

            end = (
                index
                + length
            )

            if end > len(
                normalized_words
            ):
                break

            group = normalized_words[
                index:end
            ]

            # -------------------------------------------------
            # All label words must be on approximately the
            # same horizontal row.
            # -------------------------------------------------

            if len(group) > 1:

                first_top = group[0][
                    "top"
                ]

                same_row = True

                for group_word in group[1:]:

                    if abs(
                        group_word["top"]
                        - first_top
                    ) > 20:

                        same_row = False

                        break

                if not same_row:
                    continue

            label_text = " ".join(

                word["lower"]

                for word in group
            ).strip()

            if label_text not in field_labels:
                continue

            label = field_labels[
                label_text
            ]

            # =================================================
            # LABEL BOUNDARIES
            # =================================================

            label_right = max(
                word["right"]
                for word in group
            )

            label_top = min(
                word["top"]
                for word in group
            )

            label_bottom = max(
                word["bottom"]
                for word in group
            )

            label_height = max(
                1,
                label_bottom
                - label_top
            )

            label_center = (
                label_top
                + label_bottom
            ) / 2

            # =================================================
            # FIND SAME-ROW CANDIDATES
            # =================================================

            candidate_words = []

            for candidate in normalized_words:

                if candidate["left"] <= label_right:
                    continue

                candidate_center = (
                    candidate["top"]
                    + candidate["bottom"]
                ) / 2

                if abs(
                    candidate_center
                    - label_center
                ) > max(
                    label_height * 1.2,
                    12
                ):
                    continue

                candidate_words.append(
                    candidate
                )

            if not candidate_words:
                continue

            candidate_words.sort(
                key=lambda word:
                    word["left"]
            )

            # =================================================
            # SELECT VALUE WORDS
            # =================================================

            selected = []

            previous_right = label_right

            for candidate in candidate_words:

                gap = (
                    candidate["left"]
                    - previous_right
                )

                if (
                    selected
                    and
                    gap > 100
                ):
                    break

                selected.append(
                    candidate
                )

                previous_right = (
                    candidate["right"]
                )

                if len(
                    selected
                ) >= 8:
                    break

            # =================================================
            # SPECIAL UPI HANDLING
            # =================================================
            #
            # UPI is detected ONLY when the field label
            # itself is "UPI ID".
            #
            # This is the important fix.
            #
            # Email:
            #
            #     Email Address : rahul@gmail.com
            #
            # will NEVER become UPI.
            #
            # Actual UPI:
            #
            #     UPI ID : rahulsharma@okicici
            #
            # can be detected.
            # =================================================

            if label == "UPIID":

                upi_candidates = []

                for candidate in candidate_words:

                    candidate_text = str(
                        candidate["text"]
                    ).strip()

                    candidate_text = (
                        candidate_text
                        .lstrip(
                            ":>"
                        )
                        .strip()
                    )

                    if "@" not in candidate_text:
                        continue

                    if not is_valid_upi(
                        candidate_text
                    ):
                        continue

                    upi_candidates.append(
                        candidate
                    )

                if upi_candidates:

                    selected = [

                        min(
                            upi_candidates,
                            key=lambda item:
                                item["left"]
                        )
                    ]

                else:

                    # No valid UPI value on the UPI row.
                    continue

            # =================================================
            # REMOVE SEPARATOR-ONLY WORDS
            # =================================================

            value_words = []

            for word in selected:

                raw_text = str(
                    word["text"]
                ).strip()

                if raw_text in {
                    ":",
                    ">",
                }:
                    continue

                corrected_word = (
                    correct_value_word(
                        word
                    )
                )

                value_words.append(
                    corrected_word
                )

            if not value_words:
                continue

            # =================================================
            # CONSTRUCT RAW VALUE
            # =================================================

            raw_value = " ".join(

                word["text"]

                for word in value_words
            ).strip()

            # -------------------------------------------------
            # Remove leading separators.
            # -------------------------------------------------

            value = raw_value.lstrip(
                ":>"
            ).strip()

            if not value:
                continue

            # =================================================
            # NORMALIZE
            # =================================================

            value = normalize_sensitive_ocr_value(
                value,
                label
            )

            if not value:
                continue

            # =================================================
            # UPI VALIDATION
            # =================================================

            if label == "UPIID":

                if not is_valid_upi(
                    value
                ):
                    continue

            # =================================================
            # STRUCTURED VALUE VALIDATION
            # =================================================

            valid = True

            # -------------------------------------------------
            # PAN
            # -------------------------------------------------

            if label == "PAN":

                valid = bool(
                    re.fullmatch(
                        r"[A-Z]{5}[0-9]{4}[A-Z]",
                        value.upper()
                    )
                )

            # -------------------------------------------------
            # AADHAAR
            # -------------------------------------------------

            elif label == "AADHAAR":

                digits = re.sub(
                    r"\D",
                    "",
                    value
                )

                valid = (
                    len(digits)
                    == 12
                )

            # -------------------------------------------------
            # PASSPORT
            # -------------------------------------------------

            elif label == "PASSPORTNUM":

                valid = bool(
                    re.fullmatch(
                        r"[A-Z][0-9]{7}",
                        value.upper()
                    )
                )

            # -------------------------------------------------
            # VOTER ID
            # -------------------------------------------------

            elif label == "VOTERID":

                valid = bool(
                    re.fullmatch(
                        r"[A-Z]{3}[0-9]{7}",
                        value.upper()
                    )
                )

            # -------------------------------------------------
            # IFSC
            # -------------------------------------------------

            elif label == "IFSC":

                valid = bool(
                    re.fullmatch(
                        r"[A-Z]{4}0[A-Z0-9]{6}",
                        value.upper()
                    )
                )

            # -------------------------------------------------
            # BANK ACCOUNT
            # -------------------------------------------------

            elif label == "BANK_ACCOUNT":

                digits = re.sub(
                    r"\D",
                    "",
                    value
                )

                valid = (
                    8
                    <= len(digits)
                    <= 18
                )

            # -------------------------------------------------
            # CREDIT / DEBIT CARD
            # -------------------------------------------------

            elif label in {
                "CREDITCARDNUMBER",
                "DEBITCARDNUMBER"
            }:

                digits = re.sub(
                    r"\D",
                    "",
                    value
                )

                valid = (
                    13
                    <= len(digits)
                    <= 19
                )

            # -------------------------------------------------
            # DRIVING LICENCE
            # -------------------------------------------------

            elif label == "DRIVERLICENSENUM":

                clean_value = re.sub(
                    r"[^A-Z0-9]",
                    "",
                    value.upper()
                )

                valid = (
                    len(clean_value)
                    >= 10
                )

            if not valid:
                continue

            # =================================================
            # FINAL VALUE BOUNDING BOX
            # =================================================

            left = min(
                word["left"]
                for word in value_words
            )

            top = min(
                word["top"]
                for word in value_words
            )

            right = max(
                word["right"]
                for word in value_words
            )

            bottom = max(
                word["bottom"]
                for word in value_words
            )

            # =================================================
            # STORE DETECTION
            # =================================================

            detections.append({

                "label":
                    label,

                "value":
                    value,

                "ocr_value":
                    raw_value,

                "source":
                    "ocr",

                "left":
                    left,

                "top":
                    top,

                "right":
                    right,

                "bottom":
                    bottom,
            })

            # -------------------------------------------------
            # Stop checking different label lengths once this
            # label has produced a valid detection.
            # -------------------------------------------------

            break

    # =====================================================
    # IMPORTANT:
    # NO GENERIC UPI FALLBACK
    # =====================================================
    #
    # We intentionally DO NOT scan every OCR word looking
    # for "something@something".
    #
    # Otherwise:
    #
    #     rahul@gmail.com
    #
    # becomes incorrectly classified as UPI.
    #
    # UPI must be associated with the "UPI ID" field label.
    # =====================================================

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique_detections = []

    seen = set()

    for detection in detections:

        key = (

            detection.get(
                "label"
            ),

            detection.get(
                "value"
            ),

            detection.get(
                "left"
            ),

            detection.get(
                "top"
            ),

            detection.get(
                "right"
            ),

            detection.get(
                "bottom"
            ),
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique_detections.append(
            detection
        )

    # =====================================================
    # SORT DETECTIONS
    # =====================================================

    unique_detections.sort(
        key=lambda item: (
            item.get(
                "top",
                0
            ),
            item.get(
                "left",
                0
            )
        )
    )

    return unique_detections


# =========================================================
# CLEAN OCR PREVIEW TEXT
# =========================================================

def clean_ocr_preview_text(
    text
):

    if not text:
        return ""

    lines = str(
        text
    ).splitlines()

    cleaned_lines = []

    garbage_phrases = [

        "pss JAW.",

        "pss JAW",

        "pss",

        "Url) veiw",

        "Cr)",

        "ffl",

        "lil",
    ]

    garbage_lines = {

        "®",

        "©",

        "™",

        "ffl",

        "lil",

        "b",

        "ass",

        "a",

        "—",

        "_",

        "I II",

        "Url) veiw",

        "Cr)",

        "pss JAW.",
    }

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # -------------------------------------------------
        # Remove known OCR garbage.
        # -------------------------------------------------

        for garbage in garbage_phrases:

            line = re.sub(
                re.escape(
                    garbage
                ),
                "",
                line,
                flags=re.IGNORECASE
            )

        # -------------------------------------------------
        # Remove isolated "a _".
        # -------------------------------------------------

        line = re.sub(
            r"\s+a\s+_\s*",
            " ",
            line,
            flags=re.IGNORECASE
        )

        # -------------------------------------------------
        # Remove isolated underscores.
        # -------------------------------------------------

        line = re.sub(
            r"(?<!\w)_+(?!\w)",
            "",
            line
        )

        line = line.strip()

        if not line:
            continue

        if line in garbage_lines:
            continue

        # -------------------------------------------------
        # Ignore lines containing no useful characters.
        # -------------------------------------------------

        if not any(
            character.isalnum()
            for character in line
        ):
            continue

        cleaned_lines.append(
            line
        )

    return "\n".join(
        cleaned_lines
    )


# =========================================================
# CREATE MASKED TEXT PREVIEW
# =========================================================

def create_masked_text_preview(
    document_data,
    detections
):

    if not document_data:
        return ""

    if document_data.get(
        "type"
    ) != "image":

        return ""

    words = document_data.get(
        "words",
        []
    )

    if not words:
        return ""

    from .masking import mask_value

    # =====================================================
    # GROUP OCR WORDS INTO LINES
    # =====================================================

    lines = []

    y_tolerance = 12

    sorted_words = sorted(

        words,

        key=lambda word: (
            word.get(
                "top",
                0
            ),

            word.get(
                "left",
                0
            )
        )
    )

    for word in sorted_words:

        text = str(
            word.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        top = int(
            word.get(
                "top",
                0
            )
        )

        placed = False

        for line in lines:

            if abs(
                top
                - line["top"]
            ) <= y_tolerance:

                line["words"].append(
                    word
                )

                placed = True

                break

        if not placed:

            lines.append({

                "top":
                    top,

                "words":
                    [word],
            })

    # =====================================================
    # SORT WORDS INSIDE EACH LINE
    # =====================================================

    for line in lines:

        line["words"].sort(
            key=lambda word:
                word.get(
                    "left",
                    0
                )
        )

    # =====================================================
    # VALID DETECTIONS
    # =====================================================

    valid_detections = []

    for detection in detections:

        if not detection.get(
            "value"
        ):
            continue

        if None in (

            detection.get(
                "left"
            ),

            detection.get(
                "top"
            ),

            detection.get(
                "right"
            ),

            detection.get(
                "bottom"
            ),
        ):
            continue

        valid_detections.append(
            detection
        )

    # =====================================================
    # BUILD PREVIEW
    # =====================================================

    output_lines = []

    for line in lines:

        line_words = line[
            "words"
        ]

        matching_detection = None

        # -------------------------------------------------
        # Find sensitive detection belonging to this row.
        # -------------------------------------------------

        for detection in valid_detections:

            d_left = detection[
                "left"
            ]

            d_top = detection[
                "top"
            ]

            d_right = detection[
                "right"
            ]

            d_bottom = detection[
                "bottom"
            ]

            for word in line_words:

                w_left = word.get(
                    "left",
                    0
                )

                w_top = word.get(
                    "top",
                    0
                )

                w_right = (
                    w_left
                    + word.get(
                        "width",
                        0
                    )
                )

                w_bottom = (
                    w_top
                    + word.get(
                        "height",
                        0
                    )
                )

                horizontal_overlap = (
                    w_right >= d_left
                    and
                    w_left <= d_right
                )

                vertical_overlap = (
                    w_bottom >= d_top
                    and
                    w_top <= d_bottom
                )

                if (
                    horizontal_overlap
                    and
                    vertical_overlap
                ):

                    matching_detection = (
                        detection
                    )

                    break

            if matching_detection:
                break

        # =================================================
        # SENSITIVE LINE
        # =================================================

        if matching_detection:

            label = matching_detection.get(
                "label",
                ""
            )

            value = matching_detection.get(
                "value",
                ""
            )

            masked_value = mask_value(
                value,
                label
            )

            display_label = {

                "PAN":
                    "PAN Number",

                "AADHAAR":
                    "Aadhaar Number",

                "PASSPORTNUM":
                    "Passport Number",

                "DRIVERLICENSENUM":
                    "Driving License Number",

                "VOTERID":
                    "Voter ID Number",

                "VOTERIDNUM":
                    "Voter ID Number",

                "BANK_ACCOUNT":
                    "Bank Account Number",

                "BANKACCOUNT":
                    "Bank Account Number",

                "IFSC":
                    "IFSC Code",

                "CREDITCARDNUMBER":
                    "Credit Card Number",

                "DEBITCARDNUMBER":
                    "Debit Card Number",

                "UPIID":
                    "UPI ID",
            }.get(
                label,
                label
            )

            output_lines.append(
                f"{display_label} : {masked_value}"
            )

            continue

        # =================================================
        # NORMAL LINE
        # =================================================

        normal_text = " ".join(

            str(
                word.get(
                    "text",
                    ""
                )
            ).strip()

            for word in line_words

            if str(
                word.get(
                    "text",
                    ""
                )
            ).strip()
        )

        normal_text = normal_text.strip()

        if not normal_text:
            continue

        output_lines.append(
            normal_text
        )

    preview_text = "\n".join(
        output_lines
    )

    return clean_ocr_preview_text(
        preview_text
    )