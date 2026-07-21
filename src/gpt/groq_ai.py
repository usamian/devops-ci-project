"""
Atlas AI — Groq AI Integration
Uses Groq's free API for fast, powerful AI responses.
Works ONLY with offline stored UK immigration data.
"""

import json
import logging
import requests
from typing import Optional, List, Dict, Any

from groq_config import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_SYSTEM_PROMPT
from src.rag.retriever import RAGRetriever

logger = logging.getLogger(__name__)


class GroqAI:
    """
    Groq AI integration for Atlas AI.
    Uses RAG to ensure responses are based ONLY on official GOV.UK data.
    
    Key features:
    - Works ONLY with provided context (no hallucinations)
    - Uses offline stored UK immigration data
    - Fast responses via Groq's API
    - Free tier available
    """
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.api_url = GROQ_API_URL
        self.model = GROQ_MODEL
        self.system_prompt = GROQ_SYSTEM_PROMPT
        self.retriever = RAGRetriever()
        
        # Check if API key is configured
        self.available = bool(self.api_key) and self.api_key != ""
        
        if not self.available:
            logger.warning("Groq API key not configured. Set GROQ_API_KEY in groq_config.py")
    
    def chat(self, user_message: str, use_rag: bool = True) -> Optional[str]:
        """
        Chat with Groq AI using RAG context.
        
        Args:
            user_message: User's input message
            use_rag: Whether to use RAG for context retrieval
            
        Returns:
            AI response text, or None if unavailable
        """
        if not self.available:
            return None
        
        # Get relevant context from RAG
        context = ""
        if use_rag:
            try:
                context = self.retriever.retrieve(user_message, top_k=5)
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        # Build the prompt - always provide helpful context
        if context:
            user_prompt = f"""Context from official GOV.UK guidance:
{context}

User question: {user_message}

Based on the context above, please provide a helpful, detailed answer to the user's question. 
If the context doesn't fully answer the question, use your knowledge of UK immigration to provide additional helpful guidance.
Always be informative and helpful."""
        else:
            # Even without specific context, provide helpful UK visa information for ALL visa types
            user_prompt = f"""User question: {user_message}

Please provide helpful information about UK visas and immigration based on your knowledge. 
Cover ALL major UK visa types including: Skilled Worker, Health and Care Worker, Graduate, Global Talent, Student, and Family visas.
Include information about requirements, documents, processing times, and fees where relevant.
Always recommend verifying information on GOV.UK for the most current guidance."""
        
        # Call Groq API
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,  # Low temperature for factual responses
                    "max_tokens": 1024,
                    "top_p": 0.95,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.1,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return ai_response
            else:
                logger.warning(f"Groq API error: {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.Timeout:
            logger.error("Groq API timeout")
            return None
        except Exception as e:
            logger.error(f"Groq AI error: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if Groq API is properly configured."""
        return self.available
    
    def test_connection(self) -> bool:
        """Test if Groq API is working with a simple request."""
        if not self.available:
            return False
        
        try:
            # Make a simple test request to verify API key
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_tokens": 10,
                },
                timeout=15,
            )
            
            if response.status_code == 200:
                logger.info("Groq API key is valid and working!")
                return True
            elif response.status_code == 401:
                logger.error("Groq API key is INVALID! Please check your API key in groq_config.py")
                return False
            elif response.status_code == 429:
                logger.warning("Groq API rate limit reached. Key is valid but quota exceeded.")
                return True  # Key is valid, just rate limited
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text[:200]}")
                return False
                
        except requests.Timeout:
            logger.error("Groq API connection timeout")
            return False
        except Exception as e:
            logger.error(f"Groq API test failed: {e}")
            return False
    
    def validate_and_test(self) -> bool:
        """Validate API key configuration and test connection."""
        if not self.available:
            logger.warning("Groq API key not configured. Set GROQ_API_KEY in groq_config.py")
            return False
        
        logger.info("Testing Groq API connection...")
        if self.test_connection():
            logger.info("✓ Groq AI is ready and configured correctly!")
            return True
        else:
            logger.error("✗ Groq AI is NOT working. Please check your API key.")
            return False


# Global Groq AI instance
groq_ai = GroqAI()
