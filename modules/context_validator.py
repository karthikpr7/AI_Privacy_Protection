import re

POSITIVE_INDICATORS = {
    "Bank_Account_Candidate": [
        "account", "ac no", "savings", "current", "a/c", "bank", 
        "beneficiary", "acc", "acct"
    ],
    "PAN": ["pan", "permanent account", "income tax"],
    "Credit_or_Debit_Card": ["card", "visa", "mastercard", "rupay", "amex"]
}

# Benign labels that indicate this number is NOT a bank account
BENIGN_PREFIXES = [
    "invoice", "inv", "order", "bill", "receipt", "qty", "quantity",
    "amount", "price", "total", "item", "page no", "pg"
]

def validate_detection(finding: dict, context_window: str) -> bool:
    label = finding["label"]
    val = finding["text"]

    if label == "Bank_Account_Candidate":
        # Normalize whitespace (replace newlines/tabs with spaces)
        normalized_context = re.sub(r"\s+", " ", context_window).lower()
        clean_val = val.lower()

        idx = normalized_context.find(clean_val)
        prefix = normalized_context[max(0, idx - 45):idx] if idx != -1 else normalized_context

        # Check for explicit banking anchors first
        has_positive_anchor = any(pos in prefix for pos in POSITIVE_INDICATORS["Bank_Account_Candidate"])
        
        # Check if preceded by benign non-sensitive tags
        has_benign_prefix = any(neg in prefix for neg in BENIGN_PREFIXES)

        # If a positive banking anchor exists (e.g. "bank account:"), accept it
        if has_positive_anchor:
            return True

        # Otherwise reject if it looks like an order, invoice, or unanchored number
        if has_benign_prefix:
            return False

        return False

    return True