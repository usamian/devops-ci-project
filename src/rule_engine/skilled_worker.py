"""
Atlas AI — Skilled Worker Visa Rule Engine
Deterministic, rule-based eligibility determination.
Source: GOV.UK Appendix Skilled Worker (effective April 2024)
URL: https://www.gov.uk/skilled-worker-visa

IMPORTANT: This module NEVER uses ML or GPT for eligibility decisions.
All decisions are traceable to specific GOV.UK rule references.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.core.config import AtlasConfig
from src.core.canonicalizer import canonicalizer
from src.rule_engine.base_visa import BaseVisaRuleEngine
from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)
from src.rule_engine.rules_loader import rules_loader


class SkilledWorkerRuleEngine(BaseVisaRuleEngine):
    """
    Rule engine for Skilled Worker Visa eligibility.
    
    Implements all rules from GOV.UK Appendix Skilled Worker:
    - SW-001: Sponsorship (Certificate of Sponsorship)
    - SW-002: Occupation (eligible occupation list)
    - SW-003: Salary (threshold and going rate)
    - SW-004: English Language (B1 CEFR)
    - SW-005: Points (70 points required)
    - SW-006: Age (18+)
    - SW-007: Financial (maintenance funds)
    """
    
    # ── Metadata ───────────────────────────────────────────────────────────────
    VISA_TYPE = "skilled_worker"
    VISA_NAME = "Skilled Worker Visa"
    GOV_UK_URL = "https://www.gov.uk/skilled-worker-visa"
    RULES_SOURCE = "GOV.UK Immigration Rules – Appendix Skilled Worker"
    
    # ── English Language Exempt Countries ──────────────────────────────────────
    ENGLISH_EXEMPT_COUNTRIES = {
        "antigua and barbuda", "australia", "bahamas", "barbados", "belize",
        "canada", "dominica", "grenada", "guyana", "jamaica", "malta",
        "new zealand", "st kitts and nevis", "saint kitts and nevis",
        "st lucia", "saint lucia", "st vincent and the grenadines",
        "saint vincent and the grenadines", "trinidad and tobago",
        "united states", "united states of america", "usa", "uk",
        "united kingdom", "ireland"
    }
    
    # ── Rules Configuration ────────────────────────────────────────────────────
    # Rules are loaded from JSON file via rules_loader, but we maintain 
    # hardcoded defaults for performance and fallback
    
    DEFAULT_RULES_CONFIG = {
        "sponsorship": {
            "rule_id": "SW-001",
            "description": "Applicant must have a valid Certificate of Sponsorship (CoS) from a UK-licensed sponsor",
            "source_url": "https://www.gov.uk/skilled-worker-visa/your-job",
            "source_section": "Appendix Skilled Worker – SW 6.1",
        },
        "occupation": {
            "rule_id": "SW-002",
            "description": "The job must be an eligible occupation at RQF level 3 or above",
            "source_url": "https://www.gov.uk/government/publications/skilled-worker-visa-immigration-salary-list",
            "source_section": "Appendix Skilled Occupations",
        },
        "salary": {
            "rule_id": "SW-003",
            "description": "Minimum salary thresholds",
            "source_url": "https://www.gov.uk/skilled-worker-visa/your-job",
            "source_section": "Appendix Skilled Worker – SW 13",
            "general_threshold": 38700,
            "new_entrant_threshold": 30960,
            "minimum_absolute": 26200,
        },
        "english_language": {
            "rule_id": "SW-004",
            "description": "English language at B1 CEFR or above",
            "source_url": "https://www.gov.uk/skilled-worker-visa/knowledge-of-english",
            "source_section": "Appendix English Language – Part 2",
        },
        "points": {
            "rule_id": "SW-005",
            "description": "Points-based requirements (70 points total)",
            "source_url": "https://www.gov.uk/skilled-worker-visa/eligibility",
            "source_section": "Appendix Skilled Worker – SW 1",
            "total_required": 70,
        },
        "age": {
            "rule_id": "SW-006",
            "description": "Applicant must be at least 18 years old",
            "source_url": "https://www.gov.uk/skilled-worker-visa/eligibility",
            "source_section": "Appendix Skilled Worker – SW 3.1",
            "minimum_age": 18,
        },
        "financial": {
            "rule_id": "SW-007",
            "description": "Financial maintenance — £1,270 in savings for 28 days (waivable if sponsor certifies)",
            "source_url": "https://www.gov.uk/skilled-worker-visa/financial-requirements",
            "source_section": "Appendix Finance – Part 10",
            "minimum_savings": 1270,
        },
    }
    
    def __init__(self):
        """Initialize the rule engine and load rules from JSON."""
        # Try to load rules from JSON, fall back to defaults
        json_rules = rules_loader.get_all_rules("skilled_worker")
        if json_rules:
            self.RULES_CONFIG = json_rules
        else:
            self.RULES_CONFIG = self.DEFAULT_RULES_CONFIG.copy()
    
    # ── Rule Evaluation Methods ────────────────────────────────────────────────
    
    def check_sponsorship(self, profile: ApplicantProfile) -> RuleResult:
        """SW-001: Applicant must have a valid Certificate of Sponsorship."""
        rule = self.RULES_CONFIG["sponsorship"]
        passed = profile.has_sponsor is True
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=(
                "You have a Certificate of Sponsorship from a licensed UK sponsor. ✓"
                if passed else
                "You need a Certificate of Sponsorship (CoS) from a UK-licensed Skilled Worker sponsor. "
                "Without this, you cannot apply for a Skilled Worker visa."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_occupation(self, profile: ApplicantProfile) -> tuple[RuleResult, Optional[Dict[str, Any]]]:
        """SW-002: Job must be on the eligible occupation list."""
        rule = self.RULES_CONFIG["occupation"]
        
        # Try to map job title to SOC code
        occupation = None
        if profile.soc_code:
            occupation = canonicalizer.soc_mapper.get_by_soc_code(profile.soc_code)
        elif profile.job_title:
            occupation = canonicalizer.soc_mapper.map_job_title(profile.job_title)
        
        if occupation is None:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=False,
                reason=(
                    f"The job title '{profile.job_title}' could not be matched to an eligible SOC code. "
                    "Only occupations listed in the GOV.UK Appendix Skilled Occupations are eligible."
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            ), None
        
        if not occupation.eligible:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=False,
                reason=(
                    f"SOC {occupation.soc_code} — '{occupation.title}' is not on the eligible occupations list."
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            ), occupation
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=True,
            reason=(
                f"SOC {occupation.soc_code} — '{occupation.title}' is an eligible occupation at RQF level {occupation.rqf_level}. ✓"
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        ), occupation
    
    def check_salary(
        self, 
        profile: ApplicantProfile, 
        occupation: Optional[Any]
    ) -> tuple[RuleResult, int]:
        """SW-003: Salary must meet or exceed both general threshold and going rate."""
        rule = self.RULES_CONFIG["salary"]
        
        points = 0
        
        if profile.salary_annual is None:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=False,
                reason="Salary information not provided.",
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            ), points
        
        salary = profile.salary_annual
        general_threshold = rule["general_threshold"]  # £38,700
        new_entrant_threshold = rule["new_entrant_threshold"]  # £30,960
        
        going_rate = occupation.going_rate if occupation else 0
        new_entrant_rate = occupation.new_entrant_rate if occupation else 0
        is_shortage = occupation.shortage_occupation if occupation else False
        
        # Determine effective threshold
        if profile.is_new_entrant:
            effective_threshold = min(new_entrant_threshold, new_entrant_rate)
            threshold_label = "new entrant threshold"
        elif is_shortage:
            shortage_rate = going_rate * 0.80
            effective_threshold = max(general_threshold, shortage_rate)
            threshold_label = "shortage occupation threshold"
        else:
            effective_threshold = max(general_threshold, going_rate)
            threshold_label = "standard threshold"
        
        passed = salary >= effective_threshold
        
        if passed:
            points = 20
            reason = (
                f"Your salary of £{salary:,.0f}/year meets the {threshold_label} "
                f"of £{effective_threshold:,.0f}/year. ✓"
            )
            if is_shortage:
                reason += " (Shortage occupation rate applies.)"
        else:
            shortfall = effective_threshold - salary
            reason = (
                f"Your salary of £{salary:,.0f}/year is below the required {threshold_label} "
                f"of £{effective_threshold:,.0f}/year. "
                f"You need an additional £{shortfall:,.0f}/year to qualify."
            )
            if going_rate > general_threshold and not profile.is_new_entrant:
                reason += (
                    f" Note: The going rate for this occupation (£{going_rate:,.0f}) "
                    f"is higher than the general threshold (£{general_threshold:,.0f})."
                )
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        ), points
    
    def check_english_language(self, profile: ApplicantProfile) -> RuleResult:
        """SW-004: English language at B1 CEFR or above."""
        rule = self.RULES_CONFIG["english_language"]
        
        country_lower = (profile.country_of_origin or "").lower().strip()
        is_exempt = country_lower in self.ENGLISH_EXEMPT_COUNTRIES
        
        if is_exempt:
            passed = True
            reason = (
                f"Citizens of {profile.country_of_origin} are exempt from the English language "
                f"requirement as it is a majority English-speaking country. ✓"
            )
        elif profile.english_proficiency == "test_passed":
            passed = True
            reason = (
                "You have demonstrated English language proficiency via an approved test "
                "(IELTS, TOEFL, PTE Academic or equivalent) at CEFR B1 level or above. ✓"
            )
        elif profile.english_proficiency == "native":
            passed = True
            reason = "You are a native English speaker / educated in English. ✓"
        elif profile.english_proficiency == "exempt":
            passed = True
            reason = "You are exempt from the English language requirement. ✓"
        elif profile.english_proficiency == "none":
            passed = False
            reason = (
                "You must demonstrate English language ability at CEFR B1 level. "
                "Accepted evidence includes: an approved English test (IELTS, TOEFL, PTE), "
                "a degree taught in English, or GCSE/A-Level in English."
            )
        else:
            # Not yet confirmed — treat as advisory
            passed = True
            reason = (
                "English language evidence not confirmed. You will need to demonstrate "
                "English at CEFR B1 level via an approved test (IELTS, TOEFL, PTE Academic), "
                "a UK degree taught in English, or GCSE/A-Level English."
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
    
    def check_age(self, profile: ApplicantProfile) -> RuleResult:
        """SW-006: Applicant must be at least 18 years old."""
        rule = self.RULES_CONFIG["age"]
        
        if profile.age is None:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason="Age not provided; assumed 18+ (minimum requirement). Please confirm you are 18 or older.",
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            )
        
        passed = profile.age >= rule["minimum_age"]
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=(
                f"You are {profile.age} years old, which meets the minimum age of 18. ✓"
                if passed else
                f"You must be at least 18 years old to apply. You are currently {profile.age}."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_financial(self, profile: ApplicantProfile) -> RuleResult:
        """SW-007: Financial maintenance — £1,270 in savings for 28 days (waivable)."""
        rule = self.RULES_CONFIG["financial"]
        minimum_savings = rule["minimum_savings"]
        
        # If sponsor certifies maintenance, requirement is waived
        if profile.has_sponsor and profile.sponsor_certifies_maintenance:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason=(
                    "Your sponsor has certified your maintenance on the CoS, "
                    "so the £1,270 savings requirement is waived. ✓"
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
            )
        
        # If has sponsor (A-rated), usually waived
        if profile.has_sponsor:
            return self.create_rule_result(
                rule_id=rule["rule_id"],
                rule_description=rule["description"],
                passed=True,
                reason=(
                    "If your sponsor is A-rated and certifies your maintenance on your CoS, "
                    "the £1,270 savings requirement is waived. ✓ "
                    "Confirm this with your sponsor."
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
                    f"You must hold at least £{minimum_savings:,} in personal savings for 28 consecutive days "
                    "before you apply, OR your sponsor must certify maintenance on your CoS."
                ),
                source_url=rule["source_url"],
                source_section=rule["source_section"],
                severity="advisory",
            )
        
        passed = profile.savings >= minimum_savings
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=(
                f"Your savings of £{profile.savings:,.0f} meet the £{minimum_savings:,} requirement. ✓"
                if passed else
                f"You need at least £{minimum_savings:,} in savings held for 28 days. You have £{profile.savings:,.0f}."
            ),
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def calculate_points(
        self,
        has_sponsor: bool,
        occupation_eligible: bool,
        salary_ok: bool,
        occupation: Optional[Any] = None,
        profile: Optional[ApplicantProfile] = None,
    ) -> Dict[str, Any]:
        """
        Calculate points under the GOV.UK points-based system (SW-005).
        
        The 70-point requirement:
        - 20 points: valid CoS from licensed sponsor
        - 20 points: eligible occupation at RQF 3+
        - 20 points: salary meets threshold
        - 10 points: automatic for meeting standard criteria
        - Additional tradeable points for shortage/PhD
        """
        breakdown = {}
        total = 0
        
        # 20 points: valid CoS from licensed sponsor
        if has_sponsor:
            breakdown["valid_cos"] = 20
            total += 20
        
        # 20 points: eligible occupation at RQF 3+
        if occupation_eligible:
            breakdown["eligible_occupation"] = 20
            total += 20
        
        # 20 points: salary meets general threshold and going rate
        if salary_ok:
            breakdown["salary_threshold"] = 20
            total += 20
        
        # 10 automatic tradeable points for standard applicants
        if has_sponsor and occupation_eligible and salary_ok:
            breakdown["standard_salary_band"] = 10
            total += 10
        
        # Additional tradeable points
        is_shortage = occupation.shortage_occupation if occupation else False
        if is_shortage:
            breakdown["shortage_occupation"] = 20
            total += 20
        
        if profile:
            if profile.is_stem_phd:
                breakdown["stem_phd"] = 20
                total += 20
            elif profile.has_phd:
                breakdown["phd"] = 10
                total += 10
        
        return {"total": total, "required": 70, "breakdown": breakdown}
    
    # ── Abstract Method Implementations ────────────────────────────────────────
    
    def get_required_fields(self) -> List[str]:
        """Return list of required profile fields for Skilled Worker visa."""
        return ["job_title", "salary_annual", "has_sponsor", "country_of_origin"]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        """Return summary of all rules."""
        return {
            rule["rule_id"]: rule["description"]
            for rule in self.RULES_CONFIG.values()
        }
    
    def get_visa_metadata(self) -> Optional[Dict[str, Any]]:
        """Get visa metadata from rules loader."""
        return rules_loader.get_metadata("skilled_worker")
    
    def get_visa_fees(self) -> Optional[Dict[str, Any]]:
        """Get visa fees from rules loader."""
        config = rules_loader.get_visa_config("skilled_worker")
        return config.get("fees") if config else None
    
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """
        Main eligibility function.
        Runs all rules and returns a structured EligibilityResult.
        The verdict is ALWAYS determined by rules only — never by ML.
        """
        rule_results: List[RuleResult] = []
        trace_id = self.get_trace_id()
        
        # ── Missing info check ────────────────────────────────────────────────────
        missing = profile.missing_fields()
        if missing:
            return self.create_eligibility_result(
                verdict=Verdict.INSUFFICIENT_INFO,
                rule_results=[],
                missing_info=missing,
                summary=(
                    f"I need more information to assess your eligibility. "
                    f"Please provide: {self.get_missing_info_message(missing)}"
                ),
                trace_id=trace_id,
            )
        
        # ── Run each rule ─────────────────────────────────────────────────────────
        
        # SW-001: Sponsorship
        sponsorship_result = self.check_sponsorship(profile)
        rule_results.append(sponsorship_result)
        
        # SW-002: Occupation
        occupation_result, occupation = self.check_occupation(profile)
        rule_results.append(occupation_result)
        
        # SW-006: Age (check early as it affects new entrant status)
        age_result = self.check_age(profile)
        rule_results.append(age_result)
        
        # Determine new entrant status if not set
        if profile.is_new_entrant is None and profile.age is not None:
            profile.is_new_entrant = profile.age < 26
        
        # SW-003: Salary
        salary_result, salary_points = self.check_salary(profile, occupation)
        rule_results.append(salary_result)
        
        # SW-004: English Language
        english_result = self.check_english_language(profile)
        rule_results.append(english_result)
        
        # SW-007: Financial
        financial_result = self.check_financial(profile)
        rule_results.append(financial_result)
        
        # ── Points calculation ─────────────────────────────────────────────────────
        points_data = self.calculate_points(
            has_sponsor=profile.has_sponsor is True,
            occupation_eligible=occupation_result.passed,
            salary_ok=salary_result.passed,
            occupation=occupation,
            profile=profile,
        )
        
        # ── Determine overall verdict ─────────────────────────────────────────────
        mandatory_rules = [r for r in rule_results if r.severity == "mandatory"]
        all_mandatory_passed = all(r.passed for r in mandatory_rules)
        
        if all_mandatory_passed:
            verdict = Verdict.ELIGIBLE
            summary = (
                f"✅ Based on the information you provided, you appear to be ELIGIBLE "
                f"for the Skilled Worker Visa. You scored {points_data['total']}/70 points. "
                f"This is a preliminary assessment only — please verify with an immigration professional."
            )
        else:
            verdict = Verdict.NOT_ELIGIBLE
            failed_descriptions = [
                r.rule_description for r in rule_results 
                if not r.passed and r.severity == "mandatory"
            ]
            summary = (
                f"❌ You do not currently meet the requirements for the Skilled Worker Visa. "
                f"Failed requirements: {'; '.join(failed_descriptions)}."
            )
        
        return self.create_eligibility_result(
            verdict=verdict,
            rule_results=rule_results,
            points_earned=points_data["total"],
            points_required=points_data["required"],
            summary=summary,
            trace_id=trace_id,
        )


# ── Convenience function for backward compatibility ─────────────────────────────

def check_eligibility(profile: ApplicantProfile) -> EligibilityResult:
    """
    Convenience function for checking Skilled Worker visa eligibility.
    Maintains backward compatibility with existing code.
    """
    engine = SkilledWorkerRuleEngine()
    return engine.check_eligibility(profile)