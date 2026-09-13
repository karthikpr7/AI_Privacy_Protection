import json
import random
import spacy
from spacy.tokens import DocBin

def convert(json_path: str, train_out: str, dev_out: str):
    nlp = spacy.blank("en")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    random.seed(42)
    random.shuffle(data)
    
    split_idx = int(len(data) * 0.8)
    train_data = data[:split_idx]
    dev_data = data[split_idx:]
    
    for dataset, out_path in [(train_data, train_out), (dev_data, dev_out)]:
        doc_bin = DocBin()
        skipped_count = 0
        
        for item in dataset:
            text = item["text"]
            entities = item["entities"]
            doc = nlp.make_doc(text)
            spans = []
            
            for start, end, label in entities:
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is None:
                    skipped_count += 1
                else:
                    spans.append(span)
                    
            doc.ents = spans
            doc_bin.add(doc)
            
        doc_bin.to_disk(out_path)
        print(f"Saved {len(dataset) - skipped_count} records to {out_path} (skipped {skipped_count} unaligned spans)")

if __name__ == "__main__":
    convert(
        json_path="data/synthetic_ner_data.json",
        train_out="data/train.spacy",
        dev_out="data/dev.spacy"
    )