"""
Atlas AI — NLP Preprocessing Layer
Text cleaning, tokenization, and normalisation before model inference.
"""

import re
import unicodedata
from typing import Optional


# Common UK salary patterns
_SALARY_PATTERNS = [
    r'£[\d,]+(?:\.\d{1,2})?(?:\s*(?:k|thousand|per year|p\.?a\.?|annual(?:ly)?|a year|yearly))?',
    r'[\d,]+(?:\.\d{1,2})?(?:\s*(?:k|thousand))?\s*(?:pounds?|gbp|sterling)',
    r'salary\s+of\s+[\d,£]+',
]

_CURRENCY_RE = re.compile("|".join(_SALARY_PATTERNS), re.IGNORECASE)

# Patterns for SOC codes
_SOC_RE = re.compile(r'\b(soc\s*[-:]?\s*)?(\d{4})\b', re.IGNORECASE)

# Patterns for ages
_AGE_RE = re.compile(
    r'\b(\d{1,2})\s*(?:years?\s*(?:old|of\s*age)?|y/o|yr\s*old)\b',
    re.IGNORECASE
)


def clean_text(text: str) -> str:
    """
    Clean and normalise input text:
    - Normalise unicode
    - Collapse whitespace
    - Strip leading/trailing whitespace
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def extract_salary_from_text(text: str) -> Optional[float]:
    """
    Extract salary value from raw text and normalise to annual GBP.
    Handles: £38700, £38.7k, 50 thousand pounds, etc.
    """
    text_lower = text.lower()

    # Try to find a currency/salary pattern
    match = _CURRENCY_RE.search(text)
    if not match:
        return None

    raw = match.group(0)

    # Remove non-numeric chars except . and k
    numeric_part = re.sub(r'[^0-9.k]', '', raw.lower())

    if 'k' in numeric_part:
        numeric_part = numeric_part.replace('k', '')
        try:
            value = float(numeric_part) * 1000
        except ValueError:
            return None
    else:
        try:
            value = float(numeric_part.replace(',', ''))
        except ValueError:
            return None

    # Sanity check: reasonable UK salary range
    if value < 5000:
        value *= 1000  # Might be given in thousands without 'k'
    if value < 1000 or value > 5_000_000:
        return None

    return value


def extract_salary_from_text_or_bare(text: str):
    """
    Like extract_salary_from_text but also accepts bare numbers as salary.
    Used in dialogue clarification when user types just a number.
    """
    # Try primary extraction first
    result = extract_salary_from_text(text)
    if result is not None:
        return result
    # Try bare number (user typed just digits, possibly with commas)
    import re
    bare = re.sub(r'[,\s]', '', text.strip())
    if re.fullmatch(r'\d+', bare):
        val = float(bare)
        if 5000 <= val <= 500000:
            return val
        if 50 <= val < 500:
            return val * 1000  # e.g. "50" -> 50,000
    return None


def extract_age_from_text(text: str) -> Optional[int]:
    """Extract age value from text."""
    match = _AGE_RE.search(text)
    if match:
        age = int(match.group(1))
        if 16 <= age <= 80:
            return age
    return None


def extract_soc_code_from_text(text: str) -> Optional[str]:
    """Extract a 4-digit SOC code from text if present."""
    match = _SOC_RE.search(text)
    if match:
        return match.group(2)
    return None


def normalise_country_name(country: str) -> str:
    """Normalise common country name variants."""
    mapping = {
        "usa": "United States of America",
        "us": "United States of America",
        "america": "United States of America",
        "uk": "United Kingdom",
        "britain": "United Kingdom",
        "great britain": "United Kingdom",
        "england": "United Kingdom",
        "uae": "United Arab Emirates",
        "uae": "United Arab Emirates",
        "south korea": "Republic of Korea",
        "north korea": "Democratic People's Republic of Korea",
    }
    return mapping.get(country.lower().strip(), country.strip().title())


def preprocess_for_model(text: str) -> str:
    """
    Full preprocessing pipeline for model input:
    clean + lower-case + remove special chars.
    """
    text = clean_text(text)
    # Keep alphanumeric, spaces, common punctuation
    text = re.sub(r'[^a-zA-Z0-9\s£.,?!\'"-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate_for_model(text: str, max_tokens: int = 512) -> str:
    """
    Rough truncation to avoid exceeding model token limit.
    ~4 chars per token heuristic.
    """
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        return text[:max_chars]
    return text
