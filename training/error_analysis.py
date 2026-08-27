import json
from pathlib import Path
from collections import Counter

import spacy


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "privacy_ner_dev"
    / "best"
)

VALIDATION_FILE = (
    BASE_DIR
    / "dataset"
    / "processed"
    / "dev_validation.jsonl"
)

OUTPUT_FILE = (
    BASE_DIR
    / "outputs"
    / "error_analysis.txt"
)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


print("=" * 70)
print("LOADING MODEL")
print("=" * 70)

nlp = spacy.load(MODEL_PATH)


# ---------------------------------------------------------
# Counters
# ---------------------------------------------------------

missed_entities = Counter()
wrong_predictions = Counter()

missed_examples = []
wrong_prediction_examples = []


# ---------------------------------------------------------
# Evaluate
# ---------------------------------------------------------

print()
print("=" * 70)
print("ANALYZING VALIDATION ERRORS")
print("=" * 70)


with VALIDATION_FILE.open(
    "r",
    encoding="utf-8"
) as file:

    for index, line in enumerate(file, start=1):

        line = line.strip()

        if not line:
            continue

        record = json.loads(line)

        text = record["text"]

        gold_entities = {
            (
                entity["start"],
                entity["end"],
                entity["label"]
            )
            for entity in record["entities"]
        }

        doc = nlp(text)

        predicted_entities = {
            (
                entity.start_char,
                entity.end_char,
                entity.label_
            )
            for entity in doc.ents
        }

        # -------------------------------------------------
        # Missed entities
        # -------------------------------------------------

        for gold in gold_entities:

            if gold not in predicted_entities:

                start, end, label = gold

                missed_entities[label] += 1

                if len(missed_examples) < 50:

                    missed_examples.append(
                        {
                            "text": text,
                            "gold": text[start:end],
                            "label": label,
                            "start": start,
                            "end": end
                        }
                    )

        # -------------------------------------------------
        # Wrong / extra predictions
        # -------------------------------------------------

        for predicted in predicted_entities:

            if predicted not in gold_entities:

                start, end, label = predicted

                wrong_predictions[label] += 1

                if len(wrong_prediction_examples) < 50:

                    wrong_prediction_examples.append(
                        {
                            "text": text,
                            "prediction": text[start:end],
                            "label": label,
                            "start": start,
                            "end": end
                        }
                    )


# ---------------------------------------------------------
# Print summary
# ---------------------------------------------------------

print()
print("=" * 70)
print("MISSED ENTITIES")
print("=" * 70)

for label, count in missed_entities.most_common():

    print(
        f"{label:<22}{count}"
    )


print()
print("=" * 70)
print("EXTRA / WRONG PREDICTIONS")
print("=" * 70)

for label, count in wrong_predictions.most_common():

    print(
        f"{label:<22}{count}"
    )


# ---------------------------------------------------------
# Save detailed report
# ---------------------------------------------------------

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as report:

    report.write("=" * 70 + "\n")
    report.write("MODEL ERROR ANALYSIS\n")
    report.write("=" * 70 + "\n\n")

    report.write("MISSED ENTITIES\n")
    report.write("-" * 70 + "\n")

    for label, count in missed_entities.most_common():

        report.write(
            f"{label}: {count}\n"
        )

    report.write("\n")
    report.write("EXTRA / WRONG PREDICTIONS\n")
    report.write("-" * 70 + "\n")

    for label, count in wrong_predictions.most_common():

        report.write(
            f"{label}: {count}\n"
        )

    report.write("\n")
    report.write("SAMPLE MISSED ENTITIES\n")
    report.write("-" * 70 + "\n")

    for example in missed_examples:

        report.write(
            f"\nText: {example['text']}\n"
        )

        report.write(
            f"Gold: {example['gold']}\n"
        )

        report.write(
            f"Label: {example['label']}\n"
        )

    report.write("\n")
    report.write("SAMPLE EXTRA / WRONG PREDICTIONS\n")
    report.write("-" * 70 + "\n")

    for example in wrong_prediction_examples:

        report.write(
            f"\nText: {example['text']}\n"
        )

        report.write(
            f"Prediction: {example['prediction']}\n"
        )

        report.write(
            f"Label: {example['label']}\n"
        )


print()
print("=" * 70)
print("ERROR ANALYSIS COMPLETED")
print("=" * 70)

print()
print("Report saved to:")
print(OUTPUT_FILE)