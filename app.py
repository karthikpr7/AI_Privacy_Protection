from flask import (
    Flask,
    render_template,
    request,
    send_file
)

import os
import json

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
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# TEXT ANALYSIS
# =========================================================

@app.route("/analyze", methods=["POST"])
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

@app.route("/analyze-file", methods=["POST"])
def analyze_file():

    file = request.files.get(
        "file"
    )

    if not file or not file.filename:

        return (
            "No file uploaded",
            400
        )

    filename = file.filename

    upload_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    file.save(
        upload_path
    )

    try:

        # =================================================
        # EXTRACT DOCUMENT DATA
        # =================================================
        #
        # IMPORTANT:
        #
        # This is now the ONLY extraction call.
        #
        # For images:
        #
        #     extract_document_data()
        #
        # performs OCR once and provides both:
        #
        #     document_data["text"]
        #
        # and
        #
        #     document_data["words"]
        #
        # Previously the application called:
        #
        #     extract_text_from_file()
        #
        # and then:
        #
        #     extract_document_data()
        #
        # which caused OCR to run twice.
        #
        # =================================================

        document_data = extract_document_data(
            upload_path
        )

        # =================================================
        # USE TEXT ALREADY EXTRACTED
        # =================================================

        extracted_text = document_data.get(
            "text",
            ""
        )

        # =================================================
        # OCR FIELD DETECTION
        # =================================================

        ocr_field_detections = (
            detect_sensitive_fields_from_ocr(
                document_data
            )
        )

        # =================================================
        # RUN PRIVACY DETECTION
        # =================================================

        result = analyze_text(
            extracted_text,
            document_name=filename
        )

        # =================================================
        # IMAGE DOCUMENT
        # =================================================

        if document_data.get(
            "type"
        ) == "image":

            existing_detections = result.get(
                "detections",
                []
            )

            # -------------------------------------------------
            # Use OCR positional detections for images.
            # -------------------------------------------------

            result["detections"] = (

                ocr_field_detections

                if ocr_field_detections

                else existing_detections
            )

        # =================================================
        # RECALCULATE RISK
        # =================================================

        result["risk"] = calculate_risk(
            result["detections"]
        )

        # =================================================
        # CREATE MASKED TEXT PREVIEW
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
        # GENERATE PRIVACY REPORT
        # =================================================

        result["report"] = generate_report(
            result,
            document_name=filename
        )

        # =================================================
        # STORE INFORMATION FOR /PROTECT
        # =================================================

        result["original_file"] = (
            upload_path
        )

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
        # Log the actual error on Render.
        # -------------------------------------------------

        print(
            f"ERROR PROCESSING FILE: {error}"
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

    try:

        result = json.loads(
            result_json
        )

    except Exception:

        return (
            "Invalid analysis result",
            400
        )

    detections = result.get(
        "detections",
        []
    )

    original_file = result.get(
        "original_file"
    )

    document_data = result.get(
        "document_data"
    )

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
        PROTECTED_FOLDER,
        protected_filename
    )

    # =====================================================
    # CREATE PROTECTED DOCUMENT
    # =====================================================

    create_protected_pdf(
        original_file,
        protected_path,
        detections,
        document_data
    )

    # =====================================================
    # GENERATE PRIVACY REPORT
    # =====================================================

    report_filename = (
        f"{base_name}_privacy_report.pdf"
    )

    report_path = os.path.join(
        REPORT_FOLDER,
        report_filename
    )

    generate_privacy_report_pdf(
        report_path,
        result,
        document_name
    )

    # =====================================================
    # PROTECTED PAGE
    # =====================================================

    return render_template(
        "protected.html",
        protected_filename=protected_filename,
        protected_file=protected_filename,
        report_filename=report_filename,
        document_name=document_name,
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

    file_path = os.path.join(
        app.config[
            "PROTECTED_FOLDER"
        ],
        filename
    )

    if not os.path.isfile(
        file_path
    ):

        return render_template(
            "index.html",
            error="Protected file not found."
        )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
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

    file_path = os.path.join(
        app.config[
            "REPORT_FOLDER"
        ],
        filename
    )

    if not os.path.isfile(
        file_path
    ):

        return render_template(
            "index.html",
            error="Privacy report not found."
        )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )