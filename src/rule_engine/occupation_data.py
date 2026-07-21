"""
Atlas AI — Occupation Data Loader
Loads ONS SOC codes and going rates from official data files.
Source: GOV.UK Appendix Skilled Occupations
"""

import json
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher

from config import RULES_DIR

_occupation_data: Optional[dict] = None


def _load_data() -> dict:
    global _occupation_data
    if _occupation_data is None:
        path = RULES_DIR / "occupation_codes.json"
        with open(path, encoding="utf-8") as f:
            _occupation_data = json.load(f)
    return _occupation_data


def get_occupation_by_soc(soc_code: str) -> Optional[dict]:
    """Return occupation record for a given SOC code."""
    data = _load_data()
    for occ in data["occupations"]:
        if occ["soc_code"] == soc_code:
            return occ
    return None


def get_occupation_by_title(job_title: str) -> Optional[dict]:
    """
    Return occupation record by job title using:
    1. Exact match against aliases dictionary
    2. Fuzzy match against occupation titles
    Returns the occupation dict or None if not found.
    """
    data = _load_data()
    title_lower = job_title.lower().strip()

    # 1. Check aliases
    aliases = data.get("job_title_aliases", {})
    if title_lower in aliases:
        soc_code = aliases[title_lower]
        return get_occupation_by_soc(soc_code)

    # 2. Fuzzy match against alias keys
    best_alias_score = 0.0
    best_alias_soc = None
    for alias_key, soc in aliases.items():
        score = SequenceMatcher(None, title_lower, alias_key).ratio()
        if score > best_alias_score:
            best_alias_score = score
            best_alias_soc = soc

    # 3. Fuzzy match against occupation titles
    best_title_score = 0.0
    best_occ = None
    for occ in data["occupations"]:
        score = SequenceMatcher(None, title_lower, occ["title"].lower()).ratio()
        if score > best_title_score:
            best_title_score = score
            best_occ = occ

    # Choose best match if above threshold
    threshold = 0.65
    if best_alias_score >= threshold and best_alias_score >= best_title_score:
        return get_occupation_by_soc(best_alias_soc)
    elif best_title_score >= threshold:
        return best_occ

    return None


def is_shortage_occupation(soc_code: str) -> bool:
    """Check if a SOC code is on the shortage occupation list."""
    data = _load_data()
    shortage_codes = data.get("shortage_occupations", {}).get("soc_codes", [])
    return soc_code in shortage_codes


def get_going_rate(soc_code: str) -> Optional[float]:
    """Get the annual going rate for an SOC code."""
    occ = get_occupation_by_soc(soc_code)
    return occ["going_rate_annual"] if occ else None


def get_new_entrant_rate(soc_code: str) -> Optional[float]:
    """Get the new entrant annual salary rate for an SOC code."""
    occ = get_occupation_by_soc(soc_code)
    return occ["new_entrant_rate"] if occ else None


def is_eligible_occupation(soc_code: str) -> bool:
    """Check if an occupation is on the eligible list."""
    occ = get_occupation_by_soc(soc_code)
    return bool(occ and occ.get("eligible", False))


def search_occupations(query: str, top_k: int = 5) -> list[dict]:
    """Search for matching occupations given a free-text query."""
    data = _load_data()
    query_lower = query.lower()
    scored = []

    for occ in data["occupations"]:
        if occ["soc_code"] == "9999":
            continue
        title_lower = occ["title"].lower()
        score = SequenceMatcher(None, query_lower, title_lower).ratio()
        # Also boost score if any word from query is in title
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        word_overlap = len(query_words & title_words) / max(len(query_words), 1)
        final_score = 0.6 * score + 0.4 * word_overlap
        scored.append((final_score, occ))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [occ for _, occ in scored[:top_k]]


def get_all_eligible_occupations() -> list[dict]:
    """Return all eligible occupations."""
    data = _load_data()
    return [o for o in data["occupations"] if o.get("eligible") and o["soc_code"] != "9999"]
