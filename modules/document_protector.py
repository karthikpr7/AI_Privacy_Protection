import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import io
import re

def get_masked_string(val: str, mode: str = "partial") -> str:
    if mode == "blackout":
        return ""
    clean = val.strip()
    if len(clean) <= 4:
        return "****"
    inner_stars = "*" * min(6, max(4, len(clean) - 4))
    return f"{clean[:2]}{inner_stars}{clean[-2:]}"

def get_calibrated_font(draw: ImageDraw.ImageDraw, target_text: str, target_h: int, target_w: int):
    """
    Calibrates font sizing directly against standard capital letters and digits 
    to match surrounding document typography.
    """
    candidate_fonts = ["arialbd.ttf", "arial.ttf", "calibrib.ttf", "calibri.ttf", "DejaVuSans-Bold.ttf"]
    
    # Target height scaled to match standard cap-height of document lines (~88% of line height)
    size = max(14, int(target_h * 0.88))
    
    font = None
    for name in candidate_fonts:
        try:
            font = ImageFont.truetype(name, size=size)
            break
        except IOError:
            continue
            
    if font is None:
        return ImageFont.load_default(), size

    # Adjust size downward only if the string exceeds available horizontal width
    while size > 11:
        bbox = draw.textbbox((0, 0), target_text, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= target_w:
            break
        size -= 1
        for name in candidate_fonts:
            try:
                font = ImageFont.truetype(name, size=size)
                break
            except IOError:
                continue

    return font, size

def draw_visual_partial_mask(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, masked_text: str):
    box_w = x1 - x0
    box_h = y1 - y0

    # 1. Blank out previous text with solid white patch
    draw.rectangle([(x0 - 2, y0 - 1), (x1 + 2, y1 + 1)], fill=(255, 255, 255))

    # 2. Compute exact matching font
    font, font_size = get_calibrated_font(draw, masked_text, box_h, box_w)

    # 3. Calculate baseline alignment to match adjacent text
    bbox = draw.textbbox((0, 0), masked_text, font=font)
    text_h = bbox[3] - bbox[1]
    
    # Vertically seat the text to align natural baseline
    offset_y = max(0, (box_h - text_h) // 2)
    draw.text((x0, y0 + offset_y - 1), masked_text, fill=(20, 20, 20), font=font)

def redact_image_canvas(img: Image.Image, detections: list, mode: str = "partial") -> Image.Image:
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n_boxes = len(ocr_data['text'])

    for item in detections:
        val = item.get("value", "")
        if not val:
            continue

        tokens = [t.strip() for t in re.split(r'[\s\-]+', val) if t.strip()]
        if not tokens:
            continue

        i = 0
        while i < n_boxes:
            word = ocr_data['text'][i].strip()
            if not word:
                i += 1
                continue

            if tokens[0] in word or word in tokens[0]:
                indices = [i]
                t_idx = 1
                curr_i = i + 1

                while t_idx < len(tokens) and curr_i < n_boxes:
                    next_word = ocr_data['text'][curr_i].strip()
                    if not next_word:
                        curr_i += 1
                        continue
                    if tokens[t_idx] in next_word or next_word in tokens[t_idx]:
                        indices.append(curr_i)
                        t_idx += 1
                    else:
                        break
                    curr_i += 1

                if t_idx == len(tokens):
                    pad_x = 4
                    pad_y = 2
                    x0 = max(0, min(ocr_data['left'][idx] for idx in indices) - pad_x)
                    y0 = max(0, min(ocr_data['top'][idx] for idx in indices) - pad_y)
                    x1 = min(img.width, max(ocr_data['left'][idx] + ocr_data['width'][idx] for idx in indices) + pad_x)
                    y1 = min(img.height, max(ocr_data['top'][idx] + ocr_data['height'][idx] for idx in indices) + pad_y)

                    if mode == "blackout":
                        draw.rectangle([(x0, y0), (x1, y1)], fill=(0, 0, 0))
                    else:
                        masked_str = get_masked_string(val, mode="partial")
                        draw_visual_partial_mask(draw, x0, y0, x1, y1, masked_str)

                    i = curr_i - 1
            i += 1

    return img

def save_image_to_exact_pdf(img: Image.Image, output_path: str):
    dpi = img.info.get('dpi', (150, 150))
    dpi_x = dpi[0] if isinstance(dpi, tuple) else 150
    dpi_y = dpi[1] if isinstance(dpi, tuple) else 150

    pt_width = (img.width / dpi_x) * 72
    pt_height = (img.height / dpi_y) * 72

    doc = fitz.open()
    rect = fitz.Rect(0, 0, pt_width, pt_height)
    page = doc.new_page(width=pt_width, height=pt_height)

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    page.insert_image(rect, stream=img_buffer.getvalue())

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

def apply_redaction(input_path: str, output_path: str, detections: list, mode: str = "partial"):
    doc = fitz.open(input_path)
    is_pure_image = True

    for page in doc:
        if len(page.get_text("text").strip()) > 30:
            is_pure_image = False
            break

    if is_pure_image:
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        doc.close()

        redacted_img = redact_image_canvas(img, detections, mode=mode)
        save_image_to_exact_pdf(redacted_img, output_path)
        return

    # Digital Vector PDF pipeline
    for item in detections:
        val = item.get("value", "")
        if not val:
            continue

        page_num = max(0, item.get("page", 1) - 1)
        if page_num < len(doc):
            page = doc[page_num]
            rects = page.search_for(val)
            for rect in rects:
                if mode == "blackout":
                    page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))
                else:
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    page.insert_text(
                        fitz.Point(rect.x0, rect.y1 - 2),
                        get_masked_string(val, mode="partial"),
                        fontsize=rect.height * 0.85,
                        color=(0, 0, 0)
                    )

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()