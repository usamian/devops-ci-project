"""
Atlas AI — Health and Care Worker Visa Rule Engine
Deterministic, rule-based eligibility determination.
Source: GOV.UK Health and Care Worker visa guidance
URL: https://www.gov.uk/health-care-worker-visa

This visa is for qualified doctors, nurses and health and care workers 
who want to work in the UK in an eligible job with the NHS, an NHS 
supplier, or in adult social care.
"""

from typing import Optional, Dict, Any, List

from src.core.canonicalizer import canonicalizer
from src.rule_engine.base_visa import BaseVisaRuleEngine
from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)
from src.rule_engine.rules_loader import rules_loader


class HealthCareWorkerRuleEngine(BaseVisaRuleEngine):
    """
    Rule engine for Health and Care Worker Visa eligibility.
    
    Key differences from Skilled Worker:
    - No application fee
    - Faster processing
    - Must work in eligible health/care occupation
    - Must work for NHS, NHS supplier, or adult social care
    """
    
    # ── Metadata ───────────────────────────────────────────────────────────────
    VISA_TYPE = "health_care_worker"
    VISA_NAME = "Health and Care Worker Visa"
    GOV_UK_URL = "https://www.gov.uk/health-care-worker-visa"
    RULES_SOURCE = "GOV.UK Immigration Rules – Health and Care Worker"
    
    # ── Eligible Occupations for Health and Care Worker ────────────────────────
    ELIGIBLE_SOC_CODES = {
        "2211": "Medical practitioners",
        "2212": "Psychologists",
        "2213": "Pharmacists",
        "2214": "Ophthalmic opticians",
        "2215": "Dental practitioners",
        "2217": "Medical radiographers",
        "2218": "Podiatrists",
        "2219": "Health professionals n.e.c.",
        "2221": "Physiotherapists",
        "2222": "Occupational therapists",
        "2223": "Speech and language therapists",
        "2225": "Nurses",
        "2229": "Therapy professionals n.e.c.",
        "3211": "Nursing auxiliaries and assistants",
        "3212": "Dental nurses",
        "3213": "Pharmacy technicians",
        "3214": "Medical and dental technicians",
        "3215": "Phlebotomists",
        "3216": "Ambulance staff",
        "3219": "Health associate professionals n.e.c.",
        "6145": "Care workers and home carers",
        "6146": "Senior care workers",
    }
    
    # ── Rules Configuration ────────────────────────────────────────────────────
    # Rules are loaded from JSON file via rules_loader, but we maintain 
    # hardcoded defaults for performance and fallback
    
    DEFAULT_RULES_CONFIG = {
        "sponsorship": {
            "rule_id": "HC-001",
            "description": "Applicant must have a valid Certificate of Sponsorship from an approved UK health or adult social care employer",
            "source_url": "https://www.gov.uk/health-care-worker-visa/eligibility",
            "source_section": "Health and Care Worker visa – Sponsorship",
        },
        "eligible_occupation": {
            "rule_id": "HC-002",
            "description": "Job must be in an eligible health or adult social care occupation",
            "source_url": "https://www.gov.uk/health-care-worker-visa/eligibility",
            "source_section": "Eligible occupations",
        },
        "qualifications": {
            "rule_id": "HC-003",
            "description": "Applicant must have the required professional qualifications and registration",
            "source_url": "https://www.gov.uk/health-care-worker-visa/eligibility",
            "source_section": "Professional registration",
        },
        "english_language": {
            "rule_id": "HC-004",
            "description": "English language at B1 CEFR or above",
            "source_url": "https://www.gov.uk/health-care-worker-visa/knowledge-of-english",
            "source_section": "Appendix English Language",
        },
        "maintenance": {
            "rule_id": "HC-005",
            "description": "Financial maintenance requirement (£1,270 for 28 days, waivable)",
            "source_url": "https://www.gov.uk/health-care-worker-visa/financial-requirements",
            "source_section": "Appendix Finance",
        },
    }
    
    def __init__(self):
        """Initialize the rule engine and load rules from JSON."""
        # Try to load rules from JSON, fall back to defaults
        json_rules = rules_loader.get_all_rules("health_care_worker")
        if json_rules:
            self.RULES_CONFIG = json_rules
        else:
            self.RULES_CONFIG = self.DEFAULT_RULES_CONFIG.copy()
    
    # ── English Exempt Countries (same as Skilled Worker) ──────────────────────
    ENGLISH_EXEMPT_COUNTRIES = {
        "antigua and barbuda", "australia", "bahamas", "barbados", "belize",
        "canada", "dominica", "grenada", "guyana", "jamaica", "malta",
        "new zealand", "st kitts and nevis", "saint kitts and nevis",
        "st lucia", "saint lucia", "st vincent and the grenadines",
        "saint vincent and the grenadines", "trinidad and tobago",
        "united states", "united states of america", "usa", "uk",
        "united kingdom", "ireland"
    }
    
    # ── Rule Evaluation Methods ────────────────────────────────────────────────
    
    def check_sponsorship(self, profile: ApplicantProfile) -> RuleResult:
        """HC-001: Must have CoS from approved health/care employer."""
        rule = self.RULES_CONFIG["sponsorship"]
        passed = profile.has_sponsor is True
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=(
                "You have a Certificate of Sponsorship from an approved UK health or adult social care employer. ✓"
                if passed else
                "You need a Certificate of Sponsorship from an approved UK health or adult social care employer. "
                "This must be an NHS trust, NHS supplier, or registered adult social care provider."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_eligible_occupation(self, profile: ApplicantProfile) -> RuleResult:
        """HC-002: Job must be in eligible health/care occupation."""
        rule = self.RULES_CONFIG["eligible_occupation"]
        
        # Try to get SOC code
        soc_code = profile.soc_code
        occupation = None
        
        if soc_code:
            occupation = canonicalizer.soc_mapper.get_by_soc_code(soc_code)
        elif profile.job_title:
            occupation = canonicalizer.soc_mapper.map_job_title(profile.job_title)
            if occupation:
                soc_code = occupation.soc_code
        
        if soc_code and soc_code in self.ELIGIBLE_SOC_CODES:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason=(
                    f"SOC {soc_code} — '{self.ELIGIBLE_SOC_CODES[soc_code]}' is an eligible health or adult social care occupation. ✓"
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=False,
            reason=(
                f"The occupation (SOC: {soc_code or 'unknown'}) is not on the list of eligible health and adult social care occupations. "
                "This visa is only available for qualified doctors, nurses, and health/care workers in specific roles."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_qualifications(self, profile: ApplicantProfile) -> RuleResult:
        """HC-003: Must have required professional qualifications."""
        rule = self.RULES_CONFIG["qualifications"]
        
        # Check if qualification is provided
        if profile.qualification:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason=(
                    f"You have declared a qualification: '{profile.qualification}'. "
                    "You must ensure this is recognized by the relevant UK professional body."
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
                severity="advisory",
            )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=True,
            reason=(
                "You must have the professional qualifications required for your role. "
                "This will be verified by your sponsor and may require registration with a UK professional body."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
            severity="advisory",
        )
    
    def check_english_language(self, profile: ApplicantProfile) -> RuleResult:
        """HC-004: English language requirement."""
        rule = self.RULES_CONFIG["english_language"]
        
        country_lower = (profile.country_of_origin or "").lower().strip()
        is_exempt = country_lower in self.ENGLISH_EXEMPT_COUNTRIES
        
        if is_exempt:
            passed = True
            reason = (
                f"Citizens of {profile.country_of_origin} are exempt from the English language requirement. ✓"
            )
        elif profile.english_proficiency in ("test_passed", "native", "exempt"):
            passed = True
            reason = (
                "You have demonstrated English language proficiency. ✓"
            )
        elif profile.english_proficiency == "none":
            passed = False
            reason = (
                "You must demonstrate English language ability at CEFR B1 level."
            )
        else:
            passed = True
            reason = (
                "English language evidence not yet confirmed. You will need to demonstrate "
                "English at CEFR B1 level."
            )
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=passed,
                reason=reason,
                source_url=rule["source_url"],
                source_section=rule["source_section"],
                severity="advisory",
            )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_maintenance(self, profile: ApplicantProfile) -> RuleResult:
        """HC-005: Financial maintenance requirement."""
        rule = self.RULES_CONFIG["maintenance"]
        
        if profile.has_sponsor:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason=(
                    "If your sponsor certifies your maintenance on the CoS, "
                    "the £1,270 savings requirement is waived. ✓"
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            )
        
        if profile.savings is None:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason=(
                    "You must hold at least £1,270 in savings for 28 days, "
                    "unless your sponsor certifies maintenance."
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
                severity="advisory",
            )
        
        passed = profile.savings >= 1270
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=(
                f"Your savings of £{profile.savings:,.0f} meet the requirement. ✓"
                if passed else
                f"You need at least £1,270 in savings. You have £{profile.savings:,.0f}."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    # ── Abstract Method Implementations ────────────────────────────────────────
    
    def get_required_fields(self) -> List[str]:
        return ["job_title", "has_sponsor", "country_of_origin"]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        return {rule["rule_id"]: rule["description"] for rule in self.RULES_CONFIG.values()}
    
    def get_visa_metadata(self) -> Optional[Dict[str, Any]]:
        """Get visa metadata from rules loader."""
        return rules_loader.get_metadata("health_care_worker")
    
    def get_visa_fees(self) -> Optional[Dict[str, Any]]:
        """Get visa fees from rules loader."""
        config = rules_loader.get_visa_config("health_care_worker")
        return config.get("fees") if config else None
    
    def get_eligible_soc_codes(self) -> Optional[Dict[str, str]]:
        """Get eligible SOC codes from rules loader."""
        config = rules_loader.get_visa_config("health_care_worker")
        return config.get("eligible_soc_codes") if config else None
    
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """Main eligibility check for Health and Care Worker visa."""
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
        sponsorship = self.check_sponsorship(profile)
        rule_results.append(sponsorship)
        
        occupation = self.check_eligible_occupation(profile)
        rule_results.append(occupation)
        
        qualifications = self.check_qualifications(profile)
        rule_results.append(qualifications)
        
        english = self.check_english_language(profile)
        rule_results.append(english)
        
        maintenance = self.check_maintenance(profile)
        rule_results.append(maintenance)
        
        # Determine verdict
        mandatory_failed = [r for r in rule_results if not r.passed and r.severity == "mandatory"]
        
        if not mandatory_failed:
            verdict = Verdict.ELIGIBLE
            summary = (
                f"✅ Based on the information provided, you appear to be ELIGIBLE "
                f"for the Health and Care Worker Visa. "
                f"This visa has no application fee and faster processing times. "
                f"Please verify all details with your sponsor."
            )
        else:
            verdict = Verdict.NOT_ELIGIBLE
            failed_desc = [r.rule_description for r in mandatory_failed]
            summary = (
                f"❌ You do not currently meet the requirements. "
                f"Failed: {'; '.join(failed_desc)}."
            )
        
        return self.create_eligibility_result(
            verdict=verdict,
            rule_results=rule_results,
            summary=summary,
            trace_id=trace_id,
        )


# Backward compatibility
def check_eligibility(profile: ApplicantProfile) -> EligibilityResult:
    engine = HealthCareWorkerRuleEngine()
    return engine.check_eligibility(profile)