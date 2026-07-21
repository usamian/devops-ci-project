"""
Atlas AI — Rule Engine Base Classes
All eligibility determination is done exclusively by rule-based logic,
never by ML models. This ensures determinism and traceability.

Aligned with proposal specifications for transparent, auditable decision-making.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class Verdict(str, Enum):
    """Eligibility verdict types."""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    INSUFFICIENT_INFO = "insufficient_info"


@dataclass
class RuleResult:
    """
    Result of evaluating a single rule.
    Each rule result is traceable to official GOV.UK sources.
    """
    rule_id: str
    rule_description: str
    passed: bool
    reason: str
    source_url: str
    source_section: str = ""
    severity: str = "mandatory"  # mandatory | advisory | disqualifying
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rule_id": self.rule_id,
            "rule_description": self.rule_description,
            "passed": self.passed,
            "reason": self.reason,
            "source_url": self.source_url,
            "source_section": self.source_section,
            "severity": self.severity,
        }


@dataclass
class EligibilityResult:
    """
    Aggregated result of all rule checks for a visa application.
    Contains full trace of all rule evaluations.
    """
    verdict: Verdict
    visa_type: str
    rule_results: list[RuleResult] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)
    points_earned: int = 0
    points_required: int = 70
    summary: str = ""
    trace_id: str = field(default_factory=lambda: "")
    
    @property
    def passed_rules(self) -> list[RuleResult]:
        """Get all passed rules."""
        return [r for r in self.rule_results if r.passed]
    
    @property
    def failed_rules(self) -> list[RuleResult]:
        """Get all failed rules."""
        return [r for r in self.rule_results if not r.passed]
    
    @property
    def mandatory_failed(self) -> list[RuleResult]:
        """Get failed mandatory rules."""
        return [r for r in self.failed_rules if r.severity == "mandatory"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "verdict": self.verdict.value,
            "visa_type": self.visa_type,
            "points_earned": self.points_earned,
            "points_required": self.points_required,
            "summary": self.summary,
            "trace_id": self.trace_id,
            "passed_rules": [r.to_dict() for r in self.passed_rules],
            "failed_rules": [r.to_dict() for r in self.failed_rules],
            "missing_info": self.missing_info,
            "gov_uk_sources": list(set(
                r.source_url for r in self.rule_results if r.source_url
            )),
        }
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary for audit logging."""
        return {
            "verdict": self.verdict.value,
            "visa_type": self.visa_type,
            "trace_id": self.trace_id,
            "total_rules": len(self.rule_results),
            "passed_count": len(self.passed_rules),
            "failed_count": len(self.failed_rules),
            "points": f"{self.points_earned}/{self.points_required}",
        }


@dataclass
class ApplicantProfile:
    """
    Structured representation of applicant information collected from dialogue.
    Maps to the structured JSON format specified in the proposal.
    """
    # ── Core Identity ──────────────────────────────────────────────────────────
    job_title: Optional[str] = None
    soc_code: Optional[str] = None
    salary_annual: Optional[float] = None
    age: Optional[int] = None
    country_of_origin: Optional[str] = None
    
    # ── Sponsorship ────────────────────────────────────────────────────────────
    has_sponsor: Optional[bool] = None
    sponsor_licence_number: Optional[str] = None
    
    # ── English Language ───────────────────────────────────────────────────────
    english_proficiency: Optional[str] = None  # "native" | "test_passed" | "none" | "exempt"
    english_test_type: Optional[str] = None  # "ielts" | "toefl" | "pte" etc.
    english_test_score: Optional[str] = None
    
    # ── Qualifications ─────────────────────────────────────────────────────────
    qualification: Optional[str] = None
    qualification_level: Optional[str] = None  # UK NARIC level
    is_stem_qualification: Optional[bool] = None
    has_phd: Optional[bool] = None
    is_stem_phd: Optional[bool] = None
    
    # ── Financial ──────────────────────────────────────────────────────────────
    savings: Optional[float] = None
    sponsor_certifies_maintenance: Optional[bool] = None
    
    # ── Immigration History ────────────────────────────────────────────────────
    current_visa_type: Optional[str] = None
    previous_uk_visas: Optional[bool] = None
    previous_refusals: Optional[bool] = None
    criminal_record: Optional[bool] = None
    
    # ── Special Categories ─────────────────────────────────────────────────────
    is_new_entrant: Optional[bool] = None
    shortage_occupation: Optional[bool] = None
    health_care_worker: Optional[bool] = None
    
    # ── Visa Selection ─────────────────────────────────────────────────────────
    visa_type: str = "skilled_worker"
    
    # ── Methods ────────────────────────────────────────────────────────────────
    
    def missing_fields(self) -> list[str]:
        """Return list of fields needed but not yet provided."""
        required = []
        
        # Job/Occupation
        if self.job_title is None and self.soc_code is None:
            required.append("job_title")
        
        # Salary
        if self.salary_annual is None:
            required.append("salary")
        
        # Sponsorship
        if self.has_sponsor is None:
            required.append("sponsorship")
        
        # Country
        if self.country_of_origin is None:
            required.append("country_of_origin")
        
        return required
    
    def is_complete(self) -> bool:
        """Check if all required fields are provided."""
        return len(self.missing_fields()) == 0
    
    def get_critical_slots(self) -> Dict[str, Any]:
        """
        Get critical slots as specified in proposal.
        Returns dict with value and confidence for each critical field.
        """
        slots = {}
        
        if self.country_of_origin:
            slots["nationality"] = {"value": self.country_of_origin, "conf": 0.95}
        
        if self.salary_annual:
            slots["salary_gbp"] = {"value": self.salary_annual, "conf": 0.95}
        
        if self.job_title:
            slots["job_title"] = {"value": self.job_title, "conf": 0.90}
        
        if self.soc_code:
            if "job_title" not in slots:
                slots["job_title"] = {"value": f"SOC {self.soc_code}", "conf": 0.95}
            slots["soc_code"] = {"value": self.soc_code, "conf": 0.99}
        
        if self.qualification:
            slots["qualification"] = {
                "value": self.qualification,
                "uk_level": self.qualification_level,
                "conf": 0.85,
            }
        
        if self.has_sponsor is not None:
            slots["sponsor"] = {"value": "yes" if self.has_sponsor else "no", "conf": 0.95}
        
        return slots
    
    def to_structured_json(self, intent: str = "eligibility_check", 
                          intent_confidence: float = 0.90,
                          dialogue_state: str = "collecting") -> Dict[str, Any]:
        """
        Convert to structured JSON format as specified in proposal.
        
        Example output:
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
        return {
            "intent": {
                "label": intent,
                "confidence": intent_confidence,
            },
            "slots": self.get_critical_slots(),
            "dialogue_state": dialogue_state,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to simple dictionary."""
        return {
            "job_title": self.job_title,
            "soc_code": self.soc_code,
            "salary_annual": self.salary_annual,
            "age": self.age,
            "country_of_origin": self.country_of_origin,
            "has_sponsor": self.has_sponsor,
            "english_proficiency": self.english_proficiency,
            "qualification": self.qualification,
            "has_phd": self.has_phd,
            "is_new_entrant": self.is_new_entrant,
            "savings": self.savings,
            "visa_type": self.visa_type,
        }