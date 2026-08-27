import json
from pathlib import Path
from collections import Counter

import pandas as pd


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "cleaned_train.jsonl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "preprocessed_train.jsonl"
)


# =========================================================
# LOAD CLEANED DATASET
# =========================================================

print("=" * 70)
print("DATA PREPROCESSING")
print("=" * 70)

print()
print("Loading cleaned dataset...")

records = []

with INPUT_FILE.open(
    "r",
    encoding="utf-8"
) as file:

    for line in file:

        line = line.strip()

        if not line:
            continue

        records.append(
            json.loads(line)
        )


print(
    f"Records loaded: {len(records)}"
)


# =========================================================
# CREATE DATAFRAME
# =========================================================

df = pd.DataFrame(records)


# =========================================================
# DATASET STRUCTURE
# =========================================================

print()
print("=" * 70)
print("DATASET STRUCTURE")
print("=" * 70)

print()

print(
    "Columns:"
)

for column in df.columns:

    print(
        f" - {column}"
    )


# =========================================================
# TEXT PREPROCESSING
# =========================================================

print()
print("=" * 70)
print("TEXT PREPROCESSING")
print("=" * 70)


# Remove unnecessary leading/trailing spaces

df["source_text"] = (
    df["source_text"]
    .astype(str)
    .str.strip()
)

df["masked_text"] = (
    df["masked_text"]
    .astype(str)
    .str.strip()
)


print(
    "Source text whitespace cleaned."
)

print(
    "Masked text whitespace cleaned."
)


# =========================================================
# PRIVACY MASK PROCESSING
# =========================================================

print()
print("=" * 70)
print("PRIVACY MASK PROCESSING")
print("=" * 70)


mask_count = 0

for mask in df["privacy_mask"]:

    if isinstance(mask, list):

        mask_count += len(mask)

    elif isinstance(mask, str):

        if mask.strip():

            mask_count += 1


print(
    f"Privacy mask information processed."
)

print(
    f"Total mask entries detected: {mask_count}"
)


# =========================================================
# TOKEN PROCESSING
# =========================================================

print()
print("=" * 70)
print("TOKEN PROCESSING")
print("=" * 70)


token_counts = []

for tokens in df["mbert_tokens"]:

    if isinstance(tokens, list):

        token_counts.append(
            len(tokens)
        )

    elif isinstance(tokens, str):

        try:

            parsed_tokens = json.loads(
                tokens
            )

            token_counts.append(
                len(parsed_tokens)
            )

        except Exception:

            token_counts.append(0)

    else:

        token_counts.append(0)


df["token_count"] = token_counts


print(
    f"Average tokens per record: "
    f"{df['token_count'].mean():.2f}"
)

print(
    f"Minimum tokens: "
    f"{df['token_count'].min()}"
)

print(
    f"Maximum tokens: "
    f"{df['token_count'].max()}"
)


# =========================================================
# ENTITY CLASS PROCESSING
# =========================================================

print()
print("=" * 70)
print("PII ENTITY CLASS PROCESSING")
print("=" * 70)


entity_counter = Counter()


for classes in df["mbert_token_classes"]:

    if isinstance(classes, list):

        for label in classes:

            entity_counter[
                str(label)
            ] += 1

    elif isinstance(classes, str):

        try:

            parsed_classes = json.loads(
                classes
            )

            for label in parsed_classes:

                entity_counter[
                    str(label)
                ] += 1

        except Exception:

            pass


print()

for label, count in sorted(
    entity_counter.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"{label:<25} {count}"
    )


# =========================================================
# TEXT LENGTH
# =========================================================

df["text_length"] = (
    df["source_text"]
    .str.len()
)


print()
print("=" * 70)
print("TEXT LENGTH PROCESSING")
print("=" * 70)

print(
    f"Average text length: "
    f"{df['text_length'].mean():.2f}"
)

print(
    f"Minimum text length: "
    f"{df['text_length'].min()}"
)

print(
    f"Maximum text length: "
    f"{df['text_length'].max()}"
)


# =========================================================
# KEEP REQUIRED DATA
# =========================================================

processed_records = []

for _, row in df.iterrows():

    record = {
        "source_text": row["source_text"],
        "masked_text": row["masked_text"],
        "privacy_mask": row["privacy_mask"],
        "split": row["split"],
        "uid": row["uid"],
        "language": row["language"],
        "region": row["region"],
        "script": row["script"],
        "mbert_tokens": row["mbert_tokens"],
        "mbert_token_classes": row["mbert_token_classes"]
    }

    processed_records.append(
        record
    )


# =========================================================
# SAVE PREPROCESSED DATA
# =========================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as file:

    for record in processed_records:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False
            )
            + "\n"
        )


# =========================================================
# FINAL SUMMARY
# =========================================================

print()
print("=" * 70)
print("DATA PREPROCESSING COMPLETED")
print("=" * 70)

print()
print(
    f"Input records: {len(records)}"
)

print(
    f"Processed records: "
    f"{len(processed_records)}"
)

print(
    f"Unique PII classes: "
    f"{len(entity_counter)}"
)

print()
print("Output:")
print(OUTPUT_FILE)

print()
print("=" * 70)