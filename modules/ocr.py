import os

import fitz
import pytesseract

from PIL import Image


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}

SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf",
}


def extract_text_from_image(file_path):
    """
    Extract text from PNG/JPG/JPEG using Tesseract OCR.
    """

    image = Image.open(file_path)

    text = pytesseract.image_to_string(
        image
    )

    return text


def extract_text_from_pdf(file_path):
    """
    Extract text from a PDF.

    First attempts normal PDF text extraction.
    If a page has no selectable text, OCR is used
    on that page.
    """

    document = fitz.open(file_path)

    extracted_text = []

    for page in document:

        # ---------------------------------------------------
        # Try normal PDF text extraction first
        # ---------------------------------------------------

        text = page.get_text()

        if text.strip():

            extracted_text.append(
                text
            )

        else:

            # ------------------------------------------------
            # Scanned PDF page → OCR
            # ------------------------------------------------

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image = Image.frombytes(
                "RGB",
                [
                    pixmap.width,
                    pixmap.height
                ],
                pixmap.samples
            )

            ocr_text = pytesseract.image_to_string(
                image
            )

            extracted_text.append(
                ocr_text
            )

    document.close()

    return "\n".join(
        extracted_text
    )


def extract_text_from_file(file_path):
    """
    Extract text from a supported file.

    Supported:
        PDF
        PNG
        JPG
        JPEG
    """

    if not os.path.isfile(file_path):

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = os.path.splitext(
        file_path
    )[1].lower()

    if extension in SUPPORTED_IMAGE_EXTENSIONS:

        return extract_text_from_image(
            file_path
        )

    if extension in SUPPORTED_DOCUMENT_EXTENSIONS:

        return extract_text_from_pdf(
            file_path
        )

    raise ValueError(
        "Unsupported file type. "
        "Supported formats: PDF, PNG, JPG, JPEG."
    )


if __name__ == "__main__":

    print("=" * 70)
    print("OCR MODULE")
    print("=" * 70)

    print()
    print("Supported image types:")
    print(".jpeg, .jpg, .png")

    print()
    print("Supported document types:")
    print(".pdf")

    print()
    print(
        "Tesseract version:"
    )

    print(
        pytesseract.get_tesseract_version()
    )

    print()
    print("=" * 70)
    print("OCR MODULE CHECK COMPLETED")
    print("=" * 70)