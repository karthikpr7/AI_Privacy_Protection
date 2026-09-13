import re

PATTERNS = {
    "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "Aadhaar": r"\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b",
    "Credit_or_Debit_Card": r"\b(?:\d{4}[ -]?){3}\d{4}\b",
    "CVV": r"(?i:\b(?:cvv|cvc)\s*[:#-]?\s*)([0-9]{3,4})\b",
    "IFSC": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
    "Bank_Account_Candidate": r"\b[0-9]{9,18}\b"
}

def scan_patterns(text: str):
    findings = []
    priority_order = ["Credit_or_Debit_Card", "PAN", "Aadhaar", "CVV", "IFSC", "Bank_Account_Candidate"]
    matched_spans = []

    for label in priority_order:
        pattern = PATTERNS[label]
        for match in re.finditer(pattern, text):
            # For CVV, capture only group(1) (the digits), else the full match
            if label == "CVV":
                span = match.span(1)
                matched_text = match.group(1)
            else:
                span = (match.start(), match.end())
                matched_text = match.group()

            # Prevent overlapping spans (e.g. Bank Account overlapping a Credit Card)
            overlap = any(max(span[0], s) < min(span[1], e) for s, e in matched_spans)
            if not overlap:
                matched_spans.append(span)
                findings.append({
                    "label": label,
                    "text": matched_text,
                    "start": span[0],
                    "end": span[1]
                })

    return findings