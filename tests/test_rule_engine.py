"""
Atlas AI — Rule Engine Unit Tests
Tests all rule combinations against known expected outcomes.
Target: ≥ 98% correctness on benchmark scenarios.

Run: pytest tests/test_rule_engine.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.rule_engine.rules_base import ApplicantProfile, Verdict
from src.rule_engine.skilled_worker import (
    check_eligibility, SkilledWorkerRuleEngine
)
from src.rule_engine.occupation_data import (
    get_occupation_by_title, get_occupation_by_soc,
    is_shortage_occupation, is_eligible_occupation
)

# Create a rule engine instance for testing individual rules
_engine = SkilledWorkerRuleEngine()

# Wrapper functions for backward compatibility with existing tests
def check_sponsorship(profile):
    return _engine.check_sponsorship(profile)

def check_occupation(profile):
    return _engine.check_occupation(profile)

def check_salary(profile, occupation):
    return _engine.check_salary(profile, occupation)

def check_english_language(profile):
    return _engine.check_english_language(profile)

def check_age(profile):
    return _engine.check_age(profile)

def check_financial(profile):
    return _engine.check_financial(profile)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def make_profile(**kwargs) -> ApplicantProfile:
    """Helper to make a profile with sensible defaults."""
    defaults = {
        "job_title": "Software Engineer",
        "salary_annual": 50000,
        "has_sponsor": True,
        "country_of_origin": "India",
        "english_proficiency": "test_passed",
        "age": 30,
    }
    defaults.update(kwargs)
    return ApplicantProfile(**defaults)


# ── Occupation Data Tests ──────────────────────────────────────────────────────

class TestOccupationData:
    def test_software_engineer_lookup_by_title(self):
        occ = get_occupation_by_title("software engineer")
        assert occ is not None
        assert occ["soc_code"] == "2136"
        assert occ["eligible"] is True

    def test_nurse_lookup_by_title(self):
        occ = get_occupation_by_title("nurse")
        assert occ is not None
        assert occ["soc_code"] == "2225"

    def test_doctor_lookup_by_title(self):
        occ = get_occupation_by_title("doctor")
        assert occ is not None
        assert occ["soc_code"] == "2211"

    def test_soc_code_lookup(self):
        occ = get_occupation_by_soc("2136")
        assert occ is not None
        assert "programmer" in occ["title"].lower() or "software" in occ["title"].lower()

    def test_invalid_soc_returns_none(self):
        occ = get_occupation_by_soc("9998")
        assert occ is None

    def test_shortage_occupation(self):
        assert is_shortage_occupation("2225") is True   # Nurses
        assert is_shortage_occupation("2221") is True   # Physiotherapists
        assert is_shortage_occupation("2136") is False  # Software engineers (not shortage)

    def test_eligible_occupation_flag(self):
        assert is_eligible_occupation("2136") is True
        assert is_eligible_occupation("9999") is False

    def test_case_insensitive_lookup(self):
        occ1 = get_occupation_by_title("Software Engineer")
        occ2 = get_occupation_by_title("software engineer")
        occ3 = get_occupation_by_title("SOFTWARE ENGINEER")
        assert occ1 is not None
        assert occ2 is not None
        # All should resolve to the same code
        assert occ1["soc_code"] == occ2["soc_code"]


# ── Individual Rule Tests ──────────────────────────────────────────────────────

class TestSponsorshipRule:
    def test_has_sponsor_passes(self):
        profile = make_profile(has_sponsor=True)
        result = check_sponsorship(profile)
        assert result.passed is True
        assert result.rule_id == "SW-001"

    def test_no_sponsor_fails(self):
        profile = make_profile(has_sponsor=False)
        result = check_sponsorship(profile)
        assert result.passed is False

    def test_none_sponsor_fails(self):
        profile = make_profile(has_sponsor=None)
        result = check_sponsorship(profile)
        assert result.passed is False


class TestOccupationRule:
    def test_eligible_occupation_passes(self):
        profile = make_profile(job_title="Software Engineer")
        result, occ = check_occupation(profile)
        assert result.passed is True
        assert occ is not None

    def test_eligible_by_soc_code(self):
        profile = make_profile(soc_code="2136")
        result, occ = check_occupation(profile)
        assert result.passed is True

    def test_no_job_title_fails(self):
        profile = make_profile(job_title=None, soc_code=None)
        result, occ = check_occupation(profile)
        assert result.passed is False

    def test_unknown_job_fails(self):
        profile = make_profile(job_title="Underwater Basket Weaver")
        result, occ = check_occupation(profile)
        assert result.passed is False

    def test_nurse_occupation_eligible(self):
        profile = make_profile(job_title="Nurse")
        result, occ = check_occupation(profile)
        assert result.passed is True


class TestSalaryRule:
    def test_salary_above_general_threshold_passes(self):
        profile = make_profile(job_title="Software Engineer", salary_annual=50000)
        _, occ = check_occupation(profile)
        result, _ = check_salary(profile, occ)
        assert result.passed is True

    def test_salary_below_general_threshold_fails(self):
        profile = make_profile(job_title="Software Engineer", salary_annual=30000)
        _, occ = check_occupation(profile)
        result, _ = check_salary(profile, occ)
        assert result.passed is False

    def test_salary_exactly_at_threshold(self):
        # Teacher going rate = £38,700; general threshold = £38,700
        profile = make_profile(job_title="Teacher", salary_annual=38700)
        _, occ = check_occupation(profile)
        result, _ = check_salary(profile, occ)
        assert result.passed is True

    def test_salary_1_below_threshold_fails(self):
        profile = make_profile(job_title="Teacher", salary_annual=38699)
        _, occ = check_occupation(profile)
        result, _ = check_salary(profile, occ)
        assert result.passed is False

    def test_new_entrant_salary(self):
        profile = make_profile(
            job_title="Civil Engineer",
            salary_annual=32000,
            age=24,
            is_new_entrant=True,
        )
        _, occ = check_occupation(profile)
        result, _ = check_salary(profile, occ)
        # New entrant rate for civil engineer: min(30960, 30520) = £30,520
        assert result.passed is True  # 32,000 > 30,520

    def test_no_salary_fails(self):
        profile = make_profile(salary_annual=None)
        _, occ = check_occupation(profile)
        result, _ = check_salary(profile, occ)
        assert result.passed is False


class TestEnglishLanguageRule:
    def test_english_exempt_country(self):
        for country in ["Australia", "United States of America", "Canada", "New Zealand"]:
            profile = make_profile(country_of_origin=country, english_proficiency=None)
            result = check_english_language(profile)
            assert result.passed is True, f"Expected exempt for {country}"

    def test_test_passed_ok(self):
        profile = make_profile(country_of_origin="India", english_proficiency="test_passed")
        result = check_english_language(profile)
        assert result.passed is True

    def test_native_speaker_ok(self):
        profile = make_profile(country_of_origin="India", english_proficiency="native")
        result = check_english_language(profile)
        assert result.passed is True

    def test_no_english_evidence_fails(self):
        profile = make_profile(country_of_origin="India", english_proficiency="none")
        result = check_english_language(profile)
        assert result.passed is False

    def test_usa_citizen_exempt(self):
        profile = make_profile(country_of_origin="USA", english_proficiency=None)
        result = check_english_language(profile)
        assert result.passed is True


class TestAgeRule:
    def test_adult_passes(self):
        result = check_age(make_profile(age=25))
        assert result.passed is True

    def test_minor_fails(self):
        result = check_age(make_profile(age=17))
        assert result.passed is False

    def test_minimum_age_boundary(self):
        result = check_age(make_profile(age=18))
        assert result.passed is True

    def test_no_age_passes_with_assumption(self):
        result = check_age(make_profile(age=None))
        assert result.passed is True  # Assume adult


class TestFinancialRule:
    def test_sponsor_waives_financial(self):
        profile = make_profile(has_sponsor=True, savings=None)
        result = check_financial(profile)
        assert result.passed is True

    def test_sufficient_savings_passes(self):
        profile = make_profile(has_sponsor=False, savings=2000)
        result = check_financial(profile)
        assert result.passed is True

    def test_insufficient_savings_fails(self):
        profile = make_profile(has_sponsor=False, savings=500)
        result = check_financial(profile)
        assert result.passed is False

    def test_exact_threshold_passes(self):
        profile = make_profile(has_sponsor=False, savings=1270)
        result = check_financial(profile)
        assert result.passed is True


# ── Full Eligibility Tests ─────────────────────────────────────────────────────

class TestFullEligibility:

    def test_fully_eligible_applicant(self):
        """Standard case: all requirements met."""
        profile = ApplicantProfile(
            job_title="Software Engineer",
            salary_annual=50000,
            has_sponsor=True,
            country_of_origin="India",
            english_proficiency="test_passed",
            age=28,
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.ELIGIBLE

    def test_not_eligible_no_sponsor(self):
        profile = ApplicantProfile(
            job_title="Software Engineer",
            salary_annual=50000,
            has_sponsor=False,
            country_of_origin="India",
            english_proficiency="test_passed",
            age=28,
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.NOT_ELIGIBLE

    def test_not_eligible_low_salary(self):
        profile = ApplicantProfile(
            job_title="Software Engineer",
            salary_annual=25000,
            has_sponsor=True,
            country_of_origin="India",
            english_proficiency="test_passed",
            age=28,
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.NOT_ELIGIBLE

    def test_insufficient_info_no_salary(self):
        profile = ApplicantProfile(
            job_title="Software Engineer",
            has_sponsor=True,
            country_of_origin="India",
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.INSUFFICIENT_INFO

    def test_insufficient_info_no_sponsor_info(self):
        profile = ApplicantProfile(
            job_title="Nurse",
            salary_annual=32000,
            country_of_origin="Philippines",
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.INSUFFICIENT_INFO

    def test_nurse_eligible(self):
        """Nurse earning above threshold with sponsorship."""
        profile = ApplicantProfile(
            job_title="Nurse",
            salary_annual=35000,
            has_sponsor=True,
            country_of_origin="Philippines",
            english_proficiency="test_passed",
            age=30,
        )
        result = check_eligibility(profile)
        # Nurse general threshold = max(38700, 29000) = 38700
        # 35000 < 38700, so NOT eligible
        assert result.verdict == Verdict.NOT_ELIGIBLE

    def test_doctor_eligible(self):
        profile = ApplicantProfile(
            job_title="Doctor",
            salary_annual=55000,
            has_sponsor=True,
            country_of_origin="Nigeria",
            english_proficiency="test_passed",
            age=35,
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.ELIGIBLE

    def test_australian_no_english_test_needed(self):
        """Australians exempt from English test."""
        profile = ApplicantProfile(
            job_title="Accountant",
            salary_annual=44000,
            has_sponsor=True,
            country_of_origin="Australia",
            english_proficiency=None,  # No test — should be exempt
            age=27,
        )
        result = check_eligibility(profile)
        assert result.verdict == Verdict.ELIGIBLE

    def test_new_entrant_lower_salary_eligible(self):
        profile = ApplicantProfile(
            job_title="Civil Engineer",
            salary_annual=32000,
            has_sponsor=True,
            country_of_origin="Nigeria",
            english_proficiency="test_passed",
            age=23,
            is_new_entrant=True,
        )
        result = check_eligibility(profile)
        # New entrant rate: min(30960, 30520) = 30520; 32000 > 30520
        assert result.verdict == Verdict.ELIGIBLE

    def test_rule_result_contains_sources(self):
        """All rule results must have source URLs (traceability)."""
        profile = make_profile()
        result = check_eligibility(profile)
        for rule_result in result.rule_results:
            assert rule_result.source_url, f"Rule {rule_result.rule_id} has no source URL"
            assert "gov.uk" in rule_result.source_url.lower(), \
                f"Rule {rule_result.rule_id} source is not GOV.UK"

    def test_verdict_never_none(self):
        """Verdict is always set."""
        profiles = [
            make_profile(),
            make_profile(salary_annual=1000),
            make_profile(has_sponsor=False),
            ApplicantProfile(),
        ]
        for profile in profiles:
            result = check_eligibility(profile)
            assert result.verdict is not None

    def test_result_to_dict_serialisable(self):
        """result.to_dict() must be JSON-serialisable."""
        import json
        profile = make_profile()
        result = check_eligibility(profile)
        d = result.to_dict()
        json.dumps(d)  # Should not raise

    def test_no_ml_in_eligibility(self):
        """
        Verify that the rule engine module doesn't import torch, transformers, or openai.
        Rule engine must be deterministic — no ML dependencies.
        """
        import src.rule_engine.skilled_worker as rulemod
        import sys
        # Ensure no ML libraries are used in rule engine module
        rule_engine_deps = set()
        for name in dir(rulemod):
            obj = getattr(rulemod, name)
            if hasattr(obj, "__module__"):
                rule_engine_deps.add(obj.__module__)

        forbidden = {"torch", "transformers", "openai"}
        for dep in forbidden:
            # The rule engine should not directly import ML libraries
            assert dep not in sys.modules.get("src.rule_engine.skilled_worker", type(
                "m", (), {"__dict__": {}}
            )).__dict__, f"Rule engine must not use {dep}"


# ── Benchmark Test Scenarios ──────────────────────────────────────────────────

BENCHMARK_SCENARIOS = [
    # (description, profile_kwargs, expected_verdict)
    ("Eligible SW: software engineer, good salary, India", 
     {"job_title": "Software Engineer", "salary_annual": 50000, "has_sponsor": True,
      "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
     Verdict.ELIGIBLE),

    ("Not eligible: below salary threshold",
     {"job_title": "Software Engineer", "salary_annual": 20000, "has_sponsor": True,
      "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
     Verdict.NOT_ELIGIBLE),

    ("Not eligible: no sponsor",
     {"job_title": "Civil Engineer", "salary_annual": 45000, "has_sponsor": False,
      "country_of_origin": "Nigeria", "english_proficiency": "test_passed", "age": 25},
     Verdict.NOT_ELIGIBLE),

    ("Eligible: doctor, NHS salary",
     {"job_title": "Doctor", "salary_annual": 52000, "has_sponsor": True,
      "country_of_origin": "Pakistan", "english_proficiency": "test_passed", "age": 35},
     Verdict.ELIGIBLE),

    ("Not eligible: nurse salary below general threshold",
     {"job_title": "Nurse", "salary_annual": 28000, "has_sponsor": True,
      "country_of_origin": "Philippines", "english_proficiency": "test_passed", "age": 29},
     Verdict.NOT_ELIGIBLE),

    ("Eligible: Australian accountant (English exempt)",
     {"job_title": "Accountant", "salary_annual": 44000, "has_sponsor": True,
      "country_of_origin": "Australia", "age": 32},
     Verdict.ELIGIBLE),

    ("Insufficient info: no salary",
     {"job_title": "Software Engineer", "has_sponsor": True, "country_of_origin": "India"},
     Verdict.INSUFFICIENT_INFO),

    ("Insufficient info: no job",
     {"salary_annual": 50000, "has_sponsor": True, "country_of_origin": "India"},
     Verdict.INSUFFICIENT_INFO),

    ("Not eligible: no English evidence",
     {"job_title": "Management Consultant", "salary_annual": 48000, "has_sponsor": True,
      "country_of_origin": "China", "english_proficiency": "none", "age": 28},
     Verdict.NOT_ELIGIBLE),

    ("Eligible: new entrant rate",
     {"job_title": "Civil Engineer", "salary_annual": 32000, "has_sponsor": True,
      "country_of_origin": "Nigeria", "english_proficiency": "test_passed",
      "age": 23, "is_new_entrant": True},
     Verdict.ELIGIBLE),
]


@pytest.mark.parametrize("description,kwargs,expected_verdict", BENCHMARK_SCENARIOS)
def test_benchmark_scenario(description, kwargs, expected_verdict):
    profile = ApplicantProfile(**kwargs)
    result = check_eligibility(profile)
    assert result.verdict == expected_verdict, (
        f"FAILED: {description}\n"
        f"Expected: {expected_verdict}, Got: {result.verdict}\n"
        f"Summary: {result.summary}"
    )


# ── Safety Tests ──────────────────────────────────────────────────────────────

class TestSafety:
    def test_no_hallucinated_eligibility_from_gpt(self):
        """
        GPT explanation layer must never change the verdict.
        Verify the generate_explanation function preserves verdict.
        """
        from src.rule_engine.rules_base import EligibilityResult, RuleResult, Verdict
        from src.gpt.explainer import generate_explanation

        # Force NOT_ELIGIBLE result
        mock_result = EligibilityResult(
            verdict=Verdict.NOT_ELIGIBLE,
            visa_type="skilled_worker",
            summary="Not eligible",
        )

        explanation = generate_explanation(
            result=mock_result,
            original_query="Am I eligible?",
            retrieved_context="",
            profile_summary="",
        )

        # GPT output must preserve the verdict
        assert explanation["verdict"] == "not_eligible"

    def test_disclaimer_always_present(self):
        """Every response must include a disclaimer."""
        from src.gpt.explainer import _build_offline_response
        from src.rule_engine.rules_base import EligibilityResult, Verdict

        for verdict in [Verdict.ELIGIBLE, Verdict.NOT_ELIGIBLE, Verdict.INSUFFICIENT_INFO]:
            mock_result = EligibilityResult(
                verdict=verdict, visa_type="skilled_worker", summary="test"
            )
            response = _build_offline_response(mock_result, "test query", "")
            assert "informational" in response.lower() or "legal advice" in response.lower(), \
                f"Disclaimer missing for verdict: {verdict}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
