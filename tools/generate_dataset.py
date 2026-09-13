import os
import json
import random
import string
from faker import Faker

fake = Faker('en_IN')  # Uses Indian locale for authentic names/addresses

def random_pan():
    letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    last = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{last}"

def random_bank_acc():
    return str(random.randint(10000000000, 999999999999))

def random_card():
    return fake.credit_card_number(card_type=None)

TEMPLATES = [
    # Sensitive templates with labels
    ("Please transfer the amount to Account Number: {bank_acc} immediately.", "BANK_ACC", "bank_acc"),
    ("My Permanent Account Number is {pan} for tax filing.", "PAN", "pan"),
    ("Charge the recurring subscription to card {card}.", "CARD", "card"),
    ("Beneficiary A/C: {bank_acc}, IFSC code: HDFC0001234.", "BANK_ACC", "bank_acc"),
    ("Verify PAN details: {pan} registered under business name.", "PAN", "pan"),
    
    # Distractor templates (no sensitive entity, benign business numbers)
    ("Invoice ID 982341 has been generated for order 44921.", None, None),
    ("Total quantity shipped: 1200 units at unit price 450.", None, None),
    ("Receipt reference 774892 processed on Page 12.", None, None),
    ("Tracking number 88921004 has left the logistics hub.", None, None),
]

def generate_samples(count=1000):
    dataset = []
    for _ in range(count):
        template, entity_type, key = random.choice(TEMPLATES)
        
        values = {
            "pan": random_pan(),
            "bank_acc": random_bank_acc(),
            "card": random_card()
        }

        if entity_type and key:
            entity_val = values[key]
            text = template.format(**values)
            start_idx = text.find(entity_val)
            end_idx = start_idx + len(entity_val)
            entities = [(start_idx, end_idx, entity_type)]
        else:
            text = template
            entities = []

        dataset.append({"text": text, "entities": entities})
        
    return dataset

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    samples = generate_samples(1500)
    output_path = "data/synthetic_ner_data.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
        
    print(f"Successfully generated {len(samples)} annotated samples at {output_path}")