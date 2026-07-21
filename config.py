"""
Atlas AI — Central Configuration Module (Legacy Compatibility Layer)
All runtime settings loaded from environment variables with safe defaults.

This module provides backward compatibility by importing from the new
src.core.config module while maintaining the legacy interface.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ── Import from new core config ──────────────────────────────────────────────
from src.core.config import AtlasConfig

# Use the new config class
config = AtlasConfig()

# ── Project Root ────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent

# ── OpenAI ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OFFLINE_MODE: bool = OPENAI_API_KEY == "" or OPENAI_API_KEY == "your_openai_api_key_here"

# ── Flask ────────────────────────────────────────────────────────────────────
FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "atlas-ai-dev-secret-2024")
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))

# ── Model Paths ──────────────────────────────────────────────────────────────
INTENT_MODEL_PATH: Path = BASE_DIR / os.getenv("INTENT_MODEL_PATH", "models/intent_classifier")
NER_MODEL_PATH: Path = BASE_DIR / os.getenv("NER_MODEL_PATH", "models/ner_model")
EMBEDDINGS_INDEX_PATH: Path = BASE_DIR / os.getenv("EMBEDDINGS_INDEX_PATH", "models/faiss_index")

# ── RAG ──────────────────────────────────────────────────────────────────────
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "512"))
RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))
EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── NLP Confidence Thresholds ────────────────────────────────────────────────
INTENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.80"))
NER_CONFIDENCE_THRESHOLD: float = float(os.getenv("NER_CONFIDENCE_THRESHOLD", "0.80"))

# ── Intent Classes ────────────────────────────────────────────────────────────
INTENT_LABELS = [
    "eligibility_check",
    "document_requirement",
    "processing_time",
    "general_query",
]
INTENT_LABEL2ID = {label: idx for idx, label in enumerate(INTENT_LABELS)}
INTENT_ID2LABEL = {idx: label for label, idx in INTENT_LABEL2ID.items()}

# ── NER Entity Types ──────────────────────────────────────────────────────────
NER_ENTITIES = [
    "JOB_TITLE",
    "SALARY",
    "AGE",
    "COUNTRY",
    "VISA_TYPE",
]

# ── Session ───────────────────────────────────────────────────────────────────
SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR: Path = BASE_DIR / "logs"
LOG_FILE: Path = LOG_DIR / "atlas_ai.log"

# ── Data Paths ────────────────────────────────────────────────────────────────
DATA_DIR: Path = BASE_DIR / "data"
RULES_DIR: Path = DATA_DIR / "rules"
SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"
GOV_UK_DOCS_DIR: Path = DATA_DIR / "gov_uk_docs"

# ── Disclaimer ────────────────────────────────────────────────────────────────
DISCLAIMER = (
    "⚠️ This tool provides informational guidance only, not legal advice. "
    "Immigration rules change frequently. Always consult a qualified immigration "
    "solicitor or check official GOV.UK sources before making any decisions. "
    "Visit: https://www.gov.uk/skilled-worker-visa"
)
