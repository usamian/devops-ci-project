"""
Atlas AI — Intent Classifier
Fine-tuned DistilBERT for classifying user queries into one of four intents:
  - eligibility_check
  - document_requirement
  - processing_time
  - general_query

Falls back to rule-based keyword matching when model is not loaded.
"""

import re
from pathlib import Path
from typing import Optional

from config import (
    INTENT_MODEL_PATH, INTENT_LABELS, INTENT_LABEL2ID, INTENT_ID2LABEL,
    INTENT_CONFIDENCE_THRESHOLD
)
from src.nlp.preprocessor import preprocess_for_model, truncate_for_model

# ── Lazy-loaded model ─────────────────────────────────────────────────────────
_tokenizer = None
_model = None
_pipeline = None


def _load_model():
    global _tokenizer, _model, _pipeline
    if _pipeline is not None:
        return _pipeline

    if not INTENT_MODEL_PATH.exists():
        return None  # Will use fallback

    try:
        from transformers import pipeline as hf_pipeline
        _pipeline = hf_pipeline(
            "text-classification",
            model=str(INTENT_MODEL_PATH),
            tokenizer=str(INTENT_MODEL_PATH),
            return_all_scores=True,
            device=-1,  # CPU
        )
        return _pipeline
    except Exception as e:
        print(f"[IntentClassifier] Could not load model: {e}. Using keyword fallback.")
        return None


# ── Keyword-based fallback ────────────────────────────────────────────────────
_ELIGIBILITY_KEYWORDS = {
    "eligible", "eligibility", "qualify", "qualified", "qualifies", "can i apply",
    "can i get", "do i qualify", "am i eligible", "requirements", "criteria",
    "can i apply", "can i get a", "points", "salary threshold", "going rate",
    "sponsorship", "certificate of sponsorship", "cos",
    "english language", "english requirement", "shortage occupation",
}

_DOCUMENT_KEYWORDS = {
    "document", "documents", "paperwork", "what do i need", "what documents",
    "certificate", "proof", "evidence", "ielts", "english test", "passport",
    "biometric", "tb test", "tuberculosis", "criminal record", "police clearance",
    "bank statement", "payslip", "employment contract", "reference letter",
    "application form", "supporting documents", "required documents",
}

_PROCESSING_KEYWORDS = {
    "how long", "processing time", "what is the processing", "waiting time", "when will",
    "timeline", "duration", "how soon", "time to process", "approval time",
    "delay", "urgent", "priority service", "super priority", "standard service",
    "how many weeks", "how many months",
}


_GENERAL_KEYWORDS = {
    "what is", "tell me about", "explain", "overview", "information about",
    "tier 2", "uk immigration", "uk visa", "how does",
    "can my family", "dependants", "settlement", "ilr", "citizenship",
    "health surcharge", "immigration health", "shortage", "rqf level",
    "going rate for",
}


def _keyword_classify(text: str) -> tuple[str, float]:
    """Rule-based fallback classifier using keyword matching."""
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))

    # Multi-word phrase matching
    def phrase_score(keyword_set: set) -> float:
        score = 0
        for kw in keyword_set:
            if kw in text_lower:
                score += 1
        return score

    scores = {
        "eligibility_check": phrase_score(_ELIGIBILITY_KEYWORDS),
        "document_requirement": phrase_score(_DOCUMENT_KEYWORDS),
        "processing_time": phrase_score(_PROCESSING_KEYWORDS),
        "general_query": phrase_score(_GENERAL_KEYWORDS) + 0.3,  # slight default boost
    }

    best_intent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent]

    # Normalise to confidence 0-1 (capped)
    confidence = min(0.85, 0.5 + best_score * 0.1) if best_score > 0.5 else 0.55
    return best_intent, confidence


# ── Public API ────────────────────────────────────────────────────────────────

def classify_intent(text: str) -> dict:
    """
    Classify a user query into one of the intent classes.

    Returns:
        {
            "intent": str,
            "confidence": float,
            "all_scores": dict[str, float],
            "low_confidence": bool,
            "source": "model" | "fallback"
        }
    """
    cleaned = truncate_for_model(preprocess_for_model(text))
    pipe = _load_model()

    if pipe is not None:
        try:
            raw_results = pipe(cleaned)[0]  # List of {label, score}
            scores = {r["label"]: r["score"] for r in raw_results}

            # Map back to human labels if model uses integer labels
            mapped = {}
            for label, score in scores.items():
                if label.startswith("LABEL_"):
                    idx = int(label.split("_")[1])
                    mapped[INTENT_ID2LABEL.get(idx, label)] = score
                else:
                    mapped[label] = score

            best_intent = max(mapped, key=lambda k: mapped[k])
            confidence = mapped[best_intent]

            return {
                "intent": best_intent,
                "confidence": round(confidence, 4),
                "all_scores": {k: round(v, 4) for k, v in mapped.items()},
                "low_confidence": confidence < INTENT_CONFIDENCE_THRESHOLD,
                "source": "model",
            }
        except Exception as e:
            print(f"[IntentClassifier] Inference error: {e}. Using fallback.")

    # Keyword fallback
    intent, confidence = _keyword_classify(cleaned)
    return {
        "intent": intent,
        "confidence": round(confidence, 4),
        "all_scores": {k: 0.0 for k in INTENT_LABELS},
        "low_confidence": confidence < INTENT_CONFIDENCE_THRESHOLD,
        "source": "fallback",
    }
