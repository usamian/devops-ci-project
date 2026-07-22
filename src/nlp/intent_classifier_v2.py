"""
Atlas AI — Enhanced Intent Classifier v2
Fast, comprehensive intent classification with 12+ categories.
Uses optimized keyword matching with confidence scoring for instant responses.
No ML model dependency — pure rule based for maximum speed....
"""

import re
from typing import Optional


# ── Enhanced Intent Categories ───────────────────────────────────────────────

INTENT_CATEGORIES = {
    "eligibility_check": {
        "keywords": {
            "high_weight": [
                "eligible", "eligibility", "qualify", "qualified", "can i apply",
                "can i get", "do i qualify", "am i eligible", "requirements",
                "criteria", "points", "sponsorship", "certificate of sponsorship",
                "cos", "skilled worker visa", "skill visa", "work visa",
                "i have", "i am", "i'm a", "national",
            ],
            "medium_weight": [
                "salary threshold", "going rate", "english language",
                "english requirement", "shortage occupation", "job offer",
                "licensed sponsor", "approved employer", "sponsor",
                "job letter", "offer letter", "employment letter",
            ],
            "low_weight": [
                "visa", "uk", "work", "job", "employment", "apply",
                "immigration", "home office", "get", "need",
            ],
        },
        "patterns": [
            r"can\s+(i|my|we)\s+(apply|get|qualify|be eligible)",
            r"am\s+i\s+(eligible|qualified)",
            r"do\s+i\s+(qualify|meet)\s+(the\s+)?requirements",
            r"what\s+(are\s+)?the\s+requirements\s+for",
            r"how\s+do\s+i\s+qualify\s+for",
            r"can\s+you\s+check\s+my\s+eligibility",
            r"check\s+if\s+i\s+am\s+eligible",
            r"do\s+i\s+need\s+a\s+sponsor",
            r"do\s+i\s+meet\s+the\s+criteria",
            # Pattern for descriptive eligibility queries (like user's example)
            r"i(?:'m|\s+am)\s+(?:a|an)?\s+\w+.*(?:from|of)\s+\w+.*(?:salary|sponsored|sponsor)",
            r"i\s+have\s+(?:a\s+)?(?:job|offer|letter).*(?:salary|sponsor)",
            r"(?:national|citizen).*(?:can|do|eligible|visa)",
            r"(?:from\s+)?\w+.*(?:national|citizen).*(?:visa|uk)",
            r"i.*(?:pakistani|indian|nigerian|filipino|bangladeshi).*(?:visa|uk|eligible)",
            r"i.*(?:software|engineer|developer|nurse|doctor).*(?:salary|sponsor|visa)",
        ],
    },
    "document_requirement": {
        "keywords": {
            "high_weight": [
                "document", "documents", "paperwork", "what do i need",
                "what documents", "certificate", "proof", "evidence",
                "required documents", "supporting documents",
            ],
            "medium_weight": [
                "ielts", "english test", "passport", "biometric",
                "tb test", "tuberculosis", "criminal record",
                "police clearance", "bank statement", "payslip",
                "employment contract", "reference letter",
            ],
            "low_weight": [
                "need", "provide", "submit", "show", "present",
                "bring", "have", "get",
            ],
        },
        "patterns": [
            r"what\s+(documents|papers|evidence)\s+(do\s+i\s+)?need",
            r"what\s+do\s+i\s+need\s+to\s+(provide|submit|show)",
            r"list\s+of\s+documents",
            r"documents\s+required\s+for",
            r"do\s+i\s+need\s+to\s+(show|provide)\s+",
        ],
    },
    "processing_time": {
        "keywords": {
            "high_weight": [
                "how long", "processing time", "processing", "waiting time",
                "when will", "timeline", "duration", "how soon",
                "time to process", "approval time",
            ],
            "medium_weight": [
                "delay", "urgent", "priority service", "super priority",
                "standard service", "how many weeks", "how many months",
                "decision time", "fast track",
            ],
            "low_weight": [
                "time", "long", "wait", "quick", "fast", "slow",
                "speed", "soon", "when",
            ],
        },
        "patterns": [
            r"how\s+long\s+does\s+it\s+take",
            r"how\s+long\s+to\s+get\s+a\s+decision",
            r"what\s+is\s+the\s+processing\s+time",
            r"when\s+will\s+i\s+get\s+a\s+decision",
            r"how\s+many\s+(weeks|months|days)\s+does\s+it\s+take",
            r"can\s+i\s+get\s+a\s+(priority|fast)\s+decision",
        ],
    },
    "fees_and_costs": {
        "keywords": {
            "high_weight": [
                "fee", "fees", "cost", "costs", "price", "how much",
                "application fee", "visa fee", "total cost",
            ],
            "medium_weight": [
                "ihs", "immigration health surcharge", "nhs surcharge",
                "priority fee", "biometric fee", "tb test cost",
                "english test fee", "how expensive",
            ],
            "low_weight": [
                "pay", "payment", "charge", "expensive", "cheap",
                "afford", "money", "pounds", "gbp", "£",
            ],
        },
        "patterns": [
            r"how\s+much\s+does\s+it\s+cost",
            r"what\s+are\s+the\s+fees\s+for",
            r"what\s+is\s+the\s+application\s+fee",
            r"how\s+much\s+do\s+i\s+need\s+to\s+pay",
            r"total\s+cost\s+of\s+",
            r"can\s+i\s+afford\s+",
        ],
    },
    "dependants_query": {
        "keywords": {
            "high_weight": [
                "dependant", "dependants", "family", "spouse", "partner",
                "children", "wife", "husband", "unmarried partner",
                "bring family", "family visa",
            ],
            "medium_weight": [
                "child", "son", "daughter", "minor", "under 18",
                "join me", "come with me", "live together",
                "married", "civil partner",
            ],
            "low_weight": [
                "family", "together", "bring", "join", "accompany",
            ],
        },
        "patterns": [
            r"can\s+my\s+(family|spouse|partner|children|wife|husband)",
            r"can\s+i\s+bring\s+my\s+(family|spouse|partner|children)",
            r"can\s+my\s+(family|spouse|partner|children)\s+come\s+with\s+me",
            r"what\s+about\s+my\s+(family|spouse|partner|children)",
            r"do\s+my\s+(family|dependants)\s+need",
        ],
    },
    "extension_switching": {
        "keywords": {
            "high_weight": [
                "extend", "extension", "switch", "switching", "change visa",
                "renew", "renewal", "stay longer", "continue",
            ],
            "medium_weight": [
                "from student visa", "from tier 2", "from graduate visa",
                "change status", "new visa", "different visa",
                "before visa expires",
            ],
            "low_weight": [
                "extend", "switch", "change", "renew", "continue",
                "stay", "remain",
            ],
        },
        "patterns": [
            r"can\s+i\s+(extend|switch|change|renew)\s+my\s+visa",
            r"how\s+do\s+i\s+(extend|switch|change)\s+to\s+",
            r"can\s+i\s+switch\s+from\s+",
            r"my\s+visa\s+is\s+expiring",
            r"i\s+want\s+to\s+(stay|remain)\s+longer",
        ],
    },
    "settlement_ilr": {
        "keywords": {
            "high_weight": [
                "settlement", "ilr", "indefinite leave to remain",
                "permanent residence", "pr", "citizenship",
                "naturalisation", "british citizenship",
            ],
            "medium_weight": [
                "5 years", "five years", "after 5 years",
                "settled status", "permanent", "180 days",
                "absence from uk",
            ],
            "low_weight": [
                "stay", "remain", "permanent", "settle", "citizen",
            ],
        },
        "patterns": [
            r"how\s+do\s+i\s+(apply\s+for\s+)?(ilr|settlement|citizenship)",
            r"when\s+can\s+i\s+apply\s+for\s+(ilr|settlement|citizenship)",
            r"after\s+how\s+many\s+years\s+can\s+i\s+(settle|get ilr)",
            r"what\s+are\s+the\s+requirements\s+for\s+(ilr|settlement)",
            r"can\s+i\s+become\s+a\s+(british\s+)?citizen",
        ],
    },
    "health_care_worker": {
        "keywords": {
            "high_weight": [
                "health and care worker", "health care visa",
                "nhs visa", "care worker visa", "health visa",
            ],
            "medium_weight": [
                "nhs", "doctor", "nurse", "healthcare professional",
                "social care", "allied health", "care worker",
                "lower fee", "ihs exemption",
            ],
            "low_weight": [
                "health", "care", "medical", "nhs", "hospital",
            ],
        },
        "patterns": [
            r"(health\s+and\s+)?care\s+worker\s+visa",
            r"i\s+am\s+a\s+(doctor|nurse|healthcare\s+professional)",
            r"working\s+in\s+the\s+nhs",
            r"health\s+visa\s+vs\s+skilled\s+worker",
        ],
    },
    "shortage_occupation": {
        "keywords": {
            "high_weight": [
                "shortage occupation", "immigration salary list",
                "shortage list", "isl", "shortage job",
            ],
            "keywords": [
                "80% going rate", "lower salary", "shortage job",
                "in demand job", "shortage profession",
            ],
            "low_weight": [
                "shortage", "demand", "list", "occupation",
            ],
        },
        "patterns": [
            r"is\s+.*\s+(on\s+)?the\s+shortage\s+list",
            r"is\s+.*\s+in\s+demand",
            r"what\s+is\s+the\s+immigration\s+salary\s+list",
            r"do\s+i\s+get\s+a\s+lower\s+salary\s+requirement",
        ],
    },
    "english_language": {
        "keywords": {
            "high_weight": [
                "english language", "english requirement", "english test",
                "ielts", "toefl", "pte", "cefr", "b1 level",
                "english exemption",
            ],
            "medium_weight": [
                "english speaking", "native english", "uk degree",
                "degree taught in english", "gcse english",
                "a-level english",
            ],
            "low_weight": [
                "english", "language", "test", "exam", "speak",
                "read", "write", "understand",
            ],
        },
        "patterns": [
            r"what\s+is\s+the\s+english\s+requirement",
            r"do\s+i\s+need\s+to\s+take\s+an\s+english\s+test",
            r"am\s+i\s+exempt\s+from\s+english",
            r"what\s+english\s+test\s+should\s+i\s+take",
            r"my\s+degree\s+was\s+taught\s+in\s+english",
        ],
    },
    "salary_threshold": {
        "keywords": {
            "high_weight": [
                "salary threshold", "minimum salary", "going rate",
                "salary requirement", "earnings", "annual salary",
                "£38,700", "38700",
            ],
            "medium_weight": [
                "new entrant", "under 26", "recent graduate",
                "phd salary", "shortage occupation salary",
                "80% going rate",
            ],
            "low_weight": [
                "salary", "pay", "earnings", "income", "wage",
                "money", "pounds",
            ],
        },
        "patterns": [
            r"what\s+is\s+the\s+minimum\s+salary",
            r"what\s+is\s+the\s+going\s+rate\s+for",
            r"do\s+i\s+meet\s+the\s+salary\s+requirement",
            r"my\s+salary\s+is\s+",
            r"is\s+.*\s+enough\s+salary",
        ],
    },
    "general_query": {
        "keywords": {
            "high_weight": [
                "what is", "tell me about", "explain", "overview",
                "information about", "tier 2", "uk immigration",
                "uk visa", "how does",
            ],
            "medium_weight": [
                "general information", "basics", "introduction",
                "guide", "help", "understand",
            ],
            "low_weight": [
                "hello", "hi", "hey", "thanks", "thank you",
                "goodbye", "bye", "help",
            ],
        },
        "patterns": [
            r"^(hi|hello|hey|good\s+(morning|afternoon|evening))",
            r"^(thanks?|thank\s+you)",
            r"^(bye|goodbye|see\s+you)",
            r"what\s+is\s+",
            r"tell\s+me\s+about\s+",
            r"explain\s+",
            r"how\s+does\s+",
        ],
    },
}


class EnhancedIntentClassifier:
    """
    Fast, rule-based intent classifier with 12+ categories.
    No ML model dependency — instant classification.
    """
    
    def __init__(self):
        # Pre-compile all regex patterns
        self._compiled_patterns = {}
        for intent, config in INTENT_CATEGORIES.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) 
                for p in config.get("patterns", [])
            ]
    
    def classify(self, text: str) -> dict:
        """
        Classify text into intent category with confidence score.
        Returns: {intent, confidence, all_scores, source}
        """
        text_lower = text.lower().strip()
        
        if not text_lower:
            return {
                "intent": "general_query",
                "confidence": 0.5,
                "all_scores": {k: 0.0 for k in INTENT_CATEGORIES},
                "source": "fallback",
            }
        
        scores = {}
        
        for intent, config in INTENT_CATEGORIES.items():
            score = 0.0
            
            # Check regex patterns (highest priority)
            for pattern in self._compiled_patterns[intent]:
                if pattern.search(text_lower):
                    score += 3.0  # Pattern match = high confidence
            
            # Check keywords by weight
            keywords = config.get("keywords", {})
            
            # High weight keywords
            for kw in keywords.get("high_weight", []):
                if kw in text_lower:
                    score += 2.0
            
            # Medium weight keywords
            for kw in keywords.get("medium_weight", []):
                if kw in text_lower:
                    score += 1.0
            
            # Low weight keywords
            for kw in keywords.get("low_weight", []):
                if kw in text_lower:
                    score += 0.3
            
            scores[intent] = score
        
        # Determine best intent
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # Calculate confidence (normalize to 0-1)
        total_score = sum(scores.values())
        if total_score > 0:
            # Use ratio of best score to total for confidence
            confidence = min(0.99, max(0.5, best_score / total_score))
            
            # Boost confidence if absolute score is high
            if best_score >= 5.0:
                confidence = max(confidence, 0.85)
            elif best_score >= 3.0:
                confidence = max(confidence, 0.70)
            elif best_score >= 1.0:
                confidence = max(confidence, 0.60)
        else:
            confidence = 0.5
        
        # Normalize all scores for display
        max_possible = 10.0  # Arbitrary max for normalization
        normalized_scores = {
            k: round(min(1.0, v / max_possible), 4) 
            for k, v in scores.items()
        }
        
        return {
            "intent": best_intent,
            "confidence": round(confidence, 4),
            "all_scores": normalized_scores,
            "low_confidence": confidence < 0.65,
            "source": "rule_based",
        }


# Singleton instance
_intent_classifier = None


def get_intent_classifier() -> EnhancedIntentClassifier:
    """Get or create the intent classifier singleton."""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = EnhancedIntentClassifier()
    return _intent_classifier


def classify_intent_enhanced(text: str) -> dict:
    """
    Quick function to classify intent using enhanced classifier.
    """
    classifier = get_intent_classifier()
    return classifier.classify(text)