"""
Atlas AI — Flask Web Application
Full-fledged AI Chatbot for UK Immigration Guidance
Uses enhanced dialogue management + RAG + Rule Engine for intelligent conversations.
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from flask_session import Session

from src.core.config import AtlasConfig
from src.core.audit import audit_logger, AuditEvent, AuditEventType
from src.core.updater import updater
from src.dialogue.enhanced_manager import EnhancedDialogueManager, process_message
from src.gpt.local_llm import SmartChatbot, LocalLLM
from src.gpt.groq_ai import groq_ai
from src.rag.gov_uk_scraper import scraper
from src.rule_engine.skilled_worker import SkilledWorkerRuleEngine
from src.rule_engine.health_care_worker import HealthCareWorkerRuleEngine
from src.rule_engine.graduate import GraduateRuleEngine
from src.rule_engine.global_talent import GlobalTalentRuleEngine
from src.rule_engine.student_visa import StudentVisaRuleEngine
from src.rule_engine.family_visa import FamilyVisaRuleEngine
from src.rule_engine.rules_base import ApplicantProfile

# ── Flask App Setup ────────────────────────────────────────────────────────────

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
    static_folder=str(PROJECT_ROOT / "frontend" / "static")
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "atlas-ai-dev-secret-2024")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = str(AtlasConfig.BASE_DIR / "sessions")
Session(app)
CORS(app)

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(AtlasConfig.LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── Global Chatbot Instance ────────────────────────────────────────────────────

chatbot = SmartChatbot()
enhanced_dm = EnhancedDialogueManager()

# ── Validate Groq AI Configuration at Startup ──────────────────────────────────

if groq_ai.available:
    logger.info("Groq API key found. Validating...")
    if groq_ai.validate_and_test():
        logger.info("✓ Groq AI is configured and ready!")
    else:
        logger.warning("! Groq AI validation failed. Falling back to other AI options.")
else:
    logger.info("Groq API key not configured. Set GROQ_API_KEY in groq_config.py for enhanced AI.")


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main chat interface."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "ollama_available": chatbot.llm.available,
        "model": chatbot.llm.model if chatbot.llm.available else None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/api/greeting", methods=["GET"])
def get_greeting():
    """Get welcome message."""
    return jsonify({
        "message": """🗺️ **Hello! I'm Atlas AI, your friendly UK immigration assistant.**

I'm here to help you navigate the complex world of UK visas. Whether you're looking to work, study, or settle in the UK, I can guide you through the process.

**What would you like to know about?**
- Visa eligibility and requirements
- Application process and documents
- Salary thresholds and going rates
- Switching between visa types
- Or just ask me anything about UK immigration!

*This is an informational service, not legal advice. Always verify with official GOV.UK sources.*""",
        "suggestions": [
            "What are the requirements for a Skilled Worker visa?",
            "How much salary do I need for a Skilled Worker visa?",
            "Can I switch from Student to Graduate visa?",
            "What documents do I need for a Health and Care Worker visa?",
            "Am I eligible for Global Talent visa as a software engineer?",
            "What are the requirements for a Student visa?",
            "How long does the Graduate visa last?",
            "What is the minimum income for Family visa?",
        ],
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Uses LLM (Ollama) when available for ChatGPT-like responses,
    falls back to enhanced dialogue manager for rule-based responses.
    """
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    # Get or create session ID
    session_id = session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id
    
    # Log the interaction
    import hashlib
    input_hash = hashlib.sha256(user_message.encode()).hexdigest()[:16]
    audit_logger.log_message_received(session_id, input_hash)
    
    try:
        start_time = time.time()
        
        # Priority 1: Try Groq AI (if configured) - uses RAG for accuracy
        if groq_ai.available:
            try:
                response_text = groq_ai.chat(user_message, use_rag=True)
                if response_text is not None:
                    processing_time = (time.time() - start_time) * 1000
                    
                    audit_logger.log_event(AuditEvent(
                        event_type=AuditEventType.EXPLANATION_GENERATED,
                        session_id=session_id,
                        data={"response_preview": response_text[:500], "source": "groq_rag"}
                    ))
                    
                    return jsonify({
                        "response": response_text,
                        "session_id": session_id,
                        "intent": "groq_rag_generated",
                        "confidence": 0.95,
                        "entities": {},
                        "profile": {},
                        "processing_time_ms": round(processing_time, 2),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except Exception as e:
                logger.warning(f"Groq AI failed: {e}")
        
        # Priority 2: Try Ollama LLM for ChatGPT-like responses
        if chatbot.llm.available:
            try:
                response_text = chatbot.chat(user_message)
                if response_text is not None:
                    processing_time = (time.time() - start_time) * 1000
                    
                    audit_logger.log_event(AuditEvent(
                        event_type=AuditEventType.EXPLANATION_GENERATED,
                        session_id=session_id,
                        data={"response_preview": response_text[:500], "source": "llm"}
                    ))
                    
                    return jsonify({
                        "response": response_text,
                        "session_id": session_id,
                        "intent": "llm_generated",
                        "confidence": 0.95,
                        "entities": {},
                        "profile": {},
                        "processing_time_ms": round(processing_time, 2),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
            except Exception as e:
                logger.warning(f"Ollama LLM failed: {e}")
        
        # Fallback to enhanced dialogue manager for smart, conversational responses
        result = enhanced_dm.process_message(session_id, user_message)
        response_text = result["response"]
        processing_time = result.get("processing_time_ms", 0)
        
        # Log the response
        audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.EXPLANATION_GENERATED,
            session_id=session_id,
            data={"response_preview": response_text[:500], "source": "dialogue_manager"}
        ))
        
        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "intent": result.get("intent"),
            "confidence": result.get("confidence", 0.0),
            "entities": result.get("entities", {}),
            "profile": result.get("profile", {}),
            "processing_time_ms": processing_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            "error": "An error occurred while processing your message.",
            "details": str(e) if app.debug else None,
        }), 500


@app.route("/api/reset", methods=["POST"])
def reset_session():
    """Clear session data (GDPR compliance)."""
    session.clear()
    chatbot.llm.reset()
    return jsonify({"message": "Session cleared successfully."})


@app.route("/api/visas", methods=["GET"])
def list_visas():
    """List all supported visa types."""
    visas = [
        {
            "type": "skilled_worker",
            "name": "Skilled Worker Visa",
            "description": "For workers with a job offer from a UK licensed sponsor",
            "requirements": ["Sponsorship", "Salary threshold (£38,700)", "English language", "Eligible occupation"],
        },
        {
            "type": "health_care_worker",
            "name": "Health and Care Worker Visa",
            "description": "For NHS and adult social care workers",
            "requirements": ["Sponsorship from NHS/care provider", "Eligible health occupation", "Professional qualifications"],
        },
        {
            "type": "graduate",
            "name": "Graduate Visa",
            "description": "For UK university graduates to work post-study",
            "requirements": ["UK degree", "Current Student visa", "Study completion confirmation"],
        },
        {
            "type": "global_talent",
            "name": "Global Talent Visa",
            "description": "For leaders in academia, research, digital technology, and arts",
            "requirements": ["Endorsement from competent body", "Exceptional talent or promise"],
        },
        {
            "type": "student",
            "name": "Student Visa",
            "description": "For individuals who want to study in the UK",
            "requirements": ["CAS from licensed sponsor", "English proficiency", "Maintenance funds"],
        },
        {
            "type": "family",
            "name": "Family Visa",
            "description": "For partners and family members of UK residents",
            "requirements": ["Minimum income £18,600", "Genuine relationship", "English A1 level"],
        },
    ]
    return jsonify(visas)


@app.route("/api/eligibility", methods=["POST"])
def check_eligibility():
    """
    Check visa eligibility based on user profile.
    Supports all UK visa types - dynamically selects the appropriate rule engine.
    """
    data = request.get_json()
    
    visa_type = data.get("visa_type", "skilled_worker")
    
    profile = ApplicantProfile(
        job_title=data.get("job_title"),
        salary_annual=float(data.get("salary_annual", 0)),
        has_sponsor=data.get("has_sponsor"),
        country_of_origin=data.get("country_of_origin"),
        english_proficiency=data.get("english_proficiency"),
        age=data.get("age"),
        qualification=data.get("qualification"),
        visa_type=visa_type,
    )
    
    # Map visa types to their rule engines
    engines = {
        "skilled_worker": SkilledWorkerRuleEngine(),
        "health_care_worker": HealthCareWorkerRuleEngine(),
        "healthcare_worker": HealthCareWorkerRuleEngine(),  # Alias
        "graduate": GraduateRuleEngine(),
        "global_talent": GlobalTalentRuleEngine(),
        "student": StudentVisaRuleEngine(),
        "family": FamilyVisaRuleEngine(),
    }
    
    engine = engines.get(visa_type, SkilledWorkerRuleEngine())
    result = engine.check_eligibility(profile)
    
    return jsonify(result.to_dict())


@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    """Trigger GOV.UK scraping and knowledge base build."""
    try:
        pages = scraper.scrape_all(force_refresh=True)
        kb = scraper.build_knowledge_base()
        
        return jsonify({
            "status": "success",
            "pages_scraped": len(pages),
            "knowledge_base_chunks": len(kb.get("chunks", [])),
        })
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/occupations/search", methods=["GET"])
def search_occupations():
    """Search occupations by keyword."""
    from src.core.canonicalizer import canonicalizer
    
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    
    results = canonicalizer.soc_mapper.search(query, top_k=10)
    return jsonify(results)


@app.route("/api/update-data", methods=["POST"])
def update_data():
    """
    Update data from GOV.UK with smart change detection.
    Only updates pages that have actually changed.
    """
    try:
        data = request.get_json() or {}
        action = data.get("action", "update")
        
        if action == "check":
            # Just check for updates without applying them
            result = updater.check_for_updates(scraper)
            return jsonify(result)
        else:
            # Perform the update
            result = updater.update_data(scraper)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Update error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/api/update-status", methods=["GET"])
def get_update_status():
    """Get the last update status."""
    last_update = updater.get_last_update()
    return jsonify({
        "last_update": last_update.isoformat() if last_update else None,
        "has_been_updated": last_update is not None
    })


# ── Error Handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ── Main Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting Atlas AI...")
    logger.info(f"Ollama available: {chatbot.llm.available}")
    logger.info(f"Model: {chatbot.llm.model}")
    
    app.run(
        host=AtlasConfig.FLASK_HOST,
        port=AtlasConfig.FLASK_PORT,
        debug=AtlasConfig.FLASK_DEBUG,
    )