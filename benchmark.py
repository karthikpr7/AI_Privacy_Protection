import time
from modules.rule_detector import scan_patterns
from modules.context_validator import validate_detection

# Benchmark Test Suite: Ground Truth Matrix
# Each case has the text, expected detections, and non-sensitive tokens that must NOT be detected.
TEST_CASES = [
    {
        "description": "Standard Invoice with PAN and Account",
        "text": "Tax Invoice: INV-2026-001. PAN: ABCDE1234F. Account Number: 123456789012. Total: 45000.",
        "expected_sensitive": ["ABCDE1234F", "123456789012"],
        "expected_ignored": ["INV-2026-001", "45000"]
    },
    {
        "description": "Routine Receipt with Quantities and Totals (Zero Sensitive Data)",
        "text": "Order ID: 9876543210. Item Qty: 12. Unit Price: 450. Subtotal: 5400. Page 1 of 1.",
        "expected_sensitive": [],
        "expected_ignored": ["9876543210", "12", "450", "5400"]
    },
    {
        "description": "Financial Statement with Credit Card and False-Positive Order Number",
        "text": "Order Reference: 887766554433. Payment Method: Visa Card 4532 0150 1234 5678. CVV: 891.",
        "expected_sensitive": ["4532 0150 1234 5678", "891"],
        "expected_ignored": ["887766554433"]
    },
    {
        "description": "Salary Slip with IFSC and Account",
        "text": "Employee: John Doe. IFSC Code: HDFC0001234. Salary A/C: 987654321098. Basic: 75000.",
        "expected_sensitive": ["HDFC0001234", "987654321098"],
        "expected_ignored": ["75000"]
    }
]

def run_benchmark():
    total_expected_positive = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    start_time = time.time()

    for idx, case in enumerate(TEST_CASES, start=1):
        text = case["text"]
        expected = set(case["expected_sensitive"])

        # Run pipeline
        matches = scan_patterns(text)
        detected = []
        for m in matches:
            start_w = max(0, m["start"] - 60)
            end_w = min(len(text), m["end"] + 60)
            context = text[start_w:end_w]

            if validate_detection(m, context):
                detected.append(m["text"])

        detected_set = set(detected)
        total_expected_positive += len(expected)

        tp = len(detected_set & expected)
        fp = len(detected_set - expected)
        fn = len(expected - detected_set)

        true_positives += tp
        false_positives += fp
        false_negatives += fn

        print(f"[{idx}] {case['description']}")
        print(f"    Expected : {list(expected)}")
        print(f"    Detected : {list(detected_set)}")
        print(f"    Status   : {'PASS' if detected_set == expected else 'FAIL'}")

    elapsed_ms = (time.time() - start_time) * 1000

    # Calculate Metrics
    precision = (true_positives / (true_positives + false_positives)) if (true_positives + false_positives) > 0 else 1.0
    recall = (true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) > 0 else 1.0
    f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print("\n" + "=" * 45)
    print("           BENCHMARK RESULTS")
    print("=" * 45)
    print(f"Total Test Cases   : {len(TEST_CASES)}")
    print(f"Execution Latency  : {elapsed_ms:.2f} ms")
    print(f"Precision          : {precision * 100:.1f}%")
    print(f"Recall             : {recall * 100:.1f}%")
    print(f"F1-Score           : {f1_score * 100:.1f}%")
    print(f"False Positives    : {false_positives}")
    print(f"False Negatives    : {false_negatives}")
    print("=" * 45)

if __name__ == "__main__":
    run_benchmark()