import json
from pathlib import Path

import spacy
from spacy.training import Example
from spacy.scorer import Scorer


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "privacy_ner_100k"
    / "best"
)

VALIDATION_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "dev_validation.jsonl"
)


# =========================================================
# LOAD VALIDATION DATA
# =========================================================

def load_validation_data(file_path):

    data = []

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            text = record.get(
                "text",
                ""
            )

            if not text:
                continue

            entities = []

            for entity in record.get(
                "entities",
                []
            ):

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

                    if (
                        start >= 0
                        and end > start
                        and end <= len(text)
                    ):

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

            data.append(
                (
                    text,
                    {
                        "entities": entities
                    }
                )
            )

    return data


# =========================================================
# LOAD MODEL
# =========================================================

print("=" * 70)
print("100K NER MODEL EVALUATION")
print("=" * 70)

print()
print("Model:")
print(MODEL_PATH)

if not MODEL_PATH.exists():

    raise FileNotFoundError(
        f"Model not found:\n{MODEL_PATH}"
    )

nlp = spacy.load(
    MODEL_PATH
)

print()
print("Model loaded successfully.")


# =========================================================
# LOAD VALIDATION DATA
# =========================================================

print()
print("Loading validation dataset...")

validation_data = load_validation_data(
    VALIDATION_FILE
)

print(
    f"Validation examples: {len(validation_data)}"
)


# =========================================================
# CREATE EXAMPLES
# =========================================================

print()
print("Running predictions...")

examples = []

for index, (text, annotation) in enumerate(
    validation_data,
    start=1
):

    predicted_doc = nlp(
        text
    )

    example = Example.from_dict(
        predicted_doc,
        annotation
    )

    examples.append(
        example
    )

    if index % 5000 == 0:

        print(
            f"Processed: {index}"
        )


# =========================================================
# CALCULATE METRICS
# =========================================================

print()
print("Calculating metrics...")

scorer = Scorer()

scores = scorer.score(
    examples
)


precision = scores.get(
    "ents_p",
    0.0
)

recall = scores.get(
    "ents_r",
    0.0
)

f1 = scores.get(
    "ents_f",
    0.0
)


# =========================================================
# OVERALL RESULTS
# =========================================================

print()
print("=" * 70)
print("OVERALL MODEL PERFORMANCE")
print("=" * 70)

print()
print(
    f"Precision : {precision:.4f} "
    f"({precision * 100:.2f}%)"
)

print(
    f"Recall    : {recall:.4f} "
    f"({recall * 100:.2f}%)"
)

print(
    f"F1-score  : {f1:.4f} "
    f"({f1 * 100:.2f}%)"
)


# =========================================================
# PER ENTITY RESULTS
# =========================================================

print()
print("=" * 70)
print("PER-ENTITY PERFORMANCE")
print("=" * 70)

print()

print(
    f"{'ENTITY':<22}"
    f"{'PRECISION':>12}"
    f"{'RECALL':>12}"
    f"{'F1':>12}"
)

print("-" * 58)


# spaCy stores per-label results in ents_per_type
per_type = scores.get(
    "ents_per_type",
    {}
)

for label in sorted(
    per_type.keys()
):

    metrics = per_type[label]

    label_precision = metrics.get(
        "p",
        0.0
    )

    label_recall = metrics.get(
        "r",
        0.0
    )

    label_f1 = metrics.get(
        "f",
        0.0
    )

    print(
        f"{label:<22}"
        f"{label_precision * 100:>11.2f}%"
        f"{label_recall * 100:>11.2f}%"
        f"{label_f1 * 100:>11.2f}%"
    )


# =========================================================
# COMPLETE
# =========================================================

print()
print("=" * 70)
print("100K MODEL EVALUATION COMPLETED")
print("=" * 70)