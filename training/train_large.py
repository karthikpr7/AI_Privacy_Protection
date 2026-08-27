import json
import random
from pathlib import Path

import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from spacy.scorer import Scorer


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "large_train.jsonl"
)

VALIDATION_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "dev_validation.jsonl"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "privacy_ner_100k"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# =========================================================
# CONFIGURATION
# =========================================================

N_ITER = 8

RANDOM_SEED = 42

DROPOUT = 0.2

BATCH_START = 8.0
BATCH_END = 64.0
BATCH_COMPOUND = 1.001


# =========================================================
# LOAD DATA
# =========================================================

def load_training_data(file_path):

    data = []

    with file_path.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1
        ):

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            # -------------------------------------------------
            # Support both possible text field names
            # -------------------------------------------------

            text = record.get(
                "text",
                record.get(
                    "source_text",
                    ""
                )
            )

            if not isinstance(
                text,
                str
            ):

                continue

            entities = []

            # -------------------------------------------------
            # Read entities
            # -------------------------------------------------

            for entity in record.get(
                "entities",
                []
            ):

                try:

                    # -----------------------------------------
                    # Format 1:
                    # [start, end, label]
                    # -----------------------------------------

                    if isinstance(
                        entity,
                        (list, tuple)
                    ):

                        start = int(
                            entity[0]
                        )

                        end = int(
                            entity[1]
                        )

                        label = str(
                            entity[2]
                        )

                    # -----------------------------------------
                    # Format 2:
                    # {"start": ..., "end": ..., "label": ...}
                    # -----------------------------------------

                    elif isinstance(
                        entity,
                        dict
                    ):

                        start = int(
                            entity["start"]
                        )

                        end = int(
                            entity["end"]
                        )

                        label = str(
                            entity["label"]
                        )

                    else:

                        continue

                    # -----------------------------------------
                    # Validate entity
                    # -----------------------------------------

                    if start < 0:
                        continue

                    if end <= start:
                        continue

                    if end > len(text):
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
                    IndexError,
                    TypeError,
                    ValueError
                ):

                    print(
                        f"Warning: invalid entity "
                        f"in {file_path.name} "
                        f"at line {line_number}"
                    )

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
# START
# =========================================================

print("=" * 70)
print("100K PII NER MODEL TRAINING")
print("=" * 70)


print()
print("Loading training data...")

train_data = load_training_data(
    TRAIN_FILE
)

print(
    f"Training examples: {len(train_data)}"
)


print()
print("Loading validation data...")

validation_data = load_training_data(
    VALIDATION_FILE
)

print(
    f"Validation examples: {len(validation_data)}"
)


# =========================================================
# CREATE SPACY MODEL
# =========================================================

print()
print("=" * 70)
print("CREATING NER PIPELINE")
print("=" * 70)


nlp = spacy.blank(
    "en"
)

ner = nlp.add_pipe(
    "ner"
)


# =========================================================
# COLLECT LABELS
# =========================================================

labels = set()

for text, annotation in train_data:

    for start, end, label in annotation[
        "entities"
    ]:

        labels.add(
            label
        )


print()
print("Entity labels:")

for label in sorted(labels):

    print(
        f"  {label}"
    )

    ner.add_label(
        label
    )


print()
print(
    f"Total labels: {len(labels)}"
)


# =========================================================
# INITIALIZE MODEL
# =========================================================

print()
print("=" * 70)
print("INITIALIZING MODEL")
print("=" * 70)


random.seed(
    RANDOM_SEED
)


initial_examples = []

for text, annotation in train_data[:1000]:

    doc = nlp.make_doc(
        text
    )

    example = Example.from_dict(
        doc,
        annotation
    )

    initial_examples.append(
        example
    )


optimizer = nlp.initialize(
    get_examples=lambda: initial_examples
)


# =========================================================
# VALIDATION FUNCTION
# =========================================================

def evaluate_model(nlp, data):

    examples = []

    for text, annotation in data:

        doc = nlp.make_doc(
            text
        )

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

    scorer = Scorer()

    scores = scorer.score(
        examples
    )

    return (
        scores.get("ents_p", 0.0),
        scores.get("ents_r", 0.0),
        scores.get("ents_f", 0.0)
    )


# =========================================================
# TRAINING
# =========================================================

print()
print("=" * 70)
print("STARTING 100K TRAINING")
print("=" * 70)

best_f1 = -1.0


for iteration in range(
    N_ITER
):

    random.shuffle(
        train_data
    )

    losses = {}

    batches = minibatch(
        train_data,
        size=compounding(
            BATCH_START,
            BATCH_END,
            BATCH_COMPOUND
        )
    )

    for batch in batches:

        examples = []

        for text, annotation in batch:

            doc = nlp.make_doc(
                text
            )

            example = Example.from_dict(
                doc,
                annotation
            )

            examples.append(
                example
            )

        nlp.update(
            examples,
            drop=DROPOUT,
            losses=losses
        )

    loss = losses.get(
        "ner",
        0.0
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    precision, recall, f1 = evaluate_model(
        nlp,
        validation_data
    )

    print()
    print(
        f"Iteration {iteration + 1}/{N_ITER}"
    )

    print(
        f"Loss      : {loss:.4f}"
    )

    print(
        f"Precision : {precision:.4f}"
    )

    print(
        f"Recall    : {recall:.4f}"
    )

    print(
        f"F1-score  : {f1:.4f}"
    )


    # -----------------------------------------------------
    # Save best model
    # -----------------------------------------------------

    if f1 > best_f1:

        best_f1 = f1

        best_model_dir = (
            MODEL_DIR
            / "best"
        )

        best_model_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        nlp.to_disk(
            best_model_dir
        )

        print(
            "Best model saved."
        )


# =========================================================
# SAVE FINAL MODEL
# =========================================================

final_model_dir = (
    MODEL_DIR
    / "final"
)

final_model_dir.mkdir(
    parents=True,
    exist_ok=True
)

nlp.to_disk(
    final_model_dir
)


# =========================================================
# COMPLETE
# =========================================================

print()
print("=" * 70)
print("100K TRAINING COMPLETED")
print("=" * 70)

print()
print(
    f"Best validation F1-score: {best_f1:.4f}"
)

print()
print("Best model:")
print(
    MODEL_DIR / "best"
)

print()
print("Final model:")
print(
    final_model_dir
)

print()
print("=" * 70)