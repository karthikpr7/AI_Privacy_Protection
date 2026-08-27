import json
import random
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "raw"
    / "data"
    / "train"
    / "train.jsonl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "large_train.jsonl"
)


# =========================================================
# CONFIGURATION
# =========================================================

TRAIN_SIZE = 100000
RANDOM_SEED = 42


# =========================================================
# LOAD ORIGINAL DATASET
# =========================================================

print("=" * 70)
print("CREATING 100K TRAINING DATASET")
print("=" * 70)

print()
print("Input:")
print(INPUT_FILE)

print()
print("Loading original training dataset...")


records = []

with INPUT_FILE.open(
    "r",
    encoding="utf-8"
) as file:

    for line in file:

        line = line.strip()

        if not line:
            continue

        record = json.loads(line)

        source_text = record.get(
            "source_text",
            ""
        )

        privacy_mask = record.get(
            "privacy_mask",
            []
        )

        if not source_text.strip():
            continue

        entities = []

        for entity in privacy_mask:

            try:

                start = int(
                    entity["start"]
                )

                end = int(
                    entity["end"]
                )

                label = str(
                    entity["label"]
                )

                # -----------------------------------------
                # Validate annotation
                # -----------------------------------------

                if start < 0:
                    continue

                if end <= start:
                    continue

                if end > len(source_text):
                    continue

                entities.append(
                    (
                        start,
                        end,
                        label
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue

        records.append(
            {
                "text": source_text,
                "entities": entities
            }
        )


print(
    f"Available valid records: {len(records)}"
)


# =========================================================
# CHECK DATASET SIZE
# =========================================================

if len(records) < TRAIN_SIZE:

    raise ValueError(
        f"\nNot enough training records.\n"
        f"Required: {TRAIN_SIZE}\n"
        f"Available: {len(records)}"
    )


# =========================================================
# RANDOMLY SELECT 100K
# =========================================================

random.seed(
    RANDOM_SEED
)

random.shuffle(
    records
)

selected_records = records[
    :TRAIN_SIZE
]


# =========================================================
# SAVE
# =========================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as file:

    for record in selected_records:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False
            )
            + "\n"
        )


# =========================================================
# LABEL DISTRIBUTION
# =========================================================

label_counts = {}

for record in selected_records:

    for start, end, label in record["entities"]:

        label_counts[label] = (
            label_counts.get(label, 0) + 1
        )


# =========================================================
# RESULTS
# =========================================================

print()
print("=" * 70)
print("100K DATASET CREATED SUCCESSFULLY")
print("=" * 70)

print()
print(
    f"Training records: {len(selected_records)}"
)

print()
print("Entity distribution:")

for label in sorted(label_counts):

    print(
        f"{label:<25} "
        f"{label_counts[label]}"
    )

print()
print("Output:")
print(OUTPUT_FILE)

print()
print("=" * 70)
print("DATASET PREPARATION COMPLETED")
print("=" * 70)