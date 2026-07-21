"""
Atlas AI — Base Visa Rule Engine
Abstract base class for all visa type rule engines.
Provides extensible framework for multiple visa routes as specified in proposal.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)


class VisaTypeError(Exception):
    """Raised when an unsupported visa type is requested."""
    pass


class BaseVisaRuleEngine(ABC):
    """
    Abstract base class for visa-specific rule engines.
    
    Each visa type (Skilled Worker, Health & Care Worker, Graduate, 
    Global Talent) implements this interface with its specific rules.
    
    Key design principles:
    - Deterministic: Same input always produces same output
    - Traceable: Every decision links to GOV.UK source
    - Auditable: Full rule evaluation history is recorded
    - No ML: Eligibility is NEVER determined by ML models
    """
    
    # ── Metadata (to be overridden by subclasses) ──────────────────────────────
    
    VISA_TYPE: str = "base"
    VISA_NAME: str = "Base Visa"
    GOV_UK_URL: str = "https://www.gov.uk"
    RULES_SOURCE: str = "Immigration Rules"
    
    # ── Abstract Methods (must be implemented by each visa type) ───────────────
    
    @abstractmethod
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """
        Main eligibility check. Must be implemented by each visa type.
        
        Args:
            profile: ApplicantProfile with collected user data
            
        Returns:
            EligibilityResult with verdict, rule results, and trace
        """
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        Return list of required profile fields for this visa type.
        
        Returns:
            List of field names (e.g., ["job_title", "salary", "sponsor"])
        """
        pass
    
    @abstractmethod
    def get_rules_summary(self) -> Dict[str, Any]:
        """
        Return summary of all rules for this visa type.
        
        Returns:
            Dict with rule_id -> rule description mapping
        """
        pass
    
    # ── Common Methods ─────────────────────────────────────────────────────────
    
    def validate_profile(self, profile: ApplicantProfile) -> Tuple[bool, List[str]]:
        """
        Check if profile has all required fields for this visa type.
        
        Returns:
            (is_valid, list_of_missing_fields)
        """
        required = self.get_required_fields()
        missing = []
        
        for field_name in required:
            value = getattr(profile, field_name, None)
            if value is None:
                missing.append(field_name)
        
        return len(missing) == 0, missing
    
    def get_missing_info_message(self, missing_fields: List[str]) -> str:
        """Generate user-friendly message for missing information."""
        field_labels = {
            "job_title": "job title or occupation",
            "salary_annual": "annual salary",
            "has_sponsor": "sponsorship status",
            "country_of_origin": "country of origin/nationality",
            "english_proficiency": "English language proficiency",
            "age": "age",
            "qualification": "qualifications",
            "savings": "savings amount",
        }
        
        readable_fields = [
            field_labels.get(f, f.replace('_', ' ')) 
            for f in missing_fields
        ]
        
        if len(readable_fields) == 1:
            return f"I need to know your {readable_fields[0]} to assess eligibility."
        elif len(readable_fields) == 2:
            return f"I need to know your {readable_fields[0]} and {readable_fields[1]}."
        else:
            return "I need more information: " + ", ".join(readable_fields[:-1]) + f", and {readable_fields[-1]}."
    
    def create_rule_result(
        self,
        rule_id: str,
        rule_description: str,
        passed: bool,
        reason: str,
        source_url: str,
        source_section: str = "",
        severity: str = "mandatory",
    ) -> RuleResult:
        """Helper to create a RuleResult with consistent formatting."""
        return RuleResult(
            rule_id=rule_id,
            rule_description=rule_description,
            passed=passed,
            reason=reason,
            source_url=source_url,
            source_section=source_section,
            severity=severity,
        )
    
    def create_eligibility_result(
        self,
        verdict: Verdict,
        rule_results: List[RuleResult],
        missing_info: Optional[List[str]] = None,
        points_earned: int = 0,
        points_required: int = 0,
        summary: str = "",
        trace_id: str = "",
    ) -> EligibilityResult:
        """Helper to create an EligibilityResult."""
        result = EligibilityResult(
            verdict=verdict,
            visa_type=self.VISA_TYPE,
            rule_results=rule_results,
            missing_info=missing_info or [],
            points_earned=points_earned,
            points_required=points_required,
            summary=summary,
        )
        if trace_id:
            result.trace_id = trace_id
        return result
    
    def get_trace_id(self) -> str:
        """Generate a trace ID for audit purposes."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export visa engine metadata as dictionary."""
        return {
            "visa_type": self.VISA_TYPE,
            "visa_name": self.VISA_NAME,
            "gov_uk_url": self.GOV_UK_URL,
            "rules_source": self.RULES_SOURCE,
            "rules": self.get_rules_summary(),
            "required_fields": self.get_required_fields(),
        }


class VisaRuleEngineRegistry:
    """
    Registry for visa rule engines.
    Provides factory pattern for creating appropriate engine based on visa type.
    """
    
    _engines: Dict[str, BaseVisaRuleEngine] = {}
    
    @classmethod
    def register(cls, visa_type: str, engine: BaseVisaRuleEngine):
        """Register a visa rule engine."""
        cls._engines[visa_type] = engine
    
    @classmethod
    def get_engine(cls, visa_type: str) -> BaseVisaRuleEngine:
        """Get the rule engine for a specific visa type."""
        if visa_type not in cls._engines:
            raise VisaTypeError(
                f"Unsupported visa type: {visa_type}. "
                f"Supported types: {list(cls._engines.keys())}"
            )
        return cls._engines[visa_type]
    
    @classmethod
    def get_supported_visas(cls) -> List[str]:
        """Get list of supported visa types."""
        return list(cls._engines.keys())
    
    @classmethod
    def get_all_engines(cls) -> Dict[str, BaseVisaRuleEngine]:
        """Get all registered engines."""
        return cls._engines.copy()
    
    @classmethod
    def check_eligibility_for_visa(
        cls, 
        visa_type: str, 
        profile: ApplicantProfile
    ) -> EligibilityResult:
        """
        Convenience method to check eligibility for a specific visa.
        
        Args:
            visa_type: Type of visa (e.g., "skilled_worker")
            profile: ApplicantProfile with user data
            
        Returns:
            EligibilityResult
        """
        engine = cls.get_engine(visa_type)
        return engine.check_eligibility(profile)


# ── Default Registry Setup ─────────────────────────────────────────────────────

def setup_default_registry():
    """
    Set up the registry with default visa engines.
    Called during application initialization.
    """
    # Import visa engines (lazy import to avoid circular dependencies)
    try:
        from src.rule_engine.skilled_worker import SkilledWorkerRuleEngine
        VisaRuleEngineRegistry.register("skilled_worker", SkilledWorkerRuleEngine())
    except Exception as e:
        print(f"[Registry] Could not register SkilledWorkerRuleEngine: {e}")
    
    try:
        from src.rule_engine.health_care_worker import HealthCareWorkerRuleEngine
        VisaRuleEngineRegistry.register("health_care_worker", HealthCareWorkerRuleEngine())
    except Exception as e:
        print(f"[Registry] Could not register HealthCareWorkerRuleEngine: {e}")
    
    try:
        from src.rule_engine.graduate import GraduateRuleEngine
        VisaRuleEngineRegistry.register("graduate", GraduateRuleEngine())
    except Exception as e:
        print(f"[Registry] Could not register GraduateRuleEngine: {e}")
    
    try:
        from src.rule_engine.global_talent import GlobalTalentRuleEngine
        VisaRuleEngineRegistry.register("global_talent", GlobalTalentRuleEngine())
    except Exception as e:
        print(f"[Registry] Could not register GlobalTalentRuleEngine: {e}")


def get_visa_engine(visa_type: str) -> BaseVisaRuleEngine:
    """Get visa rule engine (convenience function)."""
    return VisaRuleEngineRegistry.get_engine(visa_type)


def get_supported_visa_types() -> List[str]:
    """Get list of supported visa types (convenience function)."""
    return VisaRuleEngineRegistry.get_supported_visas()