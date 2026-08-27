import json
from pathlib import Path
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "large_train.jsonl"
)

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "eda"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# LOAD DATASET
# =========================================================

print("=" * 70)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 70)

print()
print("Loading 100K training dataset...")

records = []

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
            records.append(record)

        except json.JSONDecodeError:
            continue


print(
    f"Records loaded: {len(records)}"
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
print("DATASET INFORMATION")
print("=" * 70)

print()

df.info()


print()
print("Columns:")

for column in df.columns:

    print(
        f" - {column}"
    )


# =========================================================
# TEXT LENGTH
# =========================================================

df["text_length"] = (
    df["text"]
    .astype(str)
    .str.len()
)


# =========================================================
# ENTITY COUNT
# =========================================================

df["entity_count"] = (
    df["entities"]
    .apply(len)
)


# =========================================================
# STATISTICAL SUMMARY
# =========================================================

print()
print("=" * 70)
print("STATISTICAL SUMMARY")
print("=" * 70)

print()

print(
    df[
        [
            "text_length",
            "entity_count"
        ]
    ].describe()
)


# =========================================================
# ENTITY DISTRIBUTION
# =========================================================

print()
print("=" * 70)
print("ENTITY DISTRIBUTION")
print("=" * 70)


entity_counter = Counter()


for entities in df["entities"]:

    for entity in entities:

        # -------------------------------------------------
        # Entity format:
        #
        # [start, end, label]
        #
        # or
        #
        # (start, end, label)
        # -------------------------------------------------

        if (
            isinstance(entity, list)
            or isinstance(entity, tuple)
        ):

            if len(entity) >= 3:

                label = str(
                    entity[2]
                )

                entity_counter[
                    label
                ] += 1


        # -------------------------------------------------
        # Also support dictionary format
        # -------------------------------------------------

        elif isinstance(
            entity,
            dict
        ):

            label = entity.get(
                "label"
            )

            if label:

                entity_counter[
                    label
                ] += 1


entity_df = pd.DataFrame(
    {
        "Entity": list(
            entity_counter.keys()
        ),
        "Count": list(
            entity_counter.values()
        )
    }
)


entity_df = entity_df.sort_values(
    "Count",
    ascending=False
)


print()

print(
    entity_df.to_string(
        index=False
    )
)


# =========================================================
# 1. ENTITY DISTRIBUTION
# =========================================================

plt.figure(
    figsize=(14, 7)
)

plt.bar(
    entity_df["Entity"],
    entity_df["Count"]
)

plt.title(
    "PII Entity Distribution"
)

plt.xlabel(
    "PII Entity Type"
)

plt.ylabel(
    "Number of Entities"
)

plt.xticks(
    rotation=75
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "entity_distribution.png",
    dpi=200
)

plt.close()


# =========================================================
# 2. CLASS IMBALANCE
# =========================================================

plt.figure(
    figsize=(14, 7)
)

plt.bar(
    entity_df["Entity"],
    entity_df["Count"]
)

plt.title(
    "PII Class Distribution"
)

plt.xlabel(
    "PII Class"
)

plt.ylabel(
    "Number of Occurrences"
)

plt.xticks(
    rotation=75
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "class_imbalance.png",
    dpi=200
)

plt.close()


# =========================================================
# 3. TEXT LENGTH HISTOGRAM
# =========================================================

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    df["text_length"],
    bins=30
)

plt.title(
    "Text Length Distribution"
)

plt.xlabel(
    "Text Length"
)

plt.ylabel(
    "Number of Records"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "text_length_distribution.png",
    dpi=200
)

plt.close()


# =========================================================
# 4. TEXT LENGTH BOX PLOT
# =========================================================

plt.figure(
    figsize=(10, 6)
)

sns.boxplot(
    x=df["text_length"]
)

plt.title(
    "Text Length Box Plot"
)

plt.xlabel(
    "Text Length"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "text_length_boxplot.png",
    dpi=200
)

plt.close()


# =========================================================
# 5. PII ENTITIES PER RECORD
# =========================================================

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    df["entity_count"],
    bins=20
)

plt.title(
    "PII Entities per Record"
)

plt.xlabel(
    "Number of PII Entities"
)

plt.ylabel(
    "Number of Records"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "entities_per_record.png",
    dpi=200
)

plt.close()


# =========================================================
# 6. SCATTER PLOT
# =========================================================

plt.figure(
    figsize=(10, 6)
)

plt.scatter(
    df["text_length"],
    df["entity_count"],
    alpha=0.4
)

plt.title(
    "Text Length vs PII Entity Count"
)

plt.xlabel(
    "Text Length"
)

plt.ylabel(
    "Number of PII Entities"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "text_length_vs_entities.png",
    dpi=200
)

plt.close()


# =========================================================
# 7. CORRELATION HEATMAP
# =========================================================

correlation = df[
    [
        "text_length",
        "entity_count"
    ]
].corr()


plt.figure(
    figsize=(7, 5)
)

sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f"
)

plt.title(
    "Correlation Heatmap"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR
    / "correlation_heatmap.png",
    dpi=200
)

plt.close()


# =========================================================
# FINAL SUMMARY
# =========================================================

print()
print("=" * 70)
print("EDA COMPLETED")
print("=" * 70)

print()

print(
    f"Total records analyzed: "
    f"{len(df)}"
)

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

print(
    f"Average PII entities per record: "
    f"{df['entity_count'].mean():.2f}"
)

print(
    f"Total PII entities: "
    f"{sum(entity_counter.values())}"
)

print()

print("Generated EDA files:")

for file in sorted(
    OUTPUT_DIR.glob("*.png")
):

    print(
        f" - {file.name}"
    )

print()

print("Output directory:")

print(
    OUTPUT_DIR
)

print()
print("=" * 70)