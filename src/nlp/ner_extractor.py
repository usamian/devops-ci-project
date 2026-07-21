"""
Atlas AI — Named Entity Recognition (NER) Extractor
Extracts immigration-relevant entities from user queries:
  - JOB_TITLE
  - SALARY
  - AGE
  - COUNTRY
  - VISA_TYPE

Uses fine-tuned BERT NER model when available, with regex/SpaCy fallback.
"""

import re
from typing import Optional

from config import NER_MODEL_PATH, NER_CONFIDENCE_THRESHOLD
from src.nlp.preprocessor import (
    clean_text, extract_salary_from_text,
    extract_age_from_text, extract_soc_code_from_text,
    normalise_country_name, truncate_for_model
)

# ── Lazy model loading ────────────────────────────────────────────────────────
_ner_pipeline = None


def _load_ner_model():
    global _ner_pipeline
    if _ner_pipeline is not None:
        return _ner_pipeline

    if not NER_MODEL_PATH.exists():
        return None

    try:
        from transformers import pipeline as hf_pipeline
        _ner_pipeline = hf_pipeline(
            "ner",
            model=str(NER_MODEL_PATH),
            tokenizer=str(NER_MODEL_PATH),
            aggregation_strategy="simple",
            device=-1,
        )
        return _ner_pipeline
    except Exception as e:
        print(f"[NER] Could not load model: {e}. Using rule-based fallback.")
        return None


# ── Known Countries (partial list for regex fallback) ─────────────────────────
COUNTRY_NAMES = {
    "india", "pakistan", "nigeria", "philippines", "zimbabwe", "south africa",
    "kenya", "ghana", "bangladesh", "sri lanka", "nepal", "china", "hong kong",
    "malaysia", "indonesia", "brazil", "colombia", "mexico", "argentina",
    "ukraine", "russia", "poland", "romania", "bulgaria", "hungary",
    "france", "germany", "spain", "italy", "portugal", "netherlands",
    "australia", "new zealand", "canada", "usa", "united states",
    "united states of america", "ireland", "scotland", "wales", "uk",
    "united kingdom", "uae", "saudi arabia", "egypt", "ethiopia",
    "tanzania", "uganda", "zambia", "cameroon", "senegal", "morocco",
    "turkey", "iran", "iraq", "afghanistan", "syria", "jordan",
    "thailand", "vietnam", "south korea", "japan", "singapore",
    "taiwan", "myanmar", "cambodia", "laos",
}

VISA_TYPES = {
    "skilled worker": "skilled_worker",
    "skilled worker visa": "skilled_worker",
    "tier 2": "skilled_worker",  # Legacy name
    "health and care": "health_care_worker",
    "health and care worker": "health_care_worker",
    "student visa": "student",
    "student": "student",
    "graduate visa": "graduate",
    "graduate": "graduate",
    "global talent": "global_talent",
    "global talent visa": "global_talent",
    "innovator founder": "innovator_founder",
    "family visa": "family",
    "spouse visa": "family",
    "partner visa": "family",
    "visitor visa": "visitor",
    "standard visitor": "visitor",
}

_COUNTRY_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(c) for c in sorted(COUNTRY_NAMES, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)

_VISA_TYPE_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(v) for v in sorted(VISA_TYPES.keys(), key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)

# Job title patterns  
_JOB_TITLE_KEYWORDS = [
    "software engineer", "software developer", "data scientist", "data analyst",
    "machine learning engineer", "devops engineer", "cloud engineer",
    "backend developer", "frontend developer", "full stack developer",
    "nurse", "doctor", "physician", "pharmacist", "dentist",
    "physiotherapist", "occupational therapist", "speech therapist",
    "paramedic", "radiographer", "psychologist",
    "civil engineer", "mechanical engineer", "electrical engineer",
    "electronics engineer", "chemical engineer", "production engineer",
    "architect", "structural engineer",
    "teacher", "lecturer", "professor",
    "solicitor", "barrister", "lawyer",
    "accountant", "chartered accountant", "financial analyst",
    "management consultant", "business analyst", "project manager",
    "it manager", "it project manager", "cybersecurity analyst",
    "social worker", "welfare professional",
    "web developer", "web designer",
]

_JOB_RE = re.compile(
    r'\b(?:' + '|'.join(re.escape(j) for j in sorted(_JOB_TITLE_KEYWORDS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)


def _regex_extract(text: str) -> dict:
    """Rule-based extraction using regex patterns."""
    entities = {}
    low_confidence = []
    text_lower = text.lower()

    # Salary
    salary = extract_salary_from_text(text)
    if salary is not None:
        entities["SALARY"] = {"value": salary, "raw": f"£{salary:,.0f}", "confidence": 0.92}

    # Age
    age = extract_age_from_text(text)
    if age is not None:
        entities["AGE"] = {"value": age, "raw": str(age), "confidence": 0.90}

    # Country
    country_match = _COUNTRY_RE.search(text_lower)
    if country_match:
        raw_country = country_match.group(0)
        entities["COUNTRY"] = {
            "value": normalise_country_name(raw_country),
            "raw": raw_country,
            "confidence": 0.88,
        }

    # Job title
    job_match = _JOB_RE.search(text_lower)
    if job_match:
        entities["JOB_TITLE"] = {
            "value": job_match.group(0).title(),
            "raw": job_match.group(0),
            "confidence": 0.85,
        }
    else:
        # Heuristic: look for "work as a X" or "I am a X" patterns
        patterns = [
            r"(?:i(?:'m| am) (?:a |an )?|work(?:ing)? as (?:a |an )?|job (?:is |title )?(?:as )?)([a-z][a-z\s]+?)(?:\s+(?:with|at|in|for|making|earning|currently|and|,|\.|$))",
            r"(?:applying (?:as|for) (?:a |an )?)([a-z][a-z\s]+?)(?:\s+(?:visa|role|position|job|,|\.|$))",
        ]
        for pattern in patterns:
            m = re.search(pattern, text_lower)
            if m:
                candidate = m.group(1).strip()
                if 2 < len(candidate) < 50:
                    entities["JOB_TITLE"] = {
                        "value": candidate.title(),
                        "raw": candidate,
                        "confidence": 0.70,
                    }
                    if 0.70 < NER_CONFIDENCE_THRESHOLD:
                        low_confidence.append("JOB_TITLE")
                    break

    # SOC code
    soc_code = extract_soc_code_from_text(text)
    if soc_code:
        entities["SOC_CODE"] = {"value": soc_code, "raw": soc_code, "confidence": 0.95}

    # Visa type
    visa_match = _VISA_TYPE_RE.search(text_lower)
    if visa_match:
        raw_visa = visa_match.group(0).lower()
        entities["VISA_TYPE"] = {
            "value": VISA_TYPES.get(raw_visa, "skilled_worker"),
            "raw": visa_match.group(0),
            "confidence": 0.88,
        }

    # Sponsorship mentions — check NEGATIVE first to avoid false positives
    negative_sponsor_kws = [
        "no sponsor", "don't have a sponsor", "dont have a sponsor",
        "haven't found a sponsor", "havent found a sponsor",
        "without a sponsor", "no cos", "not yet found a sponsor",
        "haven't got a sponsor", "don't have sponsor yet",
        "i don't have a sponsor", "do not have a sponsor",
    ]
    positive_sponsor_kws = [
        "have a sponsor", "have sponsor", "found a sponsor",
        "have cos", "have a cos", "certificate of sponsorship",
        "my employer will sponsor", "employer is sponsoring",
        "sponsor will", "employer will sponsor",
    ]
    text_lower_nospace = text_lower.replace("'", "").replace('"', "")
    if any(kw in text_lower or kw in text_lower_nospace for kw in negative_sponsor_kws):
        entities["HAS_SPONSOR"] = {"value": False, "raw": "mentioned", "confidence": 0.85}
    elif any(kw in text_lower for kw in positive_sponsor_kws):
        entities["HAS_SPONSOR"] = {"value": True, "raw": "mentioned", "confidence": 0.85}

    # English language
    if any(kw in text_lower for kw in ["ielts", "toefl", "pte", "english test", "english certificate",
                                        "english exam", "passed english"]):
        entities["ENGLISH"] = {"value": "test_passed", "raw": "test mentioned", "confidence": 0.88}

    # Identify low-confidence entities
    for entity_key, entity_val in entities.items():
        if entity_val.get("confidence", 1.0) < NER_CONFIDENCE_THRESHOLD:
            low_confidence.append(entity_key)

    return {"entities": entities, "low_confidence": low_confidence, "source": "fallback"}


def extract_entities(text: str) -> dict:
    """
    Extract named entities from user query.

    Returns:
        {
            "entities": {
                "JOB_TITLE": {"value": str, "raw": str, "confidence": float},
                "SALARY": {"value": float, "raw": str, "confidence": float},
                ...
            },
            "low_confidence": [list of entity types below threshold],
            "source": "model" | "fallback"
        }
    """
    cleaned = clean_text(text)
    pipe = _load_ner_model()

    if pipe is not None:
        try:
            raw_entities = pipe(truncate_for_model(cleaned))
            entities = {}
            low_confidence = []

            for ent in raw_entities:
                etype = ent.get("entity_group", ent.get("entity", "")).upper()
                word = ent.get("word", "").strip()
                score = float(ent.get("score", 0.0))

                if not word or len(word) < 2:
                    continue

                if etype not in entities or score > entities[etype]["confidence"]:
                    entities[etype] = {
                        "value": word,
                        "raw": word,
                        "confidence": round(score, 4),
                    }

                if score < NER_CONFIDENCE_THRESHOLD:
                    low_confidence.append(etype)

            # Post-process salary values
            if "SALARY" in entities:
                val = extract_salary_from_text(entities["SALARY"]["raw"])
                if val:
                    entities["SALARY"]["value"] = val

            if "COUNTRY" in entities:
                entities["COUNTRY"]["value"] = normalise_country_name(entities["COUNTRY"]["value"])

            return {
                "entities": entities,
                "low_confidence": list(set(low_confidence)),
                "source": "model",
            }
        except Exception as e:
            print(f"[NER] Inference error: {e}. Using fallback.")

    # Regex/rule fallback
    return _regex_extract(cleaned)


def entities_to_profile_updates(entities: dict) -> dict:
    """
    Convert extracted entities dict to ApplicantProfile field updates.
    Returns a dict of field:value pairs to merge into the profile.
    """
    updates = {}
    ents = entities.get("entities", {})

    if "JOB_TITLE" in ents:
        updates["job_title"] = ents["JOB_TITLE"]["value"]
    if "SOC_CODE" in ents:
        updates["soc_code"] = ents["SOC_CODE"]["value"]
    if "SALARY" in ents:
        updates["salary_annual"] = ents["SALARY"]["value"]
    if "AGE" in ents:
        updates["age"] = ents["AGE"]["value"]
    if "COUNTRY" in ents:
        updates["country_of_origin"] = ents["COUNTRY"]["value"]
    if "VISA_TYPE" in ents:
        updates["visa_type"] = ents["VISA_TYPE"]["value"]
    if "HAS_SPONSOR" in ents:
        updates["has_sponsor"] = ents["HAS_SPONSOR"]["value"]
    if "ENGLISH" in ents:
        updates["english_proficiency"] = ents["ENGLISH"]["value"]

    return updates
