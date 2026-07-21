"""
Atlas AI — Central Configuration Module
All runtime settings loaded from environment variables with safe defaults.
Aligned with proposal specifications.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


class AtlasConfig:
    """Central configuration class for Atlas AI system."""
    
    # ── Project Root ────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # ── Application Settings ────────────────────────────────────────────────────
    APP_NAME: str = "Atlas AI"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    
    # ── OpenAI Configuration ────────────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OFFLINE_MODE: bool = OPENAI_API_KEY == "" or OPENAI_API_KEY == "your_openai_api_key_here"
    
    # ── Flask Configuration ─────────────────────────────────────────────────────
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", str(uuid.uuid4()))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    
    # ── Model Paths ──────────────────────────────────────────────────────────────
    MODELS_DIR: Path = BASE_DIR / "models"
    INTENT_MODEL_PATH: Path = MODELS_DIR / "intent_classifier"
    NER_MODEL_PATH: Path = MODELS_DIR / "ner_model"
    EMBEDDINGS_INDEX_PATH: Path = MODELS_DIR / "faiss_index"
    
    # ── RAG Configuration ───────────────────────────────────────────────────────
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "512"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # ── NLP Confidence Thresholds (Proposal: ≥0.80 for critical slots) ──────────
    INTENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.80"))
    NER_CONFIDENCE_THRESHOLD: float = float(os.getenv("NER_CONFIDENCE_THRESHOLD", "0.80"))
    CRITICAL_SLOT_THRESHOLD: float = float(os.getenv("CRITICAL_SLOT_THRESHOLD", "0.80"))
    
    # ── Intent Classes (Proposal specification) ─────────────────────────────────
    INTENT_LABELS = [
        "eligibility_check",
        "document_requirement",
        "processing_time",
        "general_query",
    ]
    INTENT_LABEL2ID: Dict[str, int] = {label: idx for idx, label in enumerate(INTENT_LABELS)}
    INTENT_ID2LABEL: Dict[int, str] = {idx: label for label, idx in INTENT_LABEL2ID.items()}
    
    # ── NER Entity Types (Proposal specification) ───────────────────────────────
    NER_ENTITIES = [
        "JOB_TITLE",
        "SALARY", 
        "AGE",
        "COUNTRY",
        "VISA_TYPE",
        "SOC_CODE",
        "QUALIFICATION",
        "SPONSOR",
    ]
    
    # ── Critical Slots (must have ≥0.80 confidence) ─────────────────────────────
    CRITICAL_SLOTS = {"nationality", "salary_gbp", "job_title", "soc_code", "sponsor"}
    
    # ── Session Configuration ────────────────────────────────────────────────────
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    MAX_CLARIFICATION_ROUNDS: int = int(os.getenv("MAX_CLARIFICATION_ROUNDS", "6"))
    
    # ── Logging Configuration ────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: Path = BASE_DIR / "logs"
    LOG_FILE: Path = LOG_DIR / "atlas_ai.log"
    AUDIT_LOG_FILE: Path = LOG_DIR / "audit.log"
    
    # ── Data Paths ───────────────────────────────────────────────────────────────
    DATA_DIR: Path = BASE_DIR / "data"
    RULES_DIR: Path = DATA_DIR / "rules"
    SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"
    GOV_UK_DOCS_DIR: Path = DATA_DIR / "gov_uk_docs"
    
    # ── Evaluation Targets (Proposal specifications) ─────────────────────────────
    TARGET_INTENT_ACCURACY: float = 0.95
    TARGET_NER_F1: float = 0.90
    TARGET_RULE_CORRECTNESS: float = 0.98
    TARGET_SAFETY_SCORE: float = 1.00
    TARGET_SUS_SCORE: float = 75.0
    
    # ── Supported Visa Types ─────────────────────────────────────────────────────
    SUPPORTED_VISAS = [
        "skilled_worker",
        "health_care_worker", 
        "graduate",
        "global_talent",
    ]
    
    # ── Disclaimer (Proposal requirement) ────────────────────────────────────────
    DISCLAIMER = (
        "⚠️ This tool provides informational guidance only, not legal advice. "
        "Immigration rules change frequently. Always consult a qualified immigration "
        "solicitor or check official GOV.UK sources before making any decisions. "
        "Visit: https://www.gov.uk/skilled-worker-visa"
    )
    
    # ── GOV.UK Source URLs ──────────────────────────────────────────────────────
    GOV_UK_BASE: str = "https://www.gov.uk"
    SKILLED_WORKER_URL: str = "https://www.gov.uk/skilled-worker-visa"
    HEALTH_CARE_WORKER_URL: str = "https://www.gov.uk/health-care-worker-visa"
    GRADUATE_URL: str = "https://www.gov.uk/graduate-visa"
    GLOBAL_TALENT_URL: str = "https://www.gov.uk/global-talent-visa"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        for path in [
            cls.LOG_DIR,
            cls.DATA_DIR,
            cls.RULES_DIR,
            cls.SYNTHETIC_DIR,
            cls.GOV_UK_DOCS_DIR,
            cls.MODELS_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "app_env": cls.APP_ENV,
            "offline_mode": cls.OFFLINE_MODE,
            "openai_model": cls.OPENAI_MODEL,
            "flask_port": cls.FLASK_PORT,
            "intent_threshold": cls.INTENT_CONFIDENCE_THRESHOLD,
            "ner_threshold": cls.NER_CONFIDENCE_THRESHOLD,
            "critical_slot_threshold": cls.CRITICAL_SLOT_THRESHOLD,
            "supported_visas": cls.SUPPORTED_VISAS,
            "target_metrics": {
                "intent_accuracy": cls.TARGET_INTENT_ACCURACY,
                "ner_f1": cls.TARGET_NER_F1,
                "rule_correctness": cls.TARGET_RULE_CORRECTNESS,
                "safety_score": cls.TARGET_SAFETY_SCORE,
                "sus_score": cls.TARGET_SUS_SCORE,
            }
        }


# Module-level convenience access
config = AtlasConfig()