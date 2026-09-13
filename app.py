import os
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from modules.privacy_engine import process_document
from modules.document_protector import apply_redaction

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, 'processed')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB upload ceiling

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/scan', methods=['POST'])
def scan_document():
    if 'document' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['document']
    if not file or file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    orig_name = secure_filename(file.filename)
    saved_name = f"{int(time.time())}_{orig_name}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_name)
    file.save(file_path)

    # Convert standard image formats directly to PDF for uniform pipeline handling
    ext = os.path.splitext(saved_name)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
        pdf_name = f"{os.path.splitext(saved_name)[0]}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        
        img = Image.open(file_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(pdf_path, "PDF", resolution=100.0)
        
        saved_name = pdf_name
        file_path = pdf_path

    detections = process_document(file_path)

    return jsonify({
        "status": "success",
        "filename": saved_name,
        "original_filename": orig_name,
        "detections": detections
    })

@app.route('/protect', methods=['POST'])
def protect_document():
    data = request.get_json() or {}
    filename = data.get('filename')
    mode = data.get('mode', 'partial')
    detections = data.get('detections', [])

    if not filename:
        return jsonify({"error": "No filename specified"}), 400

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({"error": f"File {filename} not found on server"}), 404

    out_name = f"protected_{int(time.time())}_{filename}"
    out_path = os.path.join(app.config['PROCESSED_FOLDER'], out_name)

    apply_redaction(input_path, out_path, detections, mode=mode)

    return jsonify({
        "status": "success",
        "protected_filename": out_name,
        "protected_url": f"/download/{out_name}"
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=False)

if __name__ == '__main__':
    # Binds to dynamic PORT provided by Render (falls back to 5000 locally)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)