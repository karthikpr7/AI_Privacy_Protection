import os
import re

import cv2
import fitz
import numpy as np

from PIL import Image, ImageDraw, ImageFont

from modules.masking import mask_value


# ============================================================
# CONFIGURATION
# ============================================================

PDF_RENDER_SCALE = 1.5
INPAINT_RADIUS = 3

MIN_FONT_SIZE = 5
MAX_FONT_SIZE = 100


# ============================================================
# ALLOWED SENSITIVE LABELS
# ============================================================

ALLOWED_LABELS = {
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
    "UPI_ID": "UPIID",
    "API_KEY": "APIKEY",
    "ACCESS_TOKEN": "ACCESSTOKEN",
    "SECRET_KEY": "SECRETKEY",
}


# ============================================================
# LABEL NORMALIZATION
# ============================================================

def normalize_label(label):
    label = str(label or "").strip().upper()

    return LABEL_ALIASES.get(
        label,
        label
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_compare(value):
    return re.sub(
        r"[^A-Z0-9@._-]",
        "",
        str(value or "").upper()
    )


def normalize_digits(value):
    return re.sub(
        r"\D",
        "",
        str(value or "")
    )


# ============================================================
# MASKING
# ============================================================

def get_masked_value(
    value,
    label
):
    return mask_value(
        value,
        label
    )


# ============================================================
# CLEAN DETECTIONS
# ============================================================

def clean_detections(detections):

    if not isinstance(
        detections,
        list
    ):
        return []

    result = []
    seen = set()

    for detection in detections:

        if not isinstance(
            detection,
            dict
        ):
            continue

        label = normalize_label(
            detection.get("label")
        )

        if label not in ALLOWED_LABELS:
            continue

        value = str(
            detection.get(
                "value",
                ""
            )
        ).strip()

        if not value:
            continue

        try:

            left = float(
                detection["left"]
            )

            top = float(
                detection["top"]
            )

            right = float(
                detection["right"]
            )

            bottom = float(
                detection["bottom"]
            )

        except Exception:

            continue

        if right <= left:
            continue

        if bottom <= top:
            continue

        try:

            page_number = int(
                detection.get(
                    "page_number",
                    1
                )
            )

        except Exception:

            page_number = 1

        key = (
            label,
            value.upper(),
            page_number,
            round(left, 1),
            round(top, 1),
            round(right, 1),
            round(bottom, 1)
        )

        if key in seen:
            continue

        seen.add(key)

        item = dict(
            detection
        )

        item["label"] = label
        item["value"] = value
        item["page_number"] = page_number

        result.append(
            item
        )

    return result


# ============================================================
# PAGE DETECTIONS
# ============================================================

def get_page_detections(
    detections,
    page_number
):

    result = []

    for detection in detections:

        try:

            detection_page = int(
                detection.get(
                    "page_number",
                    1
                )
            )

        except Exception:

            detection_page = 1

        if detection_page == page_number:

            result.append(
                detection
            )

    return result


# ============================================================
# PDF PAGE TYPE
# ============================================================

def is_native_text_page(
    page
):

    try:

        words = page.get_text(
            "words"
        )

    except Exception:

        return False

    meaningful_words = 0

    for word in words:

        if len(word) < 5:
            continue

        text = str(
            word[4]
        ).strip()

        if text:
            meaningful_words += 1

    return meaningful_words >= 2


# ============================================================
# GET PDF WORDS
# ============================================================

def get_pdf_words(
    page
):

    try:

        words = page.get_text(
            "words"
        )

    except Exception:

        return []

    result = []

    for word in words:

        if len(word) < 5:
            continue

        text = str(
            word[4]
        ).strip()

        if not text:
            continue

        result.append({
            "x0": float(word[0]),
            "y0": float(word[1]),
            "x1": float(word[2]),
            "y1": float(word[3]),
            "text": text,
            "block": int(word[5]),
            "line": int(word[6]),
            "word": int(word[7])
        })

    return result


# ============================================================
# GET PDF SPANS
# ============================================================

def get_pdf_spans(
    page
):

    try:

        data = page.get_text(
            "dict"
        )

    except Exception:

        return []

    result = []

    for block in data.get(
        "blocks",
        []
    ):

        if block.get(
            "type"
        ) != 0:
            continue

        for line in block.get(
            "lines",
            []
        ):

            for span in line.get(
                "spans",
                []
            ):

                text = str(
                    span.get(
                        "text",
                        ""
                    )
                ).strip()

                bbox = span.get(
                    "bbox"
                )

                if not text or not bbox:
                    continue

                result.append({
                    "text": text,

                    "bbox": tuple(
                        float(x)
                        for x in bbox
                    ),

                    "font": span.get(
                        "font",
                        ""
                    ),

                    "size": float(
                        span.get(
                            "size",
                            10
                        )
                    ),

                    "color": int(
                        span.get(
                            "color",
                            0
                        )
                    ),

                    "flags": int(
                        span.get(
                            "flags",
                            0
                        )
                    )
                })

    return result


# ============================================================
# FIND NATIVE PDF BBOX
# ============================================================

def find_native_bbox(
    page,
    detection
):

    target = normalize_compare(
        detection.get(
            "value",
            ""
        )
    )

    if not target:
        return None

    words = get_pdf_words(
        page
    )

    # --------------------------------------------------------
    # Exact single word
    # --------------------------------------------------------

    for word in words:

        if normalize_compare(
            word["text"]
        ) == target:

            return (
                word["x0"],
                word["y0"],
                word["x1"],
                word["y1"]
            )

    # --------------------------------------------------------
    # Numeric comparison
    # --------------------------------------------------------

    target_digits = normalize_digits(
        target
    )

    if target_digits:

        for word in words:

            word_digits = normalize_digits(
                word["text"]
            )

            if (
                word_digits
                and word_digits
                == target_digits
            ):

                return (
                    word["x0"],
                    word["y0"],
                    word["x1"],
                    word["y1"]
                )

    # --------------------------------------------------------
    # Consecutive words
    # --------------------------------------------------------

    for start in range(
        len(words)
    ):

        combined = ""

        bbox = None

        for end in range(
            start,
            min(
                len(words),
                start + 8
            )
        ):

            current = words[
                end
            ]

            if end > start:

                previous = words[
                    end - 1
                ]

                if (
                    current["block"]
                    != previous["block"]
                    or
                    current["line"]
                    != previous["line"]
                ):

                    break

            combined += normalize_compare(
                current["text"]
            )

            if bbox is None:

                bbox = [
                    current["x0"],
                    current["y0"],
                    current["x1"],
                    current["y1"]
                ]

            else:

                bbox[0] = min(
                    bbox[0],
                    current["x0"]
                )

                bbox[1] = min(
                    bbox[1],
                    current["y0"]
                )

                bbox[2] = max(
                    bbox[2],
                    current["x1"]
                )

                bbox[3] = max(
                    bbox[3],
                    current["y1"]
                )

            if combined == target:

                return tuple(
                    bbox
                )

            if len(combined) > len(
                target
            ):

                break

    return None


# ============================================================
# FIND BEST SPAN
# ============================================================

def find_best_span(
    page,
    bbox
):

    spans = get_pdf_spans(
        page
    )

    if not spans:
        return None

    if bbox is None:
        return spans[0]

    x0, y0, x1, y1 = bbox

    center_x = (
        x0 + x1
    ) / 2

    center_y = (
        y0 + y1
    ) / 2

    best = None
    best_score = float(
        "inf"
    )

    for span in spans:

        sx0, sy0, sx1, sy1 = (
            span["bbox"]
        )

        span_center_x = (
            sx0 + sx1
        ) / 2

        span_center_y = (
            sy0 + sy1
        ) / 2

        score = (
            abs(
                center_x
                - span_center_x
            )
            +
            abs(
                center_y
                - span_center_y
            )
        )

        if score < best_score:

            best_score = score
            best = span

    return best


# ============================================================
# PDF COLOR CONVERSION
# ============================================================

def pdf_color_to_rgb(
    color
):

    color = int(
        color or 0
    )

    return (
        (color >> 16) & 255,
        (color >> 8) & 255,
        color & 255
    )


# ============================================================
# EXTRACT ORIGINAL EMBEDDED FONT
# ============================================================

def extract_embedded_font(
    document,
    page,
    span
):

    original_font = str(
        span.get(
            "font",
            ""
        )
    ).strip().lower()

    if not original_font:
        return None

    try:

        fonts = page.get_fonts(
            full=True
        )

    except Exception:

        return None

    for font in fonts:

        if len(font) < 4:
            continue

        xref = font[0]

        basefont = str(
            font[3] or ""
        )

        if (
            original_font not in
            basefont.lower()
            and
            basefont.lower() not in
            original_font
        ):

            continue

        try:

            extracted = (
                document.extract_font(
                    xref
                )
            )

        except Exception:

            continue

        if not extracted:
            continue

        if len(extracted) < 4:
            continue

        # PyMuPDF:
        #
        # name
        # extension
        # type
        # binary content

        name = extracted[0]
        extension = extracted[1]
        content = extracted[3]

        if not content:
            continue

        if str(
            extension
        ).lower() not in {
            "ttf",
            "otf"
        }:

            continue

        return {
            "name": str(name),
            "extension": str(
                extension
            ),
            "content": content
        }

    return None


# ============================================================
# INSERT ORIGINAL FONT
# ============================================================

def insert_original_font(
    page,
    font_info
):

    if not font_info:
        return None

    safe_name = re.sub(
        r"[^A-Za-z0-9_]",
        "_",
        font_info["name"]
    )

    safe_name = (
        "privacy_"
        + safe_name[:40]
    )

    try:

        page.insert_font(
            fontname=safe_name,
            fontbuffer=font_info[
                "content"
            ]
        )

        return safe_name

    except Exception:

        return None


# ============================================================
# FONT SIZE CALCULATION
# ============================================================

def calculate_font_size(
    masked_value,
    original_size,
    original_width,
    font_name
):

    size = max(
        MIN_FONT_SIZE,
        min(
            MAX_FONT_SIZE,
            float(original_size)
        )
    )

    try:

        font = fitz.Font(
            fontname=font_name
        )

    except Exception:

        return size

    while size > MIN_FONT_SIZE:

        try:

            text_width = (
                font.text_length(
                    masked_value,
                    fontsize=size
                )
            )

        except Exception:

            break

        if text_width <= original_width:
            break

        size -= 0.25

    return max(
        MIN_FONT_SIZE,
        size
    )


# ============================================================
# MASK NATIVE PDF TEXT
# ============================================================

def mask_native_pdf_text(
    page,
    document,
    detection
):

    label = normalize_label(
        detection.get(
            "label"
        )
    )

    value = str(
        detection.get(
            "value",
            ""
        )
    ).strip()

    masked_value = get_masked_value(
        value,
        label
    )

    if not masked_value:
        return False

    # --------------------------------------------------------
    # Find actual text position.
    # --------------------------------------------------------

    bbox = find_native_bbox(
        page,
        detection
    )

    if bbox is None:

        print(
            "Could not locate native text:",
            label,
            value
        )

        return False

    # --------------------------------------------------------
    # Get ORIGINAL font/color/size BEFORE redaction.
    # --------------------------------------------------------

    span = find_best_span(
        page,
        bbox
    )

    if span is None:

        print(
            "Could not locate original font:",
            value
        )

        return False

    original_font = span.get(
        "font",
        ""
    )

    original_size = float(
        span.get(
            "size",
            10
        )
    )

    original_color = (
        pdf_color_to_rgb(
            span.get(
                "color",
                0
            )
        )
    )

    original_flags = int(
        span.get(
            "flags",
            0
        )
    )

    # --------------------------------------------------------
    # Extract embedded original font.
    # --------------------------------------------------------

    font_info = (
        extract_embedded_font(
            document,
            page,
            span
        )
    )

    font_name = (
        insert_original_font(
            page,
            font_info
        )
    )

    # Fallback only if the PDF font cannot be extracted.
    if font_name is None:

        if original_flags & 16:

            font_name = "hebo"

        else:

            font_name = "helv"

    # --------------------------------------------------------
    # Calculate replacement size.
    # --------------------------------------------------------

    original_width = max(
        1,
        bbox[2] - bbox[0]
    )

    font_size = (
        calculate_font_size(
            masked_value,
            original_size,
            original_width,
            font_name
        )
    )

    # --------------------------------------------------------
    # Remove original sensitive text.
    #
    # Only this small rectangle is affected.
    # --------------------------------------------------------

    redact_rect = fitz.Rect(
        bbox[0] - 1,
        bbox[1] - 0.5,
        bbox[2] + 1,
        bbox[3] + 0.5
    )

    page.add_redact_annot(
        redact_rect,
        fill=(
            1,
            1,
            1
        )
    )

    page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=fitz.PDF_REDACT_LINE_ART_NONE,
        text=fitz.PDF_REDACT_TEXT_REMOVE
    )

    # --------------------------------------------------------
    # Original color.
    # --------------------------------------------------------

    color = (
        original_color[0] / 255.0,
        original_color[1] / 255.0,
        original_color[2] / 255.0
    )

    # --------------------------------------------------------
    # Put masked text at original position.
    # --------------------------------------------------------

    text_rect = fitz.Rect(
        bbox[0],
        bbox[1],
        bbox[2],
        bbox[3] + 1
    )

    result = page.insert_textbox(
        text_rect,
        masked_value,
        fontname=font_name,
        fontsize=font_size,
        color=color,
        align=fitz.TEXT_ALIGN_LEFT,
        overlay=True
    )

    # --------------------------------------------------------
    # Last fallback if the replacement does not fit.
    # --------------------------------------------------------

    if result < 0:

        fallback_size = max(
            MIN_FONT_SIZE,
            font_size - 1
        )

        page.insert_text(
            fitz.Point(
                bbox[0],
                bbox[3]
            ),
            masked_value,
            fontname=font_name,
            fontsize=fallback_size,
            color=color,
            overlay=True
        )

    print(
        f"NATIVE MASKED: "
        f"{label} | "
        f"{value} -> {masked_value}"
    )

    print(
        f"Original font: {original_font}"
    )

    print(
        f"Original size: {original_size}"
    )

    print(
        f"Original color: {original_color}"
    )

    return True


# ============================================================
# RENDER SCANNED PDF PAGE
# ============================================================

def render_pdf_page(
    page
):

    matrix = fitz.Matrix(
        PDF_RENDER_SCALE,
        PDF_RENDER_SCALE
    )

    pix = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )

    raw = np.frombuffer(
        pix.samples,
        dtype=np.uint8
    )

    image = raw.reshape(
        pix.height,
        pix.width,
        pix.n
    )

    if pix.n == 4:

        image = cv2.cvtColor(
            image,
            cv2.COLOR_RGBA2BGR
        )

    else:

        image = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2BGR
        )

    return image


# ============================================================
# IMAGE BBOX
# ============================================================

def get_image_bbox(
    detection,
    image
):

    height, width = (
        image.shape[:2]
    )

    try:

        left = int(
            round(
                float(
                    detection["left"]
                )
            )
        )

        top = int(
            round(
                float(
                    detection["top"]
                )
            )
        )

        right = int(
            round(
                float(
                    detection["right"]
                )
            )
        )

        bottom = int(
            round(
                float(
                    detection["bottom"]
                )
            )
        )

    except Exception:

        return None

    left = max(
        0,
        min(
            width - 1,
            left
        )
    )

    top = max(
        0,
        min(
            height - 1,
            top
        )
    )

    right = max(
        left + 1,
        min(
            width,
            right
        )
    )

    bottom = max(
        top + 1,
        min(
            height,
            bottom
        )
    )

    return (
        left,
        top,
        right,
        bottom
    )


# ============================================================
# IMAGE TEXT COLOR
# ============================================================

def estimate_image_text_color(
    image,
    bbox
):

    left, top, right, bottom = bbox

    crop = image[
        top:bottom,
        left:right
    ]

    if crop.size == 0:

        return (
            0,
            0,
            0
        )

    rgb = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2RGB
    )

    pixels = rgb.reshape(
        -1,
        3
    )

    brightness = pixels.mean(
        axis=1
    )

    dark_pixels = pixels[
        brightness < 200
    ]

    if len(
        dark_pixels
    ) == 0:

        return (
            0,
            0,
            0
        )

    color = np.median(
        dark_pixels,
        axis=0
    )

    return tuple(
        int(
            np.clip(
                value,
                0,
                255
            )
        )
        for value in color
    )


# ============================================================
# IMAGE FONT
# ============================================================

def get_image_font(
    size
):

    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",

        "/usr/share/fonts/truetype/liberation2/"
        "LiberationSans-Regular.ttf",

        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans.ttf"
    ]

    for path in candidates:

        if not os.path.isfile(
            path
        ):
            continue

        try:

            return ImageFont.truetype(
                path,
                max(
                    5,
                    int(size)
                )
            )

        except Exception:

            pass

    return ImageFont.load_default()


# ============================================================
# REMOVE IMAGE TEXT
# ============================================================

def remove_image_text(
    image,
    bbox
):

    left, top, right, bottom = bbox

    mask = np.zeros(
        image.shape[:2],
        dtype=np.uint8
    )

    pad_x = max(
        2,
        int(
            (right - left) * 0.02
        )
    )

    pad_y = max(
        1,
        int(
            (bottom - top) * 0.08
        )
    )

    left = max(
        0,
        left - pad_x
    )

    top = max(
        0,
        top - pad_y
    )

    right = min(
        image.shape[1],
        right + pad_x
    )

    bottom = min(
        image.shape[0],
        bottom + pad_y
    )

    mask[
        top:bottom,
        left:right
    ] = 255

    try:

        return cv2.inpaint(
            image,
            mask,
            INPAINT_RADIUS,
            cv2.INPAINT_TELEA
        )

    except Exception:

        result = image.copy()

        result[
            top:bottom,
            left:right
        ] = (
            255,
            255,
            255
        )

        return result


# ============================================================
# DRAW IMAGE MASKED TEXT
# ============================================================

def draw_image_masked_text(
    image,
    bbox,
    text,
    color
):

    if not text:
        return image

    left, top, right, bottom = bbox

    box_width = max(
        1,
        right - left
    )

    box_height = max(
        1,
        bottom - top
    )

    font_size = max(
        8,
        int(
            box_height * 1.15
        )
    )

    pil_image = Image.fromarray(
        cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )
    )

    draw = ImageDraw.Draw(
        pil_image
    )

    while font_size > 6:

        font = get_image_font(
            font_size
        )

        text_box = draw.textbbox(
            (
                0,
                0
            ),
            text,
            font=font
        )

        text_width = (
            text_box[2]
            - text_box[0]
        )

        if text_width <= box_width:
            break

        font_size -= 1

    text_box = draw.textbbox(
        (
            0,
            0
        ),
        text,
        font=font
    )

    text_height = (
        text_box[3]
        - text_box[1]
    )

    x = left

    y = (
        top
        + (
            box_height
            - text_height
        ) / 2
        - text_box[1]
    )

    draw.text(
        (
            int(x),
            int(y)
        ),
        text,
        font=font,
        fill=tuple(color)
    )

    return cv2.cvtColor(
        np.array(
            pil_image
        ),
        cv2.COLOR_RGB2BGR
    )


# ============================================================
# PROTECT IMAGE
# ============================================================

def protect_image(
    image,
    detections
):

    result = image.copy()

    cleaned = clean_detections(
        detections
    )

    # Process from bottom to top so OCR coordinates
    # remain stable.
    ordered = sorted(
        cleaned,
        key=lambda item: float(
            item.get(
                "top",
                0
            )
        ),
        reverse=True
    )

    for detection in ordered:

        bbox = get_image_bbox(
            detection,
            result
        )

        if bbox is None:
            continue

        label = detection[
            "label"
        ]

        value = detection[
            "value"
        ]

        masked = get_masked_value(
            value,
            label
        )

        original_color = (
            estimate_image_text_color(
                result,
                bbox
            )
        )

        result = remove_image_text(
            result,
            bbox
        )

        result = draw_image_masked_text(
            result,
            bbox,
            masked,
            original_color
        )

    return result


# ============================================================
# IMAGE -> PDF
# ============================================================

def protect_image_file(
    input_path,
    output_path,
    detections,
    document_data=None
):

    image = cv2.imread(
        input_path,
        cv2.IMREAD_COLOR
    )

    if image is None:

        raise ValueError(
            f"Unable to read image: "
            f"{input_path}"
        )

    protected = protect_image(
        image,
        detections
    )

    success, encoded = (
        cv2.imencode(
            ".png",
            protected
        )
    )

    if not success:

        raise ValueError(
            "Unable to encode protected image."
        )

    height, width = (
        protected.shape[:2]
    )

    document = fitz.open()

    try:

        page = document.new_page(
            width=width / PDF_RENDER_SCALE,
            height=height / PDF_RENDER_SCALE
        )

        page.insert_image(
            page.rect,
            stream=encoded.tobytes()
        )

        document.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )

    finally:

        document.close()

    validate_pdf(
        output_path
    )

    return output_path


# ============================================================
# PROTECT PDF
# ============================================================

def protect_pdf_file(
    input_path,
    output_path,
    detections,
    document_data=None
):

    document = fitz.open(
        input_path
    )

    detections = clean_detections(
        detections
    )

    try:

        for index in range(
            len(document)
        ):

            page = document[
                index
            ]

            page_number = (
                index + 1
            )

            page_detections = (
                get_page_detections(
                    detections,
                    page_number
                )
            )

            # =================================================
            # NATIVE TEXT PDF
            # =================================================

            if is_native_text_page(
                page
            ):

                # IMPORTANT:
                #
                # We modify the ORIGINAL PDF page itself.
                #
                # We do NOT convert the complete page into an
                # image.
                #
                # This preserves the original:
                # - page size
                # - layout
                # - images
                # - graphics
                # - text
                # - colors
                # - fonts
                # - quality
                #

                for detection in page_detections:

                    mask_native_pdf_text(
                        page,
                        document,
                        detection
                    )

            # =================================================
            # SCANNED / IMAGE PDF
            # =================================================

            else:

                image = render_pdf_page(
                    page
                )

                if page_detections:

                    image = protect_image(
                        image,
                        page_detections
                    )

                success, encoded = (
                    cv2.imencode(
                        ".png",
                        image
                    )
                )

                if not success:

                    raise ValueError(
                        "Unable to encode scanned PDF page."
                    )

                # Only scanned pages are replaced with their
                # protected image.
                page.clean_contents()

                page.insert_image(
                    page.rect,
                    stream=encoded.tobytes()
                )

        # =====================================================
        # SAVE
        # =====================================================

        document.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )

    finally:

        document.close()

    validate_pdf(
        output_path
    )

    return output_path


# ============================================================
# MAIN FUNCTION
# ============================================================

def create_protected_pdf(
    input_path,
    output_path,
    detections,
    document_data=None
):

    if not input_path:

        raise ValueError(
            "Input file is required."
        )

    if not os.path.isfile(
        input_path
    ):

        raise FileNotFoundError(
            f"Input file not found: "
            f"{input_path}"
        )

    output_directory = (
        os.path.dirname(
            output_path
        )
        or "."
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    extension = os.path.splitext(
        input_path
    )[1].lower()

    detections = clean_detections(
        detections
    )

    print(
        "========================================"
    )

    print(
        "CREATING PROTECTED DOCUMENT"
    )

    print(
        "Original:",
        input_path
    )

    print(
        "Output:",
        output_path
    )

    print(
        "Detections:",
        detections
    )

    if extension == ".pdf":

        result = protect_pdf_file(
            input_path,
            output_path,
            detections,
            document_data
        )

    elif extension in {
        ".png",
        ".jpg",
        ".jpeg"
    }:

        result = protect_image_file(
            input_path,
            output_path,
            detections,
            document_data
        )

    else:

        raise ValueError(
            "Unsupported file type. "
            "Supported formats: "
            "PDF, PNG, JPG, JPEG."
        )

    validate_pdf(
        result
    )

    with open(
        result,
        "rb"
    ) as file:

        header = file.read(
            5
        )

    print(
        "PROTECTED FILE SIZE:",
        os.path.getsize(result)
    )

    print(
        "PROTECTED FILE HEADER:",
        header
    )

    print(
        "========================================"
    )

    return result


# ============================================================
# FINAL PDF VALIDATION
# ============================================================

def validate_pdf(
    path
):

    if not os.path.isfile(
        path
    ):

        raise ValueError(
            "Protected PDF was not created."
        )

    file_size = os.path.getsize(
        path
    )

    if file_size < 100:

        raise ValueError(
            "Protected PDF is unexpectedly small."
        )

    with open(
        path,
        "rb"
    ) as file:

        header = file.read(
            5
        )

    if header != b"%PDF-":

        raise ValueError(
            "Protected document is not a valid PDF."
        )

    test_document = fitz.open(
        path
    )

    try:

        if len(
            test_document
        ) == 0:

            raise ValueError(
                "Protected PDF contains no pages."
            )

    finally:

        test_document.close()

    return True