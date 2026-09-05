import os
import re
import io

import fitz
import numpy as np
import cv2

from PIL import Image, ImageDraw, ImageFont


# =========================================================
# FONT
# =========================================================

def get_font(size):
    """
    Get a font for drawing masked values.
    """

    possible_fonts = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for font_path in possible_fonts:

        if os.path.exists(font_path):

            try:
                return ImageFont.truetype(
                    font_path,
                    max(8, int(size))
                )
            except Exception:
                pass

    return ImageFont.load_default()


# =========================================================
# NORMALIZE OCR TEXT
# =========================================================

def normalize_ocr_text(text):

    if not text:
        return ""

    text = str(text)

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# OCR DATA
# =========================================================

def get_ocr_data(image):
    """
    Run OCR on an image and return word coordinates.
    """

    import pytesseract

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config="--psm 6"
    )

    words = []

    count = len(
        data.get(
            "text",
            []
        )
    )

    for i in range(count):

        text = str(
            data["text"][i]
        ).strip()

        if not text:
            continue

        try:
            confidence = float(
                data["conf"][i]
            )
        except Exception:
            confidence = -1

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

        words.append({
            "text": text,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "right": left + width,
            "bottom": top + height,
            "conf": confidence,
        })

    return words


# =========================================================
# DETECTION RECTANGLE
# =========================================================

def get_detection_rect(detection):
    """
    Get a safe rectangle from a detection.
    """

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

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return None

    if right <= left:
        return None

    if bottom <= top:
        return None

    return (
        left,
        top,
        right,
        bottom
    )


# =========================================================
# FIND EXACT VALUE BBOX
# =========================================================

def find_exact_value_bbox(
    words,
    value
):
    """
    Find an exact OCR value in a list of words.
    """

    if not words or not value:
        return None

    target = re.sub(
        r"\s+",
        "",
        str(value).lower()
    )

    for word in words:

        text = str(
            word.get(
                "text",
                ""
            )
        )

        normalized = re.sub(
            r"\s+",
            "",
            text.lower()
        )

        if normalized == target:

            return (
                word["left"],
                word["top"],
                word["right"],
                word["bottom"]
            )

    return None


# =========================================================
# FIND PARTIAL VALUE BBOX
# =========================================================

def find_partial_value_bbox(
    words,
    value
):
    """
    Find a value spread across multiple OCR words.

    Example:

        8851
        3371
        5419
    """

    if not words or not value:
        return None

    target = re.sub(
        r"\D",
        "",
        str(value)
    )

    if not target:
        return None

    normalized_words = []

    for word in words:

        text = str(
            word.get(
                "text",
                ""
            )
        )

        digits = re.sub(
            r"\D",
            "",
            text
        )

        if digits:

            normalized_words.append({
                **word,
                "digits": digits,
            })

    for i in range(
        len(normalized_words)
    ):

        combined = ""
        selected = []

        for j in range(
            i,
            min(
                i + 8,
                len(normalized_words)
            )
        ):

            current = normalized_words[
                j
            ]

            if selected:

                previous = selected[-1]

                previous_center = (
                    previous["top"]
                    + previous["bottom"]
                ) / 2

                current_center = (
                    current["top"]
                    + current["bottom"]
                ) / 2

                if abs(
                    previous_center
                    - current_center
                ) > 30:

                    break

                gap = (
                    current["left"]
                    - previous["right"]
                )

                if gap > 150:
                    break

            combined += current[
                "digits"
            ]

            selected.append(
                current
            )

            if combined == target:

                return (
                    min(
                        item["left"]
                        for item in selected
                    ),
                    min(
                        item["top"]
                        for item in selected
                    ),
                    max(
                        item["right"]
                        for item in selected
                    ),
                    max(
                        item["bottom"]
                        for item in selected
                    )
                )

            if not target.startswith(
                combined
            ):
                break

    return None


# =========================================================
# SAFE VALUE BBOX
# =========================================================

def get_safe_value_bbox(
    words,
    detection
):
    """
    Prefer detection coordinates supplied by the OCR
    detector. Otherwise search OCR words.
    """

    rect = get_detection_rect(
        detection
    )

    if rect is not None:
        return rect

    value = detection.get(
        "value",
        ""
    )

    rect = find_exact_value_bbox(
        words,
        value
    )

    if rect is not None:
        return rect

    return find_partial_value_bbox(
        words,
        value
    )


# =========================================================
# FIND PDF OCR VALUE BBOX
# =========================================================

def find_pdf_ocr_value_bbox(
    page_data,
    detection
):
    """
    Find the sensitive value rectangle in PDF coordinates.
    """

    rect = get_safe_value_bbox(
        page_data.get(
            "words",
            []
        ),
        detection
    )

    if rect is None:
        return None

    return rect


# =========================================================
# ESTIMATE TEXT COLOR
# =========================================================

def estimate_text_color(
    image,
    bbox
):
    """
    Estimate the original text color from the sensitive
    region.
    """

    left, top, right, bottom = bbox

    left = max(
        0,
        int(left)
    )

    top = max(
        0,
        int(top)
    )

    right = min(
        image.width,
        int(right)
    )

    bottom = min(
        image.height,
        int(bottom)
    )

    if right <= left or bottom <= top:
        return (
            30,
            30,
            30
        )

    crop = np.array(
        image.crop(
            (
                left,
                top,
                right,
                bottom
            )
        )
    )

    if crop.size == 0:
        return (
            30,
            30,
            30
        )

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_RGB2GRAY
    )

    threshold = np.percentile(
        gray,
        35
    )

    pixels = crop[
        gray <= threshold
    ]

    if len(pixels) == 0:
        return (
            30,
            30,
            30
        )

    mean_color = pixels.mean(
        axis=0
    )

    return tuple(
        int(max(0, min(255, value)))
        for value in mean_color
    )


# =========================================================
# MASKING HELPER
# =========================================================

def get_masked_value(detection):
    """
    Generate the masked representation of a sensitive value.

    Uses the same masking rules as modules.masking.
    """

    try:
        from modules.masking import mask_value

        value = detection.get(
            "value",
            ""
        )

        label = detection.get(
            "label",
            ""
        )

        return mask_value(
            value,
            label
        )

    except Exception as error:

        print(
            f"MASKING IMPORT ERROR: {error}"
        )

        # Safe fallback.
        return "****"


# =========================================================
# PRESERVE BACKGROUND MASK
# =========================================================

def preserve_background_mask(
    image,
    bbox,
    masked_text,
    label=None
):
    """
    Remove the original sensitive text while attempting
    to preserve the surrounding scanned-document background.

    OpenCV inpainting is used so the entire background is
    not replaced by a large white rectangle.
    """

    if image is None:
        return image

    left, top, right, bottom = bbox

    left = max(
        0,
        int(left)
    )

    top = max(
        0,
        int(top)
    )

    right = min(
        image.width,
        int(right)
    )

    bottom = min(
        image.height,
        int(bottom)
    )

    if right <= left or bottom <= top:
        return image

    # -----------------------------------------------------
    # Original dimensions before margin.
    # -----------------------------------------------------

    original_left = left
    original_top = top
    original_right = right
    original_bottom = bottom

    width = right - left
    height = bottom - top

    # -----------------------------------------------------
    # Add a small margin around the original text.
    # -----------------------------------------------------

    horizontal_margin = max(
        3,
        int(width * 0.08)
    )

    vertical_margin = max(
        3,
        int(height * 0.20)
    )

    left = max(
        0,
        left - horizontal_margin
    )

    right = min(
        image.width,
        right + horizontal_margin
    )

    top = max(
        0,
        top - vertical_margin
    )

    bottom = min(
        image.height,
        bottom + vertical_margin
    )

    # -----------------------------------------------------
    # Convert to OpenCV image.
    # -----------------------------------------------------

    rgb = np.array(
        image.convert(
            "RGB"
        )
    )

    bgr = cv2.cvtColor(
        rgb,
        cv2.COLOR_RGB2BGR
    )

    # -----------------------------------------------------
    # Create mask.
    # -----------------------------------------------------

    mask = np.zeros(
        (
            bgr.shape[0],
            bgr.shape[1]
        ),
        dtype=np.uint8
    )

    cv2.rectangle(
        mask,
        (
            left,
            top
        ),
        (
            right,
            bottom
        ),
        255,
        -1
    )

    # -----------------------------------------------------
    # Inpaint.
    # -----------------------------------------------------

    region_size = max(
        3,
        min(
            9,
            int(
                max(
                    width,
                    height
                ) * 0.15
            )
        )
    )

    inpainted = cv2.inpaint(
        bgr,
        mask,
        region_size,
        cv2.INPAINT_TELEA
    )

    result_rgb = cv2.cvtColor(
        inpainted,
        cv2.COLOR_BGR2RGB
    )

    result = Image.fromarray(
        result_rgb
    )

    # -----------------------------------------------------
    # Draw replacement value.
    # -----------------------------------------------------

    if not masked_text:
        return result

    draw = ImageDraw.Draw(
        result
    )

    text_color = estimate_text_color(
        image,
        (
            original_left,
            original_top,
            original_right,
            original_bottom
        )
    )

    available_width = max(
        10,
        original_right - original_left
    )

    available_height = max(
        10,
        original_bottom - original_top
    )

    # Start close to OCR text height.
    font_size = max(
        8,
        int(available_height * 0.85)
    )

    font = get_font(
        font_size
    )

    # -----------------------------------------------------
    # Fit text inside original area.
    # -----------------------------------------------------

    while font_size > 7:

        font = get_font(
            font_size
        )

        try:

            box = draw.textbbox(
                (
                    0,
                    0
                ),
                masked_text,
                font=font
            )

            text_width = (
                box[2]
                - box[0]
            )

            text_height = (
                box[3]
                - box[1]
            )

        except Exception:

            text_width = (
                len(masked_text)
                * font_size
                * 0.55
            )

            text_height = font_size

        if (
            text_width <= available_width
            and
            text_height <= available_height
        ):
            break

        font_size -= 1

    # -----------------------------------------------------
    # Calculate replacement position.
    # -----------------------------------------------------

    try:

        box = draw.textbbox(
            (
                0,
                0
            ),
            masked_text,
            font=font
        )

        text_width = (
            box[2]
            - box[0]
        )

        text_height = (
            box[3]
            - box[1]
        )

    except Exception:

        text_width = (
            len(masked_text)
            * font_size
            * 0.55
        )

        text_height = font_size

    text_x = (
        original_left
        + (
            available_width
            - text_width
        ) / 2
    )

    text_y = (
        original_top
        + (
            available_height
            - text_height
        ) / 2
        - 1
    )

    draw.text(
        (
            int(text_x),
            int(text_y)
        ),
        masked_text,
        fill=text_color,
        font=font
    )

    return result


# =========================================================
# IMAGE → PNG BYTES
# =========================================================

def image_to_png_bytes(
    image
):

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


# =========================================================
# IMAGE → PDF DOCUMENT
# =========================================================

def image_to_pdf_document(
    image,
    scale
):
    """
    Convert a PIL image into a temporary PyMuPDF PDF
    document.

    This is required because show_pdf_page() accepts
    a PDF source document, not a PNG/image document.
    """

    png_bytes = image_to_png_bytes(
        image
    )

    image_document = fitz.open()

    # Keep the same physical size as the rendered
    # original PDF page.
    pdf_width = (
        image.width / scale
    )

    pdf_height = (
        image.height / scale
    )

    pdf_page = image_document.new_page(
        width=pdf_width,
        height=pdf_height
    )

    pdf_page.insert_image(
        pdf_page.rect,
        stream=png_bytes
    )

    return image_document


# =========================================================
# PDF → PIXEL COORDINATES
# =========================================================

def pdf_rect_to_pixels(
    rect,
    page_rect,
    image_width,
    image_height
):

    if (
        page_rect.width <= 0
        or page_rect.height <= 0
    ):
        return None

    scale_x = (
        image_width
        /
        page_rect.width
    )

    scale_y = (
        image_height
        /
        page_rect.height
    )

    return (
        rect[0] * scale_x,
        rect[1] * scale_y,
        rect[2] * scale_x,
        rect[3] * scale_y,
    )


# =========================================================
# IMAGE → PDF COORDINATES
# =========================================================

def image_rect_to_pdf(
    rect,
    image_width,
    image_height,
    image_pdf_rect
):

    if (
        image_width <= 0
        or image_height <= 0
    ):
        return None

    scale_x = (
        image_pdf_rect.width
        /
        image_width
    )

    scale_y = (
        image_pdf_rect.height
        /
        image_height
    )

    return (
        image_pdf_rect.x0
        +
        rect[0] * scale_x,

        image_pdf_rect.y0
        +
        rect[1] * scale_y,

        image_pdf_rect.x0
        +
        rect[2] * scale_x,

        image_pdf_rect.y0
        +
        rect[3] * scale_y,
    )


# =========================================================
# PDF DETECTION RECTANGLE
# =========================================================

def get_pdf_detection_rect(
    page_data,
    detection,
    page_rect
):
    """
    Convert the detection rectangle into PDF coordinates.

    Supported coordinate spaces:

        pdf
        image
    """

    # -----------------------------------------------------
    # Prefer coordinates directly supplied by detection.
    # -----------------------------------------------------

    rect = get_safe_value_bbox(
        page_data.get(
            "words",
            []
        ),
        detection
    )

    if rect is None:
        return None

    coordinate_space = (
        detection.get(
            "coordinate_space"
        )
        or
        page_data.get(
            "coordinate_space"
        )
        or
        "pdf"
    )

    coordinate_space = str(
        coordinate_space
    ).lower()

    # -----------------------------------------------------
    # Already PDF coordinates.
    # -----------------------------------------------------

    if coordinate_space == "pdf":

        return fitz.Rect(
            rect[0],
            rect[1],
            rect[2],
            rect[3]
        )

    # -----------------------------------------------------
    # Image coordinates.
    # -----------------------------------------------------

    if coordinate_space == "image":

        image_width = page_data.get(
            "image_width"
        )

        image_height = page_data.get(
            "image_height"
        )

        image_pdf_rect = page_data.get(
            "pdf_rect"
        )

        # -------------------------------------------------
        # If pdf_rect is represented as a tuple/list,
        # convert it to fitz.Rect.
        # -------------------------------------------------

        if image_pdf_rect is not None:

            if isinstance(
                image_pdf_rect,
                (list, tuple)
            ) and len(image_pdf_rect) >= 4:

                try:

                    image_pdf_rect = fitz.Rect(
                        float(image_pdf_rect[0]),
                        float(image_pdf_rect[1]),
                        float(image_pdf_rect[2]),
                        float(image_pdf_rect[3])
                    )

                except Exception:

                    image_pdf_rect = None

        if (
            image_width
            and
            image_height
            and
            image_pdf_rect
        ):

            converted = image_rect_to_pdf(
                rect,
                float(image_width),
                float(image_height),
                image_pdf_rect
            )

            if converted:

                return fitz.Rect(
                    *converted
                )

        # -------------------------------------------------
        # Fallback: assume image covers whole PDF page.
        # -------------------------------------------------

        if image_width and image_height:

            converted = image_rect_to_pdf(
                rect,
                float(image_width),
                float(image_height),
                page_rect
            )

            if converted:

                return fitz.Rect(
                    *converted
                )

    return None


# =========================================================
# SCANNED PDF PAGE
# =========================================================

def protect_scanned_pdf_page(
    page,
    page_data,
    page_detections
):
    """
    Protect a scanned/image-based PDF page.

    The entire page is rendered as an image, only the
    detected sensitive regions are modified, and the
    protected image is placed back into the original page.

    This preserves the overall document appearance much
    better than reconstructing the page from scratch.
    """

    # Higher resolution gives better masking quality.
    scale = 2.5

    pix = page.get_pixmap(
        matrix=fitz.Matrix(
            scale,
            scale
        ),
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

    page_rect = page.rect

    # -----------------------------------------------------
    # Mask every approved sensitive detection.
    # -----------------------------------------------------

    for detection in page_detections:

        pdf_rect = get_pdf_detection_rect(
            page_data,
            detection,
            page_rect
        )

        if pdf_rect is None:
            continue

        pixel_bbox = pdf_rect_to_pixels(
            (
                pdf_rect.x0,
                pdf_rect.y0,
                pdf_rect.x1,
                pdf_rect.y1,
            ),
            page_rect,
            image.width,
            image.height
        )

        if pixel_bbox is None:
            continue

        try:

            masked_text = get_masked_value(
                detection
            )

        except Exception as error:

            print(
                f"MASK ERROR: {error}"
            )

            masked_text = "****"

        image = preserve_background_mask(
            image,
            pixel_bbox,
            masked_text,
            detection.get(
                "label"
            )
        )

    # -----------------------------------------------------
    # Convert protected image to a temporary PDF.
    #
    # IMPORTANT:
    # show_pdf_page() requires a PDF source document.
    # It cannot use a PNG document directly.
    # -----------------------------------------------------

    image_document = image_to_pdf_document(
        image,
        scale
    )

    try:

        page.clean_contents()

        page.show_pdf_page(
            page.rect,
            image_document,
            0
        )

    finally:

        image_document.close()


# =========================================================
# NATIVE TEXT PDF PAGE
# =========================================================

def protect_text_pdf_page(
    page,
    page_data,
    page_detections
):
    """
    Protect a native-text PDF page using PyMuPDF
    redaction annotations.
    """

    for detection in page_detections:

        rect = get_pdf_detection_rect(
            page_data,
            detection,
            page.rect
        )

        if rect is None:
            continue

        rect.x0 -= 1
        rect.y0 -= 1
        rect.x1 += 1
        rect.y1 += 1

        try:

            masked_text = get_masked_value(
                detection
            )

        except Exception as error:

            print(
                f"MASK ERROR: {error}"
            )

            masked_text = "****"

        page.add_redact_annot(
            rect,
            text=masked_text,
            fill=(
                1,
                1,
                1
            ),
            text_color=(
                0,
                0,
                0
            )
        )

    page.apply_redactions()


# =========================================================
# DETERMINE PAGE TYPE
# =========================================================

def is_scanned_page(
    page,
    page_data,
    page_detections
):
    """
    Determine whether the page should be processed as a
    scanned/image page or native text PDF page.
    """

    page_type = str(
        page_data.get(
            "type",
            ""
        )
    ).lower()

    if page_type in {
        "image",
        "ocr",
        "scanned",
        "scan",
    }:

        return True

    if page_data.get(
        "image"
    ) is not None:

        return True

    for detection in page_detections:

        coordinate_space = str(
            detection.get(
                "coordinate_space",
                ""
            )
        ).lower()

        if coordinate_space == "image":
            return True

    try:

        native_text = page.get_text(
            "text"
        ).strip()

        if native_text:
            return False

    except Exception:
        pass

    return True


# =========================================================
# MAIN PROTECTED DOCUMENT FUNCTION
# =========================================================

def create_protected_pdf(
    original_path,
    output_path,
    detections,
    document_data
):
    """
    Create a protected copy of the original document.

    Supports:

        PDF
        PNG
        JPG
        JPEG

    Only approved sensitive detections are masked.

    Names, DOB, phone, email, addresses, URLs and other
    ignored entities are not touched.
    """

    if not os.path.exists(
        original_path
    ):

        raise FileNotFoundError(
            f"Original file not found: "
            f"{original_path}"
        )

    extension = os.path.splitext(
        original_path
    )[1].lower()

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )

    detections = detections or []

    # =====================================================
    # IMAGE FILE
    # =====================================================

    if extension in {
        ".png",
        ".jpg",
        ".jpeg",
    }:

        image = Image.open(
            original_path
        ).convert(
            "RGB"
        )

        for detection in detections:

            coordinate_space = str(
                detection.get(
                    "coordinate_space",
                    "image"
                )
            ).lower()

            # Image files should use image coordinates.
            if coordinate_space != "image":
                continue

            rect = get_detection_rect(
                detection
            )

            if rect is None:
                continue

            try:

                masked_text = get_masked_value(
                    detection
                )

            except Exception as error:

                print(
                    f"MASK ERROR: {error}"
                )

                masked_text = "****"

            image = preserve_background_mask(
                image,
                rect,
                masked_text,
                detection.get(
                    "label"
                )
            )

        if extension == ".png":

            image.save(
                output_path,
                format="PNG"
            )

        else:

            image.save(
                output_path,
                format="JPEG",
                quality=95
            )

        return output_path

    # =====================================================
    # PDF FILE
    # =====================================================

    if extension == ".pdf":

        source = fitz.open(
            original_path
        )

        try:

            # -------------------------------------------------
            # Group detections by page.
            # -------------------------------------------------

            detections_by_page = {}

            for detection in detections:

                try:

                    page_number = int(
                        detection.get(
                            "page_number",
                            1
                        )
                    )

                except Exception:

                    page_number = 1

                detections_by_page.setdefault(
                    page_number,
                    []
                ).append(
                    detection
                )

            # -------------------------------------------------
            # Page metadata from OCR.
            # -------------------------------------------------

            pages_data = {}

            if document_data:

                for page_data in document_data.get(
                    "pages",
                    []
                ):

                    try:

                        page_number = int(
                            page_data.get(
                                "page_number"
                            )
                        )

                    except Exception:

                        continue

                    pages_data[
                        page_number
                    ] = page_data

            # -------------------------------------------------
            # Process pages.
            # -------------------------------------------------

            for page_index in range(
                len(source)
            ):

                page_number = (
                    page_index + 1
                )

                page_detections = (
                    detections_by_page.get(
                        page_number,
                        []
                    )
                )

                if not page_detections:
                    continue

                page = source[
                    page_index
                ]

                page_data = pages_data.get(
                    page_number,
                    {}
                )

                if is_scanned_page(
                    page,
                    page_data,
                    page_detections
                ):

                    protect_scanned_pdf_page(
                        page,
                        page_data,
                        page_detections
                    )

                else:

                    protect_text_pdf_page(
                        page,
                        page_data,
                        page_detections
                    )

            # -------------------------------------------------
            # Save protected PDF.
            # -------------------------------------------------

            source.save(
                output_path,
                garbage=4,
                deflate=True
            )

        finally:

            source.close()

        return output_path

    # =====================================================
    # UNSUPPORTED FILE
    # =====================================================

    raise ValueError(
        f"Unsupported file type: {extension}"
    )