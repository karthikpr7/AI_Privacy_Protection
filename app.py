from flask import (
    Flask,
    render_template,
    request,
    send_file,
    abort,
    url_for,
    session
)

import os
import json
import uuid
import copy

from PIL import Image

from modules.detector import analyze_text

from modules.masking import mask_text_by_values

from modules.ocr import (
    extract_document_data,
    detect_sensitive_fields_from_ocr,
    create_masked_text_preview
)

from modules.document_protector import create_protected_pdf

from modules.report_generator import (
    generate_report,
    generate_privacy_report_pdf
)

from modules.risk_analyzer import calculate_risk


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

# Secret key is required for Flask sessions.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ai-privacy-protection-local-secret-key"
)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "uploads"

PROTECTED_FOLDER = "outputs/protected"

REPORT_FOLDER = "outputs/reports"

TEMP_DATA_FOLDER = "outputs/document_data"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["PROTECTED_FOLDER"] = PROTECTED_FOLDER

app.config["REPORT_FOLDER"] = REPORT_FOLDER

app.config["TEMP_DATA_FOLDER"] = TEMP_DATA_FOLDER


# =========================================================
# CREATE FOLDERS
# =========================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    PROTECTED_FOLDER,
    exist_ok=True
)

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True
)

os.makedirs(
    TEMP_DATA_FOLDER,
    exist_ok=True
)


# =========================================================
# JSON SAFE CONVERSION
# =========================================================

def make_json_safe(data):
    """
    Convert data to JSON-safe values.

    This is used only for displaying analysis information.

    Internal document/OCR data is NOT sent to the browser
    for the protection process.
    """

    if isinstance(
        data,
        Image.Image
    ):

        return None

    if isinstance(
        data,
        dict
    ):

        cleaned = {}

        for key, value in data.items():

            if key in {
                "image",
                "pil_image",
                "page_image"
            }:

                continue

            cleaned[key] = make_json_safe(
                value
            )

        return cleaned

    if isinstance(
        data,
        list
    ):

        return [
            make_json_safe(
                item
            )
            for item in data
        ]

    if isinstance(
        data,
        tuple
    ):

        return [
            make_json_safe(
                item
            )
            for item in data
        ]

    if isinstance(
        data,
        set
    ):

        return [
            make_json_safe(
                item
            )
            for item in data
        ]

    if data is None:

        return None

    if isinstance(
        data,
        (
            str,
            int,
            float,
            bool
        )
    ):

        return data

    try:

        if hasattr(
            data,
            "item"
        ):

            return data.item()

    except Exception:

        pass

    return str(
        data
    )


# =========================================================
# SAVE INTERNAL DOCUMENT DATA
# =========================================================

def save_internal_document_data(
    document_id,
    document_data
):

    path = os.path.join(
        TEMP_DATA_FOLDER,
        f"{document_id}.pkl"
    )

    import pickle

    with open(
        path,
        "wb"
    ) as file:

        pickle.dump(
            document_data,
            file,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    return path


# =========================================================
# LOAD INTERNAL DOCUMENT DATA
# =========================================================

def load_internal_document_data(
    document_id
):

    path = os.path.join(
        TEMP_DATA_FOLDER,
        f"{document_id}.pkl"
    )

    if not os.path.isfile(
        path
    ):

        return None

    import pickle

    with open(
        path,
        "rb"
    ) as file:

        return pickle.load(
            file
        )


# =========================================================
# HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# TEXT ANALYSIS
# =========================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    text = request.form.get(
        "text",
        ""
    ).strip()

    if not text:

        return render_template(
            "index.html",
            error="Please enter some text to analyze."
        )

    result = analyze_text(
        text
    )

    return render_template(
        "result.html",
        text=text,
        result=result
    )


# =========================================================
# FILE ANALYSIS
# =========================================================

@app.route(
    "/analyze-file",
    methods=["POST"]
)
def analyze_file():

    file = request.files.get(
        "file"
    )

    # -----------------------------------------------------
    # Validate upload.
    # -----------------------------------------------------

    if not file or not file.filename:

        return (
            "No file uploaded",
            400
        )

    filename = file.filename

    # -----------------------------------------------------
    # Create unique upload name.
    # -----------------------------------------------------

    unique_id = uuid.uuid4().hex

    extension = os.path.splitext(
        filename
    )[1].lower()

    stored_filename = (
        f"{unique_id}{extension}"
    )

    upload_path = os.path.join(
        UPLOAD_FOLDER,
        stored_filename
    )

    file.save(
        upload_path
    )

    try:

        # =================================================
        # EXTRACT DOCUMENT DATA
        # =================================================

        document_data = extract_document_data(
            upload_path
        )

        # =================================================
        # EXTRACTED TEXT
        # =================================================

        extracted_text = document_data.get(
            "text",
            ""
        )

        # =================================================
        # OCR DETECTIONS
        # =================================================

        ocr_field_detections = (
            detect_sensitive_fields_from_ocr(
                document_data
            )
        )

        # =================================================
        # NORMAL ANALYSIS
        # =================================================

        result = analyze_text(
            extracted_text,
            document_name=filename
        )

        existing_detections = result.get(
            "detections",
            []
        )

        # =================================================
        # PREFER POSITIONAL OCR DETECTIONS
        # =================================================

        if ocr_field_detections:

            result["detections"] = (
                ocr_field_detections
            )

        else:

            result["detections"] = (
                existing_detections
            )

        # =================================================
        # RISK
        # =================================================

        result["risk"] = calculate_risk(
            result["detections"]
        )

        # =================================================
        # MASKED TEXT PREVIEW
        # =================================================

        if document_data.get(
            "type"
        ) == "image":

            result["masked_text"] = (
                create_masked_text_preview(
                    document_data,
                    result["detections"]
                )
            )

        else:

            result["masked_text"] = (
                mask_text_by_values(
                    extracted_text,
                    result["detections"]
                )
            )

        # =================================================
        # REPORT
        # =================================================

        result["report"] = generate_report(
            result,
            document_name=filename
        )

        # =================================================
        # ORIGINAL SERVER FILE
        # =================================================

        result["original_file"] = (
            upload_path
        )

        # =================================================
        # UNIQUE DOCUMENT ID
        # =================================================

        document_id = unique_id

        result["document_id"] = (
            document_id
        )

        # =================================================
        # SAVE COMPLETE INTERNAL OCR DATA
        # =================================================
        #
        # IMPORTANT:
        #
        # Do NOT put this data inside the HTML form.
        #
        # It may contain:
        #
        # - PIL Image
        # - OCR image information
        # - coordinates
        # - page information
        #
        # The server keeps the original data.
        # =================================================

        save_internal_document_data(
            document_id,
            document_data
        )

        # =================================================
        # ONLY JSON-SAFE DATA FOR DISPLAY
        # =================================================

        result["document_data"] = (
            make_json_safe(
                document_data
            )
        )

        # =================================================
        # RESULT PAGE
        # =================================================

        return render_template(
            "result.html",
            result=result,
            document_name=filename
        )

    except Exception as error:

        print(
            "========================================"
        )

        print(
            "ERROR PROCESSING FILE:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )

        return (
            f"Error processing file: {error}"
        ), 500


# =========================================================
# PROTECT DOCUMENT
# =========================================================

@app.route(
    "/protect",
    methods=["POST"]
)
def protect():

    # -----------------------------------------------------
    # Get form values.
    # -----------------------------------------------------

    masked_text = request.form.get(
        "masked_text",
        ""
    )

    document_name = request.form.get(
        "document_name",
        "document"
    )

    result_json = request.form.get(
        "result",
        ""
    )

    if not result_json:

        return (
            "No analysis result provided",
            400
        )

    # =====================================================
    # LOAD ANALYSIS RESULT
    # =====================================================

    try:

        result = json.loads(
            result_json
        )

    except Exception as error:

        print(
            "ERROR READING RESULT JSON:",
            repr(error)
        )

        return (
            "Invalid analysis result",
            400
        )

    # =====================================================
    # DETECTIONS
    # =====================================================

    detections = result.get(
        "detections",
        []
    )

    # =====================================================
    # ORIGINAL SERVER FILE
    # =====================================================

    original_file = result.get(
        "original_file"
    )

    if not original_file:

        return (
            "Original file information is missing",
            400
        )

    if not os.path.isfile(
        original_file
    ):

        return (
            "Original uploaded file not found",
            404
        )

    # =====================================================
    # DOCUMENT ID
    # =====================================================

    document_id = result.get(
        "document_id"
    )

    if not document_id:

        return (
            "Document processing information is missing",
            400
        )

    # =====================================================
    # LOAD ORIGINAL OCR DATA
    # =====================================================
    #
    # This is the important correction.
    #
    # We DO NOT use:
    #
    #     result["document_data"]
    #
    # because that is only the JSON-safe display copy.
    #
    # We use the original OCR data saved on the server.
    # =====================================================

    document_data = (
        load_internal_document_data(
            document_id
        )
    )

    if document_data is None:

        return (
            "Original OCR document data could not be loaded.",
            500
        )

    # =====================================================
    # FILE NAME
    # =====================================================

    base_name = os.path.splitext(
        os.path.basename(
            document_name
        )
    )[0]

    protected_filename = (
        f"{base_name}_protected.pdf"
    )

    protected_path = os.path.join(
        PROTECTED_FOLDER,
        protected_filename
    )

    # =====================================================
    # REMOVE OLD OUTPUT
    # =====================================================

    if os.path.exists(
        protected_path
    ):

        try:

            os.remove(
                protected_path
            )

        except Exception as error:

            print(
                "WARNING: Could not remove old protected file:",
                repr(error)
            )

    # =====================================================
    # CREATE PROTECTED PDF
    # =====================================================

    try:

        print(
            "========================================"
        )

        print(
            "CREATING PROTECTED DOCUMENT"
        )

        print(
            "Original:",
            original_file
        )

        print(
            "Output:",
            protected_path
        )

        print(
            "Detections:",
            detections
        )

        print(
            "Document data type:",
            document_data.get(
                "type"
            )
            if isinstance(
                document_data,
                dict
            )
            else type(
                document_data
            )
        )

        print(
            "========================================"
        )

        created_path = create_protected_pdf(
            original_file,
            protected_path,
            detections,
            document_data
        )

    except Exception as error:

        print(
            "========================================"
        )

        print(
            "ERROR CREATING PROTECTED DOCUMENT:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )

        return (
            f"Error creating protected document: {error}"
        ), 500

    # =====================================================
    # CHECK CREATED PATH
    # =====================================================

    if not created_path:

        return (
            "Protected document was not created.",
            500
        )

    if not os.path.isfile(
        created_path
    ):

        return (
            "Protected document was not created.",
            500
        )

    # =====================================================
    # CHECK FILE SIZE
    # =====================================================

    file_size = os.path.getsize(
        created_path
    )

    print(
        "PROTECTED FILE SIZE:",
        file_size
    )

    if file_size <= 0:

        return (
            "Protected document is empty.",
            500
        )

    # =====================================================
    # CHECK PDF HEADER
    # =====================================================

    try:

        with open(
            created_path,
            "rb"
        ) as pdf_file:

            header = pdf_file.read(
                5
            )

    except Exception as error:

        print(
            "ERROR READING PROTECTED FILE:",
            repr(error)
        )

        return (
            "Could not verify protected document.",
            500
        )

    print(
        "PROTECTED FILE HEADER:",
        header
    )

    if header != b"%PDF-":

        return (
            "Protected document is not a valid PDF.",
            500
        )

    # =====================================================
    # PRIVACY REPORT
    # =====================================================

    report_filename = (
        f"{base_name}_privacy_report.pdf"
    )

    report_path = os.path.join(
        REPORT_FOLDER,
        report_filename
    )

    try:

        generate_privacy_report_pdf(
            report_path,
            result,
            document_name
        )

    except Exception as error:

        print(
            "ERROR GENERATING PRIVACY REPORT:",
            repr(error)
        )

        report_filename = None

    # =====================================================
    # DOWNLOAD URL
    # =====================================================

    protected_download_url = url_for(
        "download_protected",
        filename=protected_filename
    )

    # =====================================================
    # PROTECTED PAGE
    # =====================================================

    return render_template(
        "protected.html",
        protected_filename=protected_filename,
        protected_file=protected_filename,
        protected_download_url=protected_download_url,
        report_filename=report_filename,
        document_name=document_name,
        result=result
    )


# =========================================================
# DOWNLOAD PROTECTED PDF
# =========================================================

@app.route(
    "/download-protected/<path:filename>",
    methods=["GET"]
)
def download_protected(
    filename
):

    safe_filename = os.path.basename(
        filename
    )

    # -----------------------------------------------------
    # PDF ONLY
    # -----------------------------------------------------

    if not safe_filename.lower().endswith(
        ".pdf"
    ):

        abort(
            400
        )

    # =====================================================
    # PATH
    # =====================================================

    protected_folder = os.path.abspath(
        app.config[
            "PROTECTED_FOLDER"
        ]
    )

    file_path = os.path.abspath(
        os.path.join(
            protected_folder,
            safe_filename
        )
    )

    # =====================================================
    # SECURITY
    # =====================================================

    if not file_path.startswith(
        protected_folder + os.sep
    ):

        abort(
            403
        )

    # =====================================================
    # EXISTS
    # =====================================================

    if not os.path.isfile(
        file_path
    ):

        return (
            "Protected file not found.",
            404
        )

    # =====================================================
    # VERIFY PDF
    # =====================================================

    try:

        with open(
            file_path,
            "rb"
        ) as pdf_file:

            header = pdf_file.read(
                5
            )

    except Exception as error:

        print(
            "ERROR READING DOWNLOAD FILE:",
            repr(error)
        )

        return (
            "Could not read protected PDF.",
            500
        )

    if header != b"%PDF-":

        print(
            "DOWNLOAD BLOCKED."
        )

        print(
            "INVALID HEADER:",
            header
        )

        return (
            "The protected file is invalid.",
            500
        )

    # =====================================================
    # SEND PDF
    # =====================================================

    response = send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=safe_filename,
        conditional=False,
        max_age=0
    )

    # =====================================================
    # NO CACHE
    # =====================================================

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    response.headers[
        "Content-Type"
    ] = "application/pdf"

    return response


# =========================================================
# DOWNLOAD PRIVACY REPORT
# =========================================================

@app.route(
    "/download-report/<path:filename>",
    methods=["GET"]
)
def download_report(
    filename
):

    safe_filename = os.path.basename(
        filename
    )

    if not safe_filename.lower().endswith(
        ".pdf"
    ):

        abort(
            400
        )

    report_folder = os.path.abspath(
        app.config[
            "REPORT_FOLDER"
        ]
    )

    file_path = os.path.abspath(
        os.path.join(
            report_folder,
            safe_filename
        )
    )

    if not file_path.startswith(
        report_folder + os.sep
    ):

        abort(
            403
        )

    if not os.path.isfile(
        file_path
    ):

        return (
            "Privacy report not found.",
            404
        )

    try:

        with open(
            file_path,
            "rb"
        ) as pdf_file:

            header = pdf_file.read(
                5
            )

    except Exception:

        return (
            "Could not read privacy report.",
            500
        )

    if header != b"%PDF-":

        return (
            "Privacy report is not a valid PDF.",
            500
        )

    response = send_file(
        file_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=safe_filename,
        conditional=False,
        max_age=0
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    response.headers[
        "Expires"
    ] = "0"

    response.headers[
        "Content-Type"
    ] = "application/pdf"

    return response


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )