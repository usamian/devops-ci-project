"""
Atlas AI — Optimized Dialogue Manager v2
High-performance dialogue management with instant response capabilities.
Uses enhanced intent classification and comprehensive knowledge base.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from config import SESSION_TIMEOUT_MINUTES, DISCLAIMER
from src.nlp.intent_classifier_v2 import classify_intent_enhanced
from src.nlp.ner_extractor import extract_entities, entities_to_profile_updates
from src.nlp.confidence_handler import parse_yes_no, CLARIFICATION_QUESTIONS
from src.rule_engine.rules_base import ApplicantProfile, Verdict
from src.rule_engine.skilled_worker import check_eligibility
from src.responses.knowledge_base import get_response, get_fallback_response, get_suggestion_for_intent
from src.core.cache_manager import get_query_cache, get_model_cache, generate_cache_key


class DialogueState(str, Enum):
    GREETING = "greeting"
    COLLECTING = "collecting"
    CLARIFYING = "clarifying"
    ASSESSING = "assessing"
    ANSWERED = "answered"
    ERROR = "error"


@dataclass
class ConversationTurn:
    """Single turn in the conversation."""
    role: str  # "user" | "assistant"
    text: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    intent: Optional[str] = None
    entities: Optional[dict] = None
    verdict: Optional[str] = None


@dataclass
class Session:
    """Full conversation session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: DialogueState = DialogueState.GREETING
    profile: ApplicantProfile = field(default_factory=ApplicantProfile)
    turns: list[ConversationTurn] = field(default_factory=list)
    current_intent: Optional[str] = None
    pending_clarification_field: Optional[str] = None
    asked_fields: set = field(default_factory=set)
    low_confidence_entities: list[str] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.utcnow)
    eligibility_result: Optional[dict] = None
    clarification_count: int = 0
    max_clarifications: int = 6

    def is_expired(self) -> bool:
        cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return self.last_active < cutoff

    def touch(self):
        self.last_active = datetime.utcnow()

    def add_turn(self, role: str, text: str, **kwargs):
        self.turns.append(ConversationTurn(role=role, text=text, **kwargs))
        self.touch()

    def profile_summary(self) -> str:
        p = self.profile
        parts = []
        if p.job_title:
            parts.append(f"Job: {p.job_title}")
        if p.soc_code:
            parts.append(f"SOC: {p.soc_code}")
        if p.salary_annual:
            parts.append(f"Salary: £{p.salary_annual:,.0f}/yr")
        if p.age:
            parts.append(f"Age: {p.age}")
        if p.country_of_origin:
            parts.append(f"Country: {p.country_of_origin}")
        if p.has_sponsor is not None:
            parts.append(f"Sponsor: {'Yes' if p.has_sponsor else 'No'}")
        if p.english_proficiency:
            parts.append(f"English: {p.english_proficiency}")
        return " | ".join(parts) if parts else "No profile info yet"


# ── In-memory session store ───────────────────────────────────────────────────
_sessions: dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    """Get or create a session."""
    if session_id not in _sessions or _sessions[session_id].is_expired():
        _sessions[session_id] = Session(session_id=session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> Session:
    """Clear all session data (GDPR compliance)."""
    _sessions[session_id] = Session(session_id=session_id)
    return _sessions[session_id]


def cleanup_expired_sessions():
    """Remove expired sessions."""
    expired = [sid for sid, s in _sessions.items() if s.is_expired()]
    for sid in expired:
        del _sessions[sid]


# ── Response builder helpers ─────────────────────────────────────────────────

GREETING_MESSAGE = (
    "👋 Welcome to **Atlas AI** — your UK immigration guidance assistant.\n\n"
    "I can help you check your eligibility for the **Skilled Worker Visa** and "
    "explain the requirements in plain English.\n\n"
    "To get started, tell me about your situation. For example:\n"
    "- *\"I'm a software engineer from India, earning £50,000. My employer will sponsor me.\"*\n"
    "- *\"Can I apply for a skilled worker visa as a nurse?\"*\n\n"
    f"*{DISCLAIMER}*"
)

FALLBACK_MESSAGE = (
    "I'm not sure I understood that. Could you tell me more about the visa you're "
    "interested in or your job situation? For example, your job title, salary, and "
    "whether you have a UK employer willing to sponsor you."
)


def _apply_profile_updates(profile: ApplicantProfile, updates: dict):
    """Apply extracted entity updates to the profile (non-destructive)."""
    for key, value in updates.items():
        if value is not None and getattr(profile, key, None) is None:
            setattr(profile, key, value)


def _handle_greeting(session: Session, user_text: str) -> tuple[str, Session]:
    """Initial state: switch to COLLECTING and process first message."""
    session.state = DialogueState.COLLECTING
    return _handle_collecting(session, user_text)


def _handle_collecting(session: Session, user_text: str) -> tuple[str, Session]:
    """
    Main collection state using enhanced intent classification.
    Fast, accurate intent detection with comprehensive response handling.
    """
    # Classify intent using enhanced classifier (instant)
    intent_result = classify_intent_enhanced(user_text)
    session.current_intent = intent_result["intent"]
    session.add_turn(
        "user", user_text,
        intent=intent_result["intent"],
        entities=None,
    )

    intent = intent_result["intent"]

    # ── Handle non-eligibility intents with knowledge base responses ──────────
    
    if intent == "processing_time":
        session.state = DialogueState.ANSWERED
        response_data = get_response("processing_time")
        return response_data["response"], session

    if intent == "fees_and_costs":
        session.state = DialogueState.ANSWERED
        response_data = get_response("fees_and_costs")
        return response_data["response"], session

    if intent == "document_requirement":
        # Extract any entities first to contextualise
        entity_result = extract_entities(user_text)
        updates = entities_to_profile_updates(entity_result)
        _apply_profile_updates(session.profile, updates)
        session.state = DialogueState.ANSWERED
        response_data = get_response("document_requirement")
        return response_data["response"], session

    if intent == "dependants_query":
        session.state = DialogueState.ANSWERED
        response_data = get_response("dependants_query")
        return response_data["response"], session

    if intent == "extension_switching":
        session.state = DialogueState.ANSWERED
        response_data = get_response("extension_switching")
        return response_data["response"], session

    if intent == "settlement_ilr":
        session.state = DialogueState.ANSWERED
        response_data = get_response("settlement_ilr")
        return response_data["response"], session

    if intent == "health_care_worker":
        session.state = DialogueState.ANSWERED
        response_data = get_response("health_care_worker")
        return response_data["response"], session

    if intent == "shortage_occupation":
        session.state = DialogueState.ANSWERED
        response_data = get_response("shortage_occupation")
        return response_data["response"], session

    if intent == "english_language":
        session.state = DialogueState.ANSWERED
        response_data = get_response("english_language")
        return response_data["response"], session

    if intent == "salary_threshold":
        session.state = DialogueState.ANSWERED
        response_data = get_response("salary_threshold")
        return response_data["response"], session

    if intent == "general_query":
        # Check for greetings and simple queries
        text_lower = user_text.lower().strip()
        
        # Greetings
        if any(g in text_lower for g in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
            session.state = DialogueState.ANSWERED
            return (
                "Hello! 👋 Welcome to Atlas AI. I'm here to help you with UK immigration guidance, "
                "particularly for the Skilled Worker Visa.\n\n"
                "How can I assist you today? You can ask me about:\n"
                "- Visa eligibility\n"
                "- Required documents\n"
                "- Processing times and fees\n"
                "- Bringing family members\n"
                "- And much more!\n\n"
                f"*{DISCLAIMER}*"
            ), session
        
        # Thanks
        if any(t in text_lower for t in ["thank", "thanks", "thank you"]):
            session.state = DialogueState.ANSWERED
            return (
                "You're welcome! 😊 I'm glad I could help. Is there anything else you'd like to know "
                "about UK immigration or the Skilled Worker Visa?\n\n"
                f"*{DISCLAIMER}*"
            ), session
        
        # Goodbye
        if any(b in text_lower for b in ["bye", "goodbye", "see you", "take care"]):
            session.state = DialogueState.ANSWERED
            return (
                "Goodbye! 👋 Thank you for using Atlas AI. Best of luck with your UK immigration journey!\n\n"
                "If you have any more questions in the future, feel free to return.\n\n"
                f"*{DISCLAIMER}*"
            ), session
        
        # General information queries
        session.state = DialogueState.ANSWERED
        response_data = get_response("general_query")
        return response_data["response"], session

    # ── Eligibility check ─────────────────────────────────────────────────────
    
    if intent == "eligibility_check":
        # Extract entities and update profile
        entity_result = extract_entities(user_text)
        updates = entities_to_profile_updates(entity_result)
        _apply_profile_updates(session.profile, updates)

        session.low_confidence_entities = [
            etype for etype in entity_result.get("low_confidence", [])
            if etype in ["JOB_TITLE", "SALARY", "COUNTRY"]
        ]

        # Check if we need clarification
        if _needs_clarification(session.profile, session.low_confidence_entities):
            return _ask_next_clarification(session)

        # We have enough info — run the assessment
        return _run_assessment(session, user_text)

    # ── Fallback for unrecognized intents ─────────────────────────────────────
    
    # If we get here, try to extract entities and see if it's eligibility-related
    entity_result = extract_entities(user_text)
    updates = entities_to_profile_updates(entity_result)
    _apply_profile_updates(session.profile, updates)

    # If we have key eligibility info, run assessment
    if session.profile.job_title and session.profile.salary_annual and session.profile.has_sponsor is not None:
        return _run_assessment(session, user_text)

    # Otherwise, provide fallback response
    session.state = DialogueState.ANSWERED
    response_data = get_fallback_response()
    return response_data["response"], session


def _needs_clarification(profile: ApplicantProfile, low_confidence: list[str]) -> bool:
    """Check if clarification is needed."""
    missing = profile.missing_fields()
    return bool(missing) or bool(low_confidence)


def _ask_next_clarification(session: Session) -> tuple[str, Session]:
    """Ask the next clarification question."""
    # Priority 1: Missing required fields
    missing = session.profile.missing_fields()
    for field in missing:
        if field not in session.asked_fields:
            session.state = DialogueState.CLARIFYING
            session.pending_clarification_field = field
            question = CLARIFICATION_QUESTIONS.get(field, f"Could you provide your {field.replace('_', ' ')}?")
            return question, session

    # Priority 2: Low-confidence entities
    for entity_type in session.low_confidence_entities:
        field = entity_type.lower()
        if field not in session.asked_fields:
            session.state = DialogueState.CLARIFYING
            session.pending_clarification_field = field
            return f"I detected your {entity_type.lower().replace('_', ' ')} — could you please confirm?", session

    # Nothing to clarify — run assessment
    return _run_assessment(session, "")


def _handle_clarifying(session: Session, user_text: str) -> tuple[str, Session]:
    """
    Clarification state: parse the user's answer and update profile.
    """
    field = session.pending_clarification_field

    if field:
        updated = False

        if field in ("has_sponsor", "sponsorship"):
            yn = parse_yes_no(user_text)
            if yn is not None:
                session.profile.has_sponsor = yn
                updated = True
            else:
                return (
                    "I didn't quite catch that. Do you have a Certificate of Sponsorship "
                    "from a UK employer? Please answer **Yes** or **No**.",
                    session,
                )

        elif field == "salary":
            from src.nlp.preprocessor import extract_salary_from_text_or_bare
            sal = extract_salary_from_text_or_bare(user_text)
            if sal:
                session.profile.salary_annual = sal
                updated = True
            else:
                return (
                    "I couldn't extract a salary figure. Please give your annual salary "
                    "in GBP, e.g. **£45,000** or **45k**.",
                    session,
                )

        elif field == "job_title":
            ent = extract_entities(user_text)
            upd = entities_to_profile_updates(ent)
            if "job_title" in upd:
                session.profile.job_title = upd["job_title"]
                updated = True
            elif len(user_text.strip()) > 2:
                session.profile.job_title = user_text.strip().title()
                updated = True

        elif field == "country_of_origin":
            from src.nlp.preprocessor import normalise_country_name
            ent = extract_entities(user_text)
            if "COUNTRY" in ent.get("entities", {}):
                session.profile.country_of_origin = ent["entities"]["COUNTRY"]["value"]
                updated = True
            elif len(user_text.strip()) > 2:
                session.profile.country_of_origin = normalise_country_name(user_text.strip())
                updated = True

        elif field == "english_proficiency":
            text_lower = user_text.lower()
            if any(k in text_lower for k in ["ielts", "toefl", "pte", "test", "passed", "certificate", "exam"]):
                session.profile.english_proficiency = "test_passed"
                updated = True
            elif any(k in text_lower for k in ["degree", "university", "english speaking", "native", "uk educated"]):
                session.profile.english_proficiency = "native"
                updated = True
            elif any(k in text_lower for k in ["no", "none", "don't have", "not yet"]):
                session.profile.english_proficiency = "none"
                updated = True
            else:
                ent = extract_entities(user_text)
                upd = entities_to_profile_updates(ent)
                if "english_proficiency" in upd:
                    session.profile.english_proficiency = upd["english_proficiency"]
                    updated = True

        elif field == "age":
            from src.nlp.preprocessor import extract_age_from_text
            age = extract_age_from_text(user_text)
            if age:
                session.profile.age = age
                updated = True
            else:
                import re
                m = re.search(r'\b(\d{2})\b', user_text)
                if m:
                    age = int(m.group(1))
                    if 16 <= age <= 80:
                        session.profile.age = age
                        updated = True

        if updated:
            session.asked_fields.add(field)
            session.pending_clarification_field = None

    # Check if we still need more info
    if _needs_clarification(session.profile, session.low_confidence_entities):
        session.clarification_count += 1
        if session.clarification_count >= session.max_clarifications:
            return _run_assessment(session, "")
        return _ask_next_clarification(session)

    # All info collected — run assessment
    return _run_assessment(session, "")


_ENGLISH_EXEMPT_COUNTRIES_DM = {
    "antigua and barbuda", "australia", "bahamas", "barbados", "belize",
    "canada", "dominica", "grenada", "guyana", "jamaica", "malta",
    "new zealand", "st kitts and nevis", "saint kitts and nevis",
    "st lucia", "saint lucia", "st vincent and the grenadines",
    "saint vincent and the grenadines", "trinidad and tobago",
    "united states", "united states of america", "usa",
    "uk", "united kingdom", "ireland",
}

MAX_CLARIFICATION_DEPTH = 8


def _run_assessment(session: Session, original_query: str) -> tuple[str, Session]:
    """Run the eligibility assessment pipeline."""
    session.state = DialogueState.ASSESSING

    # Run rule engine
    result = check_eligibility(session.profile)

    if result.verdict == Verdict.INSUFFICIENT_INFO:
        # Still missing info
        session.state = DialogueState.CLARIFYING
        missing = result.missing_info if result.missing_info else session.profile.missing_fields()
        if missing:
            first_missing = [f for f in missing if f not in session.asked_fields]
            if first_missing:
                field = first_missing[0]
                q = CLARIFICATION_QUESTIONS.get(field, f"Could you provide your {field.replace('_', ' ')}?")
                session.pending_clarification_field = field
                return q, session
        # Nothing new to ask — proceed with what we have
        return _run_assessment_direct(session, original_query)

    # Build response based on result
    session.eligibility_result = result.to_dict()
    session.state = DialogueState.ANSWERED

    return result.summary, session


def _run_assessment_direct(session: Session, original_query: str) -> tuple[str, Session]:
    """Run assessment without further clarification."""
    session.state = DialogueState.ASSESSING

    result = check_eligibility(session.profile)

    if result.verdict == Verdict.INSUFFICIENT_INFO:
        session.state = DialogueState.CLARIFYING
        missing = result.missing_info if result.missing_info else session.profile.missing_fields()
        if missing:
            first_missing = missing[0]
            q = CLARIFICATION_QUESTIONS.get(first_missing, f"Could you provide your {first_missing.replace('_', ' ')}?")
            session.pending_clarification_field = first_missing
            return q, session
        session.state = DialogueState.ANSWERED
        return result.summary, session

    session.eligibility_result = result.to_dict()
    session.state = DialogueState.ANSWERED

    return result.summary, session


def _safe_profile_dict(profile: ApplicantProfile) -> dict:
    """Serialise profile without PII."""
    return {
        "job_title": profile.job_title,
        "salary_annual": profile.salary_annual,
        "has_sponsor": profile.has_sponsor,
        "country_of_origin": profile.country_of_origin,
        "english_proficiency": profile.english_proficiency,
        "visa_type": profile.visa_type,
    }


# ── Main process_message entry point ────────────────────────────────────────

def process_message(session_id: str, user_text: str) -> dict:
    """
    Main dialogue processing function.
    Uses caching for improved performance.
    """
    session = get_session(session_id)
    user_text = user_text.strip()

    # Handle reset commands
    if user_text.lower() in {"reset", "start over", "restart", "new conversation", "clear"}:
        session = reset_session(session_id)
        return {
            "response": "Conversation reset. " + GREETING_MESSAGE,
            "state": session.state.value,
            "session_id": session_id,
            "verdict": None,
            "profile": {},
        }

    # Check cache for quick responses (non-eligibility queries)
    cache_key = generate_cache_key(user_text.lower())
    query_cache = get_query_cache()
    cached_response = query_cache.get(cache_key)
    
    # Only use cache for non-eligibility, non-clarifying states
    if cached_response and session.state not in (DialogueState.CLARIFYING, DialogueState.ASSESSING):
        return cached_response

    # Route based on current state
    if session.state == DialogueState.GREETING or not session.turns:
        response_text, session = _handle_greeting(session, user_text)
    elif session.state == DialogueState.CLARIFYING:
        response_text, session = _handle_clarifying(session, user_text)
    elif session.state in (DialogueState.COLLECTING, DialogueState.ANSWERED):
        # Allow follow-up questions after an answer
        session.state = DialogueState.COLLECTING
        response_text, session = _handle_collecting(session, user_text)
    else:
        response_text = FALLBACK_MESSAGE
        session.state = DialogueState.COLLECTING

    session.add_turn("assistant", response_text[:200])  # Store truncated for memory

    result = {
        "response": response_text,
        "state": session.state.value,
        "session_id": session_id,
        "verdict": session.eligibility_result.get("verdict") if session.eligibility_result else None,
        "profile": _safe_profile_dict(session.profile),
    }

    # Cache non-eligibility responses
    if result["verdict"] is None:
        query_cache.set(cache_key, result, ttl=3600)

    return result