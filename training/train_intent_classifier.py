"""
Atlas AI — Intent Classifier Fine-Tuning
Fine-tunes DistilBERT on the synthetic immigration dataset.
Target accuracy: ≥ 95% on held-out test set.

Run: python training/train_intent_classifier.py
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch
import numpy as np
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, classification_report

from config import (
    INTENT_MODEL_PATH, INTENT_LABELS, INTENT_LABEL2ID, INTENT_ID2LABEL,
    SYNTHETIC_DIR
)

MODEL_CHECKPOINT = "distilbert-base-uncased"


def load_split(split_name: str) -> list[dict]:
    path = SYNTHETIC_DIR / f"{split_name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Run: python training/generate_dataset.py"
        )
    with open(path) as f:
        return json.load(f)


def build_hf_dataset(data: list[dict], tokenizer) -> Dataset:
    """Convert list of {text, label} dicts to HuggingFace Dataset."""
    # Handle both formats
    texts = []
    labels = []
    for item in data:
        text = item.get("text") or item.get("user_input", "")
        label_str = item.get("label") or item.get("intent", "general_query")
        label_id = INTENT_LABEL2ID.get(label_str, 3)
        texts.append(text)
        labels.append(label_id)

    encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)
    dataset = Dataset.from_dict({**encodings, "labels": labels})
    return dataset


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average="macro")
    return {"accuracy": acc, "f1": f1}


def train():
    print("=" * 60)
    print("Atlas AI — Intent Classifier Training")
    print("=" * 60)

    # Check for GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Load tokenizer
    print(f"Loading tokenizer: {MODEL_CHECKPOINT}")
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_CHECKPOINT)

    # Load datasets
    print("Loading datasets...")
    train_raw = load_split("train")
    val_raw = load_split("validation")
    test_raw = load_split("test")

    train_dataset = build_hf_dataset(train_raw, tokenizer)
    val_dataset = build_hf_dataset(val_raw, tokenizer)
    test_dataset = build_hf_dataset(test_raw, tokenizer)

    print(f"  Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")

    # Load model
    print(f"Loading model: {MODEL_CHECKPOINT}")
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_CHECKPOINT,
        num_labels=len(INTENT_LABELS),
        id2label=INTENT_ID2LABEL,
        label2id=INTENT_LABEL2ID,
    )

    # Training arguments
    INTENT_MODEL_PATH.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(INTENT_MODEL_PATH),
        num_train_epochs=8,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=64,
        warmup_steps=100,
        weight_decay=0.01,
        learning_rate=3e-5,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        logging_dir=str(INTENT_MODEL_PATH / "logs"),
        logging_steps=50,
        save_total_limit=2,
        fp16=device == "cuda",
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print("\nStarting training...")
    trainer.train()

    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_results = trainer.evaluate(test_dataset)
    print(f"Test Accuracy: {test_results['eval_accuracy']:.4f}")
    print(f"Test F1 (macro): {test_results['eval_f1']:.4f}")

    # Detailed classification report
    predictions_output = trainer.predict(test_dataset)
    y_pred = np.argmax(predictions_output.predictions, axis=1)
    y_true = predictions_output.label_ids

    print("\nClassification Report:")
    print(classification_report(
        y_true, y_pred,
        target_names=INTENT_LABELS,
    ))

    # Save model and tokenizer
    print(f"\nSaving model to {INTENT_MODEL_PATH}")
    trainer.save_model(str(INTENT_MODEL_PATH))
    tokenizer.save_pretrained(str(INTENT_MODEL_PATH))

    # Save metrics
    metrics_path = INTENT_MODEL_PATH / "eval_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "test_accuracy": test_results["eval_accuracy"],
            "test_f1": test_results["eval_f1"],
            "classification_report": classification_report(
                y_true, y_pred, target_names=INTENT_LABELS, output_dict=True
            ),
        }, f, indent=2)

    target_met = test_results["eval_accuracy"] >= 0.95
    print(f"\n{'✅' if target_met else '⚠️'} Target accuracy ≥ 95%: "
          f"{'MET' if target_met else 'NOT MET'} "
          f"(achieved {test_results['eval_accuracy']:.2%})")

    return test_results


if __name__ == "__main__":
    train()
