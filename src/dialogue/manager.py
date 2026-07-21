"""
Atlas AI — Dialogue Manager
Manages multi-turn conversation state, clarification loops,
and orchestrates the full NLP → Rule Engine → GPT pipeline.

State machine:
  GREETING → COLLECTING → CLARIFYING → ASSESSING → ANSWERED → RESET
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from config import (
    INTENT_CONFIDENCE_THRESHOLD,
    NER_CONFIDENCE_THRESHOLD,
    SESSION_TIMEOUT_MINUTES,
    DISCLAIMER,
)
from src.nlp.intent_classifier import classify_intent
from src.nlp.ner_extractor import extract_entities, entities_to_profile_updates
from src.nlp.confidence_handler import (
    get_next_clarification, needs_clarification, parse_yes_no,
    CLARIFICATION_QUESTIONS
)
from src.rule_engine.rules_base import ApplicantProfile, Verdict
from src.rule_engine.skilled_worker import check_eligibility


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
    """Clear all session data (GDPR compliance — no personal data retained)."""
    _sessions[session_id] = Session(session_id=session_id)
    return _sessions[session_id]


def cleanup_expired_sessions():
    """Remove expired sessions (call periodically)."""
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


def _handle_greeting(session: Session, user_text: str) -> tuple[str, Session]:
    """Initial state: switch to COLLECTING and process first message."""
    session.state = DialogueState.COLLECTING
    return _handle_collecting(session, user_text)


def _handle_collecting(session: Session, user_text: str) -> tuple[str, Session]:
    """
    Main collection state:
    1. Classify intent
    2. Extract entities
    3. Update profile
    4. Determine if we have enough info or need clarification
    """
    # Classify intent
    intent_result = classify_intent(user_text)
    session.current_intent = intent_result["intent"]
    session.add_turn(
        "user", user_text,
        intent=intent_result["intent"],
        entities=None,
    )

    # If low-confidence intent, ask for clarification
    if intent_result["low_confidence"] and intent_result["source"] == "model":
        session.state = DialogueState.CLARIFYING
        return (
            "I want to make sure I help you correctly. Are you asking about:\n"
            "1. **Eligibility** — whether you can apply for a visa?\n"
            "2. **Documents** — what you need to provide?\n"
            "3. **Processing time** — how long it takes?\n"
            "4. **General information** about UK immigration?\n\n"
            "Please type the number or describe what you need.",
            session,
        )

    # For non-eligibility intents, give direct answers
    if intent_result["intent"] == "processing_time":
        session.state = DialogueState.ANSWERED
        return _answer_processing_time(), session

    if intent_result["intent"] == "document_requirement":
        # Extract any entities first to contextualise
        entity_result = extract_entities(user_text)
        updates = entities_to_profile_updates(entity_result)
        _apply_profile_updates(session.profile, updates)
        session.state = DialogueState.ANSWERED
        return _answer_document_requirements(session.profile), session

    # Eligibility check or general query → extract entities and update profile
    entity_result = extract_entities(user_text)
    updates = entities_to_profile_updates(entity_result)
    _apply_profile_updates(session.profile, updates)

    session.low_confidence_entities = [
        etype for etype in entity_result.get("low_confidence", [])
        if etype in ["JOB_TITLE", "SALARY", "COUNTRY"]
    ]

    # Check if we need clarification
    if needs_clarification(session.profile, session.low_confidence_entities):
        return _ask_next_clarification(session)

    # We have enough info — run the assessment
    return _run_assessment(session, user_text)


def _handle_clarifying(session: Session, user_text: str) -> tuple[str, Session]:
    """
    Clarification state: parse the user's answer to the question we asked,
    update the profile, and either ask another question or run assessment.
    """
    field = session.pending_clarification_field

    if field:
        # Parse the answer based on what we asked
        updated = False

        if field in ("has_sponsor", "sponsorship"):
            yn = parse_yes_no(user_text)
            if yn is not None:
                session.profile.has_sponsor = yn
                updated = True
            else:
                # Re-ask
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
            # Accept whatever they say as job title, and try to extract
            from src.nlp.ner_extractor import extract_entities, entities_to_profile_updates
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
            from src.nlp.ner_extractor import extract_entities
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
                # Re-extract
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
                # Try parsing plain number
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

    # Remove confirmed low-confidence entities
    session.low_confidence_entities = [
        e for e in session.low_confidence_entities
        if e.lower() not in session.asked_fields
    ]

    # Check if we still need more info
    if needs_clarification(session.profile, session.low_confidence_entities):
        session.clarification_count += 1
        if session.clarification_count >= session.max_clarifications:
            # Too many clarifications — run assessment with what we have
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

MAX_CLARIFICATION_DEPTH = 8  # Hard limit — never recurse beyond this


def _ask_next_clarification(session: Session, depth: int = 0) -> tuple[str, Session]:
    """Ask the next clarification question. depth guards against infinite recursion."""
    if depth >= MAX_CLARIFICATION_DEPTH:
        # Safety valve: run assessment with whatever we have
        return _run_assessment_direct(session, "")

    field, question = get_next_clarification(
        session.profile,
        session.low_confidence_entities,
        session.asked_fields,
    )

    if field and question:
        session.state = DialogueState.CLARIFYING
        session.pending_clarification_field = field
        return question, session

    # After core fields are known, ask English if country is non-exempt and not yet confirmed
    p = session.profile
    if (p.country_of_origin is not None
            and p.english_proficiency is None
            and "english_proficiency" not in session.asked_fields
            and p.country_of_origin.lower() not in _ENGLISH_EXEMPT_COUNTRIES_DM):
        session.state = DialogueState.CLARIFYING
        session.pending_clarification_field = "english_proficiency"
        session.asked_fields.add("english_proficiency")  # Mark asked immediately to prevent re-entry
        return CLARIFICATION_QUESTIONS["english_proficiency"], session

    # Nothing left to ask — run assessment directly (no clarification needed)
    return _run_assessment_direct(session, "")


def _run_assessment_direct(session: Session, original_query: str) -> tuple[str, Session]:
    """Run assessment without any further clarification recursion."""
    from src.rule_engine.skilled_worker import check_eligibility
    from src.rag.retriever import retrieve_for_intent, format_retrieved_context
    from src.gpt.explainer import generate_explanation

    session.state = DialogueState.ASSESSING

    # Run rule engine
    result = check_eligibility(session.profile)

    if result.verdict == Verdict.INSUFFICIENT_INFO:
        # Still missing info but we cannot ask more — return informational message
        session.state = DialogueState.CLARIFYING
        missing = result.missing_info if result.missing_info else session.profile.missing_fields()
        if missing:
            first_missing = missing[0]
            q = CLARIFICATION_QUESTIONS.get(first_missing, f"Could you provide your {first_missing.replace('_', ' ')}?")
            session.pending_clarification_field = first_missing
            return q, session
        # Truly nothing left to ask but still insufficient — give a summary
        session.state = DialogueState.ANSWERED
        return result.summary, session

    # Retrieve context from GOV.UK docs
    query_for_rag = original_query or session.profile_summary()
    try:
        chunks = retrieve_for_intent(
            query_for_rag,
            session.current_intent or "eligibility_check",
            {}
        )
        context = format_retrieved_context(chunks)
    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        context = "No relevant guidance retrieved."

    # Generate explanation (constrained GPT or offline)
    explanation_result = generate_explanation(
        result=result,
        original_query=original_query,
        retrieved_context=context,
        profile_summary=session.profile_summary(),
    )

    session.eligibility_result = result.to_dict()
    session.state = DialogueState.ANSWERED

    return explanation_result["explanation"], session


def _run_assessment(session: Session, original_query: str) -> tuple[str, Session]:
    """Run the full eligibility assessment pipeline."""
    from src.rule_engine.skilled_worker import check_eligibility
    from src.rag.retriever import retrieve_for_intent, format_retrieved_context
    from src.gpt.explainer import generate_explanation

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
        # Nothing new to ask — proceed to direct assessment
        return _run_assessment_direct(session, original_query)

    # Retrieve context from GOV.UK docs
    query_for_rag = original_query or session.profile_summary()
    try:
        chunks = retrieve_for_intent(
            query_for_rag,
            session.current_intent or "eligibility_check",
            {}
        )
        context = format_retrieved_context(chunks)
    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        context = "No relevant guidance retrieved."

    # Generate explanation (constrained GPT or offline)
    explanation_result = generate_explanation(
        result=result,
        original_query=original_query,
        retrieved_context=context,
        profile_summary=session.profile_summary(),
    )

    session.eligibility_result = result.to_dict()
    session.state = DialogueState.ANSWERED

    return explanation_result["explanation"], session


def _apply_profile_updates(profile: ApplicantProfile, updates: dict):
    """Apply extracted entity updates to the profile (non-destructive)."""
    for key, value in updates.items():
        if value is not None and getattr(profile, key, None) is None:
            setattr(profile, key, value)


def _answer_processing_time() -> str:
    return (
        "## ⏱️ Skilled Worker Visa Processing Times\n\n"
        "**Standard processing:**\n"
        "- **From outside the UK:** Usually within **3 weeks**\n"
        "- **From inside the UK (switching/extending):** Usually within **8 weeks**\n\n"
        "**Priority services (additional fee):**\n"
        "- **Priority service:** Decision within **5 working days** (+£500)\n"
        "- **Super Priority service:** Decision within **1 working day** (+£800) — "
        "available for in-country applications only\n\n"
        "⚠️ These are target times, not guarantees. Processing can take longer during "
        "peak periods. Do not book non-refundable travel before receiving your decision.\n\n"
        f"*Source: [GOV.UK – Apply for a Skilled Worker visa]"
        f"(https://www.gov.uk/skilled-worker-visa/apply)*\n\n"
        f"*{DISCLAIMER}*"
    )


def _answer_document_requirements(profile: ApplicantProfile) -> str:
    docs = (
        "## 📋 Documents Required for Skilled Worker Visa\n\n"
        "**Mandatory documents:**\n"
        "1. **Valid passport or travel document** — must cover your intended stay\n"
        "2. **Certificate of Sponsorship (CoS) reference number** — from your UK employer\n"
        "3. **Proof of English language** — IELTS/TOEFL/PTE at B1+ level, or exemption evidence\n"
        "4. **Employment contract or payslips** — showing your salary\n"
        "5. **Bank statements** — showing £1,270 held for 28+ days "
        "(waived if sponsor certifies maintenance)\n\n"
        "**You may also need:**\n"
        "- Degree/qualification certificates\n"
        "- TB (tuberculosis) test results — required from many countries outside Europe/USA\n"
        "- Overseas police clearance — for some regulated sectors\n"
        "- Previous UK visa refusal letters (if applicable)\n\n"
        "**For TB test countries**, check: "
        "[GOV.UK TB countries list](https://www.gov.uk/tb-test-visa)\n\n"
        f"*Source: [GOV.UK – Documents you must provide]"
        f"(https://www.gov.uk/skilled-worker-visa/documents-you-must-provide)*\n\n"
        f"*{DISCLAIMER}*"
    )
    return docs


# ── Main process_message entry point ────────────────────────────────────────

def process_message(session_id: str, user_text: str) -> dict:
    """
    Main dialogue processing function.
    Called by the Flask API for each user message.

    Returns:
        {
            "response": str,
            "state": str,
            "session_id": str,
            "verdict": str | None,
            "profile": dict,
        }
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

    return {
        "response": response_text,
        "state": session.state.value,
        "session_id": session_id,
        "verdict": session.eligibility_result.get("verdict") if session.eligibility_result else None,
        "profile": _safe_profile_dict(session.profile),
    }


def _safe_profile_dict(profile: ApplicantProfile) -> dict:
    """Serialise profile without PII beyond what's needed for display."""
    return {
        "job_title": profile.job_title,
        "salary_annual": profile.salary_annual,
        "has_sponsor": profile.has_sponsor,
        "country_of_origin": profile.country_of_origin,
        "english_proficiency": profile.english_proficiency,
        "visa_type": profile.visa_type,
    }
