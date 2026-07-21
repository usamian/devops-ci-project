"""
Atlas AI — Enhanced Dialogue Manager
Full-fledged AI chatbot with casual conversation, smart decision-making,
and professional fallback responses.

Features:
- Natural, casual conversation style
- Smart intent detection with confidence scoring
- Context-aware responses based on GOV.UK knowledge
- Professional fallback when unsure
- Multi-turn conversation with memory
- Emotional intelligence and empathy
"""

from __future__ import annotations
import re
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Import visa recommender for best visa recommendations
from src.rule_engine.visa_recommender import VisaRecommender, get_visa_recommendation
from src.rule_engine.rules_base import ApplicantProfile


# ============================================================================
# CONVERSATION STATES
# ============================================================================

class ConversationState(str, Enum):
    """Conversation states for the dialogue manager."""
    GREETING = "greeting"
    CASUAL_CHAT = "casual_chat"
    INFORMATION_GATHERING = "information_gathering"
    ELIGIBILITY_CHECK = "eligibility_check"
    PROVIDING_ADVICE = "providing_advice"
    CLARIFYING = "clarifying"
    FALLBACK = "fallback"
    ENDING = "ending"


# ============================================================================
# INTENT TYPES
# ============================================================================

class IntentType(str, Enum):
    """Types of user intents the chatbot can recognize."""
    # Greetings and casual
    GREETING = "greeting"
    FAREWELL = "farewell"
    CASUAL_CHAT = "casual_chat"
    THANKS = "thanks"
    
    # Visa-related intents
    ELIGIBILITY_CHECK = "eligibility_check"
    VISA_INFORMATION = "visa_information"
    REQUIREMENTS_QUERY = "requirements_query"
    DOCUMENTS_QUERY = "documents_query"
    PROCESSING_TIME_QUERY = "processing_time_query"
    FEES_QUERY = "fees_query"
    SALARY_QUERY = "salary_query"
    
    # Specific visa types
    SKILLED_WORKER_VISA = "skilled_worker_visa"
    HEALTH_CARE_WORKER_VISA = "health_care_worker_visa"
    GRADUATE_VISA = "graduate_visa"
    GLOBAL_TALENT_VISA = "global_talent_visa"
    STUDENT_VISA = "student_visa"
    FAMILY_VISA = "family_visa"
    
    # Complex intents
    COMPARE_VISAS = "compare_visas"
    SWITCH_VISA = "switch_visa"
    EXTEND_VISA = "extend_visa"
    SETTLEMENT_ILR = "settlement_ilr"
    
    # Unknown
    UNKNOWN = "unknown"


# ============================================================================
# CONVERSATION CONTEXT
# ============================================================================

@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    intent: Optional[str] = None
    confidence: float = 1.0
    entities: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    """Maintains the full context of a conversation."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ConversationState = ConversationState.GREETING
    messages: List[Message] = field(default_factory=list)
    current_intent: Optional[IntentType] = None
    intent_confidence: float = 0.0
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    conversation_topic: Optional[str] = None
    last_intent: Optional[IntentType] = None
    clarification_attempts: int = 0
    max_clarification_attempts: int = 3
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the conversation history."""
        msg = Message(
            role=role,
            content=content,
            intent=kwargs.get("intent"),
            confidence=kwargs.get("confidence", 1.0),
            entities=kwargs.get("entities"),
        )
        self.messages.append(msg)
        self.last_active = datetime.utcnow()
    
    def get_recent_context(self, n: int = 5) -> str:
        """Get the last n messages as context string."""
        recent = self.messages[-n:] if len(self.messages) >= n else self.messages
        return "\n".join([f"{m.role}: {m.content}" for m in recent])
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if the conversation has expired."""
        return datetime.utcnow() - self.last_active > timedelta(minutes=timeout_minutes)


# ============================================================================
# ENHANCED INTENT CLASSIFIER
# ============================================================================

class EnhancedIntentClassifier:
    """
    Enhanced intent classifier with:
    - Pattern matching for common intents
    - Keyword-based classification
    - Confidence scoring
    - Context-aware disambiguation
    """
    
    # Intent patterns with regex
    PATTERNS = {
        IntentType.GREETING: [
            r"\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b",
            r"\b(howdy|sup|yo|what's?\s+up)\b",
        ],
        IntentType.FAREWELL: [
            r"\b(bye|goodbye|see\s+you|take\s+care|later|gtg)\b",
            r"\b(have\s+a\s+(nice\s+)?day|catch\s+you\s+later)\b",
        ],
        IntentType.THANKS: [
            r"\b(thanks?|thank\s+you|much\s+appreciated|cheers)\b",
            r"\b(i\s+appreciate\s+(it|that|your\s+help))\b",
        ],
        IntentType.ELIGIBILITY_CHECK: [
            r"\b(am\s+i\s+)?eligible\s*(for\s+(a\s+)?(.+\s+visa))?\b",
            r"\b(can\s+i\s+)?(apply\s+for|get)\s+(a\s+)?(.+\s+visa)\b",
            r"\b(do\s+i\s+)?qualify\s+(for\s+(a\s+)?(.+\s+visa))?\b",
            r"\b(what\s+are\s+my\s+)?chances\s+(of\s+getting)?\s+(a\s+)?visa\b",
            r"\b(check\s+my\s+)?eligibility\b",
        ],
        IntentType.SALARY_QUERY: [
            r"\b(salary|wages|pay|earnings|income)\s*(requirement|threshold|needed|enough)?\b",
            r"\b(how\s+much\s+do\s+i\s+need\s+to\s+earn)\b",
            r"\b(minimum\s+salary)\b",
        ],
        IntentType.DOCUMENTS_QUERY: [
            r"\b(documents?|paperwork|evidence|proof)\s*(needed|required|for\s+visa)?\b",
            r"\b(what\s+do\s+i\s+need\s+to\s+submit|provide)\b",
            r"\b(document\s+checklist|list\s+of\s+documents)\b",
        ],
        IntentType.PROCESSING_TIME_QUERY: [
            r"\b(how\s+long\s+does?\s+it\s+take|processing\s+time|wait\s+time)\b",
            r"\b(when\s+will\s+i\s+get\s+a\s+decision)\b",
            r"\b(how\s+many\s+(weeks|months|days)\s+does?\s+it\s+take)\b",
        ],
        IntentType.FEES_QUERY: [
            r"\b(how\s+much\s+does?\s+it\s+cost|fees?|cost|price)\b",
            r"\b(application\s+fee|visa\s+fee|total\s+cost)\b",
            r"\b(health\s+surcharge|ihs)\b",
        ],
        IntentType.CASUAL_CHAT: [
            r"\b(how\s+are\s+you|how's\s+it\s+going|what's\s+up)\b",
            r"\b(can\s+you\s+)?(help\s+me|assist\s+me)\b",
            r"\b(tell\s+me\s+about|explain\s+to\s+me)\b",
            r"\b(i\s+have\s+a\s+question|i\s+wonder)\b",
            r"\b(what\s+can\s+you\s+do|who\s+are\s+you)\b",
        ],
        IntentType.SWITCH_VISA: [
            r"\b(switch|change|convert)\s+(from\s+)?(.+\s+visa)?\s+to\s+(.+\s+visa)?\b",
            r"\b(can\s+i\s+switch\s+my\s+visa)\b",
        ],
        IntentType.EXTEND_VISA: [
            r"\b(extend|renew|prolong)\s+(my\s+)?visa\b",
            r"\b(my\s+visa\s+is\s+expiring|about\s+to\s+expire)\b",
        ],
        IntentType.SETTLEMENT_ILR: [
            r"\b(ilr|indefinite\s+leave\s+to\s+remain|settlement|permanent\s+residence)\b",
            r"\b(become\s+a\s+(british\s+)?citizen|citizenship)\b",
            r"\b(how\s+long\s+to\s+settle|years\s+to\s+ilr)\b",
        ],
        IntentType.COMPARE_VISAS: [
            r"\b(difference\s+between|compare)\s+(.+\s+and\s+.+)\b",
            r"\b(which\s+visa\s+is\s+better|what\s+visa\s+should\s+i\s+choose)\b",
        ],
    }
    
    # Keywords for each intent (fallback when patterns don't match)
    KEYWORDS = {
        IntentType.GREETING: ["hi", "hello", "hey", "good morning", "good afternoon"],
        IntentType.FAREWELL: ["bye", "goodbye", "see you", "take care"],
        IntentType.THANKS: ["thanks", "thank you", "appreciate"],
        IntentType.ELIGIBILITY_CHECK: ["eligible", "eligibility", "qualify", "can i apply", "am i eligible"],
        IntentType.SALARY_QUERY: ["salary", "wages", "earnings", "threshold", "minimum wage"],
        IntentType.DOCUMENTS_QUERY: ["documents", "paperwork", "evidence", "proof", "checklist"],
        IntentType.PROCESSING_TIME_QUERY: ["processing", "how long", "wait", "decision time"],
        IntentType.FEES_QUERY: ["fees", "cost", "price", "how much", "ihs", "surcharge"],
        IntentType.SWITCH_VISA: ["switch", "change visa", "convert"],
        IntentType.EXTEND_VISA: ["extend", "renew", "expiring"],
        IntentType.SETTLEMENT_ILR: ["ilr", "settlement", "citizenship", "permanent"],
        IntentType.COMPARE_VISAS: ["compare", "difference", "which is better"],
    }
    
    def classify(self, text: str, context: Optional[ConversationContext] = None) -> Dict[str, Any]:
        """
        Classify user intent with confidence scoring.
        
        Returns:
            Dict with 'intent', 'confidence', and 'method' (pattern/keyword/fallback)
        """
        text_lower = text.lower().strip()
        
        if not text_lower:
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "method": "empty",
            }
        
        # Score each intent based on patterns
        scores = {}
        for intent, patterns in self.PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    score += len(matches) * 3.0
            scores[intent] = score
        
        # Add keyword scores
        for intent, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[intent] = scores.get(intent, 0) + 1.0
        
        # Get the best match
        if not scores or max(scores.values()) == 0:
            # Check context for follow-up
            if context and context.current_intent:
                return {
                    "intent": context.current_intent,
                    "confidence": 0.5,
                    "method": "context_followup",
                }
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "method": "fallback",
            }
        
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        total_score = max(sum(scores.values()), 1)
        
        # Calculate confidence
        confidence = min(0.99, best_score / total_score)
        
        # Determine method
        if best_score >= 5:
            method = "pattern"
            confidence = max(confidence, 0.85)
        elif best_score >= 2:
            method = "keyword"
            confidence = max(confidence, 0.65)
        else:
            method = "fallback"
            confidence = max(confidence, 0.40)
        
        return {
            "intent": best_intent,
            "confidence": round(confidence, 4),
            "method": method,
            "all_scores": scores,
        }


# ============================================================================
# ENHANCED ENTITY EXTRACTOR
# ============================================================================

class EnhancedEntityExtractor:
    """
    Enhanced entity extractor for UK visa domain.
    Extracts structured information from user messages.
    """
    
    # Countries for nationality extraction
    COUNTRIES = {
        "india", "pakistan", "bangladesh", "nigeria", "philippines",
        "china", "usa", "united states", "uk", "united kingdom",
        "canada", "australia", "new zealand", "south africa",
        "kenya", "ghana", "zimbabwe", "sri lanka", "nepal",
        "malaysia", "singapore", "japan", "south korea",
        "germany", "france", "spain", "italy", "poland",
        "romania", "bulgaria", "hungary", "ireland",
        "uae", "saudi arabia", "egypt", "turkey",
    }
    
    # Job titles commonly associated with Skilled Worker visa
    JOB_TITLES = [
        "software engineer", "software developer", "data scientist", "data analyst",
        "machine learning engineer", "devops engineer", "cloud engineer",
        "backend developer", "frontend developer", "full stack developer",
        "nurse", "doctor", "physician", "pharmacist", "dentist",
        "physiotherapist", "occupational therapist", "speech therapist",
        "civil engineer", "mechanical engineer", "electrical engineer",
        "teacher", "lecturer", "professor",
        "accountant", "financial analyst", "management consultant",
        "business analyst", "project manager", "it manager",
        "solicitor", "barrister", "lawyer",
        "architect", "chef", "social worker",
    ]
    
    # Visa types
    VISA_TYPES = {
        "skilled worker", "tier 2",
        "health and care worker", "health care", "nhs",
        "graduate", "post study",
        "global talent", "exceptional talent",
        "student", "tier 4",
        "family", "spouse", "partner",
        "innovator", "start-up",
        "visitor", "tourist",
    }
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from user text.
        
        Returns dict with extracted entities like:
        - job_title
        - salary
        - country
        - visa_type
        - sponsorship
        - english_proficiency
        - qualification
        - age
        """
        entities = {}
        text_lower = text.lower()
        
        # Extract salary
        salary_match = re.search(
            r'[\xa3$]?\s*(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|kb|000)?\s*(?:per\s+)?(?:year|annum|yr|pa)?',
            text, re.IGNORECASE
        )
        if salary_match:
            salary_str = salary_match.group(1).replace(',', '')
            salary = float(salary_str)
            # Check if it's in thousands (e.g., "50k")
            context = text[salary_match.start():salary_match.end()+10].lower()
            if 'k' in context or '000' in salary_str:
                salary *= 1000
            if salary > 10000:  # Reasonable salary threshold
                entities['salary'] = int(salary)
        
        # Extract country
        for country in sorted(self.COUNTRIES, key=len, reverse=True):
            if re.search(r'\b' + re.escape(country) + r'\b', text_lower):
                entities['country'] = country.title()
                break
        
        # Extract job title
        for job in sorted(self.JOB_TITLES, key=len, reverse=True):
            if job in text_lower:
                entities['job_title'] = job.title()
                break
        
        # Extract visa type
        for visa in sorted(self.VISA_TYPES, key=len, reverse=True):
            if visa in text_lower:
                entities['visa_type'] = visa
                break
        
        # Extract sponsorship status
        if any(kw in text_lower for kw in ["have sponsor", "with sponsor", "sponsored", "cos", "certificate of sponsorship"]):
            entities['sponsorship'] = True
        elif any(kw in text_lower for kw in ["no sponsor", "without sponsor", "not sponsored", "don't have sponsor"]):
            entities['sponsorship'] = False
        
        # Extract English proficiency
        if any(kw in text_lower for kw in ["ielts", "toefl", "pte", "english test passed"]):
            entities['english_proficiency'] = "test_passed"
        elif any(kw in text_lower for kw in ["native english", "degree in english", "uk educated"]):
            entities['english_proficiency'] = "exempt"
        
        # Extract qualification
        if any(kw in text_lower for kw in ["phd", "doctorate"]):
            entities['qualification'] = "PhD"
        elif any(kw in text_lower for kw in ["master", "msc", "m.sc", "mba"]):
            entities['qualification'] = "Master's"
        elif any(kw in text_lower for kw in ["bachelor", "bsc", "b.sc", "degree"]):
            entities['qualification'] = "Bachelor's"
        
        # Extract age
        age_match = re.search(r'\b(\d{2})\s*(?:years?\s+old|yo)?\b', text_lower)
        if age_match:
            age = int(age_match.group(1))
            if 18 <= age <= 80:
                entities['age'] = age
        
        return entities


# ============================================================================
# RESPONSE GENERATOR
# ============================================================================

class ResponseGenerator:
    """
    Generates natural, conversational responses with:
    - Casual, friendly tone
    - Professional accuracy
    - Context awareness
    - Appropriate disclaimers
    """
    
    # Casual greeting responses
    GREETINGS = [
        "Hey there! 👋 I'm Atlas, your UK immigration assistant. How can I help you today?",
        "Hello! Great to meet you. I'm here to help with anything UK visa-related. What's on your mind?",
        "Hi! Welcome to Atlas AI. Whether you're curious about visas or ready to check your eligibility, I've got you covered!",
        "Hey! I'm Atlas, your friendly UK visa expert. Ready to help you navigate the immigration system. What would you like to know?",
    ]
    
    # Casual farewell responses
    FAREWELLS = [
        "Take care! Feel free to come back anytime you have questions. Good luck with your UK visa journey! 🍀",
        "Bye! Remember, I'm always here if you need help. Best of luck! 🇬🇧",
        "See you later! Don't hesitate to return if anything comes up. Have a great day!",
        "Cheers! Wishing you all the best with your immigration plans. Come back soon!",
    ]
    
    # Thanks responses
    THANKS_RESPONSES = [
        "You're very welcome! 😊 That's what I'm here for. Anything else I can help with?",
        "Happy to help! Don't hesitate to ask if you have more questions.",
        "Anytime! I'm glad I could assist. Is there anything else on your mind?",
        "No problem at all! Feel free to ask away if you need more info.",
    ]
    
    # Smart fallback responses - context-aware and varied
    FALLBACK_RESPONSES = [
        # General fallbacks
        "I appreciate you asking, but I want to be completely honest — I'm not entirely sure about that specific detail. "
        "For the most accurate and up-to-date information, I'd recommend checking the official GOV.UK website or consulting "
        "with a qualified immigration adviser. That said, I'd be happy to help with anything related to visa eligibility, "
        "requirements, or the application process!",
        
        "That's a great question, and I wish I had a definitive answer for you. However, this particular topic might require "
        "more specialized expertise than I can provide. I'd suggest reaching out to an OISC-registered immigration adviser "
        "or checking the official guidance on GOV.UK. Is there anything else about UK visas I can help you with?",
        
        # Context-aware fallbacks with suggestions
        "I want to make sure I give you accurate information, and I'm not 100% confident about this specific point. "
        "Immigration rules can be quite nuanced, and it's always best to verify with official sources. "
        "The GOV.UK website has comprehensive guidance, or you could speak with an immigration solicitor. "
        "In the meantime, I'm here to help with eligibility checks, document requirements, processing times, and more!",
        
        # Educational fallbacks
        "That's an interesting question! While I can't give you a definitive answer on this specific point, "
        "I can share some general guidance. UK immigration rules are complex and change frequently. "
        "For the most reliable information, please check GOV.UK or consult with an immigration specialist. "
        "Is there a different aspect of UK visas I can help you with?",
        
        # Helpful redirection fallbacks - NOW INCLUDES ALL VISA TYPES
        "I don't want to give you potentially incorrect information on this topic. Immigration advice should always come "
        "from verified sources. However, I CAN help you with:\n\n"
        "• Checking your visa eligibility\n"
        "• Understanding document requirements\n"
        "• Explaining processing times\n"
        "• Breaking down visa fees\n"
        "• Answering questions about Skilled Worker, Health and Care Worker, Graduate, Global Talent, Student, and Family visas\n\n"
        "Would any of these be helpful?",
    ]
    
    # Clarification questions when the query is unclear
    CLARIFICATION_QUESTIONS = [
        "Could you please provide more details about your question? For example, which visa type are you asking about?",
        "I want to make sure I understand correctly. Are you asking about eligibility requirements, documents, or processing times?",
        "That's an interesting question. Could you tell me a bit more about your specific situation? For instance, what visa are you currently on or planning to apply for?",
        "To give you the most helpful answer, I need to understand your context better. Are you asking about a specific visa type or a general immigration process?",
    ]
    
    # Topic-specific guidance when unsure
    TOPIC_GUIDANCE = {
        "eligibility": "While I can't give a definitive answer on your specific eligibility without more details, "
                      "I can tell you that Skilled Worker visa requires a salary of at least £38,700, a job offer from "
                      "a licensed sponsor, and English proficiency. Would you like me to check your eligibility based on your profile?",
        
        "documents": "Document requirements vary by visa type. Generally, you'll need a valid passport, Certificate of Sponsorship, "
                    "proof of English, and financial evidence. For a complete checklist, I'd recommend checking the official GOV.UK "
                    "guidance for your specific visa type. Would you like me to help with something else?",
        
        "processing": "Processing times depend on whether you're applying from inside or outside the UK. Standard times are "
                     "3 weeks from outside UK and 8 weeks from inside UK. Priority services are available for faster decisions. "
                     "For the most current processing times, please check GOV.UK.",
        
        "fees": "Visa fees vary by type and duration. For example, Skilled Worker visa costs £719 for up to 3 years or £1,420 "
               "for more than 3 years, plus the Immigration Health Surcharge of £1,035 per year. For exact fees, please check "
               "the official GOV.UK fee calculator.",
    }
    
    # Casual chat responses
    CASUAL_RESPONSES = {
        "how_are_you": [
            "I'm doing great, thanks for asking! 😊 Ready to help you with all things UK immigration. How about you?",
            "I'm good! Just here, ready to assist with your visa questions. What can I do for you today?",
            "Doing well! Always excited to help someone navigate their UK visa journey. What's on your mind?",
        ],
        "who_are_you": [
            "I'm Atlas AI, your friendly UK immigration assistant! I'm here to help you understand visa requirements, "
            "check your eligibility, and guide you through the application process. Think of me as your personal "
            "immigration guide — minus the accent! 🗺️",
            "Great question! I'm Atlas, an AI assistant specialized in UK immigration. I can help you with visa eligibility, "
            "requirements, documents, and answer all sorts of questions about moving to the UK. What would you like to know?",
        ],
        "what_can_you_do": [
            "I can help you with quite a bit! Here's what I do best:\n\n"
            "🎯 Check your visa eligibility\n"
            "📋 Explain document requirements\n"
            "⏱️ Share processing times\n"
            "💰 Break down visa fees\n"
            "📚 Provide information from official GOV.UK guidance\n\n"
            "Basically, anything UK visa-related, I'm your person! What would you like to start with?",
        ],
    }
    
    def __init__(self):
        self.greeting_index = 0
        self.farewell_index = 0
    
    def generate_greeting(self) -> str:
        """Generate a greeting response."""
        response = self.GREETINGS[self.greeting_index % len(self.GREETINGS)]
        self.greeting_index += 1
        return response
    
    def generate_farewell(self) -> str:
        """Generate a farewell response."""
        response = self.FAREWELLS[self.farewell_index % len(self.FAREWELLS)]
        self.farewell_index += 1
        return response
    
    def generate_thanks_response(self) -> str:
        """Generate a response to thanks."""
        import random
        return random.choice(self.THANKS_RESPONSES)
    
    def generate_fallback(self, context: Optional[ConversationContext] = None) -> str:
        """Generate a professional fallback response when unsure."""
        import random
        base_response = random.choice(self.FALLBACK_RESPONSES)
        
        # Add context-specific guidance if available
        if context and context.current_intent:
            base_response += f"\n\nI can definitely help you with {context.current_intent.value.replace('_', ' ')} though! "
            base_response += "Just let me know what specific information you need."
        
        return base_response
    
    def generate_casual_response(self, intent: str, context: Optional[ConversationContext] = None) -> str:
        """Generate a casual conversation response."""
        import random
        
        if "how_are_you" in intent or "how's it" in intent:
            return random.choice(self.CASUAL_RESPONSES["how_are_you"])
        elif "who are you" in intent or "what are you" in intent:
            return random.choice(self.CASUAL_RESPONSES["who_are_you"])
        elif "what can you do" in intent or "help me" in intent:
            return random.choice(self.CASUAL_RESPONSES["what_can_you_do"])
        else:
            return "That's interesting! Tell me more about what you're looking for. I'm here to help with anything UK visa-related!"
    
    def add_disclaimer(self, response: str) -> str:
        """Add a professional disclaimer to the response."""
        disclaimer = (
            "\n\n---\n⚠️ **Disclaimer:** This information is for guidance purposes only and does not constitute legal advice. "
            "Immigration rules change frequently. Always verify information on the official GOV.UK website or consult with "
            "a qualified immigration adviser before making any decisions."
        )
        return response + disclaimer


# ============================================================================
# ENHANCED DIALOGUE MANAGER
# ============================================================================

class EnhancedDialogueManager:
    """
    Enhanced dialogue manager with:
    - Natural conversation flow
    - Smart decision making
    - Context awareness
    - Professional fallbacks
    - Multi-turn memory
    """
    
    def __init__(self):
        self.intent_classifier = EnhancedIntentClassifier()
        self.entity_extractor = EnhancedEntityExtractor()
        self.response_generator = ResponseGenerator()
        self.sessions: Dict[str, ConversationContext] = {}
        
        # Knowledge base for RAG (can be populated from GOV.UK scraper)
        self.knowledge_base: Dict[str, Any] = {}
    
    def get_or_create_session(self, session_id: str) -> ConversationContext:
        """Get or create a conversation session."""
        if session_id not in self.sessions or self.sessions[session_id].is_expired():
            self.sessions[session_id] = ConversationContext(session_id=session_id)
        return self.sessions[session_id]
    
    def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Main entry point for processing user messages.
        
        Args:
            session_id: Unique session identifier
            user_message: User's input message
            
        Returns:
            Dict with response, state, session_id, and other metadata
        """
        start_time = datetime.utcnow()
        
        # Get or create session
        context = self.get_or_create_session(session_id)
        
        # Handle special commands
        if user_message.lower().strip() in ["reset", "start over", "new conversation", "clear"]:
            self.sessions[session_id] = ConversationContext(session_id=session_id)
            context = self.sessions[session_id]
            response = self.response_generator.generate_greeting()
            return self._create_response(context, response, start_time)
        
        # Add user message to context
        context.add_message("user", user_message)
        
        # Classify intent
        intent_result = self.intent_classifier.classify(user_message, context)
        context.current_intent = intent_result["intent"]
        context.intent_confidence = intent_result["confidence"]
        
        # Extract entities
        entities = self.entity_extractor.extract(user_message)
        context.extracted_entities.update(entities)
        
        # Update user profile with extracted entities
        self._update_profile(context, entities)
        
        # Generate response based on intent
        response = self._generate_response(context, user_message, intent_result, entities)
        
        # Add assistant response to context
        context.add_message(
            "assistant",
            response,
            intent=intent_result["intent"].value,
            confidence=intent_result["confidence"],
        )
        
        return self._create_response(context, response, start_time)
    
    def _update_profile(self, context: ConversationContext, entities: Dict[str, Any]):
        """Update user profile with extracted entities."""
        for key, value in entities.items():
            if value is not None:
                context.user_profile[key] = value
    
    def _generate_response(
        self,
        context: ConversationContext,
        user_message: str,
        intent_result: Dict[str, Any],
        entities: Dict[str, Any],
    ) -> str:
        """Generate appropriate response based on intent and context."""
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # Handle different intents
        if intent == IntentType.GREETING:
            return self.response_generator.generate_greeting()
        
        elif intent == IntentType.FAREWELL:
            return self.response_generator.generate_farewell()
        
        elif intent == IntentType.THANKS:
            return self.response_generator.generate_thanks_response()
        
        elif intent == IntentType.CASUAL_CHAT:
            # Check for specific casual patterns
            text_lower = user_message.lower()
            if any(kw in text_lower for kw in ["how are you", "how's it going"]):
                return self.response_generator.generate_casual_response("how_are_you", context)
            elif any(kw in text_lower for kw in ["who are you", "what are you"]):
                return self.response_generator.generate_casual_response("who_are_you", context)
            elif any(kw in text_lower for kw in ["what can you do", "help me"]):
                return self.response_generator.generate_casual_response("what_can_you_do", context)
            else:
                return self.response_generator.generate_casual_response("general", context)
        
        elif intent == IntentType.UNKNOWN or confidence < 0.5:
            # Low confidence or unknown intent - use fallback
            return self.response_generator.generate_fallback(context)
        
        elif intent == IntentType.ELIGIBILITY_CHECK:
            return self._handle_eligibility_check(context, user_message, entities)
        
        elif intent in [IntentType.SALARY_QUERY, IntentType.DOCUMENTS_QUERY,
                        IntentType.PROCESSING_TIME_QUERY, IntentType.FEES_QUERY]:
            return self._handle_informational_query(context, intent, entities)
        
        elif intent in [IntentType.SWITCH_VISA, IntentType.EXTEND_VISA,
                        IntentType.SETTLEMENT_ILR, IntentType.COMPARE_VISAS]:
            return self._handle_complex_query(context, intent, user_message)
        
        else:
            # Default to informational response with RAG if available
            return self._handle_informational_query(context, intent, entities)
    
    def _handle_eligibility_check(
        self,
        context: ConversationContext,
        user_message: str,
        entities: Dict[str, Any],
    ) -> str:
        """Handle eligibility check requests."""
        profile = context.user_profile
        
        # Check if we have enough information
        required_fields = ["job_title", "salary", "sponsorship", "country"]
        missing_fields = [f for f in required_fields if f not in profile]
        
        if missing_fields:
            # Ask for missing information
            field = missing_fields[0]
            questions = {
                "job_title": "What's your job title or the role you've been offered in the UK?",
                "salary": "What's the annual salary in GBP? (e.g., £45,000 or 45k)",
                "sponsorship": "Do you have a Certificate of Sponsorship from a UK employer? (Yes/No)",
                "country": "Which country are you from?",
            }
            return questions.get(field, f"Could you please provide your {field}?")
        
        # We have enough info - provide eligibility assessment
        # In a full implementation, this would call the rule engine
        return self._provide_eligibility_assessment(context)
    
    def _handle_informational_query(
        self,
        context: ConversationContext,
        intent: IntentType,
        entities: Dict[str, Any],
    ) -> str:
        """Handle informational queries (processing times, fees, etc.).
        Now provides dynamic responses based on detected visa type.
        """
        # Detect visa type from entities or user profile
        visa_type = context.extracted_entities.get("visa_type", "").lower()
        if not visa_type and "visa_type" in context.user_profile:
            visa_type = context.user_profile["visa_type"].lower()
        
        # Check for specific visa type keywords in the conversation
        if not visa_type:
            recent_context = context.get_recent_context(3).lower()
            if "health" in recent_context or "care" in recent_context or "nhs" in recent_context or "nurse" in recent_context or "doctor" in recent_context:
                visa_type = "health_care_worker"
            elif "graduate" in recent_context or "post-study" in recent_context:
                visa_type = "graduate"
            elif "talent" in recent_context or "exceptional" in recent_context or "research" in recent_context:
                visa_type = "global_talent"
            elif "student" in recent_context or "study" in recent_context or "university" in recent_context:
                visa_type = "student"
            elif "family" in recent_context or "spouse" in recent_context or "partner" in recent_context:
                visa_type = "family"
            elif "skilled" in recent_context or "work" in recent_context or "sponsor" in recent_context:
                visa_type = "skilled_worker"
        
        intent_name = intent.value.replace("_", " ")
        
        # Visa-specific responses
        responses = self._get_visa_specific_responses(visa_type, intent_name, entities)
        
        response = responses.get(intent_name, 
            f"I can help you with {intent_name}. Could you tell me more specifically what you'd like to know? "
            f"If you're asking about a specific visa type, please mention it so I can provide more accurate information.")
        
        return self.response_generator.add_disclaimer(response)
    
    def _get_visa_specific_responses(self, visa_type: str, intent_name: str, entities: Dict[str, Any]) -> Dict[str, str]:
        """Get responses specific to each visa type."""
        
        if visa_type == "health_care_worker":
            return {
                "salary query": "Good news! Health and Care Worker visa holders are exempt from the general salary threshold of £38,700. "
                              "Instead, you must meet the 'going rate' for your specific health occupation, which is typically lower. "
                              "For example, nurses start around £28,000-£35,000 depending on experience and location.",
                
                "documents query": "For Health and Care Worker visa, you'll need: a valid passport, Certificate of Sponsorship from an NHS or approved care provider, "
                                 "proof of professional qualifications (NMC registration for nurses, GMC for doctors), proof of English language, "
                                 "and a TB test certificate if from a listed country. You may also need proof of maintenance funds.",
                
                "processing time query": "Health and Care Worker visas typically have faster processing times:\n"
                                        "• From outside UK: Usually 3 weeks\n"
                                        "• From inside UK: Usually 8 weeks\n\n"
                                        "Priority services are available:\n"
                                        "• 5-day priority: +£500\n"
                                        "• 1-day super priority: +£800 (in-country only)",
                
                "fees query": "Health and Care Worker visa fees (as of 2024):\n"
                            "• Application fee: £284 (up to 3 years) or £556 (more than 3 years)\n"
                            "• Immigration Health Surcharge (IHS): £0 - EXEMPT!\n\n"
                            "This makes it much cheaper than other work visas. Example for a 5-year visa: £556 total.",
            }
        
        elif visa_type == "graduate":
            return {
                "salary query": "The Graduate visa has no salary requirement! You can work in any job at any salary level, "
                              "or even be self-employed. This is one of the key benefits of the Graduate route.",
                
                "documents query": "For Graduate visa, you'll need: a valid passport, Confirmation of Acceptance for Studies (CAS) from your university, "
                                 "proof that you've completed your course (your university will notify the Home Office), "
                                 "and proof you held a Student visa. No sponsor or job offer is required.",
                
                "processing time query": "Graduate visa processing times:\n"
                                        "• From inside UK: Usually 8 weeks\n\n"
                                        "Priority services are available:\n"
                                        "• 5-day priority: +£500\n"
                                        "• 1-day super priority: +£800",
                
                "fees query": "Graduate visa fees (as of 2024):\n"
                            "• Application fee: £822\n"
                            "• Immigration Health Surcharge (IHS): £1,035 per year\n\n"
                            "Example for a 2-year visa: £822 + (£1,035 × 2) = £2,892 total.",
            }
        
        elif visa_type == "global_talent":
            return {
                "salary query": "The Global Talent visa has no minimum salary requirement! You can work for any employer, "
                              "be self-employed, or start your own business. Your income is not restricted.",
                
                "documents query": "For Global Talent visa, you'll need: a valid passport, endorsement letter from a designated competent body "
                                 "(Tech Nation for digital technology, UKRI for academia/research, or Arts Council for arts/culture), "
                                 "and evidence of your exceptional talent or promise in your field.",
                
                "processing time query": "Global Talent visa processing times:\n"
                                        "• From outside UK: Usually 3 weeks\n"
                                        "• From inside UK: Usually 8 weeks\n\n"
                                        "Priority services are available:\n"
                                        "• 5-day priority: +£500\n"
                                        "• 1-day super priority: +£800 (in-country only)",
                
                "fees query": "Global Talent visa fees (as of 2024):\n"
                            "• Application fee: £716\n"
                            "• Immigration Health Surcharge (IHS): £1,035 per year\n\n"
                            "Example for a 5-year visa: £716 + (£1,035 × 5) = £5,891 total.",
            }
        
        elif visa_type == "student":
            return {
                "salary query": "Student visa holders can work part-time (up to 20 hours per week during term, full-time during vacations) "
                              "but there's no minimum salary requirement. However, you cannot be self-employed or work as a professional sportsperson.",
                
                "documents query": "For Student visa, you'll need: a valid passport, Confirmation of Acceptance for Studies (CAS) from your university/college, "
                                 "proof of English language proficiency (usually IELTS/TOEFL/PTE), proof of maintenance funds "
                                 "(£1,334/month in London, £1,023/month outside London for up to 9 months), and ATAS certificate if required.",
                
                "processing time query": "Student visa processing times:\n"
                                        "• From outside UK: Usually 3 weeks\n"
                                        "• From inside UK: Usually 8 weeks\n\n"
                                        "Priority services are available:\n"
                                        "• 5-day priority: +£500\n"
                                        "• 1-day super priority: +£800 (in-country only)",
                
                "fees query": "Student visa fees (as of 2024):\n"
                            "• Application fee: £490\n"
                            "• Immigration Health Surcharge (IHS): £776 per year\n\n"
                            "Example for a 3-year course: £490 + (£776 × 3) = £2,818 total.",
            }
        
        elif visa_type == "family":
            return {
                "salary query": "For Family visa, the main financial requirement is a minimum income of £18,600 per year. "
                              "This increases to £22,400 if you have one child, and an additional £2,400 for each further child. "
                              "The income can come from employment, self-employment, savings, or pensions.",
                
                "documents query": "For Family visa, you'll need: a valid passport, proof of your relationship (marriage certificate, birth certificate), "
                                 "proof of your partner's UK status (British passport, ILR, etc.), financial evidence showing you meet the income requirement, "
                                 "proof of adequate accommodation, and English language proof (A1 level for partners).",
                
                "processing time query": "Family visa processing times:\n"
                                        "• From outside UK: Usually 24 weeks (6 months)\n"
                                        "• From inside UK: Usually 8 weeks\n\n"
                                        "Priority services are available:\n"
                                        "• 5-day priority: +£500\n"
                                        "• 1-day super priority: +£800 (in-country only)",
                
                "fees query": "Family visa fees (as of 2024):\n"
                            "• Application fee: £1,846 (from outside UK) or £1,209 (from inside UK)\n"
                            "• Immigration Health Surcharge (IHS): £1,035 per year\n\n"
                            "Example for a 2.5-year visa from outside UK: £1,846 + (£1,035 × 2.5) = £4,433.50 total.",
            }
        
        else:  # Default to Skilled Worker or general
            return {
                "salary query": "The general salary threshold for a Skilled Worker visa is £38,700 per year. "
                              "However, you must also meet the 'going rate' for your specific occupation, "
                              "which could be higher. New entrants (under 26 or recent graduates) may qualify "
                              "with a lower threshold of £30,960.",
                
                "documents query": "You'll typically need: a valid passport, Certificate of Sponsorship reference number, "
                                 "proof of English language (IELTS/TOEFL/PTE), proof of salary (contract/payslips), "
                                 "and bank statements showing £1,270 held for 28+ days (unless your sponsor certifies maintenance). "
                                 "You may also need a TB test certificate depending on your country.",
                
                "processing time query": "Standard processing times are:\n"
                                        "• From outside UK: Usually 3 weeks\n"
                                        "• From inside UK: Usually 8 weeks\n\n"
                                        "Priority services are available:\n"
                                        "• 5-day priority: +£500\n"
                                        "• 1-day super priority: +£800 (in-country only)",
                
                "fees query": "Current fees (as of 2024):\n"
                            "• Application fee: £719 (up to 3 years) or £1,420 (more than 3 years)\n"
                            "• Immigration Health Surcharge (IHS): £1,035 per year\n\n"
                            "Example for a 5-year visa: £1,420 + (£1,035 × 5) = £6,595 total.",
            }
    
    def _handle_complex_query(
        self,
        context: ConversationContext,
        intent: IntentType,
        user_message: str,
    ) -> str:
        """Handle complex queries requiring detailed explanation."""
        intent_name = intent.value.replace("_", " ")
        
        responses = {
            "switch visa": "Yes, you can often switch visas from inside the UK, but it depends on your current visa type. "
                          "For example, you can usually switch from a Student visa to a Skilled Worker visa, or from "
                          "a Graduate visa to various work visas. Some visas (like Visitor visas) generally cannot be switched. "
                          "What visa are you currently on, and what would you like to switch to?",
            
            "extend visa": "To extend your visa, you'll need to apply before your current visa expires. "
                          "The requirements are generally similar to your initial application, but you'll need to show "
                          "you've been complying with your current visa conditions. Processing times are typically 8 weeks "
                          "for in-country applications. Would you like specific information about extending a particular visa type?",
            
            "settlement ilr": "Indefinite Leave to Remain (ILR) is typically available after 5 years on most work visas "
                            "(Skilled Worker, Health and Care Worker, Global Talent). You'll need to meet requirements including:\n"
                            "• Continuous residence in the UK\n"
                            "• Meeting the Life in the UK test\n"
                            "• English language at B1 level\n"
                            "• Not exceeding absence limits (usually 180 days per year)\n\n"
                            "After ILR, you can apply for British citizenship after 12 months.",
            
            "compare visas": "Different visas serve different purposes:\n\n"
                           "• **Skilled Worker**: For those with a job offer from a licensed sponsor\n"
                           "• **Health and Care Worker**: For NHS and care workers (lower fees, faster processing)\n"
                           "• **Graduate**: For UK graduates to work for 2-3 years post-study\n"
                           "• **Global Talent**: For leaders in academia, research, or digital technology\n\n"
                           "The best visa depends on your situation. What's your background and what are you looking to do in the UK?",
        }
        
        response = responses.get(intent_name,
            f"That's an important question about {intent_name}. Let me provide some guidance... "
            f"For the most accurate advice, I'd recommend checking the official GOV.UK guidance or consulting "
            f"with an immigration specialist.")
        
        return self.response_generator.add_disclaimer(response)
    
    def _provide_eligibility_assessment(self, context: ConversationContext) -> str:
        """Provide a detailed eligibility assessment based on the detected visa type."""
        profile = context.user_profile
        
        # Detect visa type from context
        visa_type = context.extracted_entities.get("visa_type", "").lower()
        if not visa_type and "visa_type" in profile:
            visa_type = profile["visa_type"].lower()
        
        # Check recent conversation for visa type hints
        if not visa_type:
            recent_context = context.get_recent_context(3).lower()
            if "health" in recent_context or "care" in recent_context or "nhs" in recent_context:
                visa_type = "health_care_worker"
            elif "graduate" in recent_context:
                visa_type = "graduate"
            elif "talent" in recent_context:
                visa_type = "global_talent"
            elif "student" in recent_context:
                visa_type = "student"
            elif "family" in recent_context or "spouse" in recent_context:
                visa_type = "family"
            elif "skilled" in recent_context or "work" in recent_context:
                visa_type = "skilled_worker"
        
        # Default to skilled_worker if still not detected
        if not visa_type:
            visa_type = "skilled_worker"
        
        # Build assessment response
        lines = ["## 🎯 Your Eligibility Assessment\n"]
        
        # Summarize profile
        lines.append("**Your Profile:**")
        if profile.get("job_title"):
            lines.append(f"• Job: {profile['job_title']}")
        if profile.get("salary"):
            lines.append(f"• Salary: £{profile['salary']:,}/year")
        if profile.get("sponsorship") is not None:
            lines.append(f"• Sponsorship: {'Yes' if profile['sponsorship'] else 'No'}")
        if profile.get("country"):
            lines.append(f"• Country: {profile['country']}")
        if profile.get("qualification"):
            lines.append(f"• Qualification: {profile['qualification']}")
        if profile.get("english_proficiency"):
            lines.append(f"• English: {profile['english_proficiency']}")
        
        lines.append("")
        lines.append(f"**Assessing for: {visa_type.replace('_', ' ').title()} Visa**")
        lines.append("")
        
        # Visa-specific eligibility checks
        if visa_type == "skilled_worker":
            lines.extend(self._assess_skilled_worker_eligibility(profile))
        elif visa_type == "health_care_worker":
            lines.extend(self._assess_health_care_worker_eligibility(profile))
        elif visa_type == "graduate":
            lines.extend(self._assess_graduate_eligibility(profile))
        elif visa_type == "global_talent":
            lines.extend(self._assess_global_talent_eligibility(profile))
        elif visa_type == "student":
            lines.extend(self._assess_student_eligibility(profile))
        elif visa_type == "family":
            lines.extend(self._assess_family_eligibility(profile))
        else:
            # Default to skilled worker assessment
            lines.extend(self._assess_skilled_worker_eligibility(profile))
        
        return self.response_generator.add_disclaimer("\n".join(lines))
    
    def _assess_skilled_worker_eligibility(self, profile: Dict[str, Any]) -> List[str]:
        """Assess eligibility for Skilled Worker visa."""
        lines = []
        salary = profile.get("salary", 0)
        has_sponsor = profile.get("sponsorship", False)
        
        # Salary threshold check
        salary_threshold = 38700
        if profile.get("age", 30) < 26:
            salary_threshold = 30960  # New entrant threshold
        
        salary_ok = salary >= salary_threshold
        sponsor_ok = has_sponsor
        
        if sponsor_ok and salary_ok:
            lines.append(f"✅ **Good news!** Based on the information provided, you appear to meet the basic eligibility criteria for a Skilled Worker visa.")
            lines.append(f"Your salary of £{salary:,} meets the threshold of £{salary_threshold:,}.")
        elif not sponsor_ok:
            lines.append("❌ **Important:** You'll need a Certificate of Sponsorship from a UK licensed employer to apply for a Skilled Worker visa.")
        elif not salary_ok:
            lines.append(f"❌ **Salary concern:** Your salary of £{salary:,} is below the required threshold of £{salary_threshold:,}.")
        
        lines.append("")
        lines.append("**Next Steps:**")
        lines.append("1. Verify your occupation is on the eligible occupations list")
        lines.append("2. Ensure you meet the English language requirement (CEFR B1)")
        lines.append("3. Prepare your supporting documents")
        lines.append("4. Consider consulting an immigration adviser for personalized advice")
        
        return lines
    
    def _assess_health_care_worker_eligibility(self, profile: Dict[str, Any]) -> List[str]:
        """Assess eligibility for Health and Care Worker visa."""
        lines = []
        has_sponsor = profile.get("sponsorship", False)
        job_title = profile.get("job_title", "").lower()
        
        # Check if job is health-related
        health_keywords = ["nurse", "doctor", "health", "care", "medical", "clinical", "nhs"]
        is_health_job = any(kw in job_title for kw in health_keywords)
        
        sponsor_ok = has_sponsor
        job_ok = is_health_job
        
        if sponsor_ok and job_ok:
            lines.append("✅ **Good news!** Based on the information provided, you appear to meet the basic eligibility criteria for a Health and Care Worker visa.")
            lines.append("As a health professional with sponsorship, you're on the right track!")
        elif not sponsor_ok:
            lines.append("❌ **Important:** You'll need a Certificate of Sponsorship from an NHS or approved care provider.")
        elif not job_ok:
            lines.append("❌ **Occupation concern:** Your job title doesn't appear to be in an eligible health or care occupation.")
        
        lines.append("")
        lines.append("**Key Benefits of Health and Care Worker Visa:**")
        lines.append("• No Immigration Health Surcharge (IHS) - saves £1,035 per year")
        lines.append("• Faster processing times")
        lines.append("• Lower application fees")
        
        lines.append("")
        lines.append("**Next Steps:**")
        lines.append("1. Ensure your employer is an eligible NHS or adult social care provider")
        lines.append("2. Verify your professional qualifications are recognized in the UK")
        lines.append("3. Meet the English language requirement")
        lines.append("4. Prepare proof of maintenance funds if required")
        
        return lines
    
    def _assess_graduate_eligibility(self, profile: Dict[str, Any]) -> List[str]:
        """Assess eligibility for Graduate visa."""
        lines = []
        qualification = profile.get("qualification", "").lower()
        
        has_uk_degree = any(kw in qualification for kw in ["bachelor", "master", "phd", "degree"])
        
        if has_uk_degree:
            lines.append("✅ **Good news!** If you've completed a UK degree and currently hold a Student visa, you likely qualify for the Graduate visa.")
            lines.append("The Graduate visa allows you to work in any job at any salary level for 2-3 years.")
        else:
            lines.append("❌ **Important:** The Graduate visa requires you to have completed a UK degree.")
            lines.append("If you studied outside the UK, you may need to consider other visa routes like the Skilled Worker visa.")
        
        lines.append("")
        lines.append("**Key Requirements:**")
        lines.append("• Completed a UK bachelor's degree, Master's degree, or PhD")
        lines.append("• Currently hold a valid Student visa")
        lines.append("• Your university has notified the Home Office of your successful completion")
        
        lines.append("")
        lines.append("**Next Steps:**")
        lines.append("1. Confirm with your university that they've reported your completion")
        lines.append("2. Apply before your current Student visa expires")
        lines.append("3. Prepare your CAS and passport")
        lines.append("4. Pay the application fee (£822) and IHS (£1,035 per year)")
        
        return lines
    
    def _assess_global_talent_eligibility(self, profile: Dict[str, Any]) -> List[str]:
        """Assess eligibility for Global Talent visa."""
        lines = []
        job_title = profile.get("job_title", "").lower()
        qualification = profile.get("qualification", "").lower()
        
        # Check for relevant fields
        tech_keywords = ["software", "developer", "engineer", "data", "tech", "it", "digital"]
        academic_keywords = ["research", "academic", "professor", "phd", "scientist"]
        arts_keywords = ["artist", "designer", "musician", "writer", "creative", "arts"]
        
        is_tech = any(kw in job_title for kw in tech_keywords)
        is_academic = any(kw in job_title for kw in academic_keywords) or "phd" in qualification
        is_arts = any(kw in job_title for kw in arts_keywords)
        
        if is_tech or is_academic or is_arts:
            lines.append("✅ **Promising!** Your background appears to align with the Global Talent visa requirements.")
            lines.append("You'll need to obtain an endorsement from a designated competent body.")
        else:
            lines.append("❌ **Important:** The Global Talent visa is for leaders in specific fields:")
            lines.append("• Digital technology (Tech Nation endorsement)")
            lines.append("• Academia and research (UKRI endorsement)")
            lines.append("• Arts and culture (Arts Council England endorsement)")
        
        lines.append("")
        lines.append("**Key Requirements:**")
        lines.append("• Endorsement from a designated competent body")
        lines.append("• Evidence of exceptional talent or exceptional promise")
        lines.append("• Strong portfolio or track record in your field")
        
        lines.append("")
        lines.append("**Next Steps:**")
        lines.append("1. Identify the appropriate endorsing body for your field")
        lines.append("2. Prepare your portfolio and evidence of achievements")
        lines.append("3. Apply for endorsement before applying for the visa")
        lines.append("4. Consider seeking expert advice on the endorsement process")
        
        return lines
    
    def _assess_student_eligibility(self, profile: Dict[str, Any]) -> List[str]:
        """Assess eligibility for Student visa."""
        lines = []
        age = profile.get("age", 25)
        english = profile.get("english_proficiency", "")
        
        if age >= 16:
            lines.append("✅ **Good news!** You meet the basic age requirement for a Student visa (16+).")
        else:
            lines.append("❌ **Age requirement:** You must be at least 16 years old to apply for a Student visa.")
        
        lines.append("")
        lines.append("**Key Requirements:**")
        lines.append("• Confirmation of Acceptance for Studies (CAS) from a licensed student sponsor")
        lines.append("• Proof of English language proficiency (IELTS, TOEFL, or PTE)")
        lines.append("• Sufficient maintenance funds:")
        lines.append("  - £1,334 per month (up to 9 months) if studying in London")
        lines.append("  - £1,023 per month (up to 9 months) if studying outside London")
        
        lines.append("")
        lines.append("**Next Steps:**")
        lines.append("1. Secure an unconditional offer from a UK university/college")
        lines.append("2. Obtain your CAS from the institution")
        lines.append("3. Take an approved English language test if required")
        lines.append("4. Prepare bank statements showing maintenance funds")
        lines.append("5. Pay the application fee (£490) and IHS (£776 per year)")
        
        return lines
    
    def _assess_family_eligibility(self, profile: Dict[str, Any]) -> List[str]:
        """Assess eligibility for Family visa."""
        lines = []
        salary = profile.get("salary", 0)
        
        # Minimum income requirement
        min_income = 18600
        income_ok = salary >= min_income
        
        if income_ok:
            lines.append(f"✅ **Good news!** Your income of £{salary:,} meets the minimum financial requirement of £18,600 for a Family visa.")
        else:
            lines.append(f"❌ **Financial requirement:** The minimum income threshold is £18,600 per year.")
            lines.append(f"Your stated income of £{salary:,} is below this threshold.")
            lines.append("You can combine income from multiple sources or use savings to meet the requirement.")
        
        lines.append("")
        lines.append("**Key Requirements:**")
        lines.append("• Your partner must be a British citizen or settled in the UK")
        lines.append("• You must be in a genuine relationship (married, civil partnership, or unmarried partners living together for 2+ years)")
        lines.append("• Meet the financial requirement (£18,600 minimum, higher if you have children)")
        lines.append("• Meet the English language requirement (A1 level for partners)")
        lines.append("• Have adequate accommodation in the UK")
        
        lines.append("")
        lines.append("**Next Steps:**")
        lines.append("1. Gather evidence of your relationship (marriage certificate, photos, communication)")
        lines.append("2. Prepare financial evidence (payslips, bank statements, employment letter)")
        lines.append("3. Take an approved English language test if required")
        lines.append("4. Find suitable accommodation in the UK")
        lines.append("5. Pay the application fee (£1,846 from outside UK, £1,209 from inside UK)")
        
        return lines
    
    def _handle_visa_recommendation(self, context: ConversationContext) -> str:
        """
        Handle requests for visa recommendations.
        Analyzes user profile and recommends the best visa options.
        """
        profile = context.user_profile
        
        # Check if we have enough information for recommendation
        minimal_info = ["job_title", "salary", "country"]
        has_minimal = all(profile.get(f) for f in minimal_info)
        
        if not has_minimal:
            missing = [f for f in minimal_info if not profile.get(f)]
            return (
                "To recommend the best visa option for you, I need some more information:\n\n"
                + "\n".join(f"• {f.replace('_', ' ').title()}" for f in missing)
                + "\n\nPlease provide these details so I can analyze all visa options for your situation."
            )
        
        # Build ApplicantProfile from user profile
        applicant = ApplicantProfile(
            job_title=profile.get("job_title", ""),
            salary_annual=profile.get("salary", 0),
            has_sponsor=profile.get("sponsorship", None),
            country_of_origin=profile.get("country", ""),
            age=profile.get("age", None),
            qualification=profile.get("qualification", ""),
            english_proficiency=profile.get("english_proficiency", ""),
            savings=profile.get("savings", None),
        )
        
        # Get user location and intent from context
        user_location = profile.get("location", None)
        user_intent = profile.get("intent", None)
        
        # Get visa recommendations
        try:
            recommendation = get_visa_recommendation(applicant, user_location, user_intent)
            
            lines = ["## 🎯 Best Visa Options for You\n"]
            lines.append(f"**Based on your profile:** {recommendation['profile_summary']}\n")
            
            # Show top recommendation
            if recommendation["recommended_visa"]:
                top = recommendation["recommended_visa"]
                lines.append(f"### 🏆 Top Recommendation: {top.visa_name}\n")
                lines.append(f"**Eligibility:** {'✅ Eligible' if top.verdict == 'eligible' else '⚠️ May not be eligible'}")
                lines.append(f"**Score:** {top.score}/150\n")
                
                if top.matched_criteria:
                    lines.append("**Your strengths:**")
                    for criterion in top.matched_criteria[:3]:
                        lines.append(f"• {criterion}")
                
                if top.missing_criteria:
                    lines.append("\n**Areas to address:**")
                    for criterion in top.missing_criteria[:3]:
                        lines.append(f"• {criterion}")
                
                lines.append(f"\n{top.summary}\n")
            
            # Show other eligible options
            eligible = recommendation["eligible_options"]
            if len(eligible) > 1:
                lines.append("### Other Visa Options You May Qualify For:\n")
                for option in eligible[1:4]:  # Show up to 3 more options
                    lines.append(f"• **{option.visa_name}** - Score: {option.score}")
                    if option.missing_criteria:
                        lines.append(f"  _Note: {option.missing_criteria[0]}_")
                lines.append("")
            
            lines.append("---")
            lines.append("**Next Steps:**")
            lines.append("1. Review the recommended visa requirements carefully")
            lines.append("2. Gather necessary documents")
            lines.append("3. Consider consulting an immigration adviser for complex cases")
            lines.append("4. Check official GOV.UK guidance for the most current requirements")
            
            return self.response_generator.add_disclaimer("\n".join(lines))
            
        except Exception as e:
            logger.error(f"Visa recommendation error: {e}")
            return (
                "I apologize, but I encountered an issue while analyzing visa options for you. "
                "Please try again with your details, or I can help you with specific visa information instead."
            )
    
    def _build_applicant_profile(self, profile: dict) -> ApplicantProfile:
        """Convert user profile dict to ApplicantProfile object."""
        return ApplicantProfile(
            job_title=profile.get("job_title", ""),
            salary_annual=profile.get("salary", 0),
            has_sponsor=profile.get("sponsorship", None),
            country_of_origin=profile.get("country", ""),
            age=profile.get("age", None),
            qualification=profile.get("qualification", ""),
            english_proficiency=profile.get("english_proficiency", ""),
            savings=profile.get("savings", None),
            soc_code=profile.get("soc_code", None),
        )
    
    def _create_response(
        self,
        context: ConversationContext,
        response: str,
        start_time: datetime,
    ) -> Dict[str, Any]:
        """Create the final response dictionary."""
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "response": response,
            "state": context.state.value,
            "session_id": context.session_id,
            "intent": context.current_intent.value if context.current_intent else None,
            "confidence": context.intent_confidence,
            "entities": context.extracted_entities,
            "profile": context.user_profile,
            "processing_time_ms": round(processing_time, 2),
            "message_count": len(context.messages),
        }
    
    def load_knowledge_base(self, knowledge_base: Dict[str, Any]):
        """Load knowledge base from GOV.UK scraper or other source."""
        self.knowledge_base = knowledge_base
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired = [sid for sid, ctx in self.sessions.items() if ctx.is_expired()]
        for sid in expired:
            del self.sessions[sid]


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Create a global instance for easy access
enhanced_dialogue_manager = EnhancedDialogueManager()


def process_message(session_id: str, user_message: str) -> Dict[str, Any]:
    """
    Convenience function to process a message using the global dialogue manager.
    
    Args:
        session_id: Unique session identifier
        user_message: User's input message
        
    Returns:
        Dict with response and metadata
    """
    return enhanced_dialogue_manager.process_message(session_id, user_message)


if __name__ == "__main__":
    # Simple CLI test
    print("=" * 60)
    print("Atlas AI - Enhanced Chatbot (Test Mode)")
    print("=" * 60)
    print()
    
    session_id = "test_session"
    dm = EnhancedDialogueManager()
    
    # Show greeting
    greeting = dm.process_message(session_id, "hello")
    print(greeting["response"])
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                farewell = dm.process_message(session_id, "goodbye")
                print(f"\n{farewell['response']}")
                break
            
            response = dm.process_message(session_id, user_input)
            print(f"\n{response['response']}")
            print(f"\n[Intent: {response['intent']} | Confidence: {response['confidence']:.2f}]")
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")