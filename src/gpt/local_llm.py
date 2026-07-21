"""
Atlas AI — Local LLM Chat (100% Free, No API Costs)
Uses Ollama to run Llama/Mistral models locally for GPT-like chat.

This module provides:
- Local LLM chat using Ollama (Llama 2, Mistral, etc.)
- RAG integration for UK visa knowledge
- No OpenAI API costs required
- Full privacy - all processing done locally
"""

import json
import requests
import logging
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path

from src.core.config import AtlasConfig
from src.rag.retriever import RAGRetriever
from src.rag.gov_uk_scraper import scraper
from src.rule_engine.rules_base import ApplicantProfile

logger = logging.getLogger(__name__)


class LocalLLM:
    """
    Local LLM chat using Ollama.
    100% free - runs entirely on your machine.
    
    Supports:
    - Llama 2 (7B, 13B, 70B)
    - Mistral (7B)
    - Neural Chat
    - And many more Ollama models
    """
    
    DEFAULT_MODEL = "mistral"  # Free, fast, good quality
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # System prompt for UK visa assistant
    SYSTEM_PROMPT = """You are Atlas AI, an expert UK immigration assistant. 
You help users understand UK visa requirements, eligibility, and application processes.

IMPORTANT RULES:
1. Always base your answers on official GOV.UK guidance
2. Never make up information - if unsure, say so
3. Always remind users this is informational guidance, not legal advice
4. Be clear, helpful, and empathetic
5. Cite GOV.UK sources when possible
6. If a question requires eligibility assessment, guide users to provide relevant details

VISA TYPES YOU CAN HELP WITH:
- Skilled Worker Visa
- Health and Care Worker Visa  
- Graduate Visa
- Global Talent Visa
- Student Visa
- Family Visa
- Visitor Visa

TONE: Professional, friendly, and informative. Use simple language to explain complex rules.

DISCLAIMER: Always end with a reminder that users should verify information on GOV.UK or consult an immigration solicitor for legal advice."""
    
    def __init__(self, model: str = None, ollama_url: str = None):
        self.model = model or self.DEFAULT_MODEL
        self.ollama_url = ollama_url or self.OLLAMA_BASE_URL
        self.conversation_history: List[Dict[str, str]] = []
        self.retriever: Optional[RAGRetriever] = None
        
        # Check if Ollama is available
        self.available = self._check_ollama()
        
        if self.available:
            self._ensure_model_available()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            logger.warning("Ollama not running. Install from https://ollama.ai")
            return False
    
    def _ensure_model_available(self):
        """Ensure the selected model is available in Ollama."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if not any(self.model in name for name in model_names):
                logger.warning(f"Model '{self.model}' not found. Available: {model_names}")
                logger.info("Run: ollama pull mistral")
        except Exception:
            pass
    
    def chat(self, user_message: str, use_rag: bool = True) -> str:
        """
        Chat with the local LLM.
        Returns the AI response as a string.
        
        Args:
            user_message: User's input message
            use_rag: Whether to use RAG for retrieval augmentation
            
        Returns:
            AI response text
        """
        if not self.available:
            return self._fallback_response(user_message)
        
        # Get relevant context from RAG if enabled
        context = ""
        if use_rag:
            try:
                if not self.retriever:
                    self.retriever = RAGRetriever()
                context = self.retriever.retrieve(user_message, top_k=3)
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # Build the prompt with context
        if context:
            prompt = f"""Context from official GOV.UK guidance:
{context}

User question: {user_message}

Based on the context above, please answer the user's question. If the context doesn't contain the answer, say so and provide general guidance."""
        else:
            prompt = user_message
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self._build_full_prompt(prompt),
                    "stream": False,
                    "context": self._get_context_window(),
                },
                timeout=120,
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "")
                
                # Add to history
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                # Limit history to last 10 messages
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return ai_response
            else:
                logger.warning(f"Ollama returned status {response.status_code}: {response.text[:200]}")
                return None  # Return None to trigger fallback
                
        except requests.Timeout:
            return "The model is taking too long to respond. Please try again or simplify your question."
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return self._fallback_response(user_message)
    
    def chat_stream(self, user_message: str, use_rag: bool = True) -> Generator[str, None, None]:
        """
        Chat with streaming response.
        Yields tokens as they are generated.
        """
        if not self.available:
            yield self._fallback_response(user_message)
            return
        
        # Get RAG context
        context = ""
        if use_rag:
            try:
                if not self.retriever:
                    self.retriever = RAGRetriever()
                context = self.retriever.retrieve(user_message, top_k=3)
            except Exception:
                pass
        
        # Build prompt
        if context:
            prompt = f"""Context from official GOV.UK guidance:
{context}

User question: {user_message}

Based on the context above, please answer the user's question."""
        else:
            prompt = user_message
        
        # Call Ollama streaming API
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self._build_full_prompt(prompt),
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._fallback_response(user_message)
    
    def _build_full_prompt(self, user_prompt: str) -> str:
        """Build the full prompt with system message and history."""
        full_prompt = f"<s>[INST] {self.SYSTEM_PROMPT}\n\n"
        
        # Add conversation history
        for msg in self.conversation_history[:-1]:  # Exclude current message
            if msg["role"] == "user":
                full_prompt += f"User: {msg['content']}\n\n"
            else:
                full_prompt += f"Assistant: {msg['content']}\n\n"
        
        full_prompt += f"{user_prompt} [/INST]"
        return full_prompt
    
    def _get_context_window(self) -> list:
        """Get context window from conversation history."""
        return []  # Ollama handles context internally
    
    def _fallback_response(self, user_message: str) -> str:
        """Fallback response when Ollama is not available."""
        return """I'm sorry, but the local AI model (Ollama) is not currently running.

To use this free AI chat feature:
1. Install Ollama from https://ollama.ai
2. Run: ollama pull mistral
3. Start Ollama (it runs automatically after installation)
4. Try your question again

Alternatively, you can still use the rule-based eligibility checker which doesn't require Ollama.

For immediate help, visit: https://www.gov.uk/browse/visas-immigration"""
    
    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception:
            return []


class SmartChatbot:
    """
    Smart chatbot that combines:
    - Local LLM (Ollama) for natural conversation
    - Rule engine for eligibility decisions
    - RAG for accurate information retrieval
    - Self-learning from user interactions
    """
    
    def __init__(self):
        self.llm = LocalLLM()
        self.learning_data: List[Dict[str, Any]] = []
        
    def chat(self, user_message: str) -> str:
        """
        Smart chat that uses the best available method.
        """
        message_lower = user_message.lower()
        
        # Check if this is an eligibility check request
        if any(kw in message_lower for kw in ["eligible", "eligibility", "can i apply", "am i eligible", "qualify"]):
            return self._handle_eligibility_query(user_message)
        
        # Check if this is a specific visa question
        if any(kw in message_lower for kw in ["salary", "requirement", "document", "how to", "process", "time"]):
            return self.llm.chat(user_message, use_rag=True)
        
        # General conversation
        return self.llm.chat(user_message, use_rag=True)
    
    def _handle_eligibility_query(self, user_message: str) -> str:
        """Handle eligibility-related queries with rule engine.
        Now supports ALL visa types - dynamically selects the appropriate rule engine.
        """
        from src.rule_engine.skilled_worker import SkilledWorkerRuleEngine
        from src.rule_engine.health_care_worker import HealthCareWorkerRuleEngine
        from src.rule_engine.graduate import GraduateRuleEngine
        from src.rule_engine.global_talent import GlobalTalentRuleEngine
        from src.rule_engine.student_visa import StudentVisaRuleEngine
        from src.rule_engine.family_visa import FamilyVisaRuleEngine
        from src.rule_engine.rules_base import ApplicantProfile
        
        # Detect visa type from user message
        visa_type = self._detect_visa_type(user_message)
        
        # Extract information from message using simple parsing
        profile = self._parse_user_message(user_message)
        
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
        
        if profile.is_complete():
            result = engine.check_eligibility(profile)
            
            response = f"**Eligibility Assessment for {visa_type.replace('_', ' ').title()} Visa:**\n\n"
            response += result.summary + "\n\n"
            
            response += "**Details:**\n"
            for rule in result.rule_results:
                status = "✅" if rule.passed else "❌"
                response += f"{status} {rule.rule_description}: {rule.reason}\n"
            
            response += f"\n**Points:** {result.points_earned}/{result.points_required}\n"
            response += f"\n*Trace ID: {result.trace_id}*"
            
            return response
        else:
            missing = profile.missing_fields()
            return f"""To check your eligibility for the {visa_type.replace('_', ' ').title()} visa, I need more information:

{', '.join(missing)}

Please provide these details so I can give you an accurate assessment.

Example: "I'm a software engineer from India, salary £50,000, with a sponsor, BSc degree, and IELTS passed." """
    
    def _detect_visa_type(self, message: str) -> str:
        """Detect visa type from user message keywords."""
        message_lower = message.lower()
        
        # Check for specific visa type keywords
        if any(kw in message_lower for kw in ["health and care", "health care", "nhs", "nurse", "doctor", "care worker"]):
            return "health_care_worker"
        elif "graduate" in message_lower or "post-study" in message_lower or "post study" in message_lower:
            return "graduate"
        elif "global talent" in message_lower or "exceptional talent" in message_lower:
            return "global_talent"
        elif "student" in message_lower or "study" in message_lower or "university" in message_lower:
            return "student"
        elif "family" in message_lower or "spouse" in message_lower or "partner" in message_lower:
            return "family"
        elif "skilled" in message_lower or "tier 2" in message_lower:
            return "skilled_worker"
        
        # Default to skilled worker if no specific visa type detected
        return "skilled_worker"
    
    def _parse_user_message(self, message: str) -> ApplicantProfile:
        """Parse user message to extract profile information."""
        import re
        
        profile = ApplicantProfile()
        message_lower = message.lower()
        
        # Extract salary
        salary_match = re.search(r'£?(\d{2,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|per year|/year|annually)?', message_lower)
        if salary_match:
            salary_str = salary_match.group(1).replace(',', '')
            try:
                salary = float(salary_str)
                # Handle "50k" format
                if 'k' in message_lower[salary_match.start():salary_match.end()]:
                    salary *= 1000
                profile.salary_annual = salary
            except ValueError:
                pass
        
        # Extract country
        countries = ['india', 'pakistan', 'bangladesh', 'nigeria', 'philippines', 'china', 'usa', 'uk', 'canada', 'australia']
        for country in countries:
            if country in message_lower:
                profile.country_of_origin = country.title()
                break
        
        # Extract job title
        job_patterns = [
            r'(?:as a |job as |work as |working as |role of )?([\w\s]+(?:engineer|developer|doctor|nurse|teacher|analyst|manager|consultant|scientist|researcher|professor|designer|accountant|solicitor|barrister|pharmacist|therapist|architect))',
        ]
        for pattern in job_patterns:
            match = re.search(pattern, message_lower)
            if match:
                profile.job_title = match.group(1).strip().title()
                break
        
        # Check for sponsor
        if any(kw in message_lower for kw in ["with sponsor", "have sponsor", "sponsored", "cos", "certificate of sponsorship"]):
            profile.has_sponsor = True
        elif any(kw in message_lower for kw in ["no sponsor", "without sponsor", "not sponsored"]):
            profile.has_sponsor = False
        
        # Check for qualification
        if any(kw in message_lower for kw in ["bsc", "bachelor", "bachelors", "b.sc"]):
            profile.qualification = "Bachelor's Degree"
            profile.qualification_level = "6"
        elif any(kw in message_lower for kw in ["msc", "master", "masters", "m.sc", "mba"]):
            profile.qualification = "Master's Degree"
            profile.qualification_level = "7"
        elif any(kw in message_lower for kw in ["phd", "doctorate", "ph.d"]):
            profile.qualification = "PhD"
            profile.qualification_level = "8"
        
        # Check for English proficiency
        if any(kw in message_lower for kw in ["ielts", "toefl", "pte", "english test"]):
            profile.english_proficiency = "test_passed"
        
        return profile
    
    def learn_from_interaction(self, user_message: str, ai_response: str, feedback: Optional[str] = None):
        """Store interaction for self-learning."""
        self.learning_data.append({
            "user_message": user_message,
            "ai_response": ai_response,
            "feedback": feedback,
            "timestamp": __import__('time').strftime("%Y-%m-%d %H:%M:%S"),
        })
    
    def save_learning_data(self, filepath: Path = None):
        """Save learning data for future training."""
        if filepath is None:
            filepath = AtlasConfig.DATA_DIR / "learning_data.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.learning_data, f, indent=2)
    
    def load_learning_data(self, filepath: Path = None):
        """Load previous learning data."""
        if filepath is None:
            filepath = AtlasConfig.DATA_DIR / "learning_data.json"
        
        if filepath.exists():
            with open(filepath, 'r') as f:
                self.learning_data = json.load(f)


# Global chatbot instance
chatbot = SmartChatbot()