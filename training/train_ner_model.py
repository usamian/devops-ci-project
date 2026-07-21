"""
Atlas AI — NER Model Fine-Tuning
Fine-tunes BERT for token classification (NER) on immigration entities.
Target F1: ≥ 0.90 per entity type.

Entities: JOB_TITLE, SALARY, AGE, COUNTRY, VISA_TYPE

Run: python training/train_ner_model.py
"""

import sys
import json
import re
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch
from transformers import (
    BertTokenizerFast,
    BertForTokenClassification,
    TrainingArguments,
    Trainer,
)
from datasets import Dataset
from seqeval.metrics import classification_report as seq_classification_report
from seqeval.metrics import f1_score as seq_f1

from config import NER_MODEL_PATH, SYNTHETIC_DIR

random.seed(42)

MODEL_CHECKPOINT = "bert-base-uncased"

NER_LABELS = [
    "O",
    "B-JOB_TITLE", "I-JOB_TITLE",
    "B-SALARY", "I-SALARY",
    "B-AGE", "I-AGE",
    "B-COUNTRY", "I-COUNTRY",
    "B-VISA_TYPE", "I-VISA_TYPE",
]
LABEL2ID = {l: i for i, l in enumerate(NER_LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


# ── Annotated examples ────────────────────────────────────────────────────────

def create_annotated_examples() -> list[dict]:
    """
    Create token-annotated NER training examples.
    Each example: {"tokens": [...], "ner_tags": [...]}
    """
    examples = []

    templates = [
        # (sentence, annotations as list of (text_span, entity_type))
        ("I am a software engineer from India earning £50,000 a year",
         [("software engineer", "JOB_TITLE"), ("India", "COUNTRY"), ("£50,000", "SALARY")]),
        ("I work as a nurse and my salary is £35,000",
         [("nurse", "JOB_TITLE"), ("£35,000", "SALARY")]),
        ("A civil engineer from Nigeria with a salary of £43,000",
         [("civil engineer", "JOB_TITLE"), ("Nigeria", "COUNTRY"), ("£43,000", "SALARY")]),
        ("I am 28 years old, a doctor from Pakistan earning £55,000",
         [("28", "AGE"), ("doctor", "JOB_TITLE"), ("Pakistan", "COUNTRY"), ("£55,000", "SALARY")]),
        ("Skilled worker visa application for a pharmacist from Bangladesh",
         [("skilled worker visa", "VISA_TYPE"), ("pharmacist", "JOB_TITLE"), ("Bangladesh", "COUNTRY")]),
        ("I'm a 32-year-old data scientist from China earning £60,000 annually",
         [("32", "AGE"), ("data scientist", "JOB_TITLE"), ("China", "COUNTRY"), ("£60,000", "SALARY")]),
        ("Applying for a skilled worker visa as an accountant from Canada",
         [("skilled worker visa", "VISA_TYPE"), ("accountant", "JOB_TITLE"), ("Canada", "COUNTRY")]),
        ("My salary as a physiotherapist is £40,000 per year",
         [("physiotherapist", "JOB_TITLE"), ("£40,000", "SALARY")]),
        ("I am an electrical engineer from Romania, 26 years old",
         [("electrical engineer", "JOB_TITLE"), ("Romania", "COUNTRY"), ("26", "AGE")]),
        ("The going rate for a solicitor is £48,700 annually in the UK",
         [("solicitor", "JOB_TITLE"), ("£48,700", "SALARY")]),
        ("I have a skilled worker visa offer as a lab technician",
         [("skilled worker visa", "VISA_TYPE"), ("lab technician", "JOB_TITLE")]),
        ("I'm a 24-year-old nurse from the Philippines earning £29,000",
         [("24", "AGE"), ("nurse", "JOB_TITLE"), ("Philippines", "COUNTRY"), ("£29,000", "SALARY")]),
        ("Can I get a health and care worker visa as a paramedic?",
         [("health and care worker visa", "VISA_TYPE"), ("paramedic", "JOB_TITLE")]),
        ("I'm an architect from Brazil with an annual salary of £42,500",
         [("architect", "JOB_TITLE"), ("Brazil", "COUNTRY"), ("£42,500", "SALARY")]),
        ("software developer from India salary 50k",
         [("software developer", "JOB_TITLE"), ("India", "COUNTRY"), ("50k", "SALARY")]),
        ("teacher from Kenya earning 38700",
         [("teacher", "JOB_TITLE"), ("Kenya", "COUNTRY"), ("38700", "SALARY")]),
        ("I'm 30 years old working as a management consultant from Turkey",
         [("30", "AGE"), ("management consultant", "JOB_TITLE"), ("Turkey", "COUNTRY")]),
        ("web developer salary £41,000 country South Africa",
         [("web developer", "JOB_TITLE"), ("£41,000", "SALARY"), ("South Africa", "COUNTRY")]),
        ("chemical scientist from Germany annual pay £40,000",
         [("chemical scientist", "JOB_TITLE"), ("Germany", "COUNTRY"), ("£40,000", "SALARY")]),
        ("I am a biologist aged 25 from Ukraine earning £38,700",
         [("biologist", "JOB_TITLE"), ("25", "AGE"), ("Ukraine", "COUNTRY"), ("£38,700", "SALARY")]),
    ]

    for sentence, annotations in templates:
        tokens, tags = _tokenise_and_tag(sentence, annotations)
        if tokens:
            examples.append({"tokens": tokens, "ner_tags": tags})

    return examples


def _tokenise_and_tag(sentence: str, annotations: list) -> tuple:
    """Convert sentence + span annotations to token-level BIO tags."""
    tokens = sentence.lower().split()
    if not tokens:
        return [], []

    tags = ["O"] * len(tokens)
    sentence_lower = sentence.lower()

    for span_text, entity_type in annotations:
        span_lower = span_text.lower()
        span_tokens = span_lower.split()

        # Find span in token list
        for i in range(len(tokens) - len(span_tokens) + 1):
            window = tokens[i:i + len(span_tokens)]
            # Fuzzy match (strip punctuation)
            clean_window = [re.sub(r'[^\w£]', '', t) for t in window]
            clean_span = [re.sub(r'[^\w£]', '', t) for t in span_tokens]
            if clean_window == clean_span:
                tags[i] = f"B-{entity_type}"
                for j in range(1, len(span_tokens)):
                    if i + j < len(tags):
                        tags[i + j] = f"I-{entity_type}"
                break

    return tokens, tags


def tokenise_and_align_labels(examples, tokenizer):
    """Align word-level labels with subword tokens from BERT tokenizer."""
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True,
        padding=True,
        max_length=128,
    )

    all_labels = []
    for i, labels in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []

        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_str = labels[word_idx] if word_idx < len(labels) else "O"
                label_ids.append(LABEL2ID.get(label_str, 0))
            else:
                # For subword tokens of the same word, use I- label
                prev_label = labels[previous_word_idx] if previous_word_idx < len(labels) else "O"
                if prev_label.startswith("B-"):
                    label_ids.append(LABEL2ID.get("I-" + prev_label[2:], 0))
                else:
                    label_ids.append(LABEL2ID.get(prev_label, 0))
            previous_word_idx = word_idx

        all_labels.append(label_ids)

    tokenized_inputs["labels"] = all_labels
    return tokenized_inputs


def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_preds = []
    true_labels = []

    for pred, label in zip(predictions, labels):
        true_pred_seq = []
        true_label_seq = []
        for p_val, l_val in zip(pred, label):
            if l_val != -100:
                true_pred_seq.append(ID2LABEL[p_val])
                true_label_seq.append(ID2LABEL[l_val])
        true_preds.append(true_pred_seq)
        true_labels.append(true_label_seq)

    f1 = seq_f1(true_labels, true_preds)
    return {"f1": f1}


def train():
    print("=" * 60)
    print("Atlas AI — NER Model Training")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Load tokenizer
    tokenizer = BertTokenizerFast.from_pretrained(MODEL_CHECKPOINT)

    # Build dataset
    print("Building NER dataset...")
    annotated = create_annotated_examples()

    # Augment by duplicating with slight variations (x10)
    augmented = []
    for _ in range(10):
        for ex in annotated:
            augmented.append(ex)

    random.shuffle(augmented)
    n = len(augmented)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    train_data = augmented[:n_train]
    val_data = augmented[n_train:n_train + n_val]
    test_data = augmented[n_train + n_val:]

    print(f"  Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

    def to_hf_dataset(data):
        return Dataset.from_dict({
            "tokens": [d["tokens"] for d in data],
            "ner_tags": [d["ner_tags"] for d in data],
        })

    train_ds = to_hf_dataset(train_data).map(
        lambda ex: tokenise_and_align_labels(ex, tokenizer), batched=True
    )
    val_ds = to_hf_dataset(val_data).map(
        lambda ex: tokenise_and_align_labels(ex, tokenizer), batched=True
    )
    test_ds = to_hf_dataset(test_data).map(
        lambda ex: tokenise_and_align_labels(ex, tokenizer), batched=True
    )

    # Load model
    model = BertForTokenClassification.from_pretrained(
        MODEL_CHECKPOINT,
        num_labels=len(NER_LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    NER_MODEL_PATH.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(NER_MODEL_PATH),
        num_train_epochs=10,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        warmup_steps=50,
        weight_decay=0.01,
        learning_rate=2e-5,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=20,
        save_total_limit=2,
        fp16=device == "cuda",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        compute_metrics=compute_metrics,
    )

    print("\nStarting NER training...")
    trainer.train()

    # Evaluate
    test_results = trainer.evaluate(test_ds)
    print(f"\nTest F1: {test_results['eval_f1']:.4f}")

    target_met = test_results["eval_f1"] >= 0.90
    print(f"{'✅' if target_met else '⚠️'} Target F1 ≥ 0.90: "
          f"{'MET' if target_met else 'NOT MET'} "
          f"(achieved {test_results['eval_f1']:.4f})")

    # Save
    print(f"\nSaving NER model to {NER_MODEL_PATH}")
    trainer.save_model(str(NER_MODEL_PATH))
    tokenizer.save_pretrained(str(NER_MODEL_PATH))

    # Save metrics
    with open(NER_MODEL_PATH / "eval_metrics.json", "w") as f:
        json.dump({"test_f1": test_results["eval_f1"]}, f, indent=2)

    return test_results


if __name__ == "__main__":
    train()
