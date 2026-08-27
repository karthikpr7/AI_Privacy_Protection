# AI-Based Privacy Protection

An AI-based privacy protection system that detects Personally Identifiable Information (PII) in text and documents, analyzes privacy risk, partially masks sensitive information, and generates protected documents and privacy reports.

---

## 📌 Project Overview

**AI-Based Privacy Protection** is a web-based privacy protection system developed using Python and Flask.

The system combines a **100,000-record trained spaCy Named Entity Recognition (NER) model** with **Regex-based detection** to identify sensitive personal information.

After detecting PII, the system:

- Identifies sensitive information
- Calculates a privacy score
- Determines the privacy risk level
- Partially masks sensitive information
- Generates a protected PDF
- Generates a professional privacy report PDF
- Allows users to download the protected document and privacy report

---

## 🎯 Objectives

The main objectives of this project are:

1. Detect sensitive personal information automatically.
2. Use AI-based NER for contextual PII detection.
3. Use Regex for structured PII detection.
4. Combine NER and Regex detection results.
5. Calculate privacy risk.
6. Protect sensitive information through masking.
7. Generate a protected document.
8. Generate a privacy analysis report.
9. Provide an easy-to-use web interface.

---

## ✨ Features

- AI-based PII detection
- 100K-record trained NER model
- Regex-based PII detection
- Hybrid NER + Regex detection
- Duplicate and overlapping detection handling
- Privacy score calculation
- Risk-level classification
- Partial PII masking
- PDF/document text extraction
- Protected PDF generation
- Professional privacy report PDF
- Text analysis
- Document analysis
- Download protected document
- Download privacy report
- Flask web application

---

## 🔍 PII Detection

The system can detect multiple categories of Personally Identifiable Information.

The supported entity categories include:

- GIVENNAME
- SURNAME
- EMAIL
- TELEPHONENUM
- PAN
- AADHAAR
- CREDITCARDNUMBER
- PASSPORTNUM
- DRIVERLICENSENUM
- IDCARDNUM
- TAXNUM
- SOCIALNUM
- CITY
- STREET
- ZIPCODE
- DATE
- TIME
- AGE
- GENDER
- SEX
- TITLE
- BUILDINGNUM

---

## 🤖 AI Model

A spaCy Named Entity Recognition (NER) model was trained using **100,000 records** from the PII dataset.

### Training Details

| Parameter | Value |
|---|---|
| Training Records | 100,000 |
| Framework | spaCy |
| Model Type | Named Entity Recognition |
| Validation Dataset | `dev_validation.jsonl` |
| Best Model | `privacy_ner_100k/best` |

The trained model is stored locally and is excluded from GitHub using `.gitignore`.

The model can be recreated using the training scripts provided in this repository.

---

## 📊 Model Performance

The final 100K NER model achieved the following validation performance:

| Metric | Score |
|---|---:|
| Precision | 91.47% |
| Recall | 90.64% |
| F1-score | 91.05% |

### Per-Entity Performance

| Entity | Precision | Recall | F1-score |
|---|---:|---:|---:|
| AGE | 91.67% | 97.78% | 94.62% |
| BUILDINGNUM | 98.10% | 93.64% | 95.81% |
| CITY | 91.62% | 93.71% | 92.66% |
| CREDITCARDNUMBER | 62.07% | 90.00% | 73.47% |
| DATE | 100.00% | 100.00% | 100.00% |
| DRIVERLICENSENUM | 100.00% | 37.50% | 54.55% |
| EMAIL | 100.00% | 100.00% | 100.00% |
| GENDER | 78.95% | 75.00% | 76.92% |
| GIVENNAME | 90.05% | 90.90% | 90.47% |
| IDCARDNUM | 81.32% | 90.24% | 85.55% |
| PASSPORTNUM | 90.70% | 92.86% | 91.76% |
| SEX | 73.91% | 80.95% | 77.27% |
| SOCIALNUM | 71.43% | 78.95% | 75.00% |
| STREET | 94.74% | 92.31% | 93.51% |
| SURNAME | 85.53% | 75.29% | 80.08% |
| TAXNUM | 88.24% | 68.18% | 76.92% |
| TELEPHONENUM | 98.68% | 100.00% | 99.33% |
| TIME | 98.57% | 100.00% | 99.28% |
| TITLE | 98.36% | 98.36% | 98.36% |
| ZIPCODE | 86.67% | 82.98% | 84.78% |

---

## 🔀 Hybrid Detection

The project uses two complementary PII detection methods.

### 1. NER Detection

The trained spaCy NER model is used to detect contextual entities.

For example:

```text
Rahul Sharma

can be identified by the NER model as a personal name entity.

2. Regex Detection

Regex detection is used for structured PII patterns.

Examples include:

rahul@gmail.com
+91 9876543210
ABCDE1234F
1234 5678 9012
4111 1111 1111 1111
3. Combining Results

The system combines the NER and Regex results.

Overlapping duplicate detections are removed so that the same information is not reported multiple times.

Regex detections receive priority when both detection methods identify overlapping text.

🔐 Privacy Protection

The system separates PII detection from PII masking.

Names are intentionally kept visible:

Rahul Sharma

Sensitive information is partially masked.

Email
rahul@gmail.com

becomes:

r***l@gmail.com
Phone Number
+91 9876543210

becomes:

+91******3210
PAN
ABCDE1234F

becomes:

ABC*****4F
Aadhaar
1234 5678 9012

becomes:

**** **** 9012
Credit Card
4111 1111 1111 1111

becomes:

**** **** **** 1111

This approach protects sensitive identifiers while keeping selected information readable.

⚠️ Privacy Risk Analysis

The system analyzes the detected PII and calculates a privacy score.

It also classifies the privacy risk into a risk level.

Example:

Total PII Detected: 6
Privacy Score: 100/100
Risk Level: CRITICAL

The system also provides a recommendation based on the identified privacy risk.

🔄 System Workflow
                    User
                     |
                     v
              Flask Web Interface
                     |
             +-------+-------+
             |               |
             v               v
        Text Input       File Upload
                             |
                             v
                     Text Extraction
                             |
              +--------------+--------------+
              |                             |
              v                             v
        100K NER Model                   Regex
              |                             |
              +--------------+--------------+
                             |
                             v
                    Combine Results
                             |
                             v
                     Risk Analysis
                             |
                             v
                        Masking
                             |
                   +---------+---------+
                   |                   |
                   v                   v
             Protected PDF      Privacy Report PDF
                   |                   |
                   v                   v
               Download            Download
🛠️ Technologies Used
Backend
Python
Flask
Artificial Intelligence
spaCy
Named Entity Recognition (NER)
PII Detection
Regular Expressions
Hybrid NER + Regex detection
Document Processing
PyMuPDF
ReportLab
Frontend
HTML
CSS
JavaScript
Version Control
Git
GitHub
📁 Project Structure
AI_Privacy_Protection/
│
├── app.py
│
├── dataset/
│   └── processed/
│       ├── large_train.jsonl
│       └── dev_validation.jsonl
│
├── modules/
│   ├── __init__.py
│   ├── combine_results.py
│   ├── detector.py
│   ├── document_protector.py
│   ├── masking.py
│   ├── ner.py
│   ├── ocr.py
│   ├── regex_detector.py
│   ├── report_generator.py
│   └── risk_analyzer.py
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   ├── index.html
│   ├── protected.html
│   └── result.html
│
├── training/
│   ├── analyze_class_balance.py
│   ├── check_dataset.py
│   ├── create_large_dataset.py
│   ├── dataset_statistics.py
│   ├── eda.py
│   ├── error_analysis.py
│   ├── evaluate_100k.py
│   ├── train_large.py
│   └── validate_annotations.py
│
├── test_files/
│   └── privacy_test_valid.pdf
│
├── .gitignore
└── README.md
📚 Dataset

The project uses a PII dataset containing annotated personal information for training the NER model.

The final training dataset contains:

100,000 training records

The validation dataset is used to evaluate the trained NER model.

The raw dataset is kept locally and excluded from the GitHub repository.

The processed datasets used by the project are included in the repository where appropriate.

🚀 Installation
1. Clone the Repository
git clone https://github.com/karthikpr7/AI_Privacy_Protection.git
2. Navigate to the Project
cd AI_Privacy_Protection
3. Create a Virtual Environment
python -m venv venv
4. Activate the Virtual Environment

On Windows:

venv\Scripts\activate
5. Install Dependencies

Install the required Python packages:

pip install flask spacy reportlab pymupdf
🧠 Train the NER Model

The project uses a 100K-record training dataset.

Create the 100K Training Dataset
python training/create_large_dataset.py
Train the Model
python training/train_large.py
Evaluate the Model
python training/evaluate_100k.py

The trained model will be generated in:

models/privacy_ner_100k/

The best model is stored in:

models/privacy_ner_100k/best/
▶️ Run the Application

Start the Flask application:

python app.py

The application will run at:

http://127.0.0.1:5000

Open this address in a web browser.

🖥️ How to Use
Text Analysis
Open the web application.
Enter text containing personal information.
Click Analyze Text.
Review the detected PII.
Review the privacy score and risk level.
Review the partially masked text.
Click Protect Document.
Download the protected PDF.
Download the privacy report PDF.
Document Analysis
Open the web application.
Select a document.
Click Analyze Document.
The system extracts the text from the document.
The system detects PII using NER and Regex.
Review the detected PII and privacy risk.
Click Protect Document.
Download the protected document.
Download the privacy report.
🧪 Example
Input
Contact Rahul Sharma at rahul@gmail.com.
My phone number is +91 9876543210.
My PAN is ABCDE1234F.
My Aadhaar is 1234 5678 9012.
My card number is 4111 1111 1111 1111.
Detected PII
GIVENNAME
EMAIL
TELEPHONENUM
PAN
AADHAAR
CREDITCARDNUMBER
Protected Output
Contact Rahul Sharma at r***l@gmail.com.
My phone number is +91******3210.
My PAN is ABC*****4F.
My Aadhaar is **** **** 9012.
My card number is **** **** **** 1111.
Risk Result
Total PII Detected: 6
Privacy Score: 100/100
Risk Level: CRITICAL
📄 Generated Files

The application generates two main outputs.

Protected PDF

The protected PDF contains the partially masked sensitive information.

Privacy Report PDF

The privacy report contains information such as:

Document name
Total PII detected
Privacy score
Risk level
Detected PII categories
Privacy recommendation
🧪 Testing

The project includes a test PDF:

test_files/privacy_test_valid.pdf

The application was tested through the complete workflow:

Document Upload
       ↓
Text Extraction
       ↓
PII Detection
       ↓
Risk Analysis
       ↓
Masking
       ↓
Protected PDF
       ↓
Privacy Report PDF
       ↓
Download

The complete application workflow was successfully tested.

🔒 Privacy and Security

This project is intended for academic, educational, and demonstration purposes.

Do not use real sensitive personal information while testing the application.

Use synthetic or test data whenever possible.

The following files are intentionally excluded from the GitHub repository:

Virtual environment
Trained model files
Raw dataset files
Uploaded documents
Generated output files
Python cache files

These files are excluded through .gitignore.

🔮 Future Improvements

Possible future improvements include:

Improved OCR for scanned documents
Support for additional document formats
Multilingual PII detection
Improved contextual PII detection
User-configurable masking policies
Authentication and authorization
Database-based audit logs
Cloud deployment
More extensive real-world evaluation
Improved detection of difficult PII categories
👨‍💻 Project Information

Project Title: AI-Based Privacy Protection

Technology: Python, Flask, spaCy, Regex, PyMuPDF, ReportLab

Training Dataset Size: 100,000 records

Precision: 91.47%

Recall: 90.64%

F1-score: 91.05%

📌 Disclaimer

This system is an academic and educational project for privacy protection research and demonstration.

Detection results may not be perfect, and the system should not be considered a replacement for professional privacy, security, or compliance solutions.