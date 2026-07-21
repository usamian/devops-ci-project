"""
Atlas AI — Canonicalization Module
Provides mapping and normalization for:
- SOC codes (Standard Occupational Classification)
- Currencies (to GBP)
- Qualification equivalence (to UK NARIC levels)
- Country names (ISO standardization)

This module ensures consistent, standardized data processing
as specified in the proposal.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from src.core.config import AtlasConfig


class UKQualificationLevel(Enum):
    """UK NARIC qualification levels."""
    LEVEL_1 = "1"  # GCSE grades D-G
    LEVEL_2 = "2"  # GCSE grades A*-C
    LEVEL_3 = "3"  # A-Levels, Scottish Highers
    LEVEL_4 = "4"  # Certificate of Higher Education
    LEVEL_5 = "5"  # Diploma of Higher Education, Foundation Degree
    LEVEL_6 = "6"  # Bachelor's Degree with Honours
    LEVEL_7 = "7"  # Master's Degree
    LEVEL_8 = "8"  # Doctoral Degree (PhD)


@dataclass
class SOCCodeMatch:
    """Result of SOC code matching."""
    soc_code: str
    title: str
    confidence: float
    going_rate: float
    new_entrant_rate: float
    eligible: bool
    shortage_occupation: bool
    rqf_level: int
    source_url: str


@dataclass
class QualificationMatch:
    """Result of qualification matching."""
    original_qualification: str
    uk_level: UKQualificationLevel
    confidence: float
    description: str
    source: str  # e.g., "UK NARIC", "ECCTIS"


class SOCCodeMapper:
    """
    Maps job titles to SOC (Standard Occupational Classification) codes.
    Uses ONS data and GOV.UK Immigration Salary List.
    """
    
    def __init__(self, occupation_data_path: Optional[Path] = None):
        self.occupation_data_path = occupation_data_path or (
            AtlasConfig.RULES_DIR / "occupation_codes.json"
        )
        self._occupations: List[Dict[str, Any]] = []
        self._shortage_codes: set = set()
        self._load_data()
    
    def _load_data(self):
        """Load occupation data from JSON file."""
        try:
            with open(self.occupation_data_path, 'r') as f:
                data = json.load(f)
                self._occupations = data.get("occupations", [])
                shortage_data = data.get("shortage_occupations", {})
                self._shortage_codes = set(shortage_data.get("soc_codes", []))
                self._job_aliases = data.get("job_title_aliases", {})
        except (FileNotFoundError, json.JSONDecodeError):
            self._occupations = self._get_default_occupations()
            self._shortage_codes = self._get_default_shortage_codes()
            self._job_aliases = {}
    
    def _get_default_occupations(self) -> List[Dict[str, Any]]:
        """Default occupation data if file not found."""
        return [
            {
                "soc_code": "2136",
                "title": "Programmer",
                "alt_titles": ["Software Engineer", "Software Developer", "Developer", "Coder"],
                "going_rate_annual": 41500,
                "new_entrant_rate": 29050,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2135",
                "title": "IT Business Analyst",
                "alt_titles": ["Business Analyst", "Systems Analyst", "IT Analyst"],
                "going_rate_annual": 42500,
                "new_entrant_rate": 29750,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2225",
                "title": "Nurse",
                "alt_titles": ["Registered Nurse", "Staff Nurse", "Clinical Nurse"],
                "going_rate_annual": 29000,
                "new_entrant_rate": 20300,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2211",
                "title": "Medical Practitioner",
                "alt_titles": ["Doctor", "Physician", "GP", "Surgeon", "Consultant"],
                "going_rate_annual": 50000,
                "new_entrant_rate": 35000,
                "eligible": True,
                "rqf_level": 7,
            },
            {
                "soc_code": "2221",
                "title": "Physiotherapist",
                "alt_titles": ["Physical Therapist"],
                "going_rate_annual": 35000,
                "new_entrant_rate": 24500,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2112",
                "title": "Civil Engineer",
                "alt_titles": ["Engineer", "Structural Engineer"],
                "going_rate_annual": 43600,
                "new_entrant_rate": 30520,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2421",
                "title": "Accountant",
                "alt_titles": ["Chartered Accountant", "Auditor", "Tax Accountant"],
                "going_rate_annual": 44000,
                "new_entrant_rate": 30800,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2315",
                "title": "Teacher",
                "alt_titles": ["Secondary Teacher", "Primary Teacher", "High School Teacher"],
                "going_rate_annual": 38700,
                "new_entrant_rate": 27090,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2139",
                "title": "IT Specialist Manager",
                "alt_titles": ["IT Manager", "Tech Lead", "Engineering Manager"],
                "going_rate_annual": 55100,
                "new_entrant_rate": 38570,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2223",
                "title": "Pharmacist",
                "alt_titles": ["Pharmacist", "Clinical Pharmacist"],
                "going_rate_annual": 42000,
                "new_entrant_rate": 29400,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2222",
                "title": "Social Worker",
                "alt_titles": ["Social Worker", "Case Worker"],
                "going_rate_annual": 35000,
                "new_entrant_rate": 24500,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2137",
                "title": "Web Designer",
                "alt_titles": ["Web Developer", "Frontend Developer", "UI Developer"],
                "going_rate_annual": 38000,
                "new_entrant_rate": 26600,
                "eligible": True,
                "rqf_level": 6,
            },
            {
                "soc_code": "2150",
                "title": "Data Scientist",
                "alt_titles": ["Data Analyst", "Machine Learning Engineer", "AI Engineer"],
                "going_rate_annual": 50000,
                "new_entrant_rate": 35000,
                "eligible": True,
                "rqf_level": 7,
            },
        ]
    
    def _get_default_shortage_codes(self) -> set:
        """Default shortage occupation codes."""
        return {"2225", "2231", "2217", "2218", "2221", "2222", "2223", "2219", "3111"}
    
    def map_job_title(self, job_title: str) -> Optional[SOCCodeMatch]:
        """
        Map a job title to its SOC code.
        Returns the best match with confidence score.
        """
        if not job_title:
            return None
        
        job_lower = job_title.lower().strip()
        
        # First, check job title aliases (highest priority)
        if job_lower in self._job_aliases:
            soc_code = self._job_aliases[job_lower]
            return self.get_by_soc_code(soc_code)
        
        # Then, try to find by matching against occupations
        best_match = None
        best_score = 0.0
        
        for occ in self._occupations:
            score = self._calculate_title_match(job_lower, occ)
            if score > best_score and score > 0.5:
                best_score = score
                best_match = occ
        
        if best_match:
            return SOCCodeMatch(
                soc_code=best_match["soc_code"],
                title=best_match["title"],
                confidence=best_score,
                going_rate=best_match.get("going_rate_annual", 0),
                new_entrant_rate=best_match.get("new_entrant_rate", 0),
                eligible=best_match.get("eligible", False),
                shortage_occupation=best_match["soc_code"] in self._shortage_codes,
                rqf_level=best_match.get("rqf_level", 3),
                source_url="https://www.gov.uk/government/publications/skilled-worker-visa-immigration-salary-list",
            )
        return None
    
    def get_by_soc_code(self, soc_code: str) -> Optional[SOCCodeMatch]:
        """Look up occupation by exact SOC code."""
        for occ in self._occupations:
            if occ["soc_code"] == soc_code:
                return SOCCodeMatch(
                    soc_code=occ["soc_code"],
                    title=occ["title"],
                    confidence=1.0,
                    going_rate=occ.get("going_rate_annual", 0),
                    new_entrant_rate=occ.get("new_entrant_rate", 0),
                    eligible=occ.get("eligible", False),
                    shortage_occupation=occ["soc_code"] in self._shortage_codes,
                    rqf_level=occ.get("rqf_level", 3),
                    source_url="https://www.gov.uk/government/publications/skilled-worker-visa-immigration-salary-list",
                )
        return None
    
    def _calculate_title_match(self, job_lower: str, occ: Dict[str, Any]) -> float:
        """Calculate match score between job title and occupation."""
        title_lower = occ["title"].lower()
        alt_titles = [t.lower() for t in occ.get("alt_titles", [])]
        all_titles = [title_lower] + alt_titles
        
        # Exact match
        if job_lower == title_lower or job_lower in all_titles:
            return 1.0
        
        # Contains match
        for t in all_titles:
            if t in job_lower or job_lower in t:
                return 0.85
        
        # Partial word match
        job_words = set(job_lower.split())
        for t in all_titles:
            title_words = set(t.split())
            overlap = len(job_words & title_words) / max(len(job_words), len(title_words))
            if overlap > 0.5:
                return 0.7 * overlap
        
        return 0.0
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search occupations by keyword."""
        query_lower = query.lower().strip()
        results = []
        
        for occ in self._occupations:
            score = self._calculate_title_match(query_lower, occ)
            if score > 0.3:
                results.append({
                    "soc_code": occ["soc_code"],
                    "title": occ["title"],
                    "going_rate": occ.get("going_rate_annual", 0),
                    "eligible": occ.get("eligible", False),
                    "shortage": occ["soc_code"] in self._shortage_codes,
                    "score": score,
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class QualificationMapper:
    """
    Maps international qualifications to UK NARIC levels.
    Based on ECCTIS (formerly UK NARIC) guidelines.
    """
    
    # Common qualification mappings
    QUALIFICATION_MAPPINGS = {
        # UK Qualifications
        "gcse": {"level": UKQualificationLevel.LEVEL_2, "confidence": 0.95},
        "gcses": {"level": UKQualificationLevel.LEVEL_2, "confidence": 0.95},
        "a-level": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.95},
        "a level": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.95},
        "a levels": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.95},
        "scottish higher": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.95},
        "highers": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.95},
        "hnd": {"level": UKQualificationLevel.LEVEL_5, "confidence": 0.90},
        "hnc": {"level": UKQualificationLevel.LEVEL_4, "confidence": 0.90},
        "foundation degree": {"level": UKQualificationLevel.LEVEL_5, "confidence": 0.95},
        "bachelor": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "bachelor's": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.95},
        "bachelors": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.95},
        "bsc": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "ba": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "beng": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "master": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "master's": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.95},
        "masters": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.95},
        "msc": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "ma": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "mba": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.95},
        "phd": {"level": UKQualificationLevel.LEVEL_8, "confidence": 0.95},
        "doctorate": {"level": UKQualificationLevel.LEVEL_8, "confidence": 0.95},
        "dr.": {"level": UKQualificationLevel.LEVEL_8, "confidence": 0.85},
        
        # Indian qualifications
        "bachelor of technology": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "btech": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "b.e.": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "bachelor of engineering": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "master of technology": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "mtech": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "m.e.": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "master of engineering": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "bachelor of commerce": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "b.com": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "bachelor of arts": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "bachelor of science": {"level": UKQualificationLevel.LEVEL_6, "confidence": 0.90},
        "master of commerce": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "m.com": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "master of arts": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        "master of science": {"level": UKQualificationLevel.LEVEL_7, "confidence": 0.90},
        
        # Pakistani qualifications
        "intermediate": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.85},
        "fsc": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.85},
        "fa": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.85},
        "matric": {"level": UKQualificationLevel.LEVEL_2, "confidence": 0.85},
        "ssc": {"level": UKQualificationLevel.LEVEL_2, "confidence": 0.85},
        
        # US qualifications
        "associate degree": {"level": UKQualificationLevel.LEVEL_5, "confidence": 0.90},
        "high school diploma": {"level": UKQualificationLevel.LEVEL_2, "confidence": 0.85},
        
        # European qualifications
        "abitur": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.85},
        "baccalaureate": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.85},
        "bachillerato": {"level": UKQualificationLevel.LEVEL_3, "confidence": 0.85},
    }
    
    # STEM PhD indicators
    STEM_KEYWORDS = {
        "computer science", "data science", "artificial intelligence", 
        "machine learning", "cybersecurity", "software engineering",
        "electrical engineering", "mechanical engineering", "civil engineering",
        "chemical engineering", "biomedical engineering", "aerospace engineering",
        "mathematics", "statistics", "physics", "chemistry", "biology",
        "biochemistry", "molecular biology", "genetics", "neuroscience",
        "pharmacology", "medicine", "surgery", "nursing", "public health",
        "economics", "finance", "accounting", "business analytics",
    }
    
    def map_qualification(self, qualification: str) -> Optional[QualificationMatch]:
        """
        Map a qualification to UK NARIC level.
        """
        if not qualification:
            return None
        
        qual_lower = qualification.lower().strip()
        
        # Check exact matches first
        if qual_lower in self.QUALIFICATION_MAPPINGS:
            mapping = self.QUALIFICATION_MAPPINGS[qual_lower]
            return QualificationMatch(
                original_qualification=qualification,
                uk_level=mapping["level"],
                confidence=mapping["confidence"],
                description=self._get_level_description(mapping["level"]),
                source="UK NARIC/ECCTIS Guidelines",
            )
        
        # Check partial matches
        for key, mapping in self.QUALIFICATION_MAPPINGS.items():
            if key in qual_lower or qual_lower in key:
                return QualificationMatch(
                    original_qualification=qualification,
                    uk_level=mapping["level"],
                    confidence=mapping["confidence"] * 0.9,  # Slightly lower for partial
                    description=self._get_level_description(mapping["level"]),
                    source="UK NARIC/ECCTIS Guidelines",
                )
        
        # Heuristic: look for degree indicators
        if any(kw in qual_lower for kw in ["bachelor", "bsc", "ba", "bachelor's"]):
            return QualificationMatch(
                original_qualification=qualification,
                uk_level=UKQualificationLevel.LEVEL_6,
                confidence=0.80,
                description="Bachelor's degree level",
                source="Heuristic matching",
            )
        elif any(kw in qual_lower for kw in ["master", "msc", "ma", "master's"]):
            return QualificationMatch(
                original_qualification=qualification,
                uk_level=UKQualificationLevel.LEVEL_7,
                confidence=0.80,
                description="Master's degree level",
                source="Heuristic matching",
            )
        elif any(kw in qual_lower for kw in ["phd", "doctorate", "ph.d"]):
            return QualificationMatch(
                original_qualification=qualification,
                uk_level=UKQualificationLevel.LEVEL_8,
                confidence=0.85,
                description="Doctoral degree level",
                source="Heuristic matching",
            )
        
        return None
    
    def is_stem_phd(self, qualification: str, job_title: str = "") -> bool:
        """Check if a PhD is in a STEM field."""
        text = (qualification + " " + job_title).lower()
        return any(kw in text for kw in self.STEM_KEYWORDS)
    
    def _get_level_description(self, level: UKQualificationLevel) -> str:
        """Get human-readable description for qualification level."""
        descriptions = {
            UKQualificationLevel.LEVEL_1: "GCSE grades D-G or equivalent",
            UKQualificationLevel.LEVEL_2: "GCSE grades A*-C or equivalent",
            UKQualificationLevel.LEVEL_3: "A-Level, Scottish Higher or equivalent",
            UKQualificationLevel.LEVEL_4: "Certificate of Higher Education",
            UKQualificationLevel.LEVEL_5: "Diploma of Higher Education, Foundation Degree",
            UKQualificationLevel.LEVEL_6: "Bachelor's Degree with Honours",
            UKQualificationLevel.LEVEL_7: "Master's Degree",
            UKQualificationLevel.LEVEL_8: "Doctoral Degree (PhD)",
        }
        return descriptions.get(level, f"UK Level {level.value}")


class CurrencyCanonicalizer:
    """
    Converts various currency formats to GBP.
    Uses approximate exchange rates for estimation.
    """
    
    # Approximate exchange rates to GBP (as of 2024)
    EXCHANGE_RATES_TO_GBP = {
        "GBP": 1.0,
        "USD": 0.79,
        "EUR": 0.85,
        "INR": 0.0095,
        "PKR": 0.0028,
        "CAD": 0.58,
        "AUD": 0.52,
        "AED": 0.22,
        "SGD": 0.59,
        "HKD": 0.10,
        "CNY": 0.11,
        "JPY": 0.0053,
        "CHF": 0.89,
        "NZD": 0.48,
        "ZAR": 0.042,
        "NGN": 0.00051,
        "PHP": 0.014,
        "BDT": 0.0067,
        "KES": 0.0061,
    }
    
    CURRENCY_SYMBOLS = {
        "£": "GBP",
        "$": "USD",  # Default to USD, context needed for others
        "€": "EUR",
        "₹": "INR",
        "¥": "JPY",
        "A$": "AUD",
        "C$": "CAD",
        "NZ$": "NZD",
        "S$": "SGD",
        "HK$": "HKD",
        "R$": "ZAR",
        "CHF": "CHF",
        "AED": "AED",
        "Dirham": "AED",
        "Rs": "INR",
        "PKR": "PKR",
        "₨": "PKR",
    }
    
    def __init__(self):
        # Build regex pattern for currency detection
        symbols = [re.escape(s) for s in self.CURRENCY_SYMBOLS.keys() if len(s) <= 2]
        names = [re.escape(n) for n in self.CURRENCY_SYMBOLS.keys() if len(n) > 2]
        self._symbol_pattern = re.compile(
            r'([' + ''.join(symbols) + r'])\s*(\d[\d,\.]+)',
            re.IGNORECASE
        )
        self._name_pattern = re.compile(
            r'(\d[\d,\.]+)\s*(' + '|'.join(names) + r')\b',
            re.IGNORECASE
        )
    
    def extract_and_convert(self, text: str) -> Optional[Tuple[float, str]]:
        """
        Extract salary/amount from text and convert to GBP.
        Returns (amount_in_gbp, original_currency) or None.
        """
        # Try symbol pattern
        match = self._symbol_pattern.search(text)
        if match:
            symbol = match.group(1)
            amount_str = match.group(2).replace(',', '')
            try:
                amount = float(amount_str)
                currency = self.CURRENCY_SYMBOLS.get(symbol, "GBP")
                gbp_amount = amount * self.EXCHANGE_RATES_TO_GBP.get(currency, 1.0)
                return (gbp_amount, currency)
            except ValueError:
                pass
        
        # Try name pattern
        match = self._name_pattern.search(text)
        if match:
            amount_str = match.group(1).replace(',', '')
            currency_name = match.group(2)
            try:
                amount = float(amount_str)
                currency = self.CURRENCY_SYMBOLS.get(currency_name, "GBP")
                gbp_amount = amount * self.EXCHANGE_RATES_TO_GBP.get(currency, 1.0)
                return (gbp_amount, currency)
            except ValueError:
                pass
        
        return None
    
    def convert_to_gbp(self, amount: float, from_currency: str) -> float:
        """Convert an amount from a given currency to GBP."""
        rate = self.EXCHANGE_RATES_TO_GBP.get(from_currency.upper(), 1.0)
        return amount * rate


class CountryCanonicalizer:
    """
    Normalizes country names to ISO 3166-1 alpha-2 codes
    and standard full names.
    """
    
    # Common country name variations
    COUNTRY_MAPPINGS = {
        "uk": {"code": "GB", "name": "United Kingdom"},
        "united kingdom": {"code": "GB", "name": "United Kingdom"},
        "great britain": {"code": "GB", "name": "United Kingdom"},
        "england": {"code": "GB", "name": "United Kingdom"},
        "scotland": {"code": "GB", "name": "United Kingdom"},
        "wales": {"code": "GB", "name": "United Kingdom"},
        "northern ireland": {"code": "GB", "name": "United Kingdom"},
        "usa": {"code": "US", "name": "United States of America"},
        "united states": {"code": "US", "name": "United States of America"},
        "united states of america": {"code": "US", "name": "United States of America"},
        "america": {"code": "US", "name": "United States of America"},
        "us": {"code": "US", "name": "United States of America"},
        "india": {"code": "IN", "name": "India"},
        "bharat": {"code": "IN", "name": "India"},
        "pakistan": {"code": "PK", "name": "Pakistan"},
        "bangladesh": {"code": "BD", "name": "Bangladesh"},
        "nigeria": {"code": "NG", "name": "Nigeria"},
        "philippines": {"code": "PH", "name": "Philippines"},
        "china": {"code": "CN", "name": "China"},
        "prc": {"code": "CN", "name": "China"},
        "australia": {"code": "AU", "name": "Australia"},
        "oz": {"code": "AU", "name": "Australia"},
        "canada": {"code": "CA", "name": "Canada"},
        "new zealand": {"code": "NZ", "name": "New Zealand"},
        "kiwi": {"code": "NZ", "name": "New Zealand"},
        "south africa": {"code": "ZA", "name": "South Africa"},
        "rsa": {"code": "ZA", "name": "South Africa"},
        "uae": {"code": "AE", "name": "United Arab Emirates"},
        "united arab emirates": {"code": "AE", "name": "United Arab Emirates"},
        "dubai": {"code": "AE", "name": "United Arab Emirates"},
        "saudi arabia": {"code": "SA", "name": "Saudi Arabia"},
        "ksa": {"code": "SA", "name": "Saudi Arabia"},
        "ireland": {"code": "IE", "name": "Ireland"},
        "roi": {"code": "IE", "name": "Ireland"},
        "germany": {"code": "DE", "name": "Germany"},
        "deutschland": {"code": "DE", "name": "Germany"},
        "france": {"code": "FR", "name": "France"},
        "spain": {"code": "ES", "name": "Spain"},
        "italia": {"code": "IT", "name": "Italy"},
        "italy": {"code": "IT", "name": "Italy"},
        "japan": {"code": "JP", "name": "Japan"},
        "korea": {"code": "KR", "name": "South Korea"},
        "south korea": {"code": "KR", "name": "South Korea"},
        "malaysia": {"code": "MY", "name": "Malaysia"},
        "singapore": {"code": "SG", "name": "Singapore"},
        "sri lanka": {"code": "LK", "name": "Sri Lanka"},
        "ceylon": {"code": "LK", "name": "Sri Lanka"},
        "nepal": {"code": "NP", "name": "Nepal"},
        "kenya": {"code": "KE", "name": "Kenya"},
        "ghana": {"code": "GH", "name": "Ghana"},
        "zimbabwe": {"code": "ZW", "name": "Zimbabwe"},
        "tanzania": {"code": "TZ", "name": "Tanzania"},
        "uganda": {"code": "UG", "name": "Uganda"},
        "ethiopia": {"code": "ET", "name": "Ethiopia"},
        "egypt": {"code": "EG", "name": "Egypt"},
        "turkey": {"code": "TR", "name": "Turkey"},
        "türkiye": {"code": "TR", "name": "Turkey"},
        "iran": {"code": "IR", "name": "Iran"},
        "iraq": {"code": "IQ", "name": "Iraq"},
        "afghanistan": {"code": "AF", "name": "Afghanistan"},
        "syria": {"code": "SY", "name": "Syria"},
        "jordan": {"code": "JO", "name": "Jordan"},
        "lebanon": {"code": "LB", "name": "Lebanon"},
        "poland": {"code": "PL", "name": "Poland"},
        "romania": {"code": "RO", "name": "Romania"},
        "bulgaria": {"code": "BG", "name": "Bulgaria"},
        "hungary": {"code": "HU", "name": "Hungary"},
        "ukraine": {"code": "UA", "name": "Ukraine"},
        "russia": {"code": "RU", "name": "Russian Federation"},
        "brazil": {"code": "BR", "name": "Brazil"},
        "mexico": {"code": "MX", "name": "Mexico"},
        "argentina": {"code": "AR", "name": "Argentina"},
        "colombia": {"code": "CO", "name": "Colombia"},
        "chile": {"code": "CL", "name": "Chile"},
        "peru": {"code": "PE", "name": "Peru"},
        "venezuela": {"code": "VE", "name": "Venezuela"},
        "indonesia": {"code": "ID", "name": "Indonesia"},
        "vietnam": {"code": "VN", "name": "Vietnam"},
        "thailand": {"code": "TH", "name": "Thailand"},
        "myanmar": {"code": "MM", "name": "Myanmar"},
        "cambodia": {"code": "KH", "name": "Cambodia"},
        "laos": {"code": "LA", "name": "Lao People's Democratic Republic"},
        "taiwan": {"code": "TW", "name": "Taiwan"},
        "hong kong": {"code": "HK", "name": "Hong Kong"},
        "macau": {"code": "MO", "name": "Macau"},
    }
    
    def normalize(self, country: str) -> Dict[str, str]:
        """
        Normalize a country name to standard form.
        Returns {"code": ISO code, "name": standard name}
        """
        if not country:
            return {"code": "", "name": ""}
        
        country_lower = country.lower().strip()
        
        # Direct lookup
        if country_lower in self.COUNTRY_MAPPINGS:
            return self.COUNTRY_MAPPINGS[country_lower]
        
        # Try to find partial match
        for key, value in self.COUNTRY_MAPPINGS.items():
            if key in country_lower or country_lower in key:
                return value
        
        # Return as-is if no match
        return {"code": "", "name": country.strip().title()}
    
    def is_english_exempt(self, country: str) -> bool:
        """
        Check if a country is exempt from English language requirement.
        Based on GOV.UK Appendix English Language.
        """
        exempt_countries = {
            "antigua and barbuda", "australia", "bahamas", "barbados", "belize",
            "canada", "dominica", "grenada", "guyana", "jamaica", "malta",
            "new zealand", "st kitts and nevis", "saint kitts and nevis",
            "st lucia", "saint lucia", "st vincent and the grenadines",
            "saint vincent and the grenadines", "trinidad and tobago",
            "united states", "united states of america", "usa",
            "uk", "united kingdom", "ireland",
        }
        return country.lower().strip() in exempt_countries


class Canonicalizer:
    """
    Main canonicalizer class that combines all mapping functionality.
    Provides a unified interface for data normalization.
    """
    
    def __init__(self):
        self.soc_mapper = SOCCodeMapper()
        self.qual_mapper = QualificationMapper()
        self.currency_mapper = CurrencyCanonicalizer()
        self.country_mapper = CountryCanonicalizer()
    
    def canonicalize_job_title(self, job_title: str) -> Optional[SOCCodeMatch]:
        """Map job title to SOC code."""
        return self.soc_mapper.map_job_title(job_title)
    
    def canonicalize_qualification(self, qualification: str) -> Optional[QualificationMatch]:
        """Map qualification to UK NARIC level."""
        return self.qual_mapper.map_qualification(qualification)
    
    def canonicalize_currency(self, text: str) -> Optional[Tuple[float, str]]:
        """Extract and convert currency to GBP."""
        return self.currency_mapper.extract_and_convert(text)
    
    def canonicalize_country(self, country: str) -> Dict[str, str]:
        """Normalize country name."""
        return self.country_mapper.normalize(country)
    
    def is_english_exempt_country(self, country: str) -> bool:
        """Check if country is English language exempt."""
        return self.country_mapper.is_english_exempt(country)
    
    def to_structured_json(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert profile data to the structured JSON format
        specified in the proposal.
        
        Example output format:
        {
            "intent": {"label": "eligibility_check", "confidence": 0.98},
            "slots": {
                "nationality": {"value": "India", "conf": 0.99},
                "job_title": {"value": "software engineer", "conf": 0.92, "soc_code": "2136"},
                "salary_gbp": {"value": 34000, "conf": 0.97},
                "qualification": {"value": "BSc (Hons)", "uk_level": "6", "conf": 0.88},
                "sponsor": {"value": "yes", "conf": 0.63}
            },
            "dialogue_state": "awaiting_sponsor_confirmation"
        }
        """
        slots = {}
        
        # Nationality
        if profile_data.get("country_of_origin"):
            country = self.canonicalize_country(profile_data["country_of_origin"])
            slots["nationality"] = {
                "value": country["name"],
                "code": country["code"],
                "conf": 0.95,
            }
        
        # Job title with SOC code
        if profile_data.get("job_title"):
            soc_match = self.canonicalize_job_title(profile_data["job_title"])
            if soc_match:
                slots["job_title"] = {
                    "value": soc_match.title,
                    "soc_code": soc_match.soc_code,
                    "conf": soc_match.confidence,
                    "going_rate": soc_match.going_rate,
                }
            else:
                slots["job_title"] = {
                    "value": profile_data["job_title"],
                    "conf": 0.60,
                }
        
        # Salary in GBP
        if profile_data.get("salary_annual"):
            slots["salary_gbp"] = {
                "value": profile_data["salary_annual"],
                "conf": 0.95,
            }
        
        # Qualification
        if profile_data.get("qualification"):
            qual_match = self.canonicalize_qualification(profile_data["qualification"])
            if qual_match:
                slots["qualification"] = {
                    "value": profile_data["qualification"],
                    "uk_level": qual_match.uk_level.value,
                    "conf": qual_match.confidence,
                    "is_stem": self.qual_mapper.is_stem_phd(
                        profile_data.get("qualification", ""),
                        profile_data.get("job_title", ""),
                    ),
                }
        
        # Sponsor
        if profile_data.get("has_sponsor") is not None:
            slots["sponsor"] = {
                "value": "yes" if profile_data["has_sponsor"] else "no",
                "conf": 0.95,
            }
        
        return {
            "intent": {
                "label": profile_data.get("intent", "eligibility_check"),
                "confidence": profile_data.get("intent_confidence", 0.90),
            },
            "slots": slots,
            "dialogue_state": profile_data.get("dialogue_state", "collecting"),
        }


# Global canonicalizer instance
canonicalizer = Canonicalizer()