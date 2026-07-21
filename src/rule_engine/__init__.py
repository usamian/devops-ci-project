"""
Atlas AI — Rule Engine Package
Deterministic, rule-based eligibility determination for UK visa routes.

IMPORTANT: This module NEVER uses ML or GPT for eligibility decisions.
All decisions are traceable to specific GOV.UK rule references.

Available Visa Types:
- Skilled Worker Visa
- Health and Care Worker Visa
- Graduate Visa
- Global Talent Visa
- Student Visa
- Family Visa (Spouse/Partner)
"""

from src.rule_engine.rules_base import (
    Verdict,
    RuleResult,
    EligibilityResult,
    ApplicantProfile,
)
from src.rule_engine.base_visa import BaseVisaRuleEngine

# Import all visa rule engines
from src.rule_engine.skilled_worker import SkilledWorkerRuleEngine
from src.rule_engine.health_care_worker import HealthCareWorkerRuleEngine
from src.rule_engine.graduate import GraduateRuleEngine
from src.rule_engine.global_talent import GlobalTalentRuleEngine
from src.rule_engine.student_visa import StudentVisaRuleEngine
from src.rule_engine.family_visa import FamilyVisaRuleEngine

# Import visa recommender
from src.rule_engine.visa_recommender import VisaRecommender, get_visa_recommendation

# Registry of all visa engines
VISA_ENGINES = {
    "skilled_worker": SkilledWorkerRuleEngine,
    "health_care_worker": HealthCareWorkerRuleEngine,
    "graduate": GraduateRuleEngine,
    "global_talent": GlobalTalentRuleEngine,
    "student": StudentVisaRuleEngine,
    "family": FamilyVisaRuleEngine,
}

# Visa metadata for quick reference
VISA_METADATA = {
    "skilled_worker": {
        "name": "Skilled Worker Visa",
        "url": "https://www.gov.uk/skilled-worker-visa",
        "description": "For workers with a job offer from a UK licensed sponsor",
    },
    "health_care_worker": {
        "name": "Health and Care Worker Visa",
        "url": "https://www.gov.uk/health-care-worker-visa",
        "description": "For qualified doctors, nurses, and health/care workers",
    },
    "graduate": {
        "name": "Graduate Visa",
        "url": "https://www.gov.uk/graduate-visa",
        "description": "For UK graduates to work for 2-3 years post-study",
    },
    "global_talent": {
        "name": "Global Talent Visa",
        "url": "https://www.gov.uk/global-talent-visa",
        "description": "For leaders in academia, research, digital technology, or arts",
    },
    "student": {
        "name": "Student Visa",
        "url": "https://www.gov.uk/student-visa",
        "description": "For studying at a UK educational institution",
    },
    "family": {
        "name": "Family Visa (Spouse/Partner)",
        "url": "https://www.gov.uk/uk-family-visa",
        "description": "For joining or staying with family members settled in the UK",
    },
}

__all__ = [
    # Core classes
    'Verdict',
    'RuleResult', 
    'EligibilityResult',
    'ApplicantProfile',
    'BaseVisaRuleEngine',
    
    # Visa engines
    'SkilledWorkerRuleEngine',
    'HealthCareWorkerRuleEngine',
    'GraduateRuleEngine',
    'GlobalTalentRuleEngine',
    'StudentVisaRuleEngine',
    'FamilyVisaRuleEngine',
    
    # Visa recommender
    'VisaRecommender',
    'get_visa_recommendation',
    
    # Registry and metadata
    'VISA_ENGINES',
    'VISA_METADATA',
]


def get_engine(visa_type: str) -> BaseVisaRuleEngine:
    """
    Get a rule engine instance for a specific visa type.
    
    Args:
        visa_type: The visa type (e.g., 'skilled_worker', 'student', 'family')
    
    Returns:
        An instance of the appropriate rule engine
    
    Raises:
        ValueError: If visa_type is not recognized
    """
    if visa_type not in VISA_ENGINES:
        available = ', '.join(VISA_ENGINES.keys())
        raise ValueError(f"Unknown visa type: {visa_type}. Available: {available}")
    
    return VISA_ENGINES[visa_type]()


def get_all_visa_types() -> list:
    """Return a list of all supported visa types."""
    return list(VISA_ENGINES.keys())


def get_visa_info(visa_type: str) -> dict:
    """
    Get metadata information for a specific visa type.
    
    Args:
        visa_type: The visa type
    
    Returns:
        Dictionary with visa name, URL, and description
    """
    return VISA_METADATA.get(visa_type, {})