import json
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "train_spacy.jsonl"
)


entity_counts = Counter()
record_counts = Counter()

total_records = 0


print("Analyzing training dataset...")
print(f"Dataset: {TRAIN_FILE}")
print()


with TRAIN_FILE.open("r", encoding="utf-8") as file:

    for line in file:

        line = line.strip()

        if not line:
            continue

        record = json.loads(line)

        total_records += 1

        labels_in_record = set()

        for entity in record.get("entities", []):

            label = entity["label"]

            entity_counts[label] += 1
            labels_in_record.add(label)

        for label in labels_in_record:
            record_counts[label] += 1


print("=" * 70)
print("CLASS BALANCE ANALYSIS")
print("=" * 70)

print(f"Total training records: {total_records}")
print()


print(
    f"{'Entity':<22}"
    f"{'Entity Count':>15}"
    f"{'Records':>15}"
)

print("-" * 52)


for label, count in entity_counts.most_common():

    print(
        f"{label:<22}"
        f"{count:>15}"
        f"{record_counts[label]:>15}"
    )


print()
print("=" * 70)
print("LEAST FREQUENT ENTITIES")
print("=" * 70)

for label, count in entity_counts.most_common()[::-1]:

    print(
        f"{label:<22}{count}"
    )