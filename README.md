# AI-Based Privacy Protection

An AI-based privacy protection system that detects high-risk sensitive information in text and documents, analyzes privacy risk, partially masks sensitive information, and generates protected documents and privacy reports.

---

## 📌 Project Overview

**AI-Based Privacy Protection** is a web-based privacy protection system developed using **Python and Flask**.

The system combines a **100,000-record trained spaCy Named Entity Recognition (NER) model**, **Regex-based detection**, and **OCR-based document analysis** to identify high-risk sensitive information.

The system is designed to avoid unnecessary masking. Common personal information such as names, email addresses, phone numbers, addresses, dates, websites, IP addresses, and MAC addresses are intentionally ignored.

After detecting approved sensitive information, the system:

- Identifies high-risk sensitive information
- Calculates a privacy score
- Determines the privacy risk level
- Partially masks sensitive information
- Generates a protected document
- Generates a professional privacy report PDF
- Allows users to download the protected document
- Allows users to download the privacy report

---

## 🎯 Objectives

The main objectives of this project are:

1. Detect high-risk sensitive information automatically.
2. Use AI-based NER for contextual sensitive-information detection.
3. Use Regex for structured sensitive-information detection.
4. Use OCR for detecting sensitive information in image-based documents.
5. Combine NER, Regex, and OCR detection results.
6. Remove duplicate and overlapping detections.
7. Ignore unnecessary personal information and unrelated NER entities.
8. Calculate privacy risk based on detected sensitive information.
9. Partially mask high-risk sensitive information.
10. Generate protected documents while preserving the original document layout as closely as possible.
11. Generate a privacy analysis report.
12. Provide an easy-to-use Flask web interface.

---

## ✨ Features

- AI-based sensitive-information detection
- 100K-record trained spaCy NER model
- Regex-based structured detection
- OCR-based document detection
- Hybrid NER + Regex detection
- Image/document sensitive-field detection
- Duplicate and overlapping detection handling
- Strict sensitive-label filtering
- False-positive reduction
- Privacy score calculation
- Risk-level classification
- Partial sensitive-information masking
- PDF text extraction
- Image OCR
- Protected document generation
- Privacy report PDF generation
- Text analysis
- Document analysis
- Protected document download
- Privacy report download
- Flask web application

---

## 🔍 Sensitive Information Detection

The final system focuses only on approved high-risk sensitive information.

### Sensitive Information Detected and Protected

The system can detect and mask categories such as:

- PAN
- Aadhaar
- Passport Number
- Driving Licence Number
- Voter ID
- Bank Account Number
- IFSC Code
- Credit Card Number
- Debit Card Number
- UPI ID
- Password
- API Key
- Access Token
- Secret Key

The system uses both AI-based detection and rule-based detection depending on the type of sensitive information.

---

## 🚫 Information Intentionally Ignored

The system is designed to avoid unnecessary privacy masking.

The following information is intentionally ignored and remains unchanged:

- Names
- Given names
- Surnames
- Email addresses
- Phone numbers
- Addresses
- Building numbers
- Street names
- City names
- ZIP/PIN codes
- Dates
- Date of Birth
- Time
- Age
- Gender
- Sex
- Titles
- Website URLs
- Hyperlinks
- Domain names
- Social-media links
- IP addresses
- MAC addresses
- Normal numbers
- Normal dates
- Unknown or unapproved NER entities

This prevents normal personal information from being incorrectly treated as a high-risk privacy threat.

---

## 🤖 AI Model

A spaCy **Named Entity Recognition (NER)** model was trained using **100,000 records** from the PII dataset.

The trained model is used to identify sensitive information based on the context in which it appears.

### Training Details

| Parameter | Value |
|---|---|
| Training Records | 100,000 |
| Framework | spaCy |
| Model Type | Named Entity Recognition |
| Validation Dataset | `dev_validation.jsonl` |
| Model Directory | `models/privacy_ner_100k/final/` |

The trained model is included in the repository so that the application can load the trained model during execution and deployment.

---

## 📊 Model Performance

The final 100K-record NER model achieved the following validation performance:

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

**Note:** The NER model was trained on a broader set of PII entity types. The application applies a strict allowlist so that only approved high-risk sensitive categories are considered for privacy protection.

---

## 🔀 Hybrid Detection

The project uses multiple detection methods because different types of sensitive information require different approaches.

### 1. NER Detection

The trained spaCy NER model is used for contextual detection.

The application filters the NER output so that only approved sensitive labels are considered for privacy protection.

This filtering also helps reduce false positives from unrelated entities.

---

### 2. Regex Detection

Regex detection is used for structured sensitive-information patterns.

Examples include:

```text
ABCDE1234F
1234 5678 9012
4111 1111 1111 1111
SBIN0001234
rahulsharma@okicici

Regex validation helps improve the reliability of structured identifier detection.

Credit-card numbers are also checked using additional validation.

3. OCR Detection

For image-based and scanned documents, the system uses OCR to extract text and identify sensitive fields.

The OCR process:

Reads text from the uploaded document.
Identifies field labels such as PAN Number, Aadhaar Number, Bank Account Number, etc.
Locates the corresponding sensitive value.
Determines the position of the value in the document.
Sends the detected information for risk analysis.
Uses the detected coordinates to mask the sensitive information at its original position.

This allows the system to protect sensitive information in document images while preserving the original document layout as closely as possible.

4. Combining Results

The NER and Regex detection results are combined.

The system:

Filters unapproved entity labels.
Removes duplicate detections.
Handles overlapping detections.
Gives priority to Regex results when both methods detect the same information.
Keeps only approved high-risk sensitive categories.

This reduces false positives and prevents the same sensitive information from being reported multiple times.

🔐 Privacy Protection and Masking

The project separates detection from masking.

Not every detected personal entity is automatically masked.

Only approved high-risk sensitive information is masked.

Name

Input:

Rahul Sharma

Output:

Rahul Sharma

Names are intentionally left unchanged.

Email

Input:

rahul@gmail.com

Output:

rahul@gmail.com

Email addresses are intentionally left unchanged.

Phone

Input:

+91 9876543210

Output:

+91 9876543210

Phone numbers are intentionally left unchanged.

PAN

Input:

ABCDE1234F

Output:

ABC*****4F
Aadhaar

Input:

1234 5678 9012

Output:

**** **** 9012
Credit Card

Input:

4111 1111 1111 1111

Output:

**** **** **** 1111
UPI ID

Input:

rahulsharma@okicici

Output:

***************@***icici

The masking approach keeps limited information visible where appropriate while hiding the sensitive portion of the identifier.

⚠️ Privacy Risk Analysis

The system calculates a privacy score based on the detected high-risk sensitive information.

Each approved sensitive category has an associated risk weight.

The system then determines the overall privacy risk level.

Risk Levels
Privacy Score	Risk Level
0–25	LOW
26–50	MEDIUM
51–75	HIGH
Above 75	CRITICAL

For example:

Total PII Detected: 9
Privacy Score: 100/100
Risk Level: CRITICAL

The system also generates a recommendation based on the detected risk.

🔄 System Workflow
                         User
                           |
                           v
                 Flask Web Interface
                           |
                 +---------+---------+
                 |                   |
                 v                   v
             Text Input         File Upload
                 |                   |
                 |                   v
                 |             Text Extraction
                 |                   |
                 |          +--------+--------+
                 |          |                 |
                 |          v                 v
                 |      100K NER          Regex
                 |          |                 |
                 |          +--------+--------+
                 |                   |
                 |                   v
                 |            Combine Results
                 |                   |
                 |                   v
                 |             Risk Analysis
                 |                   |
                 |                   v
                 |                Masking
                 |                   |
                 |          +--------+--------+
                 |          |                 |
                 v          v                 v
             Analysis   Protected       Privacy Report
                         Document             PDF
                            |                  |
                            v                  v
                        Download           Download

For image/scanned documents:

File Upload
     |
     v
OCR Text Extraction
     |
     v
Sensitive Field Detection
     |
     v
Locate Sensitive Value
     |
     v
Mask at Original Position
     |
     v
Protected Document
🛠️ Technologies Used
Backend
Python
Flask
Artificial Intelligence
spaCy
Named Entity Recognition (NER)
100K-record trained NER model
Hybrid AI + rule-based detection
Pattern Detection
Regular Expressions
Structured identifier validation
Credit-card validation
OCR and Document Processing
PyMuPDF
Tesseract OCR
Pillow
Image processing
Report Generation
ReportLab
Frontend
HTML
CSS
JavaScript
Version Control and Deployment
Git
GitHub
Render
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
├── models/
│   └── privacy_ner_100k/
│       └── final/
│           ├── config.cfg
│           ├── meta.json
│           ├── ner/
│           └── vocab/
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

A separate validation dataset is used to evaluate the trained NER model.

The training and validation data are processed using the scripts available in the training/ directory.

The trained model is stored in:

models/privacy_ner_100k/final/
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

pip install flask spacy reportlab pymupdf pytesseract pillow

Tesseract OCR must also be installed separately for OCR-based image/document analysis.

🧠 Train the NER Model

The project uses a 100K-record training dataset.

Create the 100K Training Dataset
python training/create_large_dataset.py
Train the Model
python training/train_large.py
Evaluate the Model
python training/evaluate_100k.py

The trained model is generated under:

models/privacy_ner_100k/

The final model used by the application is:

models/privacy_ner_100k/final/
▶️ Run the Application

Start the Flask application:

python app.py

The application will run at:

http://127.0.0.1:5000

Open this address in a web browser.

🖥️ How to Use
Text Analysis
Open the web application.
Enter text containing sensitive information.
Click Analyze Text.
Review the detected sensitive information.
Review the privacy score.
Review the privacy risk level.
Review the partially masked information.
Use the protection option when required.
Download the protected document.
Download the privacy report.
Document Analysis
Open the web application.
Select a supported document.
Click Analyze Document.
The system extracts text from the document.
OCR is used when required for image-based documents.
The system detects approved sensitive information.
Review the detected sensitive information.
Review the privacy score and risk level.
Click Protect Document.
Download the protected document.
Download the privacy report.
📄 Supported File Types

The current document-processing workflow supports:

PDF
PNG
JPG
JPEG

The system can process text-based PDFs and image-based/scanned documents using OCR.

🧪 Example
Input
Contact Rahul Sharma at rahul@gmail.com.

My phone number is +91 9876543210.

My PAN is ABCDE1234F.

My Aadhaar is 1234 5678 9012.

My passport number is A1234567.

My bank account is 123456789012.

My IFSC is SBIN0001234.

My card number is 4111 1111 1111 1111.

My UPI ID is rahulsharma@okicici.
Detection Result

The system detects the approved sensitive information:

PAN
AADHAAR
PASSPORTNUM
BANK_ACCOUNT
IFSC
CREDITCARDNUMBER
UPIID

Names, email addresses, and phone numbers are intentionally ignored.

Protected Output
Contact Rahul Sharma at rahul@gmail.com.

My phone number is +91 9876543210.

My PAN is ABC*****4F.

My Aadhaar is **** **** 9012.

My passport number is ****4567.

My bank account is ********9012.

My IFSC is *******1234.

My card number is **** **** **** 1111.

My UPI ID is ***************@***icici.

The exact protected output depends on the detected values and masking rules.

📊 Example Risk Result

For a document containing several high-risk sensitive identifiers:

Total PII Detected: 9

Privacy Score: 100/100

Risk Level: CRITICAL

The system generates a recommendation based on the detected risk.

📄 Generated Files

The application generates two main outputs.

Protected Document

The protected document contains partially masked sensitive information.

For uploaded image/document files, the system uses the detected positions of sensitive values to apply masking while preserving the original document layout as closely as possible.

Privacy Report PDF

The privacy report contains information such as:

Document name
Total sensitive information detected
Privacy score
Risk level
Detected sensitive categories
Privacy recommendation
🧪 Testing

The application was tested through the complete privacy-protection workflow:

Document Upload
       ↓
Text/OCR Extraction
       ↓
Sensitive Information Detection
       ↓
NER + Regex Combination
       ↓
False-Positive Filtering
       ↓
Risk Analysis
       ↓
Masking
       ↓
Protected Document
       ↓
Privacy Report PDF
       ↓
Download

Testing includes:

Sensitive-information detection
False-positive filtering
Multiple sensitive categories
OCR-based detection
UPI detection
Sensitive-information masking
Privacy score calculation
Risk-level calculation
Protected document generation
Privacy report generation

The complete application workflow was successfully tested.

🔒 Privacy and Security

This project is intended for academic, educational, and demonstration purposes.

Do not use real sensitive personal information while testing the application.

Use synthetic or test data whenever possible.

The project follows a strict detection policy so that only approved high-risk sensitive information is considered for protection.

Sensitive information is not intentionally stored as part of the application's normal analysis workflow.

🔮 Future Improvements

Possible future improvements include:

Improved OCR accuracy for difficult scanned documents
Support for additional document formats such as DOCX
Multilingual PII detection
Improved contextual sensitive-information detection
Improved detection of difficult sensitive-information categories
User-configurable masking policies
Authentication and authorization
Database-based audit logs
Advanced document layout preservation
More extensive real-world evaluation
Improved document-processing performance
👨‍💻 Project Information

Project Title: AI-Based Privacy Protection

Technology: Python, Flask, spaCy, Regex, PyMuPDF, Tesseract OCR, Pillow, ReportLab

Training Dataset Size: 100,000 records

NER Precision: 91.47%

NER Recall: 90.64%

NER F1-score: 91.05%

Deployment: Flask application deployed using Render

📌 Disclaimer

This system is an academic and educational project for privacy protection research and demonstration.

Detection results may not be perfect, and the system should not be considered a replacement for professional privacy, security, or compliance solutions.