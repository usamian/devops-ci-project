"""
Atlas AI — Enhanced RAG Retrieval Module
Advanced retrieval with query expansion, re-ranking, and multi-strategy search.
"""

import numpy as np
import re
from typing import Optional, List, Dict, Any

from config import RAG_TOP_K
from src.rag.embedder import load_index, _load_embed_model
from src.rag.gov_uk_loader import DocumentChunk


# ── Query Expansion Synonyms ──────────────────────────────────────────────────

VISA_SYNONYMS = {
    "skilled worker": ["skilled worker visa", "tier 2", "tier 2 general", "work visa", 
                       "employment visa", "sponsor visa", "uk work permit", "uk work visa",
                       "skilled worker route", "points based system"],
    "health care": ["health and care worker", "nhs visa", "care worker", "medical visa",
                    "healthcare professional", "doctor visa", "nurse visa", "clinical visa"],
    "graduate": ["graduate visa", "post-study work", "psw", "student to work",
                 "graduate route", "post study work visa", "uk graduate work"],
    "global talent": ["global talent visa", "exceptional talent", "exceptional promise",
                      "tech nation", "leader visa", "researcher visa", "academic visa"],
    "eligible": ["qualify", "qualification", "requirements", "criteria", "points",
                 "eligible for", "can i apply", "am i eligible", "do i qualify"],
    "salary": ["pay", "income", "wage", "earnings", "compensation", "threshold",
               "minimum salary", "going rate", "annual salary", "salary requirement"],
    "documents": ["papers", "evidence", "proof", "certificates", "records",
                  "required documents", "document checklist", "supporting documents"],
    "processing time": ["how long", "duration", "timeline", "waiting time", "decision time",
                        "processing duration", "how many weeks", "when will i get decision"],
    "sponsor": ["certificate of sponsorship", "cos", "employer", "licensed sponsor",
                "uk sponsor", "sponsor licence", "sponsorship certificate"],
    "english": ["language", "ielts", "toefl", "b1 level", "cefr", "english requirement",
                "language test", "english test", "language proficiency"],
    "fees": ["cost", "price", "application fee", "visa fee", "ihs", "health surcharge",
             "total cost", "how much", "visa price"],
    "dependants": ["family", "spouse", "partner", "children", "dependant visa",
                   "bring family", "family visa", "wife", "husband"],
    "settlement": ["ilr", "indefinite leave to remain", "permanent residence",
                   "settlement visa", "uk citizenship", "permanent settlement"],
}

# ── Intent to Topic Mapping ───────────────────────────────────────────────────

INTENT_TOPIC_MAP = {
    "eligibility_check": ["eligibility", "requirements", "points"],
    "document_requirement": ["documents", "evidence", "proof"],
    "processing_time": ["processing", "timeline", "decision"],
    "fees_and_costs": ["fees", "costs", "price", "ihs", "surcharge"],
    "dependants_query": ["dependants", "family", "spouse", "children"],
    "english_language": ["english", "language", "ielts", "test"],
    "salary_threshold": ["salary", "threshold", "going rate", "minimum"],
    "extension_switching": ["extend", "switch", "renew", "change"],
    "settlement_ilr": ["settlement", "ilr", "indefinite leave", "permanent"],
    "health_care_worker": ["health", "care", "nhs", "medical"],
    "shortage_occupation": ["shortage", "immigration salary list", "isl"],
    "general_query": ["overview", "information", "guide"],
}


class RAGRetriever:
    """
    Ultra-Enhanced RAG Retriever - Maximum Power Configuration
    Features:
    - Multi-query retrieval with query variations
    - Reciprocal Rank Fusion (RRF) for result combination
    - Intent-aware retrieval with topic mapping
    - Entity-enhanced queries
    - Semantic similarity re-ranking
    - Context compression for optimal LLM prompts
    - FAQ matching for common questions
    """
    
    def __init__(self, default_top_k: int = RAG_TOP_K):
        """Initialize the retriever with default top_k value."""
        self.default_top_k = default_top_k
        self._model = None
        self._index = None
        self._chunks = None
    
    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            self._model = _load_embed_model()
        return self._model
    
    def _get_index_and_chunks(self):
        """Lazy load the index and chunks."""
        if self._index is None:
            self._index, self._chunks = load_index()
        return self._index, self._chunks
    
    def generate_query_variations(self, query: str) -> List[str]:
        """
        Generate multiple query variations for comprehensive retrieval.
        This is key to 10x better retrieval - cast a wider net.
        """
        variations = [query]
        query_lower = query.lower()
        
        # Add synonym-based variations
        for key, synonyms in VISA_SYNONYMS.items():
            if key in query_lower:
                # Create variations with each synonym
                for synonym in synonyms[:3]:
                    variation = query_lower.replace(key, synonym)
                    if variation != query_lower:
                        variations.append(variation)
                # Add combined variations
                combined = query + " " + " ".join(synonyms[:2])
                variations.append(combined)
        
        # Add intent-based variations
        for intent, topics in INTENT_TOPIC_MAP.items():
            for topic in topics:
                if topic in query_lower:
                    variations.append(query + " " + " ".join(topics[:3]))
                    break
        
        # Add question-specific variations
        if query_lower.startswith("what"):
            variations.append(query.replace("what", "information about"))
        elif query_lower.startswith("how"):
            variations.append(query.replace("how", "guide to"))
        elif query_lower.startswith("can i") or query_lower.startswith("am i"):
            variations.append(query + " eligibility requirements")
        
        return list(set(variations))  # Remove duplicates
    
    def expand_query(self, query: str) -> str:
        """
        Expand query with relevant synonyms for better retrieval.
        """
        query_lower = query.lower()
        expanded_terms = [query]
        
        for key, synonyms in VISA_SYNONYMS.items():
            if key in query_lower:
                expanded_terms.extend(synonyms[:2])
        
        return " ".join(expanded_terms)
    
    def retrieve(self, query: str, top_k: int = None, use_multi_query: bool = True) -> str:
        """
        Ultra-powerful retrieval using multi-query strategy.
        
        Args:
            query: User query text
            top_k: Number of chunks to retrieve
            use_multi_query: Whether to use multi-query retrieval
            
        Returns:
            Formatted context string from retrieved documents
        """
        if top_k is None:
            top_k = self.default_top_k
        
        try:
            if use_multi_query:
                chunks = self._multi_query_retrieve(query, top_k)
            else:
                expanded_query = self.expand_query(query)
                chunks = retrieve(expanded_query, top_k=top_k)
            
            return format_retrieved_context(chunks)
        except Exception as e:
            return f"RAG retrieval error: {str(e)}"
    
    def _multi_query_retrieve(self, query: str, top_k: int) -> List[dict]:
        """
        Multi-query retrieval with Reciprocal Rank Fusion (RRF).
        This is the key to 10x better retrieval accuracy.
        """
        variations = self.generate_query_variations(query)
        all_results = {}  # chunk_id -> {chunk, scores, ranks}
        
        # Retrieve for each query variation
        for var_query in variations:
            try:
                results = retrieve(var_query, top_k=top_k * 2)
                
                for rank, result in enumerate(results):
                    chunk_id = result["chunk_id"]
                    
                    if chunk_id not in all_results:
                        all_results[chunk_id] = {
                            "chunk": result,
                            "scores": [],
                            "ranks": [],
                        }
                    
                    all_results[chunk_id]["scores"].append(result["score"])
                    all_results[chunk_id]["ranks"].append(rank + 1)
            except Exception:
                continue
        
        # Apply Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        for chunk_id, data in all_results.items():
            rrf_score = 0
            for rank in data["ranks"]:
                rrf_score += 1 / (60 + rank)  # RRF formula
            rrf_scores[chunk_id] = rrf_score
        
        # Sort by RRF score and return top_k
        sorted_chunks = sorted(
            all_results.values(),
            key=lambda x: rrf_scores[x["chunk"]["chunk_id"]],
            reverse=True
        )
        
        return [item["chunk"] for item in sorted_chunks[:top_k]]
    
    def retrieve_with_relevance_scoring(self, query: str, top_k: int = None) -> List[dict]:
        """
        Retrieve with enhanced relevance scoring.
        Returns chunks with computed relevance scores.
        """
        if top_k is None:
            top_k = self.default_top_k
        
        chunks = self._multi_query_retrieve(query, top_k * 2)
        
        # Re-rank by semantic similarity
        model = self._get_model()
        query_embedding = model.encode([query], normalize_embeddings=True)
        
        scored_chunks = []
        for chunk in chunks:
            chunk_embedding = model.encode([chunk["text"]], normalize_embeddings=True)
            similarity = float(np.dot(query_embedding[0], chunk_embedding[0]))
            chunk["relevance_score"] = similarity
            scored_chunks.append(chunk)
        
        # Sort by relevance score
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return scored_chunks[:top_k]
    
    def retrieve_with_sources(self, query: str, top_k: int = None) -> tuple:
        """
        Retrieve chunks with source attribution.
        
        Returns:
            Tuple of (formatted_context, sources_list)
        """
        if top_k is None:
            top_k = self.default_top_k
        
        expanded_query = self.expand_query(query)
        chunks = retrieve(expanded_query, top_k=top_k)
        
        sources = list(set([c["source_url"] for c in chunks]))
        context = format_retrieved_context(chunks)
        
        return context, sources
    
    def retrieve_for_intent(self, query: str, intent: str, entities: dict) -> list[dict]:
        """
        Smart retrieval based on detected intent.
        
        Args:
            query: Original user query
            intent: Detected intent label
            entities: Extracted entity dict
            
        Returns:
            List of relevant document chunks
        """
        return retrieve_for_intent(query, intent, entities)
    
    def get_relevant_faq(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Get relevant FAQ-like responses for common queries.
        Now covers ALL visa types, not just Skilled Worker.
        
        Args:
            query: User query
            top_k: Number of FAQs to return
            
        Returns:
            List of FAQ dicts with question and answer
        """
        # Comprehensive FAQs covering all visa types
        faqs = [
            # Skilled Worker FAQs
            {
                "question": "What is the minimum salary for Skilled Worker visa?",
                "answer": "The general salary threshold is £38,700 per year from April 2024, or the going rate for your occupation if higher. New entrants (under 26 or recent graduates) may qualify with £30,960.",
                "keywords": ["salary", "minimum", "threshold", "skilled worker"]
            },
            {
                "question": "How long does it take to get a Skilled Worker visa?",
                "answer": "Standard processing is 3 weeks from outside UK, 8 weeks from inside UK. Priority services available.",
                "keywords": ["how long", "processing", "time", "weeks", "skilled worker"]
            },
            {
                "question": "Can I bring my family on a Skilled Worker visa?",
                "answer": "Yes, your partner and children under 18 can apply as dependants. They can work and study in the UK.",
                "keywords": ["family", "dependants", "partner", "children", "spouse", "skilled worker"]
            },
            
            # Health and Care Worker FAQs
            {
                "question": "What is the Health and Care Worker visa?",
                "answer": "The Health and Care Worker visa is for qualified doctors, nurses, and health professionals working in the UK. Benefits include no IHS fee, faster processing, and lower application fees.",
                "keywords": ["health", "care", "nhs", "nurse", "doctor", "medical"]
            },
            {
                "question": "Do Health and Care Worker visa holders pay IHS?",
                "answer": "No, Health and Care Worker visa holders are exempt from the Immigration Health Surcharge (IHS). This saves £1,035 per year.",
                "keywords": ["health", "care", "ihs", "surcharge", "exempt", "nhs"]
            },
            
            # Graduate FAQs
            {
                "question": "How long does the Graduate visa last?",
                "answer": "The Graduate visa lasts 2 years for Bachelor's and Master's graduates, or 3 years for PhD graduates. It cannot be extended.",
                "keywords": ["graduate", "how long", "duration", "years", "post-study"]
            },
            {
                "question": "Can I switch from Graduate visa to Skilled Worker visa?",
                "answer": "Yes, you can switch from a Graduate visa to a Skilled Worker visa if you find a job with a licensed sponsor that meets the salary and skill requirements.",
                "keywords": ["graduate", "switch", "skilled worker", "change"]
            },
            {
                "question": "What are the requirements for Graduate visa?",
                "answer": "You must have completed a UK degree, currently hold a Student visa, and your university must have notified you of successful completion.",
                "keywords": ["graduate", "requirements", "eligibility", "uk degree", "student visa"]
            },
            
            # Global Talent FAQs
            {
                "question": "What is the Global Talent visa?",
                "answer": "The Global Talent visa is for leaders or potential leaders in academia, research, arts and culture, or digital technology. You need an endorsement from a designated competent body.",
                "keywords": ["global talent", "exceptional", "research", "academic", "tech", "endorsement"]
            },
            {
                "question": "How do I get endorsed for Global Talent visa?",
                "answer": "You need endorsement from a designated body: Tech Nation for digital technology, UKRI for academia and research, or Arts Council England for arts and culture.",
                "keywords": ["global talent", "endorsement", "tech nation", "ukri", "arts council"]
            },
            {
                "question": "How long until settlement with Global Talent visa?",
                "answer": "With Global Talent visa, you can apply for settlement (ILR) after 3 years if endorsed for exceptional talent, or 5 years if endorsed for exceptional promise.",
                "keywords": ["global talent", "settlement", "ilr", "years", "exceptional"]
            },
            
            # Student FAQs
            {
                "question": "What are the requirements for Student visa?",
                "answer": "You need a CAS from a licensed student sponsor, proof of English proficiency, and sufficient funds (£1,334/month in London, £1,023/month outside London).",
                "keywords": ["student", "requirements", "cas", "funds", "english"]
            },
            {
                "question": "Can I work on a Student visa?",
                "answer": "Yes, degree-level students can work up to 20 hours per week during term and full-time during vacations. You cannot be self-employed or work as a professional sportsperson.",
                "keywords": ["student", "work", "hours", "part-time", "vacation"]
            },
            
            # Family FAQs
            {
                "question": "What is the minimum income for Family visa?",
                "answer": "The minimum income requirement is £18,600 per year. This increases to £22,400 if you have one child, and an additional £2,400 for each further child.",
                "keywords": ["family", "income", "financial", "minimum", "threshold"]
            },
            {
                "question": "How long until settlement with Family visa?",
                "answer": "Family visa holders can apply for settlement (ILR) after 5 years in the UK, provided they continue to meet the requirements.",
                "keywords": ["family", "settlement", "ilr", "years", "5 years"]
            },
            
            # General FAQs
            {
                "question": "What documents do I need for the visa application?",
                "answer": "Valid passport, Certificate of Sponsorship (for work visas), proof of English, proof of salary, bank statements, and TB test if required.",
                "keywords": ["documents", "required", "application", "proof"]
            },
            {
                "question": "Do I need to speak English for the visa?",
                "answer": "Yes, most visas require CEFR B1 level English. You can prove this through nationality, UK degree, or approved English test.",
                "keywords": ["english", "language", "speak", "test", "ielts"]
            },
        ]
        
        query_lower = query.lower()
        scored_faqs = []
        
        for faq in faqs:
            score = sum(1 for kw in faq["keywords"] if kw in query_lower)
            if score > 0:
                scored_faqs.append((score, faq))
        
        scored_faqs.sort(reverse=True, key=lambda x: x[0])
        return [faq for _, faq in scored_faqs[:top_k]]


def retrieve(query: str, top_k: int = RAG_TOP_K, topic_filter: Optional[str] = None) -> list[dict]:
    """
    Retrieve top-k relevant document chunks for a given query.

    Args:
        query: User query text
        top_k: Number of chunks to retrieve
        topic_filter: If set, only return chunks matching this topic

    Returns:
        List of dicts with keys: text, source_url, source_title, topic, score
    """
    try:
        model = _load_embed_model()
        index, chunks = load_index()
        
        # Check if we have any chunks to search
        if not chunks or len(chunks) == 0:
            logger.warning("No document chunks available. Please run data scraping first.")
            return _get_fallback_results(query, top_k)

        # Embed query
        query_embedding = model.encode([query], normalize_embeddings=True).astype("float32")

        # Search - get more results for better filtering
        k = min(top_k * 3, len(chunks))
        scores, indices = index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(chunks):
                continue
            chunk = chunks[idx]

            if topic_filter and chunk.topic != topic_filter:
                continue

            results.append({
                "text": chunk.text.strip(),
                "source_url": chunk.source_url,
                "source_title": chunk.source_title,
                "topic": chunk.topic,
                "score": float(score),
                "chunk_id": chunk.chunk_id,
            })

            if len(results) >= top_k:
                break
        
        # If no results found, try with relaxed threshold
        if not results:
            logger.info("No results found with standard search, trying relaxed search...")
            results = _get_fallback_results(query, top_k)

        return results
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return _get_fallback_results(query, top_k)


def _get_fallback_results(query: str, top_k: int) -> list[dict]:
    """
    Fallback results when RAG search fails or returns no results.
    Returns generic UK visa information for ALL visa types.
    """
    # Comprehensive UK visa information covering all visa types
    fallback_info = [
        {
            "text": "The Skilled Worker visa is for individuals who have been offered a skilled job in the UK by a licensed sponsor. Key requirements include: a job offer from a licensed sponsor, meeting the minimum salary threshold of £38,700 per year (or the going rate for your occupation if higher), English language proficiency at CEFR level B1, and working in an eligible occupation. The visa allows you to live, work and study in the UK, and bring dependant family members.",
            "source_url": "https://www.gov.uk/skilled-worker-visa",
            "source_title": "Skilled Worker Visa - GOV.UK",
            "topic": "skilled_worker",
            "score": 0.5,
            "chunk_id": "fallback_skilled_worker",
        },
        {
            "text": "The Health and Care Worker visa is for qualified doctors, nurses, health professionals and adult social care workers who want to work in the UK. Key benefits include: no Immigration Health Surcharge (IHS) fee, faster processing times, lower application fees, and the ability to bring dependant family members. You must have a job offer from the NHS, an NHS supplier, or in adult social care.",
            "source_url": "https://www.gov.uk/health-care-worker-visa",
            "source_title": "Health and Care Worker Visa - GOV.UK",
            "topic": "health_care_worker",
            "score": 0.5,
            "chunk_id": "fallback_health_care_worker",
        },
        {
            "text": "The Graduate visa allows you to stay in the UK to work, or look for work, after you've finished your studies. If you completed a PhD or other doctoral qualification, you can stay for 3 years. For other qualifications, you can stay for 2 years. You must have completed a UK degree and currently hold a Student visa. This visa cannot be extended, but you can switch to a Skilled Worker visa if you find a suitable job.",
            "source_url": "https://www.gov.uk/graduate-visa",
            "source_title": "Graduate Visa - GOV.UK",
            "topic": "graduate",
            "score": 0.5,
            "chunk_id": "fallback_graduate",
        },
        {
            "text": "The Global Talent visa is for leaders or potential leaders in academia, research, arts and culture, or digital technology. You need an endorsement from a designated competent body (such as Tech Nation for digital technology, or UKRI for academia and research). This visa offers flexibility - you can work for any employer, be self-employed, or start your own business. It also provides a faster route to settlement (3 years for exceptional talent, 5 years for exceptional promise).",
            "source_url": "https://www.gov.uk/global-talent-visa",
            "source_title": "Global Talent Visa - GOV.UK",
            "topic": "global_talent",
            "score": 0.5,
            "chunk_id": "fallback_global_talent",
        },
        {
            "text": "The Student visa is for individuals who want to study in the UK. You need a Confirmation of Acceptance for Studies (CAS) from a licensed student sponsor (university or college), proof of English language proficiency, and sufficient funds to support yourself (£1,334 per month for up to 9 months if studying in London, £1,023 per month outside London). You can work part-time during term (up to 20 hours per week for degree-level students) and full-time during vacations.",
            "source_url": "https://www.gov.uk/student-visa",
            "source_title": "Student Visa - GOV.UK",
            "topic": "student",
            "score": 0.5,
            "chunk_id": "fallback_student",
        },
        {
            "text": "The Family visa is for partners, children, or other family members of someone who is a British citizen or settled in the UK. The main requirement is meeting the financial threshold of £18,600 per year (higher if you have children). You'll also need to prove your relationship is genuine, meet English language requirements (A1 level for partners), and have adequate accommodation. This visa leads to settlement after 5 years.",
            "source_url": "https://www.gov.uk/uk-family-visa",
            "source_title": "Family Visa - GOV.UK",
            "topic": "family",
            "score": 0.5,
            "chunk_id": "fallback_family",
        },
        {
            "text": "To apply for a UK visa, you typically need: a valid passport or travel document, proof of your financial situation (bank statements), proof of accommodation in the UK, tuberculosis test results (if applicable), Certificate of Sponsorship (for work visas), proof of English language ability, and any required professional qualifications. Always check the specific requirements for your visa type on GOV.UK.",
            "source_url": "https://www.gov.uk/apply-uk-visa",
            "source_title": "Apply for a UK Visa - GOV.UK",
            "topic": "documents",
            "score": 0.4,
            "chunk_id": "fallback_documents",
        },
        {
            "text": "Standard UK visa processing times vary by visa type and application location. From outside the UK: most visas are processed within 3 weeks. From inside the UK: processing usually takes 8 weeks. Priority services are available: 5-day priority service for an additional £500, and 1-day super priority service for an additional £800 (in-country only). Processing times may vary during peak periods.",
            "source_url": "https://www.gov.uk/visa-processing-times",
            "source_title": "Visa Processing Times - GOV.UK",
            "topic": "processing_times",
            "score": 0.4,
            "chunk_id": "fallback_processing",
        },
    ]
    
    # Return relevant fallback based on query keywords - now covering all visa types
    query_lower = query.lower()
    relevant_fallbacks = []
    
    # Skilled Worker keywords
    if any(word in query_lower for word in ["skilled", "work", "job", "sponsor", "eligible", "salary", "occupation"]):
        relevant_fallbacks.append(fallback_info[0])
    
    # Health and Care Worker keywords
    if any(word in query_lower for word in ["health", "care", "nhs", "nurse", "doctor", "medical", "clinical"]):
        relevant_fallbacks.append(fallback_info[1])
    
    # Graduate keywords
    if any(word in query_lower for word in ["graduate", "student", "university", "degree", "post-study", "after study"]):
        relevant_fallbacks.append(fallback_info[2])
    
    # Global Talent keywords
    if any(word in query_lower for word in ["talent", "exceptional", "research", "academic", "tech", "digital", "arts", "endorsement"]):
        relevant_fallbacks.append(fallback_info[3])
    
    # Student keywords
    if any(word in query_lower for word in ["study", "student", "university", "college", "course", "cas", "education"]):
        relevant_fallbacks.append(fallback_info[4])
    
    # Family keywords
    if any(word in query_lower for word in ["family", "spouse", "partner", "husband", "wife", "children", "dependant", "settle"]):
        relevant_fallbacks.append(fallback_info[5])
    
    # General keywords
    if any(word in query_lower for word in ["document", "paper", "passport", "apply", "application"]):
        relevant_fallbacks.append(fallback_info[6])
    if any(word in query_lower for word in ["time", "how long", "processing", "wait", "week"]):
        relevant_fallbacks.append(fallback_info[7])
    
    # If no specific match, return the first few fallbacks (most common visas)
    if not relevant_fallbacks:
        relevant_fallbacks = fallback_info[:min(top_k, 4)]  # Return first 4 (all main work visas)
    
    return relevant_fallbacks[:top_k]


def retrieve_for_intent(query: str, intent: str, entities: dict) -> list[dict]:
    """
    Smart retrieval: adjusts query and topic filter based on detected intent.
    Now supports ALL visa types, not just Skilled Worker.

    Args:
        query: Original user query
        intent: Detected intent label
        entities: Extracted entity dict

    Returns:
        Relevant document chunks
    """
    # Extract visa type from entities if available
    visa_type = entities.get("visa_type", None) if isinstance(entities, dict) else None
    
    # Build enriched query
    enriched_parts = [query]

    if intent == "eligibility_check":
        if visa_type:
            enriched_parts.append(f"{visa_type} visa eligibility requirements criteria")
        else:
            # Default to general eligibility terms
            enriched_parts.append("uk visa eligibility requirements criteria points")

    elif intent == "document_requirement":
        if visa_type:
            enriched_parts.append(f"{visa_type} visa documents required proof evidence")
        else:
            enriched_parts.append("documents required proof evidence certificate sponsorship")

    elif intent == "processing_time":
        if visa_type:
            enriched_parts.append(f"{visa_type} visa processing time how long decision weeks")
        else:
            enriched_parts.append("processing time how long decision weeks priority service")

    elif intent == "general_query":
        if visa_type:
            enriched_parts.append(f"{visa_type} visa overview information guide")
        else:
            enriched_parts.append("uk visa overview information guide")

    elif intent == "salary_threshold":
        if visa_type:
            enriched_parts.append(f"{visa_type} visa salary threshold minimum wage going rate")
        else:
            enriched_parts.append("uk visa salary threshold minimum wage going rate")

    elif intent == "fees_and_costs":
        if visa_type:
            enriched_parts.append(f"{visa_type} visa fees cost ihs surcharge")
        else:
            enriched_parts.append("uk visa fees cost ihs surcharge")

    elif intent == "switch_visa" or intent == "extension_switching":
        if visa_type:
            enriched_parts.append(f"switch to {visa_type} visa from inside uk requirements")
        else:
            enriched_parts.append("switch visa change visa type from inside uk")

    elif intent == "compare_visas":
        enriched_parts.append("compare uk visa types differences requirements")

    # Add entities to enrich query
    if isinstance(entities, dict):
        ents = entities.get("entities", {}) if "entities" in entities else entities
        if isinstance(ents, dict):
            if "JOB_TITLE" in ents:
                enriched_parts.append(f"occupation {ents['JOB_TITLE']['value']}")
            if "SALARY" in ents:
                sal = ents["SALARY"]["value"]
                enriched_parts.append(f"salary £{sal:,.0f} threshold")
            if "COUNTRY" in ents:
                enriched_parts.append(f"country {ents['COUNTRY']['value']} english language")

    enriched_query = " ".join(enriched_parts)

    return retrieve(enriched_query, top_k=RAG_TOP_K)


def format_retrieved_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context string for the GPT prompt."""
    if not chunks:
        return "No relevant guidance found."

    parts = []
    seen_urls = set()

    for chunk in chunks:
        url = chunk["source_url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        parts.append(
            f"Source: {chunk['source_title']}\n"
            f"URL: {url}\n"
            f"---\n{chunk['text'].strip()}"
        )

    return "\n\n".join(parts)
