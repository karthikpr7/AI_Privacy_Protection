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


# ============================================================
# OCR SETTINGS
# ============================================================

PDF_OCR_SCALE = 1.5

# Memory-safe OCR limits for Render/free-tier environments.
OCR_MAX_DIMENSION = 2200
OCR_TIMEOUT = 15

# PAN fallback: one bounded OCR call only.
PAN_FALLBACK_MAX_DIMENSION = 1600
PAN_FALLBACK_TIMEOUT = 8

OCR_CONFIG = "--oem 3 --psm 6"


# ============================================================
# ONLY THESE LABELS ARE ALLOWED TO BE SENSITIVE
# ============================================================

ALLOWED_SENSITIVE_LABELS = {

    "PAN",

    "AADHAAR",

    "PASSPORTNUM",

    "DRIVERLICENSENUM",

    "VOTERID",

    "BANK_ACCOUNT",

    "BANKACCOUNT",

    "IFSC",

    "CREDITCARDNUMBER",

    "DEBITCARDNUMBER",

    "UPIID",

    "PASSWORD",

    "APIKEY",

    "ACCESSTOKEN",

    "SECRETKEY",
}


# ============================================================
# LABEL ALIASES
# ============================================================

LABEL_ALIASES = {

    "BANKACCOUNT":
        "BANK_ACCOUNT",

    "VOTERIDNUM":
        "VOTERID",

    "DEBITCARDNUMBER":
        "CREDITCARDNUMBER",

    "API_KEY":
        "APIKEY",

    "ACCESS_TOKEN":
        "ACCESSTOKEN",

    "SECRET_KEY":
        "SECRETKEY",

    "UPI_ID":
        "UPIID",
}


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
        "\r\n",
        "\n"
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


# ============================================================
# LABEL NORMALIZATION
# ============================================================

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


# ============================================================
# BASIC OCR VALUE CLEANING
# ============================================================

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




# ============================================================
# MEMORY-SAFE OCR RESIZE
# ============================================================

def resize_image_for_ocr(image, max_dimension=OCR_MAX_DIMENSION):
    """Create a bounded OCR copy and return (image, scale)."""

    if image is None:
        return None, 1.0

    width, height = image.size

    if width <= 0 or height <= 0:
        return image, 1.0

    largest = max(width, height)

    if largest <= max_dimension:
        return image, 1.0

    scale = max_dimension / float(largest)

    resized = image.resize(
        (
            max(1, int(round(width * scale))),
            max(1, int(round(height * scale)))
        ),
        Image.Resampling.LANCZOS
    )

    return resized, scale


def restore_ocr_word_scale(words, scale):
    """Map OCR boxes back to original image coordinates."""

    if not words or scale == 1.0:
        return words

    inverse = 1.0 / scale
    restored = []

    for word in words:
        item = dict(word)
        item["left"] = word["left"] * inverse
        item["top"] = word["top"] * inverse
        item["right"] = word["right"] * inverse
        item["bottom"] = word["bottom"] * inverse
        item["width"] = word["width"] * inverse
        item["height"] = word["height"] * inverse
        restored.append(item)

    return restored

# ============================================================
# OCR VARIANTS
# ============================================================

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
# OCR TEXT
# ============================================================

def extract_text_from_image(
    image,
    config=OCR_CONFIG
):

    try:

        return normalize_text(
            pytesseract.image_to_string(
                image,
                config=config,
                timeout=OCR_TIMEOUT
            )
        )

    except Exception as error:

        print(
            f"OCR TEXT ERROR: {error}"
        )

        return ""


# ============================================================
# OCR WORD DATA
# ============================================================

def get_image_ocr_data(
    image,
    config=OCR_CONFIG
):

    try:

        data = pytesseract.image_to_data(
            image,
            config=config,
            output_type=pytesseract.Output.DICT,
            timeout=OCR_TIMEOUT
        )

        words = []

        total = len(
            data.get(
                "text",
                []
            )
        )

        for index in range(total):

            text = str(
                data["text"][index]
            ).strip()

            if not text:
                continue

            try:

                left = int(
                    data["left"][index]
                )

                top = int(
                    data["top"][index]
                )

                width = int(
                    data["width"][index]
                )

                height = int(
                    data["height"][index]
                )

                conf = float(
                    data["conf"][index]
                )

            except Exception:

                continue

            words.append(
                {
                    "text":
                        text,

                    "left":
                        left,

                    "top":
                        top,

                    "width":
                        width,

                    "height":
                        height,

                    "right":
                        left + width,

                    "bottom":
                        top + height,

                    "conf":
                        conf,
                }
            )

        return words

    except Exception as error:

        print(
            f"OCR DATA ERROR: {error}"
        )

        return []


# ============================================================
# NORMALIZE OCR WORDS
# ============================================================

def normalize_ocr_words(
    words
):

    normalized = []

    for original in words:

        text = str(
            original.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        left = float(
            original.get(
                "left",
                original.get(
                    "x0",
                    0
                )
            )
        )

        top = float(
            original.get(
                "top",
                original.get(
                    "y0",
                    0
                )
            )
        )

        right = float(
            original.get(
                "right",
                original.get(
                    "x1",
                    left + 1
                )
            )
        )

        bottom = float(
            original.get(
                "bottom",
                original.get(
                    "y1",
                    top + 1
                )
            )
        )

        width = float(
            original.get(
                "width",
                right - left
            )
        )

        height = float(
            original.get(
                "height",
                bottom - top
            )
        )

        normalized.append(
            {
                "text":
                    text,

                "normalized":
                    normalize_label_text(
                        text
                    ),

                "left":
                    left,

                "top":
                    top,

                "width":
                    width,

                "height":
                    height,

                "right":
                    right,

                "bottom":
                    bottom,

                "conf":
                    original.get(
                        "conf",
                        original.get(
                            "confidence",
                            -1
                        )
                    ),
            }
        )

    return normalized


# ============================================================
# UNION BOXES
# ============================================================

def union_boxes(
    words
):

    if not words:
        return None

    return {

        "left":
            min(
                word["left"]
                for word in words
            ),

        "top":
            min(
                word["top"]
                for word in words
            ),

        "right":
            max(
                word["right"]
                for word in words
            ),

        "bottom":
            max(
                word["bottom"]
                for word in words
            ),
    }


# ============================================================
# PDF IMAGE EXTRACTION
# ============================================================

def extract_largest_pdf_image(
    page
):

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
                    or
                    area >
                    largest["area"]
                ):

                    largest = {
                        "xref":
                            xref,

                        "area":
                            area,
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
            (
                pix.width,
                pix.height
            ),
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

            "image":
                image,

            "rect":
                rect,

            "width":
                pix.width,

            "height":
                pix.height,
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
    image_height
):

    if (
        image_width <= 0
        or
        image_height <= 0
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

                "pdf_left":
                    left,

                "pdf_top":
                    top,

                "pdf_right":
                    right,

                "pdf_bottom":
                    bottom,

                "left":
                    left,

                "top":
                    top,

                "right":
                    right,

                "bottom":
                    bottom,

                "width":
                    right - left,

                "height":
                    bottom - top,
            }
        )

    return converted


# ============================================================
# AADHAAR VERHOEFF
# ============================================================

def verhoeff_validate(
    number
):

    number = re.sub(
        r"\D",
        "",
        str(number)
    )

    if len(number) != 12:
        return False

    multiplication_table = [

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],

        [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],

        [2, 7, 4, 1, 5, 9, 6, 8, 0, 3],

        [3, 8, 0, 5, 7, 2, 9, 4, 1, 6],

        [4, 9, 1, 0, 6, 3, 8, 2, 7, 5],

        [5, 4, 8, 7, 3, 0, 2, 9, 6, 1],

        [6, 2, 9, 8, 0, 1, 5, 3, 4, 7],

        [7, 0, 5, 9, 1, 6, 4, 2, 3, 8],

        [8, 1, 6, 4, 9, 5, 7, 0, 2, 3],

        [9, 3, 7, 2, 8, 4, 1, 6, 5, 0],
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

    for index, digit in enumerate(
        reversed_digits
    ):

        check = multiplication_table[
            check
        ][
            permutation_table[
                index % 8
            ][digit]
        ]

    return check == 0


# ============================================================
# LUHN
# ============================================================

def luhn_validate(
    value
):

    digits = re.sub(
        r"\D",
        "",
        str(value)
    )

    if not (
        13 <= len(digits) <= 19
    ):
        return False

    total = 0

    parity = len(digits) % 2

    for index, digit in enumerate(
        digits
    ):

        number = int(
            digit
        )

        if index % 2 == parity:

            number *= 2

            if number > 9:
                number -= 9

        total += number

    return (
        total % 10 == 0
    )


# ============================================================
# UPI VALIDATION
# ============================================================

def validate_upi(
    value
):

    if not value:
        return False

    value = str(
        value
    ).strip()

    # --------------------------------------------------------
    # A UPI ID must contain exactly one @
    # --------------------------------------------------------

    if value.count("@") != 1:
        return False

    username, provider = value.split(
        "@",
        1
    )

    username = username.strip()
    provider = provider.strip()

    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    if not re.fullmatch(
        r"[A-Za-z0-9._-]{2,80}",
        username
    ):
        return False

    # --------------------------------------------------------
    # PROVIDER
    # --------------------------------------------------------

    if not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9._-]{1,30}",
        provider
    ):
        return False

    # --------------------------------------------------------
    # IMPORTANT:
    # Normal email addresses must NEVER become UPI.
    # --------------------------------------------------------

    email_domains = {

        "gmail.com",
        "googlemail.com",

        "yahoo.com",
        "yahoo.co.in",

        "outlook.com",
        "hotmail.com",
        "live.com",

        "icloud.com",

        "protonmail.com",
        "proton.me",

        "mail.com",

        "rediffmail.com",
    }

    if provider.lower() in email_domains:
        return False

    # --------------------------------------------------------
    # A provider containing a normal web/email domain
    # should not be treated as UPI.
    # --------------------------------------------------------

    if "." in provider:
        return False

    return True


# ============================================================
# PAN CLEANING
# ============================================================

def clean_pan_candidate(
    value
):

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

    for index in range(5):

        if chars[index].isalpha():
            continue

        if chars[index] in letter_map:

            chars[index] = letter_map[
                chars[index]
            ]

        else:

            return None

    # Next 4 positions = digits

    for index in range(5, 9):

        if chars[index].isdigit():
            continue

        if chars[index] in digit_map:

            chars[index] = digit_map[
                chars[index]
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
# NORMALIZE VALUE BY LABEL
# ============================================================

def normalize_sensitive_value(
    label,
    value
):

    label = LABEL_ALIASES.get(
        str(label).upper().strip(),
        str(label).upper().strip()
    )

    value = normalize_sensitive_ocr_value(
        value
    )

    if label == "PAN":

        return re.sub(
            r"[^A-Za-z0-9]",
            "",
            value.upper()
        )

    if label == "AADHAAR":

        return re.sub(
            r"\D",
            "",
            value
        )

    if label == "PASSPORTNUM":

        return re.sub(
            r"[^A-Za-z0-9]",
            "",
            value.upper()
        )

    if label == "DRIVERLICENSENUM":

        value = re.sub(
            r"[^A-Za-z0-9-]",
            "",
            value.upper()
        )

        # OCR commonly reads O as 0 in the numeric
        # portion of an Indian driving licence.

        if len(value) >= 2:

            prefix = value[:2]

            remainder = value[2:]

            remainder = remainder.replace(
                "O",
                "0"
            )

            value = (
                prefix
                +
                remainder
            )

        return value

    if label in {
        "VOTERID",
        "VOTERIDNUM",
    }:

        return re.sub(
            r"[^A-Za-z0-9]",
            "",
            value.upper()
        )

    if label in {
        "BANK_ACCOUNT",
        "BANKACCOUNT",
    }:

        return re.sub(
            r"\D",
            "",
            value
        )

    if label == "IFSC":

        value = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value.upper()
        )

        if (
            len(value) == 11
            and value[4] == "O"
        ):

            value = (
                value[:4]
                +
                "0"
                +
                value[5:]
            )

        return value

    if label in {
        "CREDITCARDNUMBER",
        "DEBITCARDNUMBER",
    }:

        return re.sub(
            r"\D",
            "",
            value
        )

    if label in {
        "UPIID",
        "UPI_ID",
    }:

        return re.sub(
            r"\s+",
            "",
            value
        )

    return value


# ============================================================
# SENSITIVE VALUE VALIDATION
# ============================================================

def validate_sensitive_value(
    label,
    value
):

    label = LABEL_ALIASES.get(
        str(label).upper().strip(),
        str(label).upper().strip()
    )

    value = normalize_sensitive_value(
        label,
        value
    )

    if not value:
        return False

    # --------------------------------------------------------
    # PAN
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
    # PASSPORT
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
            r"[^A-Za-z0-9]",
            "",
            value.upper()
        )

        # Indian DL numbers commonly begin with
        # a two-letter state code followed by digits.

        return bool(
            re.fullmatch(
                r"[A-Z]{2}[0-9]{2}[A-Z0-9]{6,16}",
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
            value.upper()
        )

        return bool(
            re.fullmatch(
                r"[A-Z]{3}[0-9]{7}",
                compact
            )
        )

    # --------------------------------------------------------
    # BANK ACCOUNT
    # --------------------------------------------------------

    if label in {
        "BANK_ACCOUNT",
        "BANKACCOUNT",
    }:

        digits = re.sub(
            r"\D",
            "",
            value
        )

        return (
            8 <= len(digits) <= 18
        )

    # --------------------------------------------------------
    # IFSC
    # --------------------------------------------------------

    if label == "IFSC":

        compact = re.sub(
            r"[^A-Za-z0-9]",
            "",
            value.upper()
        )

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
        "DEBITCARDNUMBER",
    }:

        return luhn_validate(
            value
        )

    # --------------------------------------------------------
    # UPI
    # --------------------------------------------------------

    if label == "UPIID":

        return validate_upi(
            value
        )

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------

    if label == "PASSWORD":

        if len(value) < 8:
            return False

        if re.fullmatch(
            r"[A-Za-z]+",
            value
        ):
            return False

        return True

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    if label == "APIKEY":

        return bool(
            re.search(
                r"[A-Za-z0-9_\-]",
                value
            )
        ) and len(value) >= 12

    # --------------------------------------------------------
    # ACCESS TOKEN
    # --------------------------------------------------------

    if label == "ACCESSTOKEN":

        return (
            len(value) >= 12
            and
            (
                value.startswith("eyJ")
                or
                "." in value
            )
        )

    # --------------------------------------------------------
    # SECRET KEY
    # --------------------------------------------------------

    if label == "SECRETKEY":

        return (
            len(value) >= 8
            and
            not re.fullmatch(
                r"[A-Za-z]+",
                value
            )
        )

    return False


# ============================================================
# FIELD LABELS
# ============================================================

FIELD_LABELS = {

    "PAN": [

        "pan",
        "pan number",
        "pan no",
    ],

    "AADHAAR": [

        "aadhaar",
        "aadhaar number",
        "aadhaar no",

        "aadhar",
        "aadhar number",
        "aadhar no",
    ],

    "PASSPORTNUM": [

        "passport number",
        "passport no",
    ],

    "DRIVERLICENSENUM": [

        "driving license number",
        "driving licence number",

        "driving license no",
        "driving licence no",

        "dl number",
        "dl no",
    ],

    "VOTERID": [

        "voter id",
        "voter id number",
        "voter id no",

        "epic",
        "epic number",
        "epic no",
    ],

    "BANK_ACCOUNT": [

        "bank account",
        "bank account number",
        "bank account no",
    ],

    "IFSC": [

        "ifsc",
        "ifsc code",
        "ifsc number",
    ],

    "CREDITCARDNUMBER": [

        "credit card",
        "credit card number",
        "credit card no",
    ],

    "DEBITCARDNUMBER": [

        "debit card",
        "debit card number",
        "debit card no",
    ],

    "UPIID": [

        "upi id",
        "upi",
    ],

    "PASSWORD": [

        "password",
        "passwd",
        "pwd",
    ],

    "APIKEY": [

        "api key",
        "apikey",
    ],

    "ACCESSTOKEN": [

        "access token",
        "access_token",
        "bearer token",
    ],

    "SECRETKEY": [

        "secret key",
        "secret_key",
        "client secret",
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
        r"|"
        r"\b\d{12}\b"
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
        r"@"
        r"[A-Za-z][A-Za-z0-9._-]{1,30}\b"
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
        r"[A-Z0-9]{6,16}\b",
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
# MAKE DETECTION
# ============================================================

def make_detection(
    label,
    value,
    bbox=None,
    page_number=None,
    source="ocr"
):

    label = LABEL_ALIASES.get(
        str(label).upper(),
        str(label).upper()
    )

    value = normalize_sensitive_value(
        label,
        value
    )

    detection = {

        "label":
            label,

        "value":
            value,

        "text":
            value,

        "source":
            source,
    }

    if bbox:

        detection.update(
            {
                "left":
                    bbox.get(
                        "left"
                    ),

                "top":
                    bbox.get(
                        "top"
                    ),

                "right":
                    bbox.get(
                        "right"
                    ),

                "bottom":
                    bbox.get(
                        "bottom"
                    ),
            }
        )

    if page_number is not None:

        detection[
            "page_number"
        ] = page_number

    return detection


# ============================================================
# FIND EXACT VALUE BBOX
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

        candidate = normalize_label_text(
            word.get(
                "text",
                ""
            )
        )

        if candidate == target:

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
# FIND PARTIAL VALUE BBOX
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

    for index in range(
        len(words)
    ):

        combined = ""

        selected = []

        for j in range(
            index,
            min(
                len(words),
                index + 5
            )
        ):

            text = words[j].get(
                "text",
                ""
            )

            normalized = normalize_label_text(
                text
            )

            if not normalized:
                break

            combined += normalized

            selected.append(
                words[j]
            )

            if combined == target:

                return union_boxes(
                    selected
                )

            if len(combined) >= len(target):

                break

    return None


# ============================================================
# ATTACH BBOX TO FULL-TEXT DETECTION
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

    if not bbox:

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
    # CREDIT CARD
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
                        digits,

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

        # IMPORTANT:
        # Email addresses are rejected here.

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

        context_normalized = normalize_label_text(
            context
        )

        if "PASSPORT" not in context_normalized:

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
                match.start() - 150
            ):
            min(
                len(text),
                match.end() + 150
            )
        ]

        context_normalized = normalize_label_text(
            context
        )

        if not (
            "DRIVINGLICENCE"
            in context_normalized
            or
            "DRIVINGLICENSE"
            in context_normalized
            or
            "DLNUMBER"
            in context_normalized
            or
            "DLNO"
            in context_normalized
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

        context_normalized = normalize_label_text(
            context
        )

        if not (
            "VOTERID"
            in context_normalized
            or
            "EPIC"
            in context_normalized
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
# LABEL-BASED DETECTION
# ============================================================

def detect_labeled_value(
    words,
    label
):

    label = LABEL_ALIASES.get(
        str(label).upper(),
        str(label).upper()
    )

    label_variants = FIELD_LABELS.get(
        label,
        []
    )

    normalized_labels = {

        normalize_label_text(
            item
        )

        for item in label_variants
    }

    if not normalized_labels:
        return []

    detections = []

    strict_credentials = {

        "PASSWORD",
        "APIKEY",
        "ACCESSTOKEN",
        "SECRETKEY",
    }

    for index, word in enumerate(
        words
    ):

        current = word.get(
            "normalized",
            ""
        )

        if not current:
            continue

        # ----------------------------------------------------
        # Single-word labels
        # ----------------------------------------------------

        matched_label_length = 0
        matched_label_words = []

        for length in range(
            1,
            5
        ):

            end = index + length

            if end > len(words):
                break

            group = words[
                index:end
            ]

            # All label words should be on same row.

            if len(group) > 1:

                tops = [
                    item["top"]
                    for item in group
                ]

                if (
                    max(tops)
                    -
                    min(tops)
                    > 80
                ):
                    break

            group_text = "".join(
                item.get(
                    "normalized",
                    ""
                )
                for item in group
            )

            group_text_spaced = normalize_label_text(
                " ".join(
                    item.get(
                        "text",
                        ""
                    )
                    for item in group
                )
            )

            if (
                group_text in normalized_labels
                or
                group_text_spaced in normalized_labels
            ):

                matched_label_length = length

                matched_label_words = group

        if not matched_label_length:
            continue

        label_right = max(
            item["right"]
            for item in matched_label_words
        )

        label_top = min(
            item["top"]
            for item in matched_label_words
        )

        # ----------------------------------------------------
        # Look AFTER the complete label.
        #
        # This is the important fix.
        #
        # Example:
        #
        # Bank Account Number : 123456789012
        #
        # The value may be 4 words after "Bank".
        # ----------------------------------------------------

        start_value_index = (
            index
            +
            matched_label_length
        )

        candidate_words = []

        for j in range(
            start_value_index,
            min(
                len(words),
                start_value_index + 7
            )
        ):

            candidate = words[j]

            value_text = str(
                candidate.get(
                    "text",
                    ""
                )
            ).strip()

            if not value_text:
                continue

            normalized_candidate = candidate.get(
                "normalized",
                ""
            )

            # ------------------------------------------------
            # Same-row check
            # ------------------------------------------------

            vertical_distance = abs(
                candidate["top"]
                -
                label_top
            )

            if vertical_distance > 80:

                break

            # ------------------------------------------------
            # Horizontal distance
            # ------------------------------------------------

            horizontal_distance = (
                candidate["left"]
                -
                label_right
            )

            if horizontal_distance > 500:

                break

            # ------------------------------------------------
            # Ignore separators.
            #
            # This fixes:
            #
            # Label : VALUE
            #
            # where ":" occupies its own OCR word.
            # ------------------------------------------------

            if normalized_candidate in {
                "",
                ":",
                "-",
                "–",
                "—",
                ">",
                "|",
            }:

                continue

            if value_text in {
                ":",
                "-",
                "–",
                "—",
                ">",
                "|",
            }:

                continue

            # ------------------------------------------------
            # If another approved field label is encountered,
            # stop searching.
            # ------------------------------------------------

            all_label_values = set()

            for values in FIELD_LABELS.values():

                for item in values:

                    all_label_values.add(
                        normalize_label_text(
                            item
                        )
                    )

            if normalized_candidate in all_label_values:

                break

            candidate_words.append(
                candidate
            )

            # ------------------------------------------------
            # For these document fields, the value is normally
            # one OCR word. Therefore validate each candidate.
            # ------------------------------------------------

            candidate_value = candidate.get(
                "text",
                ""
            )

            candidate_value = normalize_sensitive_value(
                label,
                candidate_value
            )

            # ------------------------------------------------
            # Credential protection
            # ------------------------------------------------

            if label in strict_credentials:

                if len(candidate_value) < 8:
                    continue

                if re.fullmatch(
                    r"[A-Za-z]+",
                    candidate_value
                ):

                    continue

                if not re.search(
                    r"[0-9_\-+=/:.@]",
                    candidate_value
                ):

                    continue

            # ------------------------------------------------
            # UPI
            # ------------------------------------------------

            if label == "UPIID":

                # Never accept an email address.

                if "@" not in candidate_value:

                    continue

                if not validate_upi(
                    candidate_value
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
                        candidate_value,
                        bbox=bbox,
                        source="ocr_label"
                    )
                )

                break

            # ------------------------------------------------
            # Normal sensitive identifiers
            # ------------------------------------------------

            if validate_sensitive_value(
                label,
                candidate_value
            ):

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
                        candidate_value,
                        bbox=bbox,
                        source="ocr_label"
                    )
                )

                break

            # ------------------------------------------------
            # Don't keep combining arbitrary words.
            #
            # This prevents:
            #
            # "Father's"
            # "Department"
            # "Sharma"
            #
            # from becoming credentials.
            # ------------------------------------------------

            if len(candidate_words) >= 2:

                break

    return detections


# ============================================================
# NUMERIC CANDIDATES
# ============================================================

def get_numeric_candidates(
    words
):

    candidates = []

    for word in words:

        digits = re.sub(
            r"\D",
            "",
            word.get(
                "text",
                ""
            )
        )

        if not digits:
            continue

        candidates.append(
            {
                **word,

                "digits":
                    digits,
            }
        )

    return candidates


# ============================================================
# AADHAAR WORD DETECTION
# ============================================================

def detect_aadhaar_from_words(
    words
):

    detections = []

    candidates = get_numeric_candidates(
        words
    )

    for index in range(
        len(candidates)
    ):

        first = candidates[index]

        # One word containing 12 digits

        if len(
            first["digits"]
        ) == 12:

            number = first[
                "digits"
            ]

            if validate_sensitive_value(
                "AADHAAR",
                number
            ):

                bbox = union_boxes(
                    [first]
                )

                detections.append(
                    make_detection(
                        "AADHAAR",
                        number,
                        bbox=bbox,
                        source="ocr_words"
                    )
                )

        # Three groups:
        # 1234 5678 9012

        if index + 2 >= len(
            candidates
        ):
            continue

        second = candidates[
            index + 1
        ]

        third = candidates[
            index + 2
        ]

        if not (
            len(first["digits"]) == 4
            and
            len(second["digits"]) == 4
            and
            len(third["digits"]) == 4
        ):

            continue

        if abs(
            second["top"]
            -
            first["top"]
        ) > 40:

            continue

        if abs(
            third["top"]
            -
            first["top"]
        ) > 40:

            continue

        number = (
            first["digits"]
            +
            second["digits"]
            +
            third["digits"]
        )

        if not validate_sensitive_value(
            "AADHAAR",
            number
        ):

            continue

        bbox = union_boxes(
            [
                first,
                second,
                third,
            ]
        )

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

    for index in range(
        len(words)
    ):

        combined = ""

        selected = []

        for j in range(
            index,
            min(
                len(words),
                index + 5
            )
        ):

            digits = re.sub(
                r"\D",
                "",
                words[j].get(
                    "text",
                    ""
                )
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

                if len(combined) > 19:
                    break

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
            word.get(
                "text",
                ""
            )
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

        value = str(
            word.get(
                "text",
                ""
            )
        ).strip()

        if "@" not in value:
            continue

        # IMPORTANT:
        # validate_upi() rejects normal emails.

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
            word.get(
                "text",
                ""
            )
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
# PAN TARGETED OCR
# ============================================================

def detect_pan_with_targeted_ocr(image):

    # Last-resort fallback: ONE bounded Tesseract call.
    if image is None:
        return []

    try:
        working_image, scale = resize_image_for_ocr(
            image,
            PAN_FALLBACK_MAX_DIMENSION
        )

        if working_image.mode != "RGB":
            working_image = working_image.convert("RGB")

        gray = ImageOps.grayscale(working_image)
        gray = ImageOps.autocontrast(gray)

        try:
            import cv2
            import numpy as np

            array = np.asarray(gray)
            _, thresholded = cv2.threshold(
                array,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            processed = Image.fromarray(thresholded)
        except Exception:
            processed = gray

        try:
            data = pytesseract.image_to_data(
                processed,
                config="--oem 3 --psm 6",
                output_type=pytesseract.Output.DICT,
                timeout=PAN_FALLBACK_TIMEOUT
            )
        except Exception as error:
            print(f"PAN fallback OCR skipped: {error}")
            return []

        detections = []
        total = len(data.get("text", []))

        for index in range(total):
            raw = str(data["text"][index]).strip()

            if not raw:
                continue

            candidate = clean_pan_candidate(raw)

            if not candidate:
                compact = re.sub(r"[^A-Za-z0-9]", "", raw)
                candidate = clean_pan_candidate(compact)

            if not candidate:
                continue

            if not validate_sensitive_value("PAN", candidate):
                continue

            detection = {
                "label": "PAN",
                "value": candidate,
                "source": "pan_targeted_ocr",
                "ocr_variant": "fast",
                "ocr_config": "--oem 3 --psm 6",
            }

            try:
                left = float(data["left"][index]) / scale
                top = float(data["top"][index]) / scale
                right = (
                    float(data["left"][index])
                    + float(data["width"][index])
                ) / scale
                bottom = (
                    float(data["top"][index])
                    + float(data["height"][index])
                ) / scale

                detection.update({
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                })
            except Exception:
                pass

            detections.append(detection)

        return deduplicate_detections(detections)

    except Exception as error:
        print(f"PAN fallback OCR error: {error}")
        return []



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

        for first, second in zip(
            candidate,
            target
        ):

            if first == second:
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
# DETECTION OVERLAP
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


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_detections(
    detections
):

    final = []

    for detection in detections:

        label = LABEL_ALIASES.get(
            str(
                detection.get(
                    "label",
                    ""
                )
            ).upper(),
            str(
                detection.get(
                    "label",
                    ""
                )
            ).upper()
        )

        value = detection.get(
            "value",
            ""
        )

        duplicate = False

        for existing in final:

            existing_label = existing.get(
                "label",
                ""
            )

            existing_value = existing.get(
                "value",
                ""
            )

            same_label = (
                label
                ==
                existing_label
            )

            same_value = (
                normalize_label_text(
                    value
                )
                ==
                normalize_label_text(
                    existing_value
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

                duplicate = True

                # Prefer detection with coordinates.

                if (
                    "left" in detection
                    and
                    "left" not in existing
                ):

                    existing.update(
                        detection
                    )

                break

        if not duplicate:

            final.append(
                detection
            )

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
    # 1. NORMAL FULL-TEXT DETECTION
    # ========================================================

    full_text_detections = detect_from_full_text(full_text)

    for detection in full_text_detections:
        detection = attach_bbox_to_detection(
            detection,
            words
        )
        detections.append(detection)

    # ========================================================
    # 2. NORMAL WORD DETECTION
    # ========================================================

    detections.extend(detect_pan_from_ocr_words(words))
    detections.extend(detect_aadhaar_from_words(words))
    detections.extend(detect_card_from_words(words))
    detections.extend(detect_ifsc_from_words(words))
    detections.extend(detect_upi_from_words(words))

    # ========================================================
    # 3. LABEL DETECTION
    # ========================================================

    for label in FIELD_LABELS:
        detections.extend(
            detect_labeled_value(words, label)
        )

    # ========================================================
    # 4. PAN FALLBACK ONLY IF NORMAL OCR MISSED PAN
    # ========================================================

    pan_already_found = any(
        LABEL_ALIASES.get(
            str(item.get("label", "")).upper().strip(),
            str(item.get("label", "")).upper().strip()
        ) == "PAN"
        for item in detections
    )

    if image is not None and not pan_already_found:
        detections.extend(
            detect_pan_with_targeted_ocr(image)
        )

    # ========================================================
    # 5. STRICT FINAL VALIDATION
    # ========================================================

    valid = []

    for detection in detections:
        label = detection.get("label", "")
        value = detection.get("value", "")

        label = LABEL_ALIASES.get(
            str(label).upper(),
            str(label).upper()
        )

        if label not in ALLOWED_SENSITIVE_LABELS:
            continue

        if not validate_sensitive_value(label, value):
            continue

        detection["label"] = label
        valid.append(detection)

    return deduplicate_detections(valid)



# ============================================================
# DOCUMENT-LEVEL DETECTION
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

    if not os.path.exists(
        file_path
    ):

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension not in SUPPORTED_EXTENSIONS:

        raise ValueError(
            "Unsupported file type: "
            +
            extension
        )

    # ========================================================
    # IMAGE
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

        ocr_source, ocr_scale = resize_image_for_ocr(
            image
        )

        ocr_image = preprocess_ocr_image(
            ocr_source
        )

        full_text = extract_text_from_image(
            ocr_image,
            OCR_CONFIG
        )

        raw_words = get_image_ocr_data(
            ocr_image,
            OCR_CONFIG
        )

        words = normalize_ocr_words(raw_words)

        words = restore_ocr_word_scale(
            words,
            ocr_scale
        )

        return {

            "type":
                "image",

            "path":
                file_path,

            "pages": [

                {
                    "page_number":
                        1,

                    "type":
                        "image",

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

        # ====================================================
        # FIRST:
        # Try embedded scanned image.
        # ====================================================

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
                    OCR_CONFIG
                )
            )

            raw_words = get_image_ocr_data(
                ocr_image,
                OCR_CONFIG
            )

            words = normalize_ocr_words(
                raw_words
            )

            words = (
                convert_image_words_to_pdf(
                    words,

                    image_info[
                        "rect"
                    ],

                    image_info[
                        "width"
                    ],

                    image_info[
                        "height"
                    ]
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
                        words,

                    "full_text":
                        full_text,

                    "text":
                        full_text,

                    "pdf_rect":
                        page.rect,

                    "image_rect":
                        image_info[
                            "rect"
                        ],

                    "width":
                        image.width,

                    "height":
                        image.height,
                }
            )

            all_text.append(
                full_text
            )

            continue

        # ====================================================
        # SECOND:
        # Native PDF text.
        # ====================================================

        native_text = normalize_text(
            page.get_text(
                "text"
            )
        )

        if native_text:

            native_words = []

            try:

                raw_words = page.get_text(
                    "words"
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

                            "conf":
                                100,
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
                }
            )

            all_text.append(
                native_text
            )

            continue

        # ====================================================
        # THIRD:
        # Render PDF page and OCR it.
        # ====================================================

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
            (
                pix.width,
                pix.height
            ),
            pix.samples
        )

        ocr_source, ocr_scale = resize_image_for_ocr(
            image
        )

        ocr_image = preprocess_ocr_image(
            ocr_source
        )

        full_text = extract_text_from_image(
            ocr_image,
            OCR_CONFIG
        )

        raw_words = get_image_ocr_data(
            ocr_image,
            OCR_CONFIG
        )

        image_words = normalize_ocr_words(raw_words)

        image_words = restore_ocr_word_scale(
            image_words,
            ocr_scale
        )

        page_words = []

        for word in image_words:

            page_words.append(
                {
                    **word,

                    "left":
                        word["left"]
                        /
                        PDF_OCR_SCALE,

                    "top":
                        word["top"]
                        /
                        PDF_OCR_SCALE,

                    "right":
                        word["right"]
                        /
                        PDF_OCR_SCALE,

                    "bottom":
                        word["bottom"]
                        /
                        PDF_OCR_SCALE,

                    "width":
                        word["width"]
                        /
                        PDF_OCR_SCALE,

                    "height":
                        word["height"]
                        /
                        PDF_OCR_SCALE,
                }
            )

        pages.append(
            {
                "page_number":
                    page_number,

                "type":
                    "ocr",

                "image":
                    image,

                "ocr_image":
                    ocr_image,

                "words":
                    page_words,

                "full_text":
                    full_text,

                "text":
                    full_text,

                "scale":
                    PDF_OCR_SCALE,

                "width":
                    pix.width,

                "height":
                    pix.height,

                "pdf_width":
                    page.rect.width,

                "pdf_height":
                    page.rect.height,

                "pdf_rect":
                    page.rect,
            }
        )

        all_text.append(
            full_text
        )

    document.close()

    return {

        "type":
            "pdf",

        "path":
            file_path,

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