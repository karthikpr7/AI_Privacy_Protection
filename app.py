from flask import (
    Flask,
    render_template,
    request,
    send_file
)
import os

from modules.detector import analyze_text
from modules.ocr import extract_text_from_file
from modules.document_protector import create_protected_pdf
from modules.report_generator import generate_privacy_report_pdf

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

PROTECTED_FOLDER = "outputs/protected"

REPORT_FOLDER = "outputs/reports"

app.config["REPORT_FOLDER"] = REPORT_FOLDER

os.makedirs(
    REPORT_FOLDER,
    exist_ok=True
)

app.config["PROTECTED_FOLDER"] = PROTECTED_FOLDER

os.makedirs(
    PROTECTED_FOLDER,
    exist_ok=True
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


@app.route("/", methods=["GET"])
def home():

    return render_template(
        "index.html"
    )


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


@app.route("/analyze-file", methods=["POST"])
def analyze_file():

    uploaded_file = request.files.get("file")

    if uploaded_file is None:
        return render_template(
            "index.html",
            error="Please select a file."
        )

    if uploaded_file.filename == "":
        return render_template(
            "index.html",
            error="Please select a file."
        )

    filename = uploaded_file.filename

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    uploaded_file.save(file_path)

    try:

        # --------------------------------
        # EXTRACT TEXT / OCR
        # --------------------------------

        extracted_text = extract_text_from_file(
            file_path
        )

        if not extracted_text or not extracted_text.strip():

            return render_template(
                "index.html",
                error="No text could be extracted from the file."
            )

        # --------------------------------
        # PRIVACY ANALYSIS
        # --------------------------------

        result = analyze_text(
            extracted_text,
            document_name=filename
        )

        # --------------------------------
        # RESULTS PAGE
        # ---------------------- ----------

        return render_template(
            "result.html",
            text=extracted_text,
            result=result,
            document_name=filename
        )

    except Exception as error:

        print("\n" + "=" * 70)
        print("FILE ANALYSIS ERROR")
        print("=" * 70)
        print(error)
        print("=" * 70 + "\n")

        return render_template(
            "index.html",
            error=f"File processing failed: {error}"
        )
    
@app.route("/protect", methods=["POST"])
def protect_document():

    masked_text = request.form.get(
        "masked_text",
        ""
    )

    document_name = request.form.get(
        "document_name",
        "protected_document"
    )

    result_json = request.form.get(
        "result",
        ""
    )

    # -----------------------------------------
    # VALIDATE PROTECTED TEXT
    # -----------------------------------------

    if not masked_text.strip():

        return render_template(
            "index.html",
            error="No protected text is available."
        )

    # -----------------------------------------
    # RESTORE ANALYSIS RESULT
    # -----------------------------------------

    import json

    try:

        result = json.loads(
            result_json
        )

        # Make sure required keys exist
        if not isinstance(result, dict):

            raise ValueError(
                "Invalid analysis result."
            )

        if "detections" not in result:

            raise ValueError(
                "Analysis result does not contain detections."
            )

        if "risk" not in result:

            raise ValueError(
                "Analysis result does not contain risk information."
            )

    except Exception as error:

        print("\n" + "=" * 70)
        print("PROTECTION RESULT ERROR")
        print("=" * 70)
        print(error)
        print("=" * 70 + "\n")

        return render_template(
            "index.html",
            error=(
                "Analysis result could not be recovered. "
                "Please analyze the document again."
            )
        )

    # -----------------------------------------
    # FILE NAME
    # -----------------------------------------

    base_name = os.path.splitext(
        document_name
    )[0]

    # -----------------------------------------
    # PROTECTED PDF
    # -----------------------------------------

    protected_filename = (
        f"{base_name}_protected.pdf"
    )

    protected_path = os.path.join(
        app.config["PROTECTED_FOLDER"],
        protected_filename
    )

    create_protected_pdf(
        masked_text,
        protected_path
    )

    # -----------------------------------------
    # PRIVACY REPORT PDF
    # -----------------------------------------

    report_filename = (
        f"{base_name}_privacy_report.pdf"
    )

    report_path = os.path.join(
        app.config["REPORT_FOLDER"],
        report_filename
    )

    generate_privacy_report_pdf(
        report_path,
        result,
        document_name
    )

    # -----------------------------------------
    # SUCCESS
    # -----------------------------------------

    return render_template(
        "protected.html",
        protected_file=protected_filename,
        report_file=report_filename
    )

@app.route("/download-protected/<filename>")
def download_protected(filename):

    file_path = os.path.join(
        app.config["PROTECTED_FOLDER"],
        filename
    )

    if not os.path.isfile(file_path):

        return render_template(
            "index.html",
            error="Protected file not found."
        )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )

@app.route("/download-report/<filename>")
def download_report(filename):

    file_path = os.path.join(
        app.config["REPORT_FOLDER"],
        filename
    )

    if not os.path.isfile(file_path):

        return render_template(
            "index.html",
            error="Privacy report not found."
        )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":

    app.run(
        debug=True
    )