import spacy
from spacy.scorer import Scorer
from spacy.training import Example

def evaluate(model_path: str, eval_data_path: str):
    print(f"[*] Loading model from {model_path}...")
    nlp = spacy.load(model_path)
    
    doc_bin = spacy.tokens.DocBin().from_disk(eval_data_path)
    docs = list(doc_bin.get_docs(nlp.vocab))
    
    examples = []
    for doc in docs:
        pred = nlp(doc.text)
        example = Example(pred, doc)
        examples.append(example)

    scorer = Scorer()
    scores = scorer.score(examples)

    print("\n" + "=" * 45)
    print("        MODEL EVALUATION RESULTS")
    print("=" * 45)
    print(f"Overall P:  {scores['ents_p'] * 100:.2f}%")
    print(f"Overall R:  {scores['ents_r'] * 100:.2f}%")
    print(f"Overall F1: {scores['ents_f'] * 100:.2f}%")
    print("-" * 45)
    print("Per-Entity Breakdown:")
    for label, metrics in scores.get('ents_per_type', {}).items():
        print(f"  {label:<10} -> P: {metrics['p']*100:.1f}% | R: {metrics['r']*100:.1f}% | F1: {metrics['f']*100:.1f}%")
    print("=" * 45 + "\n")

if __name__ == "__main__":
    evaluate("models/model-best", "data/dev.spacy")