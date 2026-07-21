"""
Atlas AI — Global Talent Visa Rule Engine
Deterministic, rule-based eligibility determination.
Source: GOV.UK Global Talent visa guidance
URL: https://www.gov.uk/global-talent-visa

This visa is for leaders or potential leaders in academia, research, 
digital technology, arts and culture, or other eligible fields.
"""

from typing import Optional, Dict, Any, List

from src.rule_engine.base_visa import BaseVisaRuleEngine
from src.rule_engine.rules_base import (
    ApplicantProfile, EligibilityResult, RuleResult, Verdict
)
from src.rule_engine.rules_loader import rules_loader


class GlobalTalentRuleEngine(BaseVisaRuleEngine):
    """
    Rule engine for Global Talent Visa eligibility.
    
    Key features:
    - No sponsorship required
    - No minimum salary requirement
    - Must be endorsed by designated competent body
    - Two stages: endorsement then visa application
    - 5 years path to settlement
    """
    
    # ── Metadata ───────────────────────────────────────────────────────────────
    VISA_TYPE = "global_talent"
    VISA_NAME = "Global Talent Visa"
    GOV_UK_URL = "https://www.gov.uk/global-talent-visa"
    RULES_SOURCE = "GOV.UK Immigration Rules – Global Talent"
    
    # ── Eligible Fields and Endorsing Bodies ───────────────────────────────────
    ELIGIBLE_FIELDS = {
        "academia_research": {
            "name": "Academia or Research",
            "bodies": ["Royal Society", "British Academy", "Royal Academy of Engineering", "UKRI"],
            "categories": ["exceptional_promise", "exceptional_talent"],
        },
        "digital_technology": {
            "name": "Digital Technology",
            "bodies": ["Tech Nation"],
            "categories": ["exceptional_promise", "exceptional_talent"],
        },
        "arts_culture": {
            "name": "Arts and Culture",
            "bodies": ["Arts Council England"],
            "categories": ["exceptional_promise", "exceptional_talent"],
        },
    }
    
    # ── Rules Configuration ────────────────────────────────────────────────────
    # Rules are loaded from JSON file via rules_loader, but we maintain 
    # hardcoded defaults for performance and fallback
    
    DEFAULT_RULES_CONFIG = {
        "endorsement": {
            "rule_id": "GT-001",
            "description": "Applicant must have endorsement from a designated competent body",
            "source_url": "https://www.gov.uk/global-talent-visa/eligibility",
            "source_section": "Endorsement requirements",
        },
        "eligible_field": {
            "rule_id": "GT-002",
            "description": "Applicant must work in an eligible field (academia, research, digital technology, arts)",
            "source_url": "https://www.gov.uk/global-talent-visa/eligibility",
            "source_section": "Eligible fields",
        },
        "exceptional_criteria": {
            "rule_id": "GT-003",
            "description": "Applicant must demonstrate exceptional talent or exceptional promise",
            "source_url": "https://www.gov.uk/global-talent-visa/eligibility",
            "source_section": "Talent and promise criteria",
        },
    }
    
    def __init__(self):
        """Initialize the rule engine and load rules from JSON."""
        # Try to load rules from JSON, fall back to defaults
        json_rules = rules_loader.get_all_rules("global_talent")
        if json_rules:
            self.RULES_CONFIG = json_rules
        else:
            self.RULES_CONFIG = self.DEFAULT_RULES_CONFIG.copy()
    
    # ── Rule Evaluation Methods ────────────────────────────────────────────────
    
    def check_endorsement(self, profile: ApplicantProfile) -> RuleResult:
        """GT-001: Must have endorsement from designated body."""
        rule = self.RULES_CONFIG["endorsement"]
        
        # Check if user indicates they have endorsement
        # This is a simplified check - actual endorsement is a separate application
        has_endorsement = getattr(profile, 'has_endorsement', None)
        
        if has_endorsement is True:
            reason = (
                "You indicate you have (or are applying for) endorsement from a designated competent body. ✓\n"
                "The endorsement must be from: Royal Society, British Academy, Royal Academy of Engineering, "
                "UKRI (for academia/research), Tech Nation (for digital technology), or Arts Council England (for arts)."
            )
            passed = True
        elif has_endorsement is False:
            reason = (
                "You must obtain endorsement from a designated competent body before applying for this visa. "
                "This involves demonstrating your achievements and potential in your field."
            )
            passed = False
        else:
            reason = (
                "The Global Talent visa requires endorsement from a designated competent body. "
                "You must first apply for endorsement, then apply for the visa. "
                "The endorsement body depends on your field: "
                "Tech Nation (digital), Arts Council England (arts), or UK academies (academia/research)."
            )
            passed = True  # Advisory - provide information
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_eligible_field(self, profile: ApplicantProfile) -> RuleResult:
        """GT-002: Must work in eligible field."""
        rule = self.RULES_CONFIG["eligible_field"]
        
        job_title = (profile.job_title or "").lower()
        
        # Check for eligible field indicators
        eligible_keywords = {
            "academia_research": ["professor", "researcher", "scientist", "academic", "lecturer", "phd", "postdoc"],
            "digital_technology": ["software", "developer", "engineer", "data scientist", "ai", "machine learning",
                                  "cybersecurity", "blockchain", "fintech", "tech lead", "cto", "founder"],
            "arts_culture": ["artist", "designer", "musician", "writer", "actor", "director", 
                           "curator", "photographer", "filmmaker", "dancer", "composer"],
        }
        
        matched_field = None
        for field, keywords in eligible_keywords.items():
            if any(kw in job_title for kw in keywords):
                matched_field = field
                break
        
        if matched_field:
            field_info = self.ELIGIBLE_FIELDS[matched_field]
            reason = (
                f"Your profession appears to be in the field of {field_info['name']}. ✓\n"
                f"The endorsing body for this field is: {', '.join(field_info['bodies'])}."
            )
            passed = True
        else:
            reason = (
                f"Your job title '{profile.job_title}' doesn't clearly match an eligible field. "
                "The Global Talent visa covers: Academia/Research, Digital Technology, and Arts/Culture. "
                "You may still be eligible if your work falls into one of these categories."
            )
            passed = True  # Advisory
        
        return self.create_rule_result(
            rule_id=rule["rule_id"],
            rule_description=rule["description"],
            passed=passed,
            reason=reason,
            source_url=rule["source_url"],
            source_section=rule["source_section"],
        )
    
    def check_exceptional_criteria(self, profile: ApplicantProfile) -> RuleResult:
        """GT-003: Must demonstrate exceptional talent or promise."""
        rule = self.RULES_CONFIG["exceptional_criteria"]
        
        # This is assessed by the endorsing body, not us
        reason = (
            "You must demonstrate either:\n"
            "• Exceptional Promise: You are an emerging leader with potential to become a world leader\n"
            "• Exceptional Talent: You are already a recognised world leader in your field\n\n"
            "Evidence may include: awards, publications, patents, media coverage, speaking engagements, "
            "leadership roles, significant contributions to your field, or letters of recommendation."
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
        return ["job_title"]
    
    def get_rules_summary(self) -> Dict[str, Any]:
        return {rule["rule_id"]: rule["description"] for rule in self.RULES_CONFIG.values()}
    
    def get_visa_metadata(self) -> Optional[Dict[str, Any]]:
        """Get visa metadata from rules loader."""
        return rules_loader.get_metadata("global_talent")
    
    def get_visa_fees(self) -> Optional[Dict[str, Any]]:
        """Get visa fees from rules loader."""
        config = rules_loader.get_visa_config("global_talent")
        return config.get("fees") if config else None
    
    def get_eligible_fields(self) -> Optional[Dict[str, Any]]:
        """Get eligible fields from rules loader."""
        config = rules_loader.get_visa_config("global_talent")
        return config.get("eligible_fields") if config else None
    
    def check_eligibility(self, profile: ApplicantProfile) -> EligibilityResult:
        """Main eligibility check for Global Talent visa."""
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
        endorsement = self.check_endorsement(profile)
        rule_results.append(endorsement)
        
        field = self.check_eligible_field(profile)
        rule_results.append(field)
        
        criteria = self.check_exceptional_criteria(profile)
        rule_results.append(criteria)
        
        # Determine verdict
        mandatory_failed = [r for r in rule_results if not r.passed and r.severity == "mandatory"]
        
        if not mandatory_failed:
            verdict = Verdict.ELIGIBLE
            summary = (
                f"✅ Based on the information provided, you may be eligible for the Global Talent Visa.\n\n"
                f"**Next Steps:**\n"
                f"1. Apply for endorsement from the relevant competent body\n"
                f"2. Once endorsed, apply for the visa within 3 months\n\n"
                f"This visa offers a 5-year path to settlement (ILR) and does not require sponsorship."
            )
        else:
            verdict = Verdict.NOT_ELIGIBLE
            failed_desc = [r.rule_description for r in mandatory_failed]
            summary = (
                f"❌ Based on the information provided, you may not be eligible. "
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
    engine = GlobalTalentRuleEngine()
    return engine.check_eligibility(profile)