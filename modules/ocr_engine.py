import pytesseract
from PIL import Image
import io

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

def get_ocr_boxes_for_page(page):
    """
    Renders a raster page to an image and runs Tesseract image_to_data
    using pure Python dictionary output to avoid the pandas dependency.
    """
    zoom = 2.0  # 144 DPI
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))
    
    # Use DICT output instead of DATAFRAME
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    scale_x = page.rect.width / pix.width
    scale_y = page.rect.height / pix.height
    
    word_boxes = []
    total_tokens = len(data.get('text', []))
    
    for i in range(total_tokens):
        text = str(data['text'][i]).strip()
        if not text:
            continue
            
        x = data['left'][i]
        y = data['top'][i]
        w = data['width'][i]
        h = data['height'][i]
        
        rect = pymupdf.Rect(
            x * scale_x,
            y * scale_y,
            (x + w) * scale_x,
            (y + h) * scale_y
        )
        word_boxes.append({"text": text, "rect": rect})
        
    return word_boxes

def extract_text_with_ocr(page) -> str:
    """Extracts plain text for detection matching."""
    zoom = 2.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))
    return pytesseract.image_to_string(image, config="--psm 6")