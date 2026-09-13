import os
import re
import random
import spacy
from spacy.tokens import DocBin
from tqdm import tqdm

PATTERNS = {
    "PAN": re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'),
    "BANK_ACC": re.compile(r'\b[0-9]{9,18}\b'),
}

def create_spacy_dataset(texts, out_path):
    nlp = spacy.blank("en")
    db = DocBin()
    total_ents = 0

    for text in tqdm(texts, desc=f"Building {os.path.basename(out_path)}"):
        text = text.strip()
        if not text:
            continue
        doc = nlp.make_doc(text)
        ents = []

        for label, regex in PATTERNS.items():
            for match in regex.finditer(text):
                start, end = match.span()
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is not None:
                    ents.append(span)
                    total_ents += 1

        # Drop overlapping entities
        doc.ents = spacy.util.filter_spans(ents)
        db.add(doc)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    db.to_disk(out_path)
    print(f"[+] Saved {len(texts)} docs ({total_ents} entities) -> {out_path}")

if __name__ == "__main__":
    extracted_texts = []

    # 1. Harvest texts from NEXORA
    nexora_dir = "data/raw_kaggle/nexora"
    if os.path.exists(nexora_dir):
        for root, _, files in os.walk(nexora_dir):
            for f in files:
                if f.endswith((".txt", ".json", ".csv")):
                    p = os.path.join(root, f)
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        extracted_texts.extend(fp.readlines())

    # Fallback to current synthetic generator if corpus is small
    if len(extracted_texts) < 100:
        print("[*] Augmenting with varied context templates...")
        prefixes = ["Tax ID: ", "Beneficiary PAN: ", "Account No: ", "Permanent A/C: ", "Cardholder ID: "]
        for _ in range(500):
            pan = f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}{random.randint(1000,9999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            acc = f"{random.randint(1000000000, 999999999999)}"
            pref = random.choice(prefixes)
            extracted_texts.append(f"{pref}{pan} linked with beneficiary bank account {acc}.")

    random.shuffle(extracted_texts)
    split = int(len(extracted_texts) * 0.8)
    
    create_spacy_dataset(extracted_texts[:split], "data/train.spacy")
    create_spacy_dataset(extracted_texts[split:], "data/dev.spacy")