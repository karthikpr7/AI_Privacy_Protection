import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    BASE_DIR
    / "dataset"
    / "raw"
    / "data"
    / "train"
    / "train.jsonl"
)

REPORT_FILE = BASE_DIR / "outputs" / "annotation_validation.txt"
REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Counters
# ---------------------------------------------------------

total_records = 0
valid_records = 0
invalid_records = 0

total_entities = 0
valid_entities = 0
invalid_entities = 0

empty_text_records = 0
empty_annotation_records = 0
malformed_records = 0

overlapping_entities = 0
duplicate_entities = 0

invalid_labels = Counter()
invalid_reasons = Counter()


# ---------------------------------------------------------
# First pass: collect all labels
# ---------------------------------------------------------

print("Collecting entity labels...")

all_labels = set()

with TRAIN_FILE.open("r", encoding="utf-8") as file:

    for line in file:

        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        privacy_mask = record.get("privacy_mask", [])

        if isinstance(privacy_mask, list):

            for entity in privacy_mask:

                if isinstance(entity, dict):

                    label = entity.get("label")

                    if label:
                        all_labels.add(label)


print("Labels found:")
print(sorted(all_labels))
print()


# ---------------------------------------------------------
# Validate records
# ---------------------------------------------------------

print("Starting annotation validation...\n")

with TRAIN_FILE.open("r", encoding="utf-8") as file:

    for line_number, line in enumerate(file, start=1):

        line = line.strip()

        if not line:
            continue

        total_records += 1

        record_valid = True

        # -------------------------------------------------
        # Parse JSON
        # -------------------------------------------------

        try:
            record = json.loads(line)

        except json.JSONDecodeError:

            malformed_records += 1
            invalid_records += 1
            invalid_reasons["Malformed JSON"] += 1
            continue

        # -------------------------------------------------
        # Source text
        # -------------------------------------------------

        source_text = record.get("source_text")

        if not isinstance(source_text, str):

            record_valid = False
            invalid_reasons["Missing or invalid source_text"] += 1

            source_text = ""

        if len(source_text) == 0:

            empty_text_records += 1
            record_valid = False
            invalid_reasons["Empty source_text"] += 1

        # -------------------------------------------------
        # Privacy mask
        # -------------------------------------------------

        privacy_mask = record.get("privacy_mask")

        if not isinstance(privacy_mask, list):

            record_valid = False
            invalid_reasons["Invalid privacy_mask"] += 1

            privacy_mask = []

        if len(privacy_mask) == 0:

            empty_annotation_records += 1

        # Store entity ranges for overlap checking
        entity_ranges = []

        # -------------------------------------------------
        # Validate every entity
        # -------------------------------------------------

        for entity in privacy_mask:

            total_entities += 1

            entity_valid = True

            if not isinstance(entity, dict):

                entity_valid = False
                invalid_reasons["Entity is not a dictionary"] += 1

                invalid_entities += 1
                record_valid = False

                continue

            label = entity.get("label")
            start = entity.get("start")
            end = entity.get("end")
            value = entity.get("value")

            # ---------------------------------------------
            # Validate label
            # ---------------------------------------------

            if not isinstance(label, str) or not label:

                entity_valid = False
                invalid_reasons["Missing label"] += 1

            # ---------------------------------------------
            # Validate start/end
            # ---------------------------------------------

            if not isinstance(start, int):

                entity_valid = False
                invalid_reasons["Invalid start"] += 1

            if not isinstance(end, int):

                entity_valid = False
                invalid_reasons["Invalid end"] += 1

            if isinstance(start, int) and isinstance(end, int):

                if start < 0:

                    entity_valid = False
                    invalid_reasons["start < 0"] += 1

                if end > len(source_text):

                    entity_valid = False
                    invalid_reasons["end > text length"] += 1

                if start >= end:

                    entity_valid = False
                    invalid_reasons["start >= end"] += 1

                # -----------------------------------------
                # Check extracted text
                # -----------------------------------------

                if 0 <= start < end <= len(source_text):

                    extracted_value = source_text[start:end]

                    if value != extracted_value:

                        entity_valid = False
                        invalid_reasons["Value does not match source text"] += 1

                    entity_ranges.append(
                        (start, end, label)
                    )

            # ---------------------------------------------
            # Count invalid labels
            # ---------------------------------------------

            if label and label not in all_labels:

                invalid_labels[label] += 1

            # ---------------------------------------------
            # Entity result
            # ---------------------------------------------

            if entity_valid:

                valid_entities += 1

            else:

                invalid_entities += 1
                record_valid = False

        # -------------------------------------------------
        # Check duplicate entities
        # -------------------------------------------------

        seen_entities = set()

        for start, end, label in entity_ranges:

            key = (start, end, label)

            if key in seen_entities:

                duplicate_entities += 1

                invalid_reasons["Duplicate entity"] += 1

                record_valid = False

            else:

                seen_entities.add(key)

        # -------------------------------------------------
        # Check overlapping entities
        # -------------------------------------------------

        sorted_ranges = sorted(
            entity_ranges,
            key=lambda x: (x[0], x[1])
        )

        for i in range(len(sorted_ranges)):

            current_start, current_end, current_label = sorted_ranges[i]

            for j in range(i + 1, len(sorted_ranges)):

                next_start, next_end, next_label = sorted_ranges[j]

                if next_start >= current_end:
                    break

                # Ignore exact duplicates because they were
                # already counted above.
                if (
                    current_start,
                    current_end,
                    current_label
                ) == (
                    next_start,
                    next_end,
                    next_label
                ):
                    continue

                overlapping_entities += 1

                invalid_reasons["Overlapping entities"] += 1

                record_valid = False

        # -------------------------------------------------
        # Record result
        # -------------------------------------------------

        if record_valid:

            valid_records += 1

        else:

            invalid_records += 1


# ---------------------------------------------------------
# Print report
# ---------------------------------------------------------

report_lines = []

report_lines.append("=" * 70)
report_lines.append("ANNOTATION VALIDATION REPORT")
report_lines.append("=" * 70)

report_lines.append("")
report_lines.append(f"Total records: {total_records}")
report_lines.append(f"Valid records: {valid_records}")
report_lines.append(f"Invalid records: {invalid_records}")

report_lines.append("")
report_lines.append(f"Total entities: {total_entities}")
report_lines.append(f"Valid entities: {valid_entities}")
report_lines.append(f"Invalid entities: {invalid_entities}")

report_lines.append("")
report_lines.append(f"Empty source text records: {empty_text_records}")
report_lines.append(
    f"Records without annotations: {empty_annotation_records}"
)

report_lines.append(
    f"Malformed JSON records: {malformed_records}"
)

report_lines.append(
    f"Duplicate entities: {duplicate_entities}"
)

report_lines.append(
    f"Overlapping entities: {overlapping_entities}"
)

report_lines.append("")
report_lines.append("=" * 70)
report_lines.append("VALIDATION REASONS")
report_lines.append("=" * 70)

if invalid_reasons:

    for reason, count in invalid_reasons.most_common():

        report_lines.append(
            f"{reason}: {count}"
        )

else:

    report_lines.append("No validation errors found.")


report_lines.append("")
report_lines.append("=" * 70)
report_lines.append("ENTITY LABELS")
report_lines.append("=" * 70)

for label in sorted(all_labels):

    report_lines.append(label)


report = "\n".join(report_lines)

print(report)

REPORT_FILE.write_text(
    report,
    encoding="utf-8"
)

print()
print("Validation report saved to:")
print(REPORT_FILE)