# modules/document_protector.py

import os
import fitz

from PIL import Image, ImageDraw, ImageFont

from .masking import mask_value


# =========================================================
# FONT
# =========================================================

def get_font(size=20):

    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in font_paths:

        if os.path.exists(path):

            try:
                return ImageFont.truetype(
                    path,
                    size
                )

            except Exception:
                pass

    return ImageFont.load_default()


# =========================================================
# CHECK SAME ROW
# =========================================================

def is_same_row(
    word,
    detection
):
    """
    Check whether an OCR word belongs to the same
    horizontal row as a detection.
    """

    word_top = int(
        word.get(
            "top",
            0
        )
    )

    word_height = int(
        word.get(
            "height",
            0
        )
    )

    word_bottom = (
        word_top
        + word_height
    )

    detection_top = int(
        detection.get(
            "top",
            0
        )
    )

    detection_bottom = int(
        detection.get(
            "bottom",
            0
        )
    )

    word_center = (
        word_top
        + word_bottom
    ) / 2

    detection_center = (
        detection_top
        + detection_bottom
    ) / 2

    detection_height = max(
        1,
        detection_bottom
        - detection_top
    )

    return abs(
        word_center
        - detection_center
    ) <= max(
        20,
        detection_height * 1.2
    )


# =========================================================
# GET VALUE-ONLY BOUNDING BOX
# =========================================================

def get_value_only_bbox(
    detection,
    document_data,
    image
):
    """
    Find the actual sensitive-value bounding box.

    This prevents ':' or '>' from being included in the
    white masking rectangle.

    Handles both situations:

        1. OCR separates ':' and the value.

        2. OCR combines ':' with the value.
    """

    detection_left = int(
        detection.get(
            "left",
            0
        )
    )

    detection_top = int(
        detection.get(
            "top",
            0
        )
    )

    detection_right = int(
        detection.get(
            "right",
            0
        )
    )

    detection_bottom = int(
        detection.get(
            "bottom",
            0
        )
    )

    words = document_data.get(
        "words",
        []
    )

    if not words:

        return (
            detection_left,
            detection_top,
            detection_right,
            detection_bottom
        )

    # =====================================================
    # FIND WORDS ON THE SAME ROW
    # =====================================================

    same_row_words = []

    for word in words:

        text = str(
            word.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        if not is_same_row(
            word,
            detection
        ):
            continue

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

        right = (
            left
            + width
        )

        same_row_words.append({

            "text":
                text,

            "left":
                left,

            "right":
                right,

            "top":
                int(
                    word.get(
                        "top",
                        0
                    )
                ),

            "bottom":
                int(
                    word.get(
                        "top",
                        0
                    )
                )
                + int(
                    word.get(
                        "height",
                        0
                    )
                ),

            "width":
                width,

            "height":
                int(
                    word.get(
                        "height",
                        0
                    )
                ),
        })

    if not same_row_words:

        return (
            detection_left,
            detection_top,
            detection_right,
            detection_bottom
        )

    same_row_words.sort(
        key=lambda word:
            word["left"]
    )

    # =====================================================
    # FIND SEPARATOR IMMEDIATELY BEFORE VALUE
    # =====================================================

    separator_words = []

    for word in same_row_words:

        text = word[
            "text"
        ]

        if text in {
            ":",
            ">"
        }:

            if word["right"] <= (
                detection_right + 20
            ):

                separator_words.append(
                    word
                )

    # =====================================================
    # FIND VALUE WORDS
    # =====================================================

    value_words = []

    detection_value = str(
        detection.get(
            "value",
            ""
        )
    ).strip()

    detection_ocr_value = str(
        detection.get(
            "ocr_value",
            ""
        )
    ).strip()

    for word in same_row_words:

        text = word[
            "text"
        ]

        # -------------------------------------------------
        # Never use separator-only words as value.
        # -------------------------------------------------

        if text in {
            ":",
            ">"
        }:
            continue

        # -------------------------------------------------
        # Word should be near the detection area.
        # -------------------------------------------------

        horizontal_near = (

            word["right"]
            >= detection_left - 20

            and

            word["left"]
            <= detection_right + 20
        )

        if not horizontal_near:
            continue

        value_words.append(
            word
        )

    # =====================================================
    # SPECIAL CASE:
    # OCR COMBINED ":" + VALUE
    # =====================================================

    combined_separator_word = None

    for word in value_words:

        text = word[
            "text"
        ]

        if text.startswith(
            (
                ":",
                ">"
            )
        ):

            combined_separator_word = (
                word
            )

            break

    if combined_separator_word:

        left = (
            combined_separator_word[
                "left"
            ]
        )

        width = (
            combined_separator_word[
                "width"
            ]
        )

        height = (
            combined_separator_word[
                "height"
            ]
        )

        # -------------------------------------------------
        # Estimate separator width.
        # -------------------------------------------------

        separator_width = max(
            3,
            min(
                6,
                int(
                    height * 0.30
                )
            )
        )

        left = (
            left
            + separator_width
        )

        return (

            max(
                0,
                left
            ),

            max(
                0,
                combined_separator_word[
                    "top"
                ]
            ),

            min(
                image.width,
                combined_separator_word[
                    "right"
                ]
            ),

            min(
                image.height,
                combined_separator_word[
                    "bottom"
                ]
            ),
        )

    # =====================================================
    # IF SEPARATE ":" EXISTS
    # =====================================================

    if separator_words:

        nearest_separator = min(

            separator_words,

            key=lambda word:
                abs(
                    word["right"]
                    - detection_left
                )
        )

        # -------------------------------------------------
        # Remove separator from possible value words.
        # -------------------------------------------------

        value_words_after_separator = [

            word

            for word in value_words

            if word["left"]
            >= nearest_separator["right"]
        ]

        if value_words_after_separator:

            value_words = (
                value_words_after_separator
            )

    # =====================================================
    # USE DETECTION VALUE AREA
    # =====================================================

    if value_words:

        # -------------------------------------------------
        # Prefer words that overlap the original detection.
        # -------------------------------------------------

        overlapping_words = [

            word

            for word in value_words

            if (
                word["right"]
                >= detection_left

                and

                word["left"]
                <= detection_right
            )
        ]

        if overlapping_words:

            value_words = (
                overlapping_words
            )

        # -------------------------------------------------
        # Calculate value-only rectangle.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Do not allow the calculated box to move
        # significantly outside the detection.
        # -------------------------------------------------

        if left < (
            detection_left - 20
        ):

            left = detection_left

        if right > (
            detection_right + 20
        ):

            right = detection_right

        return (

            max(
                0,
                left
            ),

            max(
                0,
                top
            ),

            min(
                image.width,
                right
            ),

            min(
                image.height,
                bottom
            ),
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    return (

        max(
            0,
            detection_left
        ),

        max(
            0,
            detection_top
        ),

        min(
            image.width,
            detection_right
        ),

        min(
            image.height,
            detection_bottom
        ),
    )


# =========================================================
# CREATE PROTECTED PDF
# =========================================================

def create_protected_pdf(
    original_path,
    output_path,
    detections,
    document_data
):

    document_type = document_data.get(
        "type"
    )

    # =====================================================
    # IMAGE DOCUMENT
    # =====================================================

    if document_type == "image":

        image = Image.open(
            original_path
        ).convert(
            "RGB"
        )

        draw = ImageDraw.Draw(
            image
        )

        # =================================================
        # PROCESS EACH SENSITIVE DETECTION
        # =================================================

        for detection in detections:

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

            # =================================================
            # GET VALUE-ONLY COORDINATES
            # =================================================

            (
                left,
                top,
                right,
                bottom
            ) = get_value_only_bbox(
                detection,
                document_data,
                image
            )

            # =================================================
            # SMALL VERTICAL PADDING ONLY
            # =================================================

            mask_left = max(
                0,
                int(left)
            )

            mask_top = max(
                0,
                int(top) - 2
            )

            mask_right = min(
                image.width,
                int(right) + 3
            )

            mask_bottom = min(
                image.height,
                int(bottom) + 2
            )

            # =================================================
            # EXISTING PROJECT MASKING FUNCTION
            # =================================================

            masked_value = mask_value(
                value,
                label
            )

            if not masked_value:
                continue

            # =================================================
            # COVER ONLY SENSITIVE VALUE
            # =================================================

            draw.rectangle(
                [
                    mask_left,
                    mask_top,
                    mask_right,
                    mask_bottom
                ],
                fill="white"
            )

            # =================================================
            # BOX SIZE
            # =================================================

            box_width = (
                mask_right
                - mask_left
            )

            box_height = (
                mask_bottom
                - mask_top
            )

            # =================================================
            # FONT SIZE
            # =================================================

            font_size = max(
                12,
                int(
                    box_height * 0.75
                )
            )

            font = get_font(
                font_size
            )

            # =================================================
            # REDUCE FONT IF NECESSARY
            # =================================================

            while font_size > 8:

                bbox = draw.textbbox(
                    (0, 0),
                    masked_value,
                    font=font
                )

                text_width = (
                    bbox[2]
                    - bbox[0]
                )

                if text_width <= (
                    box_width + 10
                ):
                    break

                font_size -= 1

                font = get_font(
                    font_size
                )

            # =================================================
            # TEXT BOUNDING BOX
            # =================================================

            bbox = draw.textbbox(
                (0, 0),
                masked_value,
                font=font
            )

            text_height = (
                bbox[3]
                - bbox[1]
            )

            # =================================================
            # TEXT POSITION
            # =================================================

            text_x = mask_left

            text_y = (
                mask_top
                + max(
                    0,
                    (
                        box_height
                        - text_height
                    ) // 2
                )
            )

            # =================================================
            # DRAW MASKED VALUE
            # =================================================

            draw.text(
                (
                    text_x,
                    text_y
                ),
                masked_value,
                fill="black",
                font=font
            )

        # =====================================================
        # SAVE IMAGE AS PDF
        # =====================================================

        image.save(
            output_path,
            "PDF",
            resolution=100.0
        )

        return output_path

    # =====================================================
    # PDF DOCUMENT
    # =====================================================

    if document_type == "pdf":

        doc = fitz.open(
            original_path
        )

        pages = document_data.get(
            "pages",
            []
        )

        for page_number, page_data in enumerate(
            pages
        ):

            if page_number >= len(doc):
                break

            page = doc[
                page_number
            ]

            for detection in detections:

                detection_page = detection.get(
                    "page",
                    page_number
                )

                if detection_page != page_number:
                    continue

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

                # -------------------------------------------------
                # Search canonical value.
                # -------------------------------------------------

                rectangles = page.search_for(
                    value
                )

                # -------------------------------------------------
                # Search OCR value if necessary.
                # -------------------------------------------------

                if not rectangles:

                    ocr_value = detection.get(
                        "ocr_value"
                    )

                    if (
                        ocr_value
                        and
                        ocr_value != value
                    ):

                        rectangles = page.search_for(
                            ocr_value
                        )

                # -------------------------------------------------
                # Apply redactions.
                # -------------------------------------------------

                for rect in rectangles:

                    masked_value = mask_value(
                        value,
                        label
                    )

                    page.add_redact_annot(
                        rect,
                        text=masked_value,
                        fill=(1, 1, 1),
                        text_color=(0, 0, 0)
                    )

            page.apply_redactions()

        # =====================================================
        # SAVE PDF
        # =====================================================

        doc.save(
            output_path,
            garbage=4,
            deflate=True
        )

        doc.close()

        return output_path

    # =====================================================
    # UNSUPPORTED
    # =====================================================

    raise ValueError(
        f"Unsupported document type: {document_type}"
    )