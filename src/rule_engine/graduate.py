"""
Atlas AI — Graduate Visa Rule Engine
Deterministic, rule-based eligibility determination.
Source: GOV.UK Graduate visa guidance
URL: https://www.gov.uk/graduate-visa

This visa allows international students who have completed a UK degree
to stay in the UK to work for 2 years (3 years for PhD graduates).
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from src.rule_engine.base_visa import BaseVisaRuleEngine
from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)
from src.rule_engine.rules_loader import rules_loader


class GraduateRuleEngine(BaseVisaRuleEngine):
    """
    Rule engine for Graduate Visa eligibility.
    
    Key features:
    - No sponsorship required
    - No minimum salary requirement
    - Must have completed UK degree
    - 2 years (Bachelor's/Master's) or 3 years (PhD)
    """
    
    # ── Metadata ───────────────────────────────────────────────────────────────
    VISA_TYPE = "graduate"
    VISA_NAME = "Graduate Visa"
    GOV_UK_URL = "https://www.gov.uk/graduate-visa"
    RULES_SOURCE = "GOV.UK Immigration Rules – Graduate Route"
    
    # ── Rules Configuration ────────────────────────────────────────────────────
    # Rules are loaded from JSON file via rules_loader, but we maintain 
    # hardcoded defaults for performance and fallback
    
    DEFAULT_RULES_CONFIG = {
        "uk_degree": {
            "rule_id": "GR-001",
            "description": "Applicant must have completed an eligible UK degree",
            "source_url": "https://www.gov.uk/graduate-visa/eligibility",
            "source_section": "Graduate Route – Qualification requirements",
        },
        "student_visa": {
            "rule_id": "GR-002",
            "description": "Applicant must currently hold a valid Student visa",
            "source_url": "https://www.gov.uk/graduate-visa/eligibility",
            "source_section": "Current immigration status",
        },
        "study_duration": {
            "rule_id": "GR-003",
            "description": "Applicant must have studied in the UK for the required duration",
            "source_url": "https://www.gov.uk/graduate-visa/eligibility",
            "source_section": "Study requirements",
        },
        "institution_status": {
            "rule_id": "GR-004",
            "description": "Educational institution must have a track record of compliance",
            "source_url": "https://www.gov.uk/graduate-visa/eligibility",
            "source_section": "Institution requirements",
        },
    }
    
    def __init__(self):
        """Initialize the rule engine and load rules from JSON."""
        # Try to load rules from JSON, fall back to defaults
        json_rules = rules_loader.get_all_rules("graduate")
        if json_rules:
            self.RULES_CONFIG = json_rules
        else:
            self.RULES_CONFIG = self.DEFAULT_RULES_CONFIG.copy()
    
    # ── Rule Evaluation Methods ────────────────────────────────────────────────
    
    def check_uk_degree(self, profile: ApplicantProfile) -> RuleResult:
        """GR-001: Must have completed eligible UK degree."""
        rule = self.RULES_CONFIG["uk_degree"]
        
        qualification = (profile.qualification or "").lower()
        qualification_level = profile.qualification_level
        
        # Check for degree indicators
        is_degree = any(kw in qualification for kw in [
            "bachelor", "bsc", "ba", "beng",
            "master", "msc", "ma", "mba",
            "phd", "doctorate",
        ])
        
        # Check UK NARIC level (6, 7, or 8)
        is_valid_level = qualification_level in ("6", "7", "8")
        
        passed = is_degree or is_valid_level
        
        if passed:
            level_desc = {
                "6": "Bachelor's degree",
                "7": "Master's degree", 
                "8": "Doctoral degree (PhD)",
            }
            level_text = level_desc.get(qualification_level, "UK degree") if qualification_level else "a UK degree"
            reason = (
                f"You appear to have completed {level_text} from a UK institution. ✓\n"
                f"You will be granted {'3 years' if qualification_level == '8' else '2 years'} of post-study work permission."
            )
        else:
            reason = (
                "You must have completed an eligible UK Bachelor's, Master's, or PhD degree. "
                "Other qualifications may not qualify for the Graduate Route."
            )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_student_visa(self, profile: ApplicantProfile) -> RuleResult:
        """GR-002: Must hold valid Student visa."""
        rule = self.RULES_CONFIG["student_visa"]
        
        current_visa = (profile.current_visa_type or "").lower()
        
        is_student_visa = current_visa in [
            "student", "tier 4", "tier 4 (general)",
            "student route",
        ]
        
        passed = is_student_visa
        
        if passed:
            reason = "You currently hold a valid Student visa (or Tier 4). ✓"
        else:
            reason = (
                "You must currently be in the UK with a valid Student visa (or Tier 4 visa) "
                "to apply for the Graduate Route. "
                "If you are on a different visa type, you may need to explore other options."
            )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_study_duration(self, profile: ApplicantProfile) -> RuleResult:
        """GR-003: Must have studied in UK for required duration."""
        rule = self.RULES_CONFIG["study_duration"]
        
        # This is typically verified by the institution
        # We provide advisory guidance
        reason = (
            "You must have studied in the UK for the minimum required duration: "
            "12 months for courses longer than 12 months, or the full duration for shorter courses. "
            "Your university will confirm this to UKVI."
        )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=True,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
            severity="advisory",
        )
    
    def check_institution_status(self, profile: ApplicantProfile) -> RuleResult:
        """GR-004: Institution must have compliance track record."""
        rule = self.RULES_CONFIG["institution_status"]
        
        reason = (
            "Your UK educational institution must have a track record of compliance "
            "with UKVI sponsor duties. Most UK universities meet this requirement. "
            "Your institution will notify you if there are any issues."
        )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=True,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
            severity="advisory",
        )
    
    # ── Abstract Method Implementations ────────────────────────────────────────
    
    def get_required_fields(self) -> List[str]:
        return ["qualification", "current_visa_type"]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        return {rule["rule_id"]: rule["description"] for rule in self.RULES_CONFIG.values()}
    
    def get_visa_metadata(self) -> Optional[Dict[str, Any]]:
        """Get visa metadata from rules loader."""
        return rules_loader.get_metadata("graduate")
    
    def get_visa_fees(self) -> Optional[Dict[str, Any]]:
        """Get visa fees from rules loader."""
        config = rules_loader.get_visa_config("graduate")
        return config.get("fees") if config else None
    
    def get_qualification_levels(self) -> Optional[Dict[str, Any]]:
        """Get qualification levels from rules loader."""
        config = rules_loader.get_visa_config("graduate")
        return config.get("qualification_levels") if config else None
    
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """Main eligibility check for Graduate visa."""
        rule_results: List[RuleResult] = []
        trace_id = self.get_trace_id()
        
        # Check required fields
        missing = profile.missing_fields()
        if missing:
            return self.create_eligibility_result(
                verdict=Verdict.INSUFFICIENT_INFO,
                rule_results=[],
                missing_info=missing,
                summary=f"I need more information: {self.get_missing_info_message(missing)}",
                trace_id=trace_id,
            )
        
        # Run rules
        degree = self.check_uk_degree(profile)
        rule_results.append(degree)
        
        student_visa = self.check_student_visa(profile)
        rule_results.append(student_visa)
        
        study_duration = self.check_study_duration(profile)
        rule_results.append(study_duration)
        
        institution = self.check_institution_status(profile)
        rule_results.append(institution)
        
        # Determine verdict
        mandatory_failed = [r for r in rule_results if not r.passed and r.severity == "mandatory"]
        
        if not mandatory_failed:
            verdict = Verdict.ELIGIBLE
            is_phd = profile.qualification_level == "8" or "phd" in (profile.qualification or "").lower()
            duration = "3 years" if is_phd else "2 years"
            summary = (
                f"✅ Based on the information provided, you appear to be ELIGIBLE "
                f"for the Graduate Visa. "
                f"This visa grants {duration} of post-study work permission with no sponsorship required. "
                f"You can work in most jobs and switch to a Skilled Worker visa later."
            )
        else:
            verdict = Verdict.NOT_ELIGIBLE
            failed_desc = [r.rule_description for r in mandatory_failed]
            summary = (
                f"❌ You may not be eligible for the Graduate Visa. "
                f"Issues: {'; '.join(failed_desc)}."
            )
        
        return self.create_eligibility_result(
            verdict=verdict,
            rule_results=rule_results,
            summary=summary,
            trace_id=trace_id,
        )


# Backward compatibility
def check_eligibility(profile: ApplicantProfile) -> EligibilityResult:
    engine = GraduateRuleEngine()
    return engine.check_eligibility(profile)