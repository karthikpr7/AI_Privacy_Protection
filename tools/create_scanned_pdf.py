import fitz
from PIL import Image, ImageDraw, ImageFont
import io

def create_scanned_sample(output_path="scanned_test.pdf"):
    # 1. Create an in-memory image simulating a scanned document page
    img = Image.new("RGB", (800, 1000), color=(248, 248, 248))
    draw = ImageDraw.Draw(img)

    # Use default bitmap font
    font = ImageFont.load_default()

    # Draw simulated scanned text (including distractors and sensitive data)
    lines = [
        "ACME LOGISTICS INVOICE",
        "Date: 2026-09-12",
        "Invoice ID: 982341",
        "Tracking Code: 44921",
        "",
        "CUSTOMER VERIFICATION SECTION",
        "Tax ID / PAN: ABCDE1234F",
        "Beneficiary A/C: 987654321098",
        "Total Due: INR 14,500.00"
    ]

    y = 60
    for line in lines:
        draw.text((60, y), line, fill=(20, 20, 20), font=font)
        y += 35

    # 2. Convert the image into a pure raster PDF (no embedded text layer)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=800, height=1000)
    rect = fitz.Rect(0, 0, 800, 1000)
    page.insert_image(rect, stream=img_byte_arr)

    doc.save(output_path)
    doc.close()
    print(f"Created scanned raster test PDF at: {output_path}")

if __name__ == "__main__":
    create_scanned_sample()