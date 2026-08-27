import json
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    BASE_DIR
    / "dataset"
    / "raw"
    / "data"
    / "train"
    / "train.jsonl"
)

OUTPUT_DIR = BASE_DIR / "outputs" / "eda"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Counters
language_counts = Counter()
region_counts = Counter()
script_counts = Counter()
entity_counts = Counter()

text_lengths = []

total_records = 0
records_with_pii = 0
records_without_pii = 0

missing_fields = Counter()
invalid_annotations = 0


required_fields = [
    "source_text",
    "masked_text",
    "privacy_mask",
    "split",
    "uid",
    "language",
    "region",
    "script",
    "mbert_tokens",
    "mbert_token_classes",
]


print("Starting EDA...")
print(f"Dataset: {TRAIN_FILE}")
print()


with TRAIN_FILE.open("r", encoding="utf-8") as file:

    for line_number, line in enumerate(file, start=1):

        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            invalid_annotations += 1
            continue

        total_records += 1

        # Check missing fields
        for field in required_fields:
            if field not in record or record[field] is None:
                missing_fields[field] += 1

        source_text = record.get("source_text", "")
        privacy_mask = record.get("privacy_mask", [])

        # Language
        language = record.get("language")
        if language:
            language_counts[language] += 1

        # Region
        region = record.get("region")
        if region:
            region_counts[region] += 1

        # Script
        script = record.get("script")
        if script:
            script_counts[script] += 1

        # Text length
        if isinstance(source_text, str):
            text_lengths.append(len(source_text))

        # PII entities
        if isinstance(privacy_mask, list) and len(privacy_mask) > 0:
            records_with_pii += 1

            for entity in privacy_mask:

                if not isinstance(entity, dict):
                    invalid_annotations += 1
                    continue

                label = entity.get("label")

                start = entity.get("start")
                end = entity.get("end")

                if label:
                    entity_counts[label] += 1

                # Validate annotation positions
                if (
                    not isinstance(start, int)
                    or not isinstance(end, int)
                    or start < 0
                    or end < start
                    or end > len(source_text)
                ):
                    invalid_annotations += 1

        else:
            records_without_pii += 1


print("=" * 70)
print("EDA SUMMARY")
print("=" * 70)

print(f"\nTotal records: {total_records}")

print(f"Records with PII: {records_with_pii}")

print(f"Records without PII: {records_without_pii}")

print(f"Invalid annotations: {invalid_annotations}")


print("\n" + "=" * 70)
print("LANGUAGE DISTRIBUTION")
print("=" * 70)

for language, count in language_counts.most_common():
    print(f"{language}: {count}")


print("\n" + "=" * 70)
print("REGION DISTRIBUTION")
print("=" * 70)

for region, count in region_counts.most_common():
    print(f"{region}: {count}")


print("\n" + "=" * 70)
print("SCRIPT DISTRIBUTION")
print("=" * 70)

for script, count in script_counts.most_common():
    print(f"{script}: {count}")


print("\n" + "=" * 70)
print("PII ENTITY DISTRIBUTION")
print("=" * 70)

for entity, count in entity_counts.most_common():
    print(f"{entity}: {count}")


print("\n" + "=" * 70)
print("MISSING FIELDS")
print("=" * 70)

for field in required_fields:
    print(f"{field}: {missing_fields.get(field, 0)}")


if text_lengths:
    print("\n" + "=" * 70)
    print("TEXT LENGTH")
    print("=" * 70)

    print(f"Minimum: {min(text_lengths)}")
    print(f"Maximum: {max(text_lengths)}")
    print(f"Average: {sum(text_lengths) / len(text_lengths):.2f}")


# ---------------------------------------------------------
# Graph 1: PII entity distribution
# ---------------------------------------------------------

if entity_counts:

    plt.figure(figsize=(12, 6))

    entities = list(entity_counts.keys())
    counts = list(entity_counts.values())

    sns.barplot(x=counts, y=entities)

    plt.title("PII Entity Distribution")
    plt.xlabel("Number of Entities")
    plt.ylabel("PII Category")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "entity_distribution.png",
        dpi=150
    )

    plt.close()


# ---------------------------------------------------------
# Graph 2: Language distribution
# ---------------------------------------------------------

if language_counts:

    top_languages = language_counts.most_common(20)

    labels = [item[0] for item in top_languages]
    counts = [item[1] for item in top_languages]

    plt.figure(figsize=(12, 6))

    sns.barplot(x=counts, y=labels)

    plt.title("Top 20 Languages")
    plt.xlabel("Number of Records")
    plt.ylabel("Language")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "language_distribution.png",
        dpi=150
    )

    plt.close()


# ---------------------------------------------------------
# Graph 3: Region distribution
# ---------------------------------------------------------

if region_counts:

    top_regions = region_counts.most_common(20)

    labels = [item[0] for item in top_regions]
    counts = [item[1] for item in top_regions]

    plt.figure(figsize=(12, 6))

    sns.barplot(x=counts, y=labels)

    plt.title("Top 20 Regions")
    plt.xlabel("Number of Records")
    plt.ylabel("Region")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "region_distribution.png",
        dpi=150
    )

    plt.close()


# ---------------------------------------------------------
# Graph 4: Text length histogram
# ---------------------------------------------------------

if text_lengths:

    plt.figure(figsize=(10, 6))

    sns.histplot(
        text_lengths,
        bins=50,
        kde=True
    )

    plt.title("Source Text Length Distribution")
    plt.xlabel("Text Length")
    plt.ylabel("Frequency")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "text_length_distribution.png",
        dpi=150
    )

    plt.close()


# ---------------------------------------------------------
# Graph 5: Class imbalance
# ---------------------------------------------------------

if entity_counts:

    plt.figure(figsize=(12, 6))

    sorted_entities = entity_counts.most_common()

    labels = [item[0] for item in sorted_entities]
    counts = [item[1] for item in sorted_entities]

    sns.barplot(x=counts, y=labels)

    plt.title("PII Class Frequency / Class Imbalance")
    plt.xlabel("Entity Count")
    plt.ylabel("PII Class")

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "class_imbalance.png",
        dpi=150
    )

    plt.close()


print("\nEDA completed successfully.")

print("\nEDA graphs saved to:")

print(OUTPUT_DIR)