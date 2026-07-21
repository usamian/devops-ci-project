"""
Atlas AI — Confidence Handler
Manages clarification dialogues when NER confidence is below threshold
or when required entities are missing from the applicant profile.
"""

from config import NER_CONFIDENCE_THRESHOLD
from src.rule_engine.rules_base import ApplicantProfile


# Maps entity type → clarification question
CLARIFICATION_QUESTIONS = {
    "job_title": (
        "What is your current job title or the role you've been offered in the UK? "
        "(e.g., 'Software Engineer', 'Nurse', 'Civil Engineer')"
    ),
    "salary": (
        "What is the annual salary (in GBP) offered for this role? "
        "(e.g., '£45,000 per year')"
    ),
    "country_of_origin": (
        "Which country are you applying from / are you a national of? "
        "This helps us assess the English language requirement."
    ),
    "has_sponsor": (
        "Do you have a Certificate of Sponsorship (CoS) from a UK-licensed employer? "
        "You cannot apply for a Skilled Worker visa without a sponsor. "
        "(Yes / No)"
    ),
    "sponsorship": (
        "Do you have a Certificate of Sponsorship (CoS) from a UK-licensed employer? "
        "You cannot apply for a Skilled Worker visa without a sponsor. "
        "(Yes / No)"
    ),
    "english_proficiency": (
        "Can you confirm your English language evidence? For example: "
        "a) IELTS/TOEFL/PTE test result at B1+ level, "
        "b) A degree taught in English, or "
        "c) You are a national of a majority English-speaking country."
    ),
    "age": (
        "Could you tell me your age? This helps determine whether the new entrant "
        "salary threshold applies to you."
    ),
    "savings": (
        "Do you have at least £1,270 in personal savings held for 28 consecutive days, "
        "OR has your sponsor indicated they will certify your maintenance?"
    ),
}

LOW_CONFIDENCE_QUESTIONS = {
    "JOB_TITLE": (
        "I detected your job title as '{value}' — is that correct? "
        "Please confirm or provide the exact job title."
    ),
    "SALARY": (
        "I picked up a salary of £{value:,.0f} — is that your annual gross salary? "
        "Please confirm."
    ),
    "COUNTRY": (
        "I identified your country as '{value}' — is that correct?"
    ),
    "AGE": (
        "I noted your age as {value} — is that right?"
    ),
}


def get_next_clarification(
    profile: ApplicantProfile,
    low_confidence_entities: list[str],
    asked_already: set[str],
) -> tuple[str | None, str | None]:
    """
    Determine the next clarification question to ask.
    Priority: missing required fields > low-confidence entities.

    Returns:
        (field_name, question_text) or (None, None) if nothing to ask
    """
    # Priority 1: Ask about missing required fields
    missing = profile.missing_fields()
    for field in missing:
        if field not in asked_already:
            return field, CLARIFICATION_QUESTIONS.get(field)

    # Priority 2: Low-confidence entities
    for entity_type in low_confidence_entities:
        field = entity_type.lower()
        if field not in asked_already:
            question = LOW_CONFIDENCE_QUESTIONS.get(entity_type, "")
            return field, question

    return None, None


def parse_yes_no(text: str) -> bool | None:
    """Parse yes/no from user response."""
    text_lower = text.lower().strip()
    yes_indicators = {"yes", "y", "yep", "yeah", "yup", "correct", "that's right", "affirmative", "i do", "i have"}
    no_indicators = {"no", "n", "nope", "nah", "negative", "i don't", "i don't have", "not yet", "none"}

    for ind in yes_indicators:
        if ind in text_lower:
            return True
    for ind in no_indicators:
        if ind in text_lower:
            return False
    return None


def needs_clarification(
    profile: ApplicantProfile,
    low_confidence: list[str],
) -> bool:
    """Return True if clarification is needed before running the rule engine."""
    return bool(profile.missing_fields()) or bool(low_confidence)
