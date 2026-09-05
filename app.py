from flask import (
    Flask,
    render_template,
    request,
    send_file
)

import os
import json
from werkzeug.utils import secure_filename

from modules.detector import analyze_text

from modules.masking import mask_text_by_values

from modules.ocr import (
    extract_document_data,
    detect_sensitive_fields_from_ocr,
    create_masked_text_preview
)

from modules.document_protector import (
    create_protected_pdf
)

from modules.report_generator import (
    generate_report,
    generate_privacy_report_pdf
)

from modules.risk_analyzer import (
    calculate_risk
)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "uploads"

PROTECTED_FOLDER = "outputs/protected"

REPORT_FOLDER = "outputs/reports"


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["PROTECTED_FOLDER"] = PROTECTED_FOLDER

app.config["REPORT_FOLDER"] = REPORT_FOLDER


# =========================================================
# CREATE REQUIRED FOLDERS
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


# =========================================================
# ALLOWED FILE EXTENSIONS
# =========================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}


def allowed_file(filename):
    """
    Check whether the uploaded file type
    is supported by the project.
    """

    if not filename:
        return False

    extension = os.path.splitext(
        filename
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


# =========================================================
# HOME PAGE
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

    try:

        # -------------------------------------------------
        # Analyze normal text
        # -------------------------------------------------

        result = analyze_text(
            text
        )

        # -------------------------------------------------
        # Recalculate risk using the final
        # approved sensitive detections.
        # -------------------------------------------------

        result["risk"] = calculate_risk(
            result.get(
                "detections",
                []
            )
        )

        # -------------------------------------------------
        # Create masked preview
        # -------------------------------------------------

        result["masked_text"] = (
            mask_text_by_values(
                text,
                result.get(
                    "detections",
                    []
                )
            )
        )

        # -------------------------------------------------
        # Generate report information
        # -------------------------------------------------

        result["report"] = generate_report(
            result
        )

        return render_template(
            "result.html",
            text=text,
            result=result
        )

    except Exception as error:

        print(
            f"ERROR ANALYZING TEXT: {error}"
        )

        return (
            f"Error analyzing text: {error}"
        ), 500


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
    # Check uploaded file
    # -----------------------------------------------------

    if not file or not file.filename:

        return (
            "No file uploaded",
            400
        )

    original_filename = file.filename

    # -----------------------------------------------------
    # Check extension
    # -----------------------------------------------------

    if not allowed_file(
        original_filename
    ):

        return (
            "Unsupported file type. "
            "Please upload PDF, PNG, JPG or JPEG.",
            400
        )

    # -----------------------------------------------------
    # Secure filename
    # -----------------------------------------------------

    filename = secure_filename(
        original_filename
    )

    if not filename:

        return (
            "Invalid file name.",
            400
        )

    upload_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    try:

        # =================================================
        # SAVE UPLOADED FILE
        # =================================================

        file.save(
            upload_path
        )

        print(
            f"FILE UPLOADED: {filename}"
        )

        # =================================================
        # EXTRACT DOCUMENT DATA
        # =================================================
        #
        # This performs:
        #
        #   PDF/image text extraction
        #   Full OCR
        #   Word-level OCR
        #   Position extraction
        #
        # It is the ONLY document extraction call.
        #
        # =================================================

        document_data = (
            extract_document_data(
                upload_path
            )
        )

        # =================================================
        # GET EXTRACTED TEXT
        # =================================================

        extracted_text = (
            document_data.get(
                "text",
                ""
            )
        )

        # =================================================
        # DETECT APPROVED SENSITIVE FIELDS
        # =================================================
        #
        # IMPORTANT:
        #
        # detect_sensitive_fields_from_ocr()
        # only returns approved sensitive categories.
        #
        # It should ignore:
        #
        #   Name
        #   Address
        #   DOB
        #   Phone
        #   Email
        #   Website
        #   URL
        #   IP
        #   MAC
        #   normal dates
        #   normal numbers
        #   unknown NER entities
        #
        # =================================================

        ocr_field_detections = (
            detect_sensitive_fields_from_ocr(
                document_data
            )
        )

        print(
            "OCR DETECTIONS:",
            ocr_field_detections
        )

        # =================================================
        # RUN TEXT DETECTION
        # =================================================
        #
        # This provides NER + regex detection.
        #
        # combine_results.py already filters
        # NER results to approved sensitive labels.
        #
        # =================================================

        result = analyze_text(
            extracted_text,
            document_name=filename
        )

        existing_detections = (
            result.get(
                "detections",
                []
            )
        )

        # =================================================
        # FINAL DETECTION SELECTION
        # =================================================
        #
        # OCR detections are preferred because they
        # contain document positions needed for masking.
        #
        # If OCR finds nothing, fall back to the
        # normal NER + regex detector.
        #
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
        # PRINT FINAL DETECTIONS
        # =================================================

        print(
            "FINAL DETECTIONS:",
            result["detections"]
        )

        # =================================================
        # RECALCULATE PRIVACY RISK
        # =================================================

        result["risk"] = calculate_risk(
            result.get(
                "detections",
                []
            )
        )

        # =================================================
        # CREATE MASKED TEXT PREVIEW
        # =================================================
        #
        # Both images and PDFs can now have OCR
        # positional information.
        #
        # Therefore both are sent through the OCR
        # preview function.
        #
        # =================================================

        document_type = (
            document_data.get(
                "type"
            )
        )

        if document_type in {
            "image",
            "pdf"
        }:

            result["masked_text"] = (
                create_masked_text_preview(
                    document_data,
                    result.get(
                        "detections",
                        []
                    )
                )
            )

        else:

            result["masked_text"] = (
                mask_text_by_values(
                    extracted_text,
                    result.get(
                        "detections",
                        []
                    )
                )
            )

        # =================================================
        # GENERATE PRIVACY REPORT DATA
        # =================================================

        result["report"] = (
            generate_report(
                result,
                document_name=filename
            )
        )

        # =================================================
        # STORE ORIGINAL FILE PATH
        # =================================================

        result["original_file"] = (
            upload_path
        )

        # =================================================
        # STORE DOCUMENT DATA
        # =================================================
        #
        # NOTE:
        #
        # Flask/Jinja can work with this while the result
        # page is being rendered.
        #
        # =================================================

        result["document_data"] = (
            document_data
        )

        # =================================================
        # SHOW RESULT PAGE
        # =================================================

        return render_template(
            "result.html",
            result=result,
            document_name=filename
        )

    except Exception as error:

        # -------------------------------------------------
        # Print complete error to terminal / Render logs.
        # -------------------------------------------------

        print(
            "ERROR PROCESSING FILE:"
        )

        print(
            repr(error)
        )

        # -------------------------------------------------
        # Remove partially saved upload if necessary.
        # -------------------------------------------------

        try:

            if os.path.exists(
                upload_path
            ):

                os.remove(
                    upload_path
                )

        except Exception:
            pass

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

    # =====================================================
    # GET FORM DATA
    # =====================================================

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

    # =====================================================
    # CHECK RESULT
    # =====================================================

    if not result_json:

        return (
            "No analysis result provided",
            400
        )

    # =====================================================
    # LOAD RESULT JSON
    # =====================================================

    try:

        result = json.loads(
            result_json
        )

    except Exception as error:

        print(
            f"ERROR READING RESULT JSON: {error}"
        )

        return (
            "Invalid analysis result",
            400
        )

    # =====================================================
    # GET DETECTIONS
    # =====================================================

    detections = result.get(
        "detections",
        []
    )

    # =====================================================
    # GET ORIGINAL FILE
    # =====================================================

    original_file = result.get(
        "original_file"
    )

    # =====================================================
    # GET DOCUMENT DATA
    # =====================================================

    document_data = result.get(
        "document_data"
    )

    # =====================================================
    # VALIDATE ORIGINAL FILE
    # =====================================================

    if not original_file:

        return (
            "Original file information is missing",
            400
        )

    if not os.path.exists(
        original_file
    ):

        return (
            "Original uploaded file not found",
            404
        )

    # =====================================================
    # VALIDATE DOCUMENT DATA
    # =====================================================

    if not document_data:

        return (
            "Document position data is missing",
            400
        )

    # =====================================================
    # PROTECTED FILE NAME
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
        app.config[
            "PROTECTED_FOLDER"
        ],
        protected_filename
    )

    # =====================================================
    # CREATE PROTECTED DOCUMENT
    # =====================================================
    #
    # For PDF:
    #
    #   original layout/page size is preserved
    #
    # For scanned documents:
    #
    #   sensitive fields are masked at their
    #   detected positions.
    #
    # =====================================================

    try:

        create_protected_pdf(
            original_file,
            protected_path,
            detections,
            document_data
        )

    except Exception as error:

        print(
            "ERROR CREATING PROTECTED FILE:"
        )

        print(
            repr(error)
        )

        return (
            f"Error creating protected document: "
            f"{error}"
        ), 500

    # =====================================================
    # GENERATE PRIVACY REPORT
    # =====================================================

    report_filename = (
        f"{base_name}_privacy_report.pdf"
    )

    report_path = os.path.join(
        app.config[
            "REPORT_FOLDER"
        ],
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
            "ERROR GENERATING PRIVACY REPORT:"
        )

        print(
            repr(error)
        )

        return (
            f"Error generating privacy report: "
            f"{error}"
        ), 500

    # =====================================================
    # PROTECTED PAGE
    # =====================================================

    return render_template(
        "protected.html",

        protected_filename=(
            protected_filename
        ),

        protected_file=(
            protected_filename
        ),

        report_filename=(
            report_filename
        ),

        document_name=(
            document_name
        ),

        result=result
    )


# =========================================================
# DOWNLOAD PROTECTED DOCUMENT
# =========================================================

@app.route(
    "/download-protected/<filename>"
)
def download_protected(
    filename
):

    # -----------------------------------------------------
    # Prevent directory traversal.
    # -----------------------------------------------------

    safe_filename = secure_filename(
        filename
    )

    if not safe_filename:

        return render_template(
            "index.html",
            error="Invalid protected file name."
        )

    file_path = os.path.join(
        app.config[
            "PROTECTED_FOLDER"
        ],
        safe_filename
    )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if not os.path.isfile(
        file_path
    ):

        return render_template(
            "index.html",
            error="Protected file not found."
        )

    # -----------------------------------------------------
    # Send file
    # -----------------------------------------------------

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_filename
    )


# =========================================================
# DOWNLOAD PRIVACY REPORT
# =========================================================

@app.route(
    "/download-report/<filename>"
)
def download_report(
    filename
):

    # -----------------------------------------------------
    # Prevent directory traversal.
    # -----------------------------------------------------

    safe_filename = secure_filename(
        filename
    )

    if not safe_filename:

        return render_template(
            "index.html",
            error="Invalid report file name."
        )

    file_path = os.path.join(
        app.config[
            "REPORT_FOLDER"
        ],
        safe_filename
    )

    # -----------------------------------------------------
    # Check file
    # -----------------------------------------------------

    if not os.path.isfile(
        file_path
    ):

        return render_template(
            "index.html",
            error="Privacy report not found."
        )

    # -----------------------------------------------------
    # Send report
    # -----------------------------------------------------

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_filename
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )