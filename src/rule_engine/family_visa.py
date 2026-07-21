"""
Atlas AI — Family Visa Rule Engine
Deterministic, rule-based eligibility determination.
Source: GOV.UK Family visa guidance
URL: https://www.gov.uk/uk-family-visa

This visa is for individuals who want to join or stay with family members 
who are settled in the UK (spouse, partner, parent, or child).
"""

from typing import Optional, Dict, Any, List

from src.rule_engine.base_visa import BaseVisaRuleEngine
from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)
from src.rule_engine.rules_loader import rules_loader


class FamilyVisaRuleEngine(BaseVisaRuleEngine):
    """
    Rule engine for Family Visa eligibility (Spouse/Partner route).
    
    Key features:
    - Must be married to or in a genuine relationship with a UK settled person
    - Must meet financial requirement (£18,600 minimum income)
    - Must meet English language requirement
    - Must have adequate accommodation
    - Path to settlement after 5 years
    """
    
    # ── Metadata ───────────────────────────────────────────────────────────────
    VISA_TYPE = "family"
    VISA_NAME = "Family Visa (Spouse/Partner)"
    GOV_UK_URL = "https://www.gov.uk/uk-family-visa"
    RULES_SOURCE = "GOV.UK Immigration Rules – Appendix FM"
    
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
    
    # ── Financial Requirements ──────────────────────────────────────────────────
    MINIMUM_INCOME = 18600  # Annual income requirement for spouse
    MINIMUM_INCOME_WITH_CHILDREN = 22400  # With one child
    ADDITIONAL_CHILD = 2400  # Per additional child
    CASH_SAVINGS_THRESHOLD = 16000  # Minimum savings to use cash route
    SAVINGS_MULTIPLIER = 2.5  # Savings divided by 2.5 for income equivalent
    
    # ── Rules Configuration ────────────────────────────────────────────────────
    # Rules are loaded from JSON file via rules_loader, but we maintain 
    # hardcoded defaults for performance and fallback
    
    DEFAULT_RULES_CONFIG = {
        "relationship": {
            "rule_id": "FV-001",
            "description": "Must be married to or in a genuine subsisting relationship with a UK settled person",
            "source_url": "https://www.gov.uk/uk-family-visa/eligibility",
            "source_section": "Relationship requirements",
        },
        "sponsor_status": {
            "rule_id": "FV-002",
            "description": "Sponsor must be a British citizen, settled person, or have refugee/humanitarian protection",
            "source_url": "https://www.gov.uk/uk-family-visa/eligibility",
            "source_section": "Sponsor eligibility",
        },
        "financial": {
            "rule_id": "FV-003",
            "description": "Must meet minimum income requirement (£18,600 annually, higher with children)",
            "source_url": "https://www.gov.uk/uk-family-visa/financial-requirements",
            "source_section": "Financial requirement",
        },
        "accommodation": {
            "rule_id": "FV-004",
            "description": "Must have adequate accommodation without recourse to public funds",
            "source_url": "https://www.gov.uk/uk-family-visa/eligibility",
            "source_section": "Accommodation requirement",
        },
        "english_language": {
            "rule_id": "FV-005",
            "description": "Must meet English language requirement at CEFR A1 (initial) / A2 (extension)",
            "source_url": "https://www.gov.uk/uk-family-visa/knowledge-of-english",
            "source_section": "English language requirement",
        },
        "genuine_relationship": {
            "rule_id": "FV-006",
            "description": "Must intend to live together permanently in the UK",
            "source_url": "https://www.gov.uk/uk-family-visa/eligibility",
            "source_section": "Genuine relationship",
        },
    }
    
    def __init__(self):
        """Initialize the rule engine and load rules from JSON."""
        # Try to load rules from JSON, fall back to defaults
        json_rules = rules_loader.get_all_rules("family")
        if json_rules:
            self.RULES_CONFIG = json_rules
        else:
            self.RULES_CONFIG = self.DEFAULT_RULES_CONFIG.copy()
    
    # ── Rule Evaluation Methods ────────────────────────────────────────────────
    
    def check_relationship(self, profile: ApplicantProfile) -> RuleResult:
        """FV-001: Must be in qualifying relationship."""
        rule = self.RULES_CONFIG["relationship"]
        
        relationship_status = getattr(profile, 'relationship_status', None)
        partner_uk_status = getattr(profile, 'partner_uk_status', None)
        
        valid_relationships = ["married", "civil_partnership", "unmarried_partner"]
        
        if relationship_status and relationship_status.lower() in valid_relationships:
            relationship_type = {
                "married": "married",
                "civil_partnership": "in a civil partnership",
                "unmarried_partner": "in a genuine relationship (living together for 2+ years)",
            }
            reason = (
                f"You are {relationship_type.get(relationship_status.lower(), relationship_status)} "
                f"with a person who is {partner_uk_status or 'settled in the UK'}. ✓\n"
                "You will need to provide evidence of your relationship "
                "(marriage certificate, civil partnership certificate, or proof of cohabitation)."
            )
            passed = True
        else:
            reason = (
                "You must be either:\n"
                "• Married to or in a civil partnership with a UK settled person, OR\n"
                "• In a genuine relationship (unmarried partners) having lived together for at least 2 years\n\n"
                "Same-sex relationships are recognized equally."
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
    
    def check_sponsor_status(self, profile: ApplicantProfile) -> RuleResult:
        """FV-002: Sponsor must be eligible."""
        rule = self.RULES_CONFIG["sponsor_status"]
        
        partner_uk_status = getattr(profile, 'partner_uk_status', None)
        
        eligible_statuses = [
            "british citizen", "british", "uk citizen",
            "settled", "ilr", "indefinite leave to remain",
            "pre-settled", "eu settled",
            "refugee", "humanitarian protection",
        ]
        
        if partner_uk_status:
            status_lower = partner_uk_status.lower()
            is_eligible = any(s in status_lower for s in eligible_statuses)
            
            if is_eligible:
                reason = (
                    f"Your partner's status ({partner_uk_status}) qualifies them to sponsor you. ✓\n"
                    "They will need to provide proof of their status (passport, BRP, etc.)."
                )
                passed = True
            else:
                reason = (
                    f"Your partner's status '{partner_uk_status}' may not qualify them to sponsor you. "
                    "The sponsor must be:\n"
                    "• A British citizen\n"
                    "• Settled in the UK (ILR, EU Settled Status)\n"
                    "• A refugee or person with humanitarian protection"
                )
                passed = False
        else:
            reason = (
                "Your partner must be a British citizen, settled in the UK (ILR/EU Settled Status), "
                "or have refugee/humanitarian protection status. "
                "They will need to provide proof of their status."
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
    
    def check_financial(self, profile: ApplicantProfile) -> RuleResult:
        """FV-003: Financial requirement."""
        rule = self.RULES_CONFIG["financial"]
        
        # Get income information
        sponsor_income = getattr(profile, 'sponsor_income', None)
        applicant_income = getattr(profile, 'applicant_income', None)
        cash_savings = profile.savings
        children_count = getattr(profile, 'children_count', 0)
        
        # Calculate required income
        required_income = self.MINIMUM_INCOME
        if children_count > 0:
            required_income = self.MINIMUM_INCOME_WITH_CHILDREN
            if children_count > 1:
                required_income += (children_count - 1) * self.ADDITIONAL_CHILD
        
        # Calculate total income
        total_income = (sponsor_income or 0) + (applicant_income or 0)
        
        # Check if income requirement is met
        income_met = total_income >= required_income
        
        # Check if cash savings can be used
        savings_income = 0
        if cash_savings and cash_savings > self.CASH_SAVINGS_THRESHOLD:
            savings_income = (cash_savings - self.CASH_SAVINGS_THRESHOLD) / self.SAVINGS_MULTIPLIER
        
        total_with_savings = total_income + savings_income
        savings_route_met = total_with_savings >= required_income
        
        if income_met:
            reason = (
                f"The combined income of £{total_income:,.0f}/year meets the requirement of "
                f"£{required_income:,.0f}/year. ✓\n"
                "Income can be from employment, self-employment, pensions, or certain benefits."
            )
            passed = True
        elif savings_route_met and cash_savings:
            reason = (
                f"While income alone (£{total_income:,.0f}) is below the requirement, "
                f"your savings of £{cash_savings:,.0f} can be used to meet the requirement. ✓\n"
                f"Savings contribution: £{savings_income:,.0f}/year equivalent.\n"
                f"Total equivalent income: £{total_with_savings:,.0f}/year (required: £{required_income:,.0f})."
            )
            passed = True
        elif not sponsor_income and not applicant_income:
            reason = (
                f"You must meet the minimum income requirement of £{required_income:,.0f}/year.\n\n"
                f"This can be met through:\n"
                f"• Employment income (UK or overseas)\n"
                f"• Self-employment income\n"
                f"• Cash savings above £16,000 (held for 6 months)\n"
                f"• Certain benefits (if sponsor receives disability benefits)\n\n"
                f"Note: Income from children's benefits does not count."
            )
            passed = False
        else:
            shortfall = required_income - total_income
            reason = (
                f"The combined income of £{total_income:,.0f}/year is below the required "
                f"£{required_income:,.0f}/year. Shortfall: £{shortfall:,.0f}/year.\n\n"
                f"Ways to meet the requirement:\n"
                f"• Increase employment income\n"
                f"• Use cash savings above £16,000 (need £{required_income * 2.5 + 16000:,.0f} in savings)\n"
                f"• Check if sponsor receives qualifying benefits (disability-related)"
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
    
    def check_accommodation(self, profile: ApplicantProfile) -> RuleResult:
        """FV-004: Accommodation requirement."""
        rule = self.RULES_CONFIG["accommodation"]
        
        reason = (
            "You must have adequate accommodation in the UK that:\n"
            "• Is owned or occupied exclusively by your family\n"
            "• Does not contravene overcrowding rules\n"
            "• Does not rely on public funds\n\n"
            "Evidence needed: property inspection report, tenancy agreement, "
            "or mortgage statement showing adequate space for your family."
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
    
    def check_english_language(self, profile: ApplicantProfile) -> RuleResult:
        """FV-005: English language requirement."""
        rule = self.RULES_CONFIG["english_language"]
        
        country_lower = (profile.country_of_origin or "").lower().strip()
        is_exempt = country_lower in self.ENGLISH_EXEMPT_COUNTRIES
        
        # Age exemption
        age = profile.age
        is_age_exempt = age is not None and (age < 18 or age >= 65)
        
        # Disability exemption
        has_disability = getattr(profile, 'has_disability_exemption', False)
        
        if is_exempt:
            passed = True
            reason = (
                f"Citizens of {profile.country_of_origin} are exempt from the English language requirement. ✓"
            )
        elif is_age_exempt:
            passed = True
            reason = (
                f"At age {age}, you are exempt from the English language requirement. ✓"
            )
        elif has_disability:
            passed = True
            reason = (
                "You have an exemption due to a physical or mental condition. ✓\n"
                "You will need medical evidence to support this claim."
            )
        elif profile.english_proficiency in ("test_passed", "native", "exempt"):
            passed = True
            reason = (
                "You have demonstrated English language proficiency through an approved test "
                "(IELTS for UKVI, PTE Academic, or equivalent) at CEFR A1 level. ✓"
            )
        elif profile.english_proficiency == "none":
            passed = False
            reason = (
                "You must demonstrate English language ability at CEFR A1 level (basic). "
                "Take an approved English language test (IELTS for UKVI, PTE Academic, "
                "or LanguageCert) at A1 level or higher."
            )
        else:
            passed = True
            reason = (
                "English language evidence not yet confirmed. You will need to take an approved "
                "English test at CEFR A1 level (basic) for the initial application. "
                "For extension applications, A2 level will be required."
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
    
    def check_genuine_relationship(self, profile: ApplicantProfile) -> RuleResult:
        """FV-006: Genuine relationship requirement."""
        rule = self.RULES_CONFIG["genuine_relationship"]
        
        reason = (
            "You and your partner must intend to live together permanently in the UK. "
            "You will need to provide evidence of:\n"
            "• Your relationship history (how you met, communication)\n"
            "• Plans to live together in the UK\n"
            "• Any previous cohabitation\n\n"
            "For unmarried partners, you must prove you have been in a genuine relationship "
            "similar to marriage for at least 2 years."
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
        return ["relationship_status", "partner_uk_status", "sponsor_income", "english_proficiency"]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        return {rule["rule_id"]: rule["description"] for rule in self.RULES_CONFIG.values()}
    
    def get_visa_metadata(self) -> Optional[Dict[str, Any]]:
        """Get visa metadata from rules loader."""
        return rules_loader.get_metadata("family")
    
    def get_visa_fees(self) -> Optional[Dict[str, Any]]:
        """Get visa fees from rules loader."""
        config = rules_loader.get_visa_config("family")
        return config.get("fees") if config else None
    
    def get_financial_calculations(self) -> Optional[Dict[str, Any]]:
        """Get financial calculation rules from rules loader."""
        config = rules_loader.get_visa_config("family")
        return config.get("financial_calculations") if config else None
    
    def get_english_exemptions(self) -> Optional[Dict[str, Any]]:
        """Get English language exemptions from rules loader."""
        config = rules_loader.get_visa_config("family")
        return config.get("english_exemptions") if config else None
    
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """Main eligibility check for Family visa."""
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
        relationship = self.check_relationship(profile)
        rule_results.append(relationship)
        
        sponsor = self.check_sponsor_status(profile)
        rule_results.append(sponsor)
        
        financial = self.check_financial(profile)
        rule_results.append(financial)
        
        accommodation = self.check_accommodation(profile)
        rule_results.append(accommodation)
        
        english = self.check_english_language(profile)
        rule_results.append(english)
        
        genuine = self.check_genuine_relationship(profile)
        rule_results.append(genuine)
        
        # Determine verdict
        mandatory_failed = [r for r in rule_results if not r.passed and r.severity == "mandatory"]
        
        if not mandatory_failed:
            verdict = Verdict.ELIGIBLE
            summary = (
                f"✅ Based on the information provided, you appear to be ELIGIBLE "
                f"for the Family Visa (Spouse/Partner route).\n\n"
                f"This visa grants 2.5 years initially, after which you can extend for another 2.5 years. "
                f"After 5 years in the UK, you may be eligible to apply for Indefinite Leave to Remain (ILR)."
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
    engine = FamilyVisaRuleEngine()
    return engine.check_eligibility(profile)