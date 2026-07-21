"""
Atlas AI — Student Visa Rule Engine
Deterministic, rule-based eligibility determination.
Source: GOV.UK Student visa guidance
URL: https://www.gov.uk/student-visa

This visa is for individuals who want to study in the UK at a licensed 
student sponsor (school, college or university).
"""

from typing import Optional, Dict, Any, List

from src.rule_engine.base_visa import BaseVisaRuleEngine
from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)
from src.rule_engine.rules_loader import rules_loader


class StudentVisaRuleEngine(BaseVisaRuleEngine):
    """
    Rule engine for Student Visa eligibility.
    
    Key features:
    - Must have unconditional offer from licensed sponsor
    - Must meet English language requirements
    - Must have sufficient funds for course and living costs
    - Can work limited hours during term time
    """
    
    # ── Metadata ───────────────────────────────────────────────────────────────
    VISA_TYPE = "student"
    VISA_NAME = "Student Visa"
    GOV_UK_URL = "https://www.gov.uk/student-visa"
    RULES_SOURCE = "GOV.UK Immigration Rules – Student Route"
    
    # ── English Exempt Countries ────────────────────────────────────────────────
    ENGLISH_EXEMPT_COUNTRIES = {
        "antigua and barbuda", "australia", "bahamas", "barbados", "belize",
        "canada", "dominica", "grenada", "guyana", "jamaica", "malta",
        "new zealand", "st kitts and nevis", "saint kitts and nevis",
        "st lucia", "saint lucia", "st vincent and the grenadines",
        "saint vincent and the grenadines", "trinidad and tobago",
        "united states", "united states of america", "usa", "uk",
        "united kingdom", "ireland",
    }
    
    # ── Maintenance Fund Requirements ───────────────────────────────────────────
    LONDON_MONTHLY = 1334  # Per month for courses in London
    OUTSIDE_LONDON_MONTHLY = 1023  # Per month for courses outside London
    MAX_MONTHS = 9  # Maximum months to show funds for
    
    # ── Rules Configuration ────────────────────────────────────────────────────
    # Rules are loaded from JSON file via rules_loader, but we maintain 
    # hardcoded defaults for performance and fallback
    
    DEFAULT_RULES_CONFIG = {
        "cas_offer": {
            "rule_id": "ST-001",
            "description": "Must have unconditional offer and CAS from licensed student sponsor",
            "source_url": "https://www.gov.uk/student-visa/eligibility",
            "source_section": "Confirmation of Acceptance for Studies (CAS)",
        },
        "english_language": {
            "rule_id": "ST-002",
            "description": "Must meet English language requirements at CEFR level B1 (or higher for degree level)",
            "source_url": "https://www.gov.uk/student-visa/knowledge-of-english",
            "source_section": "English language requirements",
        },
        "maintenance": {
            "rule_id": "ST-003",
            "description": "Must have sufficient funds for course fees and living costs",
            "source_url": "https://www.gov.uk/student-visa/money",
            "source_section": "Maintenance funds",
        },
        "academic_progression": {
            "rule_id": "ST-004",
            "description": "Course must represent academic progression from previous study (if applicable)",
            "source_url": "https://www.gov.uk/student-visa/eligibility",
            "source_section": "Academic progression",
        },
        "genuine_student": {
            "rule_id": "ST-005",
            "description": "Must be a genuine student intending to study and leave UK after studies",
            "source_url": "https://www.gov.uk/student-visa/eligibility",
            "source_section": "Genuine student requirement",
        },
    }
    
    def __init__(self):
        """Initialize the rule engine and load rules from JSON."""
        # Try to load rules from JSON, fall back to defaults
        json_rules = rules_loader.get_all_rules("student")
        if json_rules:
            self.RULES_CONFIG = json_rules
        else:
            self.RULES_CONFIG = self.DEFAULT_RULES_CONFIG.copy()
    
    # ── Rule Evaluation Methods ────────────────────────────────────────────────
    
    def check_cas_offer(self, profile: ApplicantProfile) -> RuleResult:
        """ST-001: Must have CAS from licensed sponsor."""
        rule = self.RULES_CONFIG["cas_offer"]
        
        has_cas = getattr(profile, 'has_cas', None) or profile.has_sponsor
        course_level = getattr(profile, 'course_level', None)
        
        if has_cas:
            level_text = f" at {course_level}" if course_level else ""
            reason = (
                f"You have (or are applying for) a Confirmation of Acceptance for Studies (CAS){level_text} "
                "from a licensed UK student sponsor. ✓\n"
                "Your CAS reference number will be needed for your visa application."
            )
            passed = True
        else:
            reason = (
                "You must have an unconditional offer from a licensed UK student sponsor "
                "and receive a Confirmation of Acceptance for Studies (CAS) reference number. "
                "Apply to universities/colleges through UCAS or directly."
            )
            passed = False
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_english_language(self, profile: ApplicantProfile) -> RuleResult:
        """ST-002: English language requirement."""
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
                "You have demonstrated English language proficiency through an approved test "
                "(IELTS for UKVI, PTE Academic, or equivalent). ✓"
            )
        elif profile.english_proficiency == "none":
            passed = False
            reason = (
                "You must demonstrate English language ability at CEFR level B1 (or B2 for degree-level study). "
                "Take an approved English language test (IELTS for UKVI, PTE Academic, or LanguageCert)."
            )
        else:
            passed = True
            reason = (
                "English language evidence not yet confirmed. You will need to take an approved "
                "English test (IELTS for UKVI, PTE Academic, or LanguageCert) at CEFR B1 level "
                "(or B2 for degree-level courses)."
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
        """ST-003: Financial maintenance requirement."""
        rule = self.RULES_CONFIG["maintenance"]
        
        savings = profile.savings
        course_fees = getattr(profile, 'course_fees', None)
        study_location = getattr(profile, 'study_location', 'outside_london')
        
        # Calculate required maintenance
        monthly_requirement = LONDON_MONTHLY if study_location == 'london' else OUTSIDE_LONDON_MONTHLY
        max_maintenance = monthly_requirement * self.MAX_MONTHS
        total_required = (course_fees or 0) + max_maintenance
        
        if savings is None:
            location_text = "London" if study_location == 'london' else "outside London"
            reason = (
                f"You must show sufficient funds for your course fees plus living costs:\n"
                f"• Course fees: £{course_fees:,} (if not already paid)\n"
                f"• Living costs: £{monthly_requirement:,}/month × up to 9 months = £{max_maintenance:,}\n"
                f"• Total required: £{total_required:,}\n\n"
                f"Funds must be held for 28 consecutive days before applying."
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
        
        passed = savings >= total_required
        if passed:
            reason = (
                f"Your savings of £{savings:,.0f} meet the financial requirement of £{total_required:,}. ✓\n"
                f"Funds must be held for 28 consecutive days before applying."
            )
        else:
            shortfall = total_required - savings
            reason = (
                f"Your savings of £{savings:,.0f} are below the required £{total_required:,}. "
                f"You need an additional £{shortfall:,.0f}.\n\n"
                f"Required breakdown:\n"
                f"• Course fees: £{course_fees or 0:,}\n"
                f"• Living costs: £{max_maintenance:,}\n"
                f"Funds must be held for 28 consecutive days."
            )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_academic_progression(self, profile: ApplicantProfile) -> RuleResult:
        """ST-004: Academic progression requirement."""
        rule = self.RULES_CONFIG["academic_progression"]
        
        previous_qualification = getattr(profile, 'previous_qualification', None)
        course_level = getattr(profile, 'course_level', None)
        
        reason = (
            "Your course must represent academic progression from your previous study. "
            "For example, a Bachelor's after A-levels, or a Master's after a Bachelor's. "
            "Your sponsor will assess this when issuing your CAS."
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
    
    def check_genuine_student(self, profile: ApplicantProfile) -> RuleResult:
        """ST-005: Genuine student requirement."""
        rule = self.RULES_CONFIG["genuine_student"]
        
        reason = (
            "You must be a genuine student who intends to:\n"
            "• Study the course you have been accepted onto\n"
            "• Leave the UK when your visa expires (unless switching to another visa)\n\n"
            "You may be asked about your study plans, finances, and future intentions "
            "during a credibility interview."
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
        return ["has_cas", "english_proficiency", "savings"]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        return {rule["rule_id"]: rule["description"] for rule in self.RULES_CONFIG.values()}
    
    def get_visa_metadata(self) -> Optional[Dict[str, Any]]:
        """Get visa metadata from rules loader."""
        return rules_loader.get_metadata("student")
    
    def get_visa_fees(self) -> Optional[Dict[str, Any]]:
        """Get visa fees from rules loader."""
        config = rules_loader.get_visa_config("student")
        return config.get("fees") if config else None
    
    def get_work_permissions(self) -> Optional[Dict[str, Any]]:
        """Get work permissions from rules loader."""
        config = rules_loader.get_visa_config("student")
        return config.get("work_permissions") if config else None
    
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """Main eligibility check for Student visa."""
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
        cas = self.check_cas_offer(profile)
        rule_results.append(cas)
        
        english = self.check_english_language(profile)
        rule_results.append(english)
        
        maintenance = self.check_maintenance(profile)
        rule_results.append(maintenance)
        
        progression = self.check_academic_progression(profile)
        rule_results.append(progression)
        
        genuine = self.check_genuine_student(profile)
        rule_results.append(genuine)
        
        # Determine verdict
        mandatory_failed = [r for r in rule_results if not r.passed and r.severity == "mandatory"]
        
        if not mandatory_failed:
            verdict = Verdict.ELIGIBLE
            summary = (
                f"✅ Based on the information provided, you appear to be ELIGIBLE "
                f"for the Student Visa. "
                f"This visa allows you to study in the UK and work limited hours "
                f"(up to 20 hours/week during term time for degree-level courses). "
                f"After graduation, you may be eligible for the Graduate Visa."
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
    engine = StudentVisaRuleEngine()
    return engine.check_eligibility(profile)