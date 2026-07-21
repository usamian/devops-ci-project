"""
Atlas AI — Responses Module
Comprehensive knowledge base and response generation.
"""

from src.responses.knowledge_base import (
    KNOWLEDGE_BASE,
    get_response,
    get_fallback_response,
    get_suggestion_for_intent,
)

__all__ = [
    "KNOWLEDGE_BASE",
    "get_response",
    "get_fallback_response",
    "get_suggestion_for_intent",
]