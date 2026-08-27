import json
from pathlib import Path
import pandas as pd


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
    / "cleaned_train.jsonl"
)


# =========================================================
# LOAD DATASET
# =========================================================

print("=" * 70)
print("DATA CLEANING")
print("=" * 70)

print()
print("Loading dataset...")

records = []

invalid_json = 0

with INPUT_FILE.open(
    "r",
    encoding="utf-8"
) as file:

    for line in file:

        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)

            if isinstance(record, dict):
                records.append(record)

        except json.JSONDecodeError:
            invalid_json += 1


print(
    f"Original records: {len(records)}"
)


# =========================================================
# CREATE DATAFRAME
# =========================================================

df = pd.DataFrame(records)


# =========================================================
# DATASET INFORMATION
# =========================================================

print()
print("=" * 70)
print("DATASET COLUMNS")
print("=" * 70)

print(
    df.columns.tolist()
)


# =========================================================
# MISSING VALUES
# =========================================================

print()
print("=" * 70)
print("MISSING VALUES")
print("=" * 70)

print(
    df.isnull().sum()
)


# =========================================================
# REMOVE MISSING SOURCE TEXT
# =========================================================

before_missing = len(df)

df = df.dropna(
    subset=["source_text"]
)

df = df[
    df["source_text"]
    .astype(str)
    .str.strip()
    != ""
]

removed_missing = (
    before_missing - len(df)
)

print()
print(
    f"Records removed because of "
    f"missing/empty source_text: "
    f"{removed_missing}"
)


# =========================================================
# DUPLICATE RECORDS
# =========================================================

print()
print("=" * 70)
print("DUPLICATE RECORDS")
print("=" * 70)

duplicate_count = df.duplicated(
    subset=["source_text"]
).sum()

print(
    f"Duplicate records: "
    f"{duplicate_count}"
)


df = df.drop_duplicates(
    subset=["source_text"]
)


# =========================================================
# TEXT CLEANING
# =========================================================

print()
print("=" * 70)
print("TEXT CLEANING")
print("=" * 70)


df["source_text"] = (
    df["source_text"]
    .astype(str)
    .str.strip()
)


# =========================================================
# CHECK PRIVACY MASK
# =========================================================

if "privacy_mask" in df.columns:

    missing_mask = df[
        "privacy_mask"
    ].isnull().sum()

    print(
        f"Missing privacy masks: "
        f"{missing_mask}"
    )


# =========================================================
# CHECK LANGUAGE
# =========================================================

if "language" in df.columns:

    print(
        f"Missing language values: "
        f"{df['language'].isnull().sum()}"
    )


# =========================================================
# CHECK REGION
# =========================================================

if "region" in df.columns:

    print(
        f"Missing region values: "
        f"{df['region'].isnull().sum()}"
    )


# =========================================================
# CHECK SCRIPT
# =========================================================

if "script" in df.columns:

    print(
        f"Missing script values: "
        f"{df['script'].isnull().sum()}"
    )


# =========================================================
# SAVE CLEANED DATA
# =========================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as file:

    for record in df.to_dict(
        orient="records"
    ):

        file.write(
            json.dumps(
                record,
                ensure_ascii=False
            )
            + "\n"
        )


# =========================================================
# FINAL RESULTS
# =========================================================

print()
print("=" * 70)
print("DATA CLEANING COMPLETED")
print("=" * 70)

print()
print(
    f"Original records : {len(records)}"
)

print(
    f"Invalid JSON     : {invalid_json}"
)

print(
    f"Final clean records: {len(df)}"
)

print(
    f"Duplicate records: {duplicate_count}"
)

print()
print("Output:")
print(OUTPUT_FILE)

print()
print("=" * 70)