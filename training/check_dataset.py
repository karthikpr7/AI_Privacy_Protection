from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

train_file = BASE_DIR / "dataset" / "raw" / "data" / "train" / "train.jsonl"
validation_file = BASE_DIR / "dataset" / "raw" / "data" / "validation" / "test.jsonl"

print("Project directory:")
print(BASE_DIR)

print("\nTraining file:")
print(train_file)
print("Exists:", train_file.exists())

print("\nValidation file:")
print(validation_file)
print("Exists:", validation_file.exists())

if train_file.exists():
    print(
        "Training file size:",
        round(train_file.stat().st_size / (1024 * 1024), 2),
        "MB"
    )

if validation_file.exists():
    print(
        "Validation file size:",
        round(validation_file.stat().st_size / (1024 * 1024), 2),
        "MB"
    )