import spacy

# Load the newly trained pipeline
nlp = spacy.load("models/model-best")

test_phrases = [
    "Kindly update my records with PAN: BZRPK9012M as requested.",
    "Please send the funds directly to Account 987654321098 today.",
    "Billed against card 4532890123456789 for the annual license.",
    "Order #88921004 processed on Page 12 with tracking number 9912039.",
    "The total invoice charge is 4500 for item code 11029.",
]

print("=" * 60)
for text in test_phrases:
    doc = nlp(text)
    print(f"\nText: {text}")
    if doc.ents:
        for ent in doc.ents:
            print(f"  --> Found [{ent.label_}]: {ent.text} (chars {ent.start_char}-{ent.end_char})")
    else:
        print("  --> [No sensitive entities detected]")
print("=" * 60)