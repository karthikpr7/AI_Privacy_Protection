import os
import re
import fitz
import pytesseract

from PIL import (
    Image,
    ImageOps,
    ImageFilter,
)


# ============================================================
# SUPPORTED FILE TYPES
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}

PDF_OCR_SCALE = 2


# ============================================================
# APPROVED SENSITIVE LABELS
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
    "UPI_ID",

    "PASSWORD",
    "APIKEY",
    "API_KEY",

    "ACCESSTOKEN",
    "ACCESS_TOKEN",

    "SECRETKEY",
    "SECRET_KEY",
}


# ============================================================
# LABEL ALIASES
# ============================================================

LABEL_ALIASES = {
    "BANKACCOUNT": "BANK_ACCOUNT",
    "VOTERIDNUM": "VOTERID",
    "DEBITCARDNUMBER": "CREDITCARDNUMBER",

    "API_KEY": "APIKEY",
    "ACCESS_TOKEN": "ACCESSTOKEN",
    "SECRET_KEY": "SECRETKEY",

    "UPI_ID": "UPIID",
}


# ============================================================
# NORMALIZE LABEL
# ============================================================

def normalize_label(label):

    label = str(
        label
    ).strip().upper()

    return LABEL_ALIASES.get(
        label,
        label
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\u00a0",
        " "
    )

    text = text.replace(
        "\r",
        "\n"
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    return text.strip()


def normalize_label_text(text):

    if text is None:
        return ""

    text = str(text).upper()

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


def normalize_sensitive_ocr_value(value):

    if value is None:
        return ""

    value = str(value)

    value = value.replace(
        "\u00a0",
        " "
    )

    value = value.strip()

    value = value.strip(
        ".,;:|[]{}()"
    )

    return value


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_ocr_image(image):

    if image.mode != "RGB":

        image = image.convert(
            "RGB"
        )

    gray = ImageOps.grayscale(
        image
    )

    gray = ImageOps.autocontrast(
        gray
    )

    gray = gray.filter(
        ImageFilter.SHARPEN
    )

    return gray


def make_ocr_variants(image):

    variants = []

    if image.mode != "RGB":

        image = image.convert(
            "RGB"
        )

    # --------------------------------------------------------
    # Original
    # --------------------------------------------------------

    variants.append(
        (
            "original",
            image
        )
    )

    # --------------------------------------------------------
    # Grayscale
    # --------------------------------------------------------

    gray = ImageOps.grayscale(
        image
    )

    gray = ImageOps.autocontrast(
        gray
    )

    variants.append(
        (
            "gray",
            gray
        )
    )

    # --------------------------------------------------------
    # Sharpened
    # --------------------------------------------------------

    sharp = gray.filter(
        ImageFilter.SHARPEN
    )

    variants.append(
        (
            "sharp",
            sharp
        )
    )

    return variants


# ============================================================
# WORD LEVEL OCR
# ============================================================

def get_image_ocr_data(
    image,
    config="--oem 3 --psm 6"
):

    try:

        return pytesseract.image_to_data(
            image,
            config=config,
            output_type=pytesseract.Output.DICT,
        )

    except Exception as error:

        print(
            f"OCR DATA ERROR: {error}"
        )

        return {
            "text": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
            "conf": [],
        }


# ============================================================
# FULL TEXT OCR
# ============================================================

def extract_text_from_image(
    image,
    config="--oem 3 --psm 6"
):

    try:

        text = pytesseract.image_to_string(
            image,
            config=config
        )

        return normalize_text(
            text
        )

    except Exception as error:

        print(
            f"OCR TEXT ERROR: {error}"
        )

        return ""


# ============================================================
# NORMALIZE OCR WORDS
# ============================================================

def normalize_ocr_words(data):

    words = []

    if not data:
        return words

    texts = data.get(
        "text",
        []
    )

    for i, raw_text in enumerate(
        texts
    ):

        text = normalize_sensitive_ocr_value(
            raw_text
        )

        if not text:
            continue

        try:

            left = int(
                data["left"][i]
            )

            top = int(
                data["top"][i]
            )

            width = int(
                data["width"][i]
            )

            height = int(
                data["height"][i]
            )

        except Exception:

            continue

        try:

            confidence = float(
                data["conf"][i]
            )

        except Exception:

            confidence = -1

        words.append(
            {
                "text": text,

                "normalized":
                    normalize_label_text(
                        text
                    ),

                "left": left,
                "top": top,

                "width": width,
                "height": height,

                "right":
                    left + width,

                "bottom":
                    top + height,

                "confidence":
                    confidence,
            }
        )

    return words


# ============================================================
# PDF IMAGE EXTRACTION
# ============================================================

def extract_largest_pdf_image(page):

    try:

        images = page.get_images(
            full=True
        )

        if not images:
            return None

        largest = None

        for image_info in images:

            xref = image_info[0]

            try:

                pix = fitz.Pixmap(
                    page.parent,
                    xref
                )

                area = (
                    pix.width *
                    pix.height
                )

                if (
                    largest is None
                    or area > largest["area"]
                ):

                    largest = {
                        "xref": xref,
                        "area": area,
                    }

            except Exception:

                continue

        if largest is None:
            return None

        pix = fitz.Pixmap(
            page.parent,
            largest["xref"]
        )

        if pix.alpha:

            pix = fitz.Pixmap(
                fitz.csRGB,
                pix
            )

        image = Image.frombytes(
            "RGB",
            [
                pix.width,
                pix.height,
            ],
            pix.samples
        )

        rects = page.get_image_rects(
            largest["xref"]
        )

        rect = (
            rects[0]
            if rects
            else page.rect
        )

        return {
            "image": image,
            "rect": rect,
            "width": pix.width,
            "height": pix.height,
        }

    except Exception as error:

        print(
            f"PDF IMAGE ERROR: {error}"
        )

        return None


# ============================================================
# IMAGE COORDINATES → PDF COORDINATES
# ============================================================

def convert_image_words_to_pdf(
    words,
    image_rect,
    image_width,
    image_height,
):

    if (
        image_width <= 0
        or image_height <= 0
    ):

        return words

    scale_x = (
        image_rect.width /
        float(image_width)
    )

    scale_y = (
        image_rect.height /
        float(image_height)
    )

    converted = []

    for word in words:

        left = (
            image_rect.x0
            +
            word["left"] *
            scale_x
        )

        top = (
            image_rect.y0
            +
            word["top"] *
            scale_y
        )

        right = (
            image_rect.x0
            +
            word["right"] *
            scale_x
        )

        bottom = (
            image_rect.y0
            +
            word["bottom"] *
            scale_y
        )

        converted.append(
            {
                **word,

                "pdf_left": left,
                "pdf_top": top,

                "pdf_right": right,
                "pdf_bottom": bottom,

                "coordinate_space":
                    "pdf",
            }
        )

    return converted


# ============================================================
# AADHAAR VERHOEFF VALIDATION
# ============================================================

def verhoeff_validate(number):

    number = re.sub(
        r"\D",
        "",
        str(number)
    )

    if len(number) != 12:
        return False

    multiplication_table = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
        [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
        [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
        [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
        [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
        [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
        [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
        [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
        [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
    ]

    permutation_table = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
        [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
        [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
        [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
        [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
        [2, 7, 9, 5, 8, 1, 4, 0, 6, 3],
        [7, 0, 4, 3, 2, 5, 9, 1, 8, 6],
    ]

    check = 0

    reversed_digits = list(
        map(
            int,
            reversed(number)
        )
    )

    for i, digit in enumerate(
        reversed_digits
    ):

        check = multiplication_table[
            check
        ][
            permutation_table[
                i % 8
            ][digit]
        ]

    return check == 0


# ============================================================
# LUHN VALIDATION
# ============================================================

def luhn_validate(value):

    digits = re.sub(
        r"\D",
        "",
        str(value)
    )

    if len(digits) < 12:
        return False

    total = 0

    parity = len(digits) % 2

    for i, digit in enumerate(
        digits
    ):

        number = int(
            digit
        )

        if i % 2 == parity:

            number *= 2

            if number > 9:
                number -= 9

        total += number

    return total % 10 == 0


# ============================================================
# UPI VALIDATION
# ============================================================

def validate_upi(value):

    value = str(
        value
    ).strip()

    pattern = re.compile(
        r"^[A-Za-z0-9._-]{2,80}"
        r"@[A-Za-z][A-Za-z0-9._-]{1,30}$"
    )

    return bool(
        pattern.fullmatch(
            value
        )
    )


# ============================================================
# PAN CLEANING
# ============================================================

def clean_pan_candidate(value):

    value = re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value)
    ).upper()

    if len(value) != 10:
        return None

    chars = list(
        value
    )

    letter_map = {
        "0": "O",
        "1": "I",
        "2": "Z",
        "5": "S",
        "6": "G",
        "8": "B",
    }

    digit_map = {
        "O": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "Z": "2",
        "S": "5",
        "G": "6",
        "T": "7",
        "B": "8",
        "Q": "0",
    }

    # First 5 positions = letters

    for i in range(5):

        if chars[i].isalpha():
            continue

        if chars[i] in letter_map:

            chars[i] = letter_map[
                chars[i]
            ]

        else:

            return None

    # Next 4 positions = digits

    for i in range(5, 9):

        if chars[i].isdigit():
            continue

        if chars[i] in digit_map:

            chars[i] = digit_map[
                chars[i]
            ]

        else:

            return None

    # Last position = letter

    if not chars[9].isalpha():

        if chars[9] in letter_map:

            chars[9] = letter_map[
                chars[9]
            ]

        else:

            return None

    candidate = "".join(
        chars
    )

    if re.fullmatch(
        r"[A-Z]{5}[0-9]{4}[A-Z]",
        candidate
    ):

        return candidate

    return None


# ============================================================
# SENSITIVE VALUE VALIDATION
# ============================================================

def validate_sensitive_value(
    label,
    value
):

    label = normalize_label(
        label
    )

    value = normalize_sensitive_ocr_value(
        value
    )

    if not value:
        return False

    # --------------------------------------------------------
    # PAN
    # --------------------------------------------------------

    if label == "PAN":

        compact = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value
        ).upper()

        return bool(
            re.fullmatch(
                r"[A-Z]{5}[0-9]{4}[A-Z]",
                compact
            )
        )

    # --------------------------------------------------------
    # AADHAAR
    # --------------------------------------------------------

    if label == "AADHAAR":

        digits = re.sub(
            r"\D",
            "",
            value
        )

        if len(digits) != 12:
            return False

        if digits.startswith("0"):
            return False

        if digits.startswith("1"):
            return False

        return verhoeff_validate(
            digits
        )

    # --------------------------------------------------------
    # CREDIT / DEBIT CARD
    # --------------------------------------------------------

    if label == "CREDITCARDNUMBER":

        digits = re.sub(
            r"\D",
            "",
            value
        )

        if not (
            13 <= len(digits) <= 19
        ):
            return False

        return luhn_validate(
            digits
        )

    # --------------------------------------------------------
    # IFSC
    # --------------------------------------------------------

    if label == "IFSC":

        compact = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value
        ).upper()

        return bool(
            re.fullmatch(
                r"[A-Z]{4}0[A-Z0-9]{6}",
                compact
            )
        )

    # --------------------------------------------------------
    # UPI
    # --------------------------------------------------------

    if label == "UPIID":

        return validate_upi(
            value
        )

    # --------------------------------------------------------
    # PASSPORT
    # --------------------------------------------------------

    if label == "PASSPORTNUM":

        compact = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value
        ).upper()

        return bool(
            re.fullmatch(
                r"[A-Z][0-9]{7}",
                compact
            )
        )

    # --------------------------------------------------------
    # DRIVING LICENCE
    # --------------------------------------------------------

    if label == "DRIVERLICENSENUM":

        compact = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value
        ).upper()

        return bool(
            re.fullmatch(
                r"[A-Z]{2}[0-9]{2}"
                r"[0-9A-Z]{4,16}",
                compact
            )
        )

    # --------------------------------------------------------
    # VOTER ID
    # --------------------------------------------------------

    if label == "VOTERID":

        compact = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value
        ).upper()

        return bool(
            re.fullmatch(
                r"[A-Z]{3}[0-9]{7}",
                compact
            )
        )

    # --------------------------------------------------------
    # BANK ACCOUNT
    # --------------------------------------------------------

    if label == "BANK_ACCOUNT":

        digits = re.sub(
            r"\D",
            "",
            value
        )

        return bool(
            9 <= len(digits) <= 18
        )

    # --------------------------------------------------------
    # CREDENTIALS
    # --------------------------------------------------------

    if label in {
        "PASSWORD",
        "APIKEY",
        "ACCESSTOKEN",
        "SECRETKEY",
    }:

        if len(value) < 8:
            return False

        # A normal word is not a credential.

        if re.fullmatch(
            r"[A-Za-z]+",
            value
        ):

            return False

        # Require numbers or credential
        # punctuation.

        if not re.search(
            r"[0-9_\-+=/:.@]",
            value
        ):

            return False

        return True

    return False


# ============================================================
# FIELD LABELS
# ============================================================

FIELD_LABELS = {

    "PAN": [
        "PAN",
        "PERMANENT ACCOUNT NUMBER",
        "PERMANENT ACCOUNT NUMBER CARD",
    ],

    "AADHAAR": [
        "AADHAAR",
        "AADHAAR NUMBER",
        "AADHAAR NO",
        "UID",
        "UNIQUE IDENTIFICATION NUMBER",
    ],

    "PASSPORTNUM": [
        "PASSPORT",
        "PASSPORT NUMBER",
        "PASSPORT NO",
    ],

    "DRIVERLICENSENUM": [
        "DRIVING LICENCE",
        "DRIVING LICENSE",
        "DRIVING LICENCE NUMBER",
        "DRIVING LICENSE NUMBER",
        "DL NUMBER",
        "DL NO",
    ],

    "VOTERID": [
        "VOTER ID",
        "VOTER ID NUMBER",
        "EPIC",
        "EPIC NUMBER",
    ],

    "BANK_ACCOUNT": [
        "BANK ACCOUNT",
        "ACCOUNT NUMBER",
        "ACCOUNT NO",
        "A/C NO",
        "A/C NUMBER",
    ],

    "IFSC": [
        "IFSC",
        "IFSC CODE",
    ],

    "CREDITCARDNUMBER": [
        "CREDIT CARD",
        "CREDIT CARD NUMBER",
        "CREDIT CARD NO",
    ],

    "DEBITCARDNUMBER": [
        "DEBIT CARD",
        "DEBIT CARD NUMBER",
        "DEBIT CARD NO",
    ],

    "UPIID": [
        "UPI",
        "UPI ID",
        "UPI ID NUMBER",
    ],

    "PASSWORD": [
        "PASSWORD",
        "PASSCODE",
        "PWD",
    ],

    "APIKEY": [
        "API KEY",
        "APIKEY",
    ],

    "ACCESSTOKEN": [
        "ACCESS TOKEN",
        "AUTH TOKEN",
        "BEARER TOKEN",
    ],

    "SECRETKEY": [
        "SECRET KEY",
        "CLIENT SECRET",
    ],
}


# ============================================================
# DIRECT REGEX PATTERNS
# ============================================================

DIRECT_PATTERNS = {

    "PAN": re.compile(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        re.IGNORECASE
    ),

    "AADHAAR": re.compile(
        r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b"
        r"|\b\d{12}\b"
    ),

    "CREDITCARDNUMBER": re.compile(
        r"\b(?:\d[ -]?){13,19}\b"
    ),

    "IFSC": re.compile(
        r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
        re.IGNORECASE
    ),

    "UPIID": re.compile(
        r"\b[A-Za-z0-9._-]{2,80}"
        r"@[A-Za-z][A-Za-z0-9._-]{1,30}\b"
    ),

    "PASSPORTNUM": re.compile(
        r"\b[A-Z][0-9]{7}\b",
        re.IGNORECASE
    ),

    "VOTERID": re.compile(
        r"\b[A-Z]{3}[0-9]{7}\b",
        re.IGNORECASE
    ),

    "DRIVERLICENSENUM": re.compile(
        r"\b[A-Z]{2}[0-9]{2}"
        r"[0-9A-Z]{4,16}\b",
        re.IGNORECASE
    ),

    "APIKEY": re.compile(
        r"\b(?:sk|pk|api)[-_]"
        r"[A-Za-z0-9_-]{12,}\b",
        re.IGNORECASE
    ),

    "ACCESSTOKEN": re.compile(
        r"\b(?:eyJ[A-Za-z0-9_-]{10,}"
        r"(?:\.[A-Za-z0-9_-]+){1,2})\b"
    ),

    "SECRETKEY": re.compile(
        r"\b(?:secret|client_secret)"
        r"[-_=:\s]+"
        r"[A-Za-z0-9_\-]{8,}\b",
        re.IGNORECASE
    ),

    "PASSWORD": re.compile(
        r"\b(?:password|passwd|pwd)"
        r"\s*[:=]\s*"
        r"[^\s,;]{8,}\b",
        re.IGNORECASE
    ),
}


# ============================================================
# CREATE DETECTION
# ============================================================

def make_detection(
    label,
    value,
    bbox=None,
    page_number=None,
    source="ocr",
    coordinate_space=None,
):

    label = normalize_label(
        label
    )

    value = normalize_sensitive_ocr_value(
        value
    )

    detection = {
        "label": label,
        "value": value,
        "text": value,
        "source": source,
    }

    if bbox:

        detection.update(
            {
                "left":
                    bbox.get("left"),

                "top":
                    bbox.get("top"),

                "right":
                    bbox.get("right"),

                "bottom":
                    bbox.get("bottom"),
            }
        )

    if coordinate_space:

        detection[
            "coordinate_space"
        ] = coordinate_space

    if page_number is not None:

        detection[
            "page_number"
        ] = page_number

    return detection


# ============================================================
# FULL TEXT DETECTION
# ============================================================

def detect_from_full_text(
    full_text
):

    detections = []

    if not full_text:
        return detections

    text = normalize_text(
        full_text
    )

    # --------------------------------------------------------
    # PAN
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "PAN"
    ].finditer(text):

        candidate = clean_pan_candidate(
            match.group()
        )

        if not candidate:
            continue

        if validate_sensitive_value(
            "PAN",
            candidate
        ):

            detections.append(
                {
                    "label":
                        "PAN",

                    "value":
                        candidate,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # AADHAAR
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "AADHAAR"
    ].finditer(text):

        value = match.group()

        if validate_sensitive_value(
            "AADHAAR",
            value
        ):

            detections.append(
                {
                    "label":
                        "AADHAAR",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # IFSC
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "IFSC"
    ].finditer(text):

        value = match.group()

        if validate_sensitive_value(
            "IFSC",
            value
        ):

            detections.append(
                {
                    "label":
                        "IFSC",

                    "value":
                        value.upper(),

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # CARD
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "CREDITCARDNUMBER"
    ].finditer(text):

        value = match.group()

        digits = re.sub(
            r"\D",
            "",
            value
        )

        if validate_sensitive_value(
            "CREDITCARDNUMBER",
            digits
        ):

            detections.append(
                {
                    "label":
                        "CREDITCARDNUMBER",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # UPI
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "UPIID"
    ].finditer(text):

        value = match.group()

        if validate_sensitive_value(
            "UPIID",
            value
        ):

            detections.append(
                {
                    "label":
                        "UPIID",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # PASSPORT
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "PASSPORTNUM"
    ].finditer(text):

        value = match.group()

        if not validate_sensitive_value(
            "PASSPORTNUM",
            value
        ):
            continue

        context = text[
            max(
                0,
                match.start() - 100
            ):
            min(
                len(text),
                match.end() + 100
            )
        ]

        normalized_context = normalize_label_text(
            context
        )

        if "PASSPORT" not in normalized_context:
            continue

        detections.append(
            {
                "label":
                    "PASSPORTNUM",

                "value":
                    value.upper(),

                "source":
                    "ocr_full_text",

                "text_start":
                    match.start(),

                "text_end":
                    match.end(),
            }
        )

    # --------------------------------------------------------
    # DRIVING LICENCE
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "DRIVERLICENSENUM"
    ].finditer(text):

        value = match.group()

        if not validate_sensitive_value(
            "DRIVERLICENSENUM",
            value
        ):
            continue

        context = text[
            max(
                0,
                match.start() - 120
            ):
            min(
                len(text),
                match.end() + 120
            )
        ]

        normalized_context = normalize_label_text(
            context
        )

        if not (
            "DRIVINGLICENCE"
            in normalized_context
            or
            "DRIVINGLICENSE"
            in normalized_context
            or
            "DLNUMBER"
            in normalized_context
            or
            "DLNO"
            in normalized_context
        ):
            continue

        detections.append(
            {
                "label":
                    "DRIVERLICENSENUM",

                "value":
                    value.upper(),

                "source":
                    "ocr_full_text",

                "text_start":
                    match.start(),

                "text_end":
                    match.end(),
            }
        )

    # --------------------------------------------------------
    # VOTER ID
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "VOTERID"
    ].finditer(text):

        value = match.group()

        if not validate_sensitive_value(
            "VOTERID",
            value
        ):
            continue

        context = text[
            max(
                0,
                match.start() - 100
            ):
            min(
                len(text),
                match.end() + 100
            )
        ]

        normalized_context = normalize_label_text(
            context
        )

        if not (
            "VOTERID"
            in normalized_context
            or
            "EPIC"
            in normalized_context
        ):
            continue

        detections.append(
            {
                "label":
                    "VOTERID",

                "value":
                    value.upper(),

                "source":
                    "ocr_full_text",

                "text_start":
                    match.start(),

                "text_end":
                    match.end(),
            }
        )

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "APIKEY"
    ].finditer(text):

        value = match.group()

        if validate_sensitive_value(
            "APIKEY",
            value
        ):

            detections.append(
                {
                    "label":
                        "APIKEY",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # ACCESS TOKEN
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "ACCESSTOKEN"
    ].finditer(text):

        value = match.group()

        if validate_sensitive_value(
            "ACCESSTOKEN",
            value
        ):

            detections.append(
                {
                    "label":
                        "ACCESSTOKEN",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # SECRET KEY
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "SECRETKEY"
    ].finditer(text):

        full_value = match.group()

        parts = re.split(
            r"[-_=:\s]+",
            full_value,
            maxsplit=1
        )

        value = (
            parts[1]
            if len(parts) == 2
            else full_value
        )

        if validate_sensitive_value(
            "SECRETKEY",
            value
        ):

            detections.append(
                {
                    "label":
                        "SECRETKEY",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    for match in DIRECT_PATTERNS[
        "PASSWORD"
    ].finditer(text):

        full_value = match.group()

        parts = re.split(
            r"[:=]\s*",
            full_value,
            maxsplit=1
        )

        value = (
            parts[1]
            if len(parts) == 2
            else full_value
        )

        if validate_sensitive_value(
            "PASSWORD",
            value
        ):

            detections.append(
                {
                    "label":
                        "PASSWORD",

                    "value":
                        value,

                    "source":
                        "ocr_full_text",

                    "text_start":
                        match.start(),

                    "text_end":
                        match.end(),
                }
            )

    return detections


# ============================================================
# BOUNDING BOX UTILITIES
# ============================================================

def make_bbox(
    left,
    top,
    width,
    height
):

    return {
        "left": int(left),
        "top": int(top),
        "right": int(
            left + width
        ),
        "bottom": int(
            top + height
        ),
    }


def union_boxes(boxes):

    if not boxes:
        return None

    return {
        "left": min(
            box["left"]
            for box in boxes
        ),

        "top": min(
            box["top"]
            for box in boxes
        ),

        "right": max(
            box["right"]
            for box in boxes
        ),

        "bottom": max(
            box["bottom"]
            for box in boxes
        ),
    }


# ============================================================
# EXACT VALUE BBOX
# ============================================================

def find_exact_value_bbox(
    words,
    value
):

    target = normalize_label_text(
        value
    )

    if not target:
        return None

    for word in words:

        if (
            word.get("normalized", "")
            ==
            target
        ):

            return {
                "left":
                    word["left"],

                "top":
                    word["top"],

                "right":
                    word["right"],

                "bottom":
                    word["bottom"],
            }

    return None


# ============================================================
# MULTI-WORD VALUE BBOX
# ============================================================

def find_partial_value_bbox(
    words,
    value
):

    target = normalize_label_text(
        value
    )

    if not target:
        return None

    for start in range(
        len(words)
    ):

        combined = ""

        selected = []

        for end in range(
            start,
            min(
                len(words),
                start + 8
            )
        ):

            combined += (
                words[end].get(
                    "normalized",
                    ""
                )
            )

            selected.append(
                words[end]
            )

            if combined == target:

                return union_boxes(
                    selected
                )

            if len(combined) > len(target):
                break

    return None


# ============================================================
# ATTACH BBOX
# ============================================================

def attach_bbox_to_detection(
    detection,
    words
):

    value = detection.get(
        "value",
        ""
    )

    bbox = find_exact_value_bbox(
        words,
        value
    )

    if bbox:

        detection.update(
            bbox
        )

        return detection

    bbox = find_partial_value_bbox(
        words,
        value
    )

    if bbox:

        detection.update(
            bbox
        )

    return detection


# ============================================================
# PAN LABEL LOCATION
# ============================================================

def find_pan_label_region(
    words,
    image_width,
    image_height
):

    """
    Find the PAN label dynamically.

    No fixed PAN-card coordinates are used.

    The function looks for words such as:
        PERMANENT
        ACCOUNT
        NUMBER
        CARD
    """

    normalized = [
        word.get(
            "normalized",
            ""
        )
        for word in words
    ]

    target_words = {
        "PERMANENT",
        "ACCOUNT",
        "NUMBER",
        "CARD",
    }

    for i, word in enumerate(
        words
    ):

        current = word.get(
            "normalized",
            ""
        )

        if current not in target_words:
            continue

        selected = [word]

        combined = current

        for j in range(
            i + 1,
            min(
                len(words),
                i + 6
            )
        ):

            next_word = words[j]

            # Keep approximately same text line.
            if abs(
                next_word["top"]
                -
                word["top"]
            ) > 100:

                break

            selected.append(
                next_word
            )

            combined += (
                next_word.get(
                    "normalized",
                    ""
                )
            )

            if (
                "PERMANENTACCOUNTNUMBER"
                in combined
                or
                "PERMANENTACCOUNTNUMBERCARD"
                in combined
            ):

                return union_boxes(
                    selected
                )

    return None


# ============================================================
# TARGETED PAN OCR WITH BOUNDING BOX
# ============================================================

def detect_pan_with_targeted_ocr(
    image
):

    """
    Generic targeted PAN detection.

    It does NOT assume where the PAN is located.

    It performs:
        1. Normal OCR data
        2. Multiple OCR configurations
        3. PAN whitelist OCR
        4. Dynamic label-based crop when required

    Returned coordinates are IMAGE coordinates.
    """

    if image is None:
        return []

    detections = []

    seen = set()

    if image.mode != "RGB":

        image = image.convert(
            "RGB"
        )

    variants = make_ocr_variants(
        image
    )

    # --------------------------------------------------------
    # Pass 1:
    # Search normal OCR data.
    # --------------------------------------------------------

    for variant_name, variant in variants:

        configs = [
            "--oem 3 --psm 6",
            "--oem 3 --psm 11",
            "--oem 3 --psm 12",
        ]

        for config in configs:

            data = get_image_ocr_data(
                variant,
                config=config
            )

            words = normalize_ocr_words(
                data
            )

            for word in words:

                candidate = (
                    clean_pan_candidate(
                        word["text"]
                    )
                )

                if not candidate:
                    continue

                if not validate_sensitive_value(
                    "PAN",
                    candidate
                ):
                    continue

                if candidate in seen:
                    continue

                seen.add(
                    candidate
                )

                bbox = {
                    "left":
                        word["left"],

                    "top":
                        word["top"],

                    "right":
                        word["right"],

                    "bottom":
                        word["bottom"],
                }

                detections.append(
                    make_detection(
                        "PAN",
                        candidate,
                        bbox=bbox,
                        source="pan_ocr_data",
                        coordinate_space="image",
                    )
                )

    # --------------------------------------------------------
    # Pass 2:
    # Full OCR text.
    # --------------------------------------------------------

    for variant_name, variant in variants:

        for config in [
            "--oem 3 --psm 6",
            "--oem 3 --psm 11",
            "--oem 3 --psm 12",
        ]:

            try:

                text = pytesseract.image_to_string(
                    variant,
                    config=config
                )

            except Exception:

                continue

            if not text:
                continue

            # Search all plausible alphanumeric tokens.
            tokens = re.findall(
                r"[A-Za-z0-9]{8,14}",
                text
            )

            for token in tokens:

                candidate = (
                    clean_pan_candidate(
                        token
                    )
                )

                if not candidate:
                    continue

                if not validate_sensitive_value(
                    "PAN",
                    candidate
                ):
                    continue

                if candidate in seen:
                    continue

                # We found the PAN value but not its position.
                # Continue below and try to find its bbox.
                seen.add(
                    candidate
                )

                detections.append(
                    make_detection(
                        "PAN",
                        candidate,
                        source="pan_targeted_ocr",
                        coordinate_space="image",
                    )
                )

    # --------------------------------------------------------
    # Pass 3:
    # Dynamic PAN-label crop.
    #
    # This is NOT a fixed card coordinate.
    # It finds "Permanent Account Number Card"
    # and examines the area around that detected label.
    # --------------------------------------------------------

    for variant_name, variant in variants:

        data = get_image_ocr_data(
            variant,
            config="--oem 3 --psm 11"
        )

        words = normalize_ocr_words(
            data
        )

        label_bbox = (
            find_pan_label_region(
                words,
                image.width,
                image.height
            )
        )

        if not label_bbox:
            continue

        # ----------------------------------------------------
        # Dynamic crop below the detected label.
        # ----------------------------------------------------

        crop_left = max(
            0,
            int(
                label_bbox["left"]
                - label_bbox["left"] * 0.20
            )
        )

        crop_top = max(
            0,
            int(
                label_bbox["bottom"]
                - 10
            )
        )

        crop_right = min(
            image.width,
            int(
                label_bbox["right"]
                +
                max(
                    100,
                    image.width * 0.35
                )
            )
        )

        crop_bottom = min(
            image.height,
            int(
                label_bbox["bottom"]
                +
                max(
                    120,
                    image.height * 0.25
                )
            )
        )

        if crop_right <= crop_left:
            continue

        if crop_bottom <= crop_top:
            continue

        crop = variant.crop(
            (
                crop_left,
                crop_top,
                crop_right,
                crop_bottom,
            )
        )

        crop_configs = [
            "--oem 3 --psm 6 "
            "-c tessedit_char_whitelist="
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",

            "--oem 3 --psm 11 "
            "-c tessedit_char_whitelist="
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",

            "--oem 3 --psm 12 "
            "-c tessedit_char_whitelist="
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        ]

        for config in crop_configs:

            crop_data = get_image_ocr_data(
                crop,
                config=config
            )

            crop_words = normalize_ocr_words(
                crop_data
            )

            for word in crop_words:

                candidate = (
                    clean_pan_candidate(
                        word["text"]
                    )
                )

                if not candidate:
                    continue

                if not validate_sensitive_value(
                    "PAN",
                    candidate
                ):
                    continue

                bbox = {
                    "left":
                        crop_left
                        +
                        word["left"],

                    "top":
                        crop_top
                        +
                        word["top"],

                    "right":
                        crop_left
                        +
                        word["right"],

                    "bottom":
                        crop_top
                        +
                        word["bottom"],
                }

                if candidate in seen:

                    # Upgrade a previous detection
                    # that had no coordinates.
                    for existing in detections:

                        if (
                            existing.get(
                                "value"
                            )
                            ==
                            candidate
                        ):

                            existing.update(
                                bbox
                            )

                            existing[
                                "coordinate_space"
                            ] = "image"

                    continue

                seen.add(
                    candidate
                )

                detections.append(
                    make_detection(
                        "PAN",
                        candidate,
                        bbox=bbox,
                        source="pan_targeted_crop",
                        coordinate_space="image",
                    )
                )

    return detections


# ============================================================
# AADHAAR WORD DETECTION
# ============================================================

def get_numeric_candidates(words):

    candidates = []

    for word in words:

        digits = re.sub(
            r"\D",
            "",
            word["text"]
        )

        if not digits:
            continue

        candidates.append(
            {
                **word,
                "digits": digits,
            }
        )

    return candidates


def detect_aadhaar_from_words(
    words
):

    candidates = get_numeric_candidates(
        words
    )

    detections = []

    for i in range(
        len(candidates) - 2
    ):

        first = candidates[i]
        second = candidates[i + 1]
        third = candidates[i + 2]

        if not (
            len(first["digits"]) == 4
            and
            len(second["digits"]) == 4
            and
            len(third["digits"]) == 4
        ):
            continue

        if abs(
            first["top"]
            -
            second["top"]
        ) > 40:
            continue

        if abs(
            second["top"]
            -
            third["top"]
        ) > 40:
            continue

        number = (
            first["digits"]
            +
            second["digits"]
            +
            third["digits"]
        )

        if not verhoeff_validate(
            number
        ):
            continue

        bbox = {
            "left": min(
                first["left"],
                second["left"],
                third["left"]
            ),

            "top": min(
                first["top"],
                second["top"],
                third["top"]
            ),

            "right": max(
                first["right"],
                second["right"],
                third["right"]
            ),

            "bottom": max(
                first["bottom"],
                second["bottom"],
                third["bottom"]
            ),
        }

        detections.append(
            make_detection(
                "AADHAAR",
                number,
                bbox=bbox,
                source="ocr_words"
            )
        )

    return detections


# ============================================================
# CARD WORD DETECTION
# ============================================================

def detect_card_from_words(
    words
):

    detections = []

    for i in range(
        len(words)
    ):

        combined = ""

        selected = []

        for j in range(
            i,
            min(
                len(words),
                i + 5
            )
        ):

            digits = re.sub(
                r"\D",
                "",
                words[j]["text"]
            )

            if not digits:
                break

            combined += digits

            selected.append(
                words[j]
            )

            if not (
                13 <= len(combined) <= 19
            ):
                continue

            if luhn_validate(
                combined
            ):

                bbox = union_boxes(
                    selected
                )

                detections.append(
                    make_detection(
                        "CREDITCARDNUMBER",
                        combined,
                        bbox=bbox,
                        source="ocr_words"
                    )
                )

                break

    return detections


# ============================================================
# IFSC WORD DETECTION
# ============================================================

def detect_ifsc_from_words(
    words
):

    detections = []

    for word in words:

        value = re.sub(
            r"[^A-Za-z0-9]",
            "",
            word["text"]
        ).upper()

        if validate_sensitive_value(
            "IFSC",
            value
        ):

            bbox = {
                "left":
                    word["left"],

                "top":
                    word["top"],

                "right":
                    word["right"],

                "bottom":
                    word["bottom"],
            }

            detections.append(
                make_detection(
                    "IFSC",
                    value,
                    bbox=bbox,
                    source="ocr_words"
                )
            )

    return detections


# ============================================================
# UPI WORD DETECTION
# ============================================================

def detect_upi_from_words(
    words
):

    detections = []

    for word in words:

        value = word[
            "text"
        ].strip()

        if "@" not in value:
            continue

        if validate_sensitive_value(
            "UPIID",
            value
        ):

            bbox = {
                "left":
                    word["left"],

                "top":
                    word["top"],

                "right":
                    word["right"],

                "bottom":
                    word["bottom"],
            }

            detections.append(
                make_detection(
                    "UPIID",
                    value,
                    bbox=bbox,
                    source="ocr_words"
                )
            )

    return detections


# ============================================================
# PAN WORD DETECTION
# ============================================================

def detect_pan_from_ocr_words(
    words
):

    detections = []

    for word in words:

        candidate = clean_pan_candidate(
            word["text"]
        )

        if not candidate:
            continue

        if validate_sensitive_value(
            "PAN",
            candidate
        ):

            bbox = {
                "left":
                    word["left"],

                "top":
                    word["top"],

                "right":
                    word["right"],

                "bottom":
                    word["bottom"],
            }

            detections.append(
                make_detection(
                    "PAN",
                    candidate,
                    bbox=bbox,
                    source="ocr_words"
                )
            )

    return detections


# ============================================================
# LABEL BASED DETECTION
# ============================================================

def detect_labeled_value(
    words,
    label
):

    label = normalize_label(
        label
    )

    labels = [
        normalize_label_text(
            item
        )
        for item in FIELD_LABELS.get(
            label,
            []
        )
    ]

    if not labels:
        return []

    detections = []

    strict_credentials = {
        "PASSWORD",
        "APIKEY",
        "ACCESSTOKEN",
        "SECRETKEY",
    }

    for i, word in enumerate(
        words
    ):

        current = word.get(
            "normalized",
            ""
        )

        if current not in labels:
            continue

        for j in range(
            i + 1,
            min(
                len(words),
                i + 5
            )
        ):

            candidate = words[j]

            value = candidate.get(
                "text",
                ""
            ).strip()

            if not value:
                continue

            candidate_normalized = (
                candidate.get(
                    "normalized",
                    ""
                )
            )

            if candidate_normalized in labels:
                continue

            # ------------------------------------------------
            # Same approximate line.
            # ------------------------------------------------

            vertical_distance = abs(
                candidate["top"]
                -
                word["top"]
            )

            if vertical_distance > 80:
                break

            # ------------------------------------------------
            # Reasonable horizontal distance.
            # ------------------------------------------------

            horizontal_distance = (
                candidate["left"]
                -
                word["right"]
            )

            if horizontal_distance > 350:
                break

            # ------------------------------------------------
            # Credentials require stronger evidence.
            # ------------------------------------------------

            if label in strict_credentials:

                if len(value) < 8:
                    continue

                if re.fullmatch(
                    r"[A-Za-z]+",
                    value
                ):
                    continue

                if not re.search(
                    r"[0-9_\-+=/:.@]",
                    value
                ):
                    continue

            # ------------------------------------------------
            # Validate.
            # ------------------------------------------------

            if not validate_sensitive_value(
                label,
                value
            ):
                continue

            bbox = {
                "left":
                    candidate["left"],

                "top":
                    candidate["top"],

                "right":
                    candidate["right"],

                "bottom":
                    candidate["bottom"],
            }

            detections.append(
                make_detection(
                    label,
                    value,
                    bbox=bbox,
                    source="ocr_label",
                    coordinate_space=
                        candidate.get(
                            "coordinate_space"
                        )
                )
            )

            break

    return detections


# ============================================================
# FIND PAN BBOX
# ============================================================

def find_pan_bbox(
    words,
    pan_value
):

    bbox = find_exact_value_bbox(
        words,
        pan_value
    )

    if bbox:
        return bbox

    bbox = find_partial_value_bbox(
        words,
        pan_value
    )

    if bbox:
        return bbox

    # --------------------------------------------------------
    # OCR similarity fallback.
    # --------------------------------------------------------

    target = normalize_label_text(
        pan_value
    )

    best_word = None
    best_score = 0

    for word in words:

        candidate = word.get(
            "normalized",
            ""
        )

        if not candidate:
            continue

        if len(candidate) < 8:
            continue

        matches = 0

        for a, b in zip(
            candidate,
            target
        ):

            if a == b:
                matches += 1

        score = (
            matches /
            max(
                len(target),
                len(candidate)
            )
        )

        if score > best_score:

            best_score = score
            best_word = word

    if (
        best_word is not None
        and
        best_score >= 0.70
    ):

        return {
            "left":
                best_word["left"],

            "top":
                best_word["top"],

            "right":
                best_word["right"],

            "bottom":
                best_word["bottom"],
        }

    return None


# ============================================================
# DEDUPLICATION
# ============================================================

def detections_overlap(
    first,
    second
):

    required = (
        "left",
        "top",
        "right",
        "bottom",
    )

    if not all(
        key in first
        for key in required
    ):
        return False

    if not all(
        key in second
        for key in required
    ):
        return False

    return (
        first["left"]
        <
        second["right"]
        and
        second["left"]
        <
        first["right"]
        and
        first["top"]
        <
        second["bottom"]
        and
        second["top"]
        <
        first["bottom"]
    )


def detection_priority(
    detection
):

    source = detection.get(
        "source",
        ""
    )

    # Prefer detections having coordinates.
    has_bbox = all(
        key in detection
        for key in (
            "left",
            "top",
            "right",
            "bottom"
        )
    )

    if has_bbox and (
        "targeted"
        in source
        or
        "ocr_data"
        in source
    ):
        return 4

    if has_bbox:
        return 3

    if "ocr" in source:
        return 2

    return 1


def deduplicate_detections(
    detections
):

    final = []

    for detection in detections:

        duplicate_index = None

        for index, existing in enumerate(
            final
        ):

            same_label = (
                normalize_label(
                    detection.get(
                        "label",
                        ""
                    )
                )
                ==
                normalize_label(
                    existing.get(
                        "label",
                        ""
                    )
                )
            )

            same_value = (
                normalize_label_text(
                    detection.get(
                        "value",
                        ""
                    )
                )
                ==
                normalize_label_text(
                    existing.get(
                        "value",
                        ""
                    )
                )
            )

            overlap = detections_overlap(
                detection,
                existing
            )

            if (
                same_label
                and
                (
                    same_value
                    or
                    overlap
                )
            ):

                duplicate_index = index
                break

        if duplicate_index is None:

            final.append(
                detection
            )

        else:

            existing = final[
                duplicate_index
            ]

            if (
                detection_priority(
                    detection
                )
                >
                detection_priority(
                    existing
                )
            ):

                final[
                    duplicate_index
                ] = detection

    return final


# ============================================================
# MAIN PAGE DETECTOR
# ============================================================

def detect_sensitive_fields_from_page(
    words,
    full_text="",
    image=None
):

    detections = []

    # ========================================================
    # PAN TARGETED OCR
    # ========================================================

    if image is not None:

        pan_detections = (
            detect_pan_with_targeted_ocr(
                image
            )
        )

        # ----------------------------------------------------
        # Try to attach PDF/image bbox from normal words.
        # ----------------------------------------------------

        for detection in pan_detections:

            if not all(
                key in detection
                for key in (
                    "left",
                    "top",
                    "right",
                    "bottom"
                )
            ):

                bbox = find_pan_bbox(
                    words,
                    detection[
                        "value"
                    ]
                )

                if bbox:

                    detection.update(
                        bbox
                    )

                    # The words may already be in
                    # PDF coordinate space.
                    if words and words[0].get(
                        "coordinate_space"
                    ) == "pdf":

                        detection[
                            "coordinate_space"
                        ] = "pdf"

            detections.append(
                detection
            )

    # ========================================================
    # FULL TEXT
    # ========================================================

    full_text_detections = (
        detect_from_full_text(
            full_text
        )
    )

    for detection in (
        full_text_detections
    ):

        detection = (
            attach_bbox_to_detection(
                detection,
                words
            )
        )

        if all(
            key in detection
            for key in (
                "left",
                "top",
                "right",
                "bottom"
            )
        ):

            if words:

                coordinate_space = (
                    words[0].get(
                        "coordinate_space"
                    )
                )

                if coordinate_space:

                    detection[
                        "coordinate_space"
                    ] = coordinate_space

        detections.append(
            detection
        )

    # ========================================================
    # WORD DETECTION
    # ========================================================

    detections.extend(
        detect_pan_from_ocr_words(
            words
        )
    )

    detections.extend(
        detect_aadhaar_from_words(
            words
        )
    )

    detections.extend(
        detect_card_from_words(
            words
        )
    )

    detections.extend(
        detect_ifsc_from_words(
            words
        )
    )

    detections.extend(
        detect_upi_from_words(
            words
        )
    )

    # ========================================================
    # LABEL DETECTION
    # ========================================================

    for label in FIELD_LABELS:

        detections.extend(
            detect_labeled_value(
                words,
                label
            )
        )

    # ========================================================
    # FINAL STRICT VALIDATION
    # ========================================================

    valid = []

    for detection in detections:

        label = normalize_label(
            detection.get(
                "label",
                ""
            )
        )

        value = detection.get(
            "value",
            ""
        )

        # Only approved sensitive labels.
        if label not in (
            ALLOWED_SENSITIVE_LABELS
        ):

            continue

        # Validate value.
        if not validate_sensitive_value(
            label,
            value
        ):

            continue

        detection[
            "label"
        ] = label

        valid.append(
            detection
        )

    # ========================================================
    # DEDUPLICATE
    # ========================================================

    return deduplicate_detections(
        valid
    )


# ============================================================
# DOCUMENT LEVEL DETECTION
# ============================================================

def detect_sensitive_fields_from_ocr(
    document_data
):

    detections = []

    if not document_data:
        return detections

    pages = document_data.get(
        "pages",
        []
    )

    for page_index, page in enumerate(
        pages
    ):

        words = page.get(
            "words",
            []
        )

        full_text = page.get(
            "full_text",
            page.get(
                "text",
                ""
            )
        )

        image = page.get(
            "image"
        )

        page_number = page.get(
            "page_number",
            page_index + 1
        )

        page_detections = (
            detect_sensitive_fields_from_page(
                words,
                full_text=full_text,
                image=image
            )
        )

        for detection in page_detections:

            detection[
                "page_number"
            ] = page_number

        detections.extend(
            page_detections
        )

    return deduplicate_detections(
        detections
    )


# ============================================================
# DOCUMENT EXTRACTION
# ============================================================

def extract_document_data(
    file_path
):

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in (
        SUPPORTED_EXTENSIONS
    ):

        raise ValueError(
            "Unsupported file type: "
            + extension
        )

    # ========================================================
    # IMAGE FILE
    # ========================================================

    if extension in {
        ".png",
        ".jpg",
        ".jpeg",
    }:

        image = Image.open(
            file_path
        ).convert(
            "RGB"
        )

        ocr_image = (
            preprocess_ocr_image(
                image
            )
        )

        full_text = (
            extract_text_from_image(
                ocr_image,
                config="--oem 3 --psm 6"
            )
        )

        data = get_image_ocr_data(
            ocr_image,
            config="--oem 3 --psm 6"
        )

        words = normalize_ocr_words(
            data
        )

        # ----------------------------------------------------
        # Image coordinates are kept as image coordinates.
        # ----------------------------------------------------

        for word in words:

            word[
                "coordinate_space"
            ] = "image"

        return {
            "type":
                "image",

            "pages": [
                {
                    "page_number":
                        1,

                    "image":
                        image,

                    "ocr_image":
                        ocr_image,

                    "words":
                        words,

                    "full_text":
                        full_text,

                    "text":
                        full_text,

                    "width":
                        image.width,

                    "height":
                        image.height,

                    "coordinate_space":
                        "image",
                }
            ],

            "text":
                full_text,
        }

    # ========================================================
    # PDF
    # ========================================================

    document = fitz.open(
        file_path
    )

    pages = []

    all_text = []

    for page_index, page in enumerate(
        document
    ):

        page_number = (
            page_index + 1
        )

        # ----------------------------------------------------
        # Native PDF text
        # ----------------------------------------------------

        native_text = normalize_text(
            page.get_text(
                "text"
            )
        )

        # ----------------------------------------------------
        # Embedded image
        # ----------------------------------------------------

        image_info = (
            extract_largest_pdf_image(
                page
            )
        )

        if image_info:

            image = image_info[
                "image"
            ]

            ocr_image = (
                preprocess_ocr_image(
                    image
                )
            )

            full_text = (
                extract_text_from_image(
                    ocr_image,
                    config="--oem 3 --psm 6"
                )
            )

            data = get_image_ocr_data(
                ocr_image,
                config="--oem 3 --psm 6"
            )

            image_words = normalize_ocr_words(
                data
            )

            pdf_words = (
                convert_image_words_to_pdf(
                    image_words,
                    image_info["rect"],
                    image_info["width"],
                    image_info["height"]
                )
            )

            page_text = (
                full_text
                if full_text
                else native_text
            )

            pages.append(
                {
                    "page_number":
                        page_number,

                    "type":
                        "image",

                    "image":
                        image,

                    "ocr_image":
                        ocr_image,

                    "words":
                        pdf_words,

                    "image_words":
                        image_words,

                    "full_text":
                        page_text,

                    "text":
                        page_text,

                    "pdf_rect":
                        image_info["rect"],

                    "image_width":
                        image_info["width"],

                    "image_height":
                        image_info["height"],

                    "coordinate_space":
                        "pdf",
                }
            )

            all_text.append(
                page_text
            )

            continue

        # ----------------------------------------------------
        # Native PDF text
        # ----------------------------------------------------

        if native_text:

            native_words = []

            try:

                raw_words = (
                    page.get_text(
                        "words"
                    )
                )

                for item in raw_words:

                    if len(item) < 5:
                        continue

                    x0, y0, x1, y1, text = (
                        item[:5]
                    )

                    text = (
                        normalize_sensitive_ocr_value(
                            text
                        )
                    )

                    if not text:
                        continue

                    native_words.append(
                        {
                            "text":
                                text,

                            "normalized":
                                normalize_label_text(
                                    text
                                ),

                            "left":
                                x0,

                            "top":
                                y0,

                            "right":
                                x1,

                            "bottom":
                                y1,

                            "width":
                                x1 - x0,

                            "height":
                                y1 - y0,

                            "pdf_left":
                                x0,

                            "pdf_top":
                                y0,

                            "pdf_right":
                                x1,

                            "pdf_bottom":
                                y1,

                            "confidence":
                                100,

                            "coordinate_space":
                                "pdf",
                        }
                    )

            except Exception:

                native_words = []

            pages.append(
                {
                    "page_number":
                        page_number,

                    "type":
                        "pdf",

                    "image":
                        None,

                    "ocr_image":
                        None,

                    "words":
                        native_words,

                    "full_text":
                        native_text,

                    "text":
                        native_text,

                    "pdf_rect":
                        page.rect,

                    "coordinate_space":
                        "pdf",
                }
            )

            all_text.append(
                native_text
            )

            continue

        # ----------------------------------------------------
        # Render PDF page when no text/image is available.
        # ----------------------------------------------------

        matrix = fitz.Matrix(
            PDF_OCR_SCALE,
            PDF_OCR_SCALE
        )

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image = Image.frombytes(
            "RGB",
            [
                pix.width,
                pix.height
            ],
            pix.samples
        )

        ocr_image = (
            preprocess_ocr_image(
                image
            )
        )

        full_text = (
            extract_text_from_image(
                ocr_image,
                config="--oem 3 --psm 6"
            )
        )

        data = get_image_ocr_data(
            ocr_image,
            config="--oem 3 --psm 6"
        )

        image_words = normalize_ocr_words(
            data
        )

        pdf_words = (
            convert_image_words_to_pdf(
                image_words,
                page.rect,
                image.width,
                image.height
            )
        )

        pages.append(
            {
                "page_number":
                    page_number,

                "type":
                    "image",

                "image":
                    image,

                "ocr_image":
                    ocr_image,

                "words":
                    pdf_words,

                "image_words":
                    image_words,

                "full_text":
                    full_text,

                "text":
                    full_text,

                "pdf_rect":
                    page.rect,

                "image_width":
                    image.width,

                "image_height":
                    image.height,

                "coordinate_space":
                    "pdf",
            }
        )

        all_text.append(
            full_text
        )

    document.close()

    return {
        "type":
            "pdf",

        "pages":
            pages,

        "text":
            "\n".join(
                all_text
            ).strip(),
    }


# ============================================================
# MASKED TEXT PREVIEW
# ============================================================

def create_masked_text_preview(
    document_data,
    detections
):

    try:

        from modules.masking import (
            mask_text_by_values
        )

        text = document_data.get(
            "text",
            ""
        )

        return mask_text_by_values(
            text,
            detections
        )

    except Exception:

        return document_data.get(
            "text",
            ""
        )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def get_masked_text_preview(
    document_data,
    detections
):

    return create_masked_text_preview(
        document_data,
        detections
    )