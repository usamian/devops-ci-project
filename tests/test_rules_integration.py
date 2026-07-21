"""
Atlas AI — Rules Integration Test
Tests the JSON rules loading and visa recommendation system.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rule_engine.rules_loader import rules_loader
from src.rule_engine.rules_base import ApplicantProfile
from src.rule_engine.visa_recommender import get_visa_recommendation
from src.gpt.visa_advisor import visa_advisor


def test_rules_loader():
    """Test that all JSON rule files can be loaded."""
    print("=" * 60)
    print("Testing Rules Loader")
    print("=" * 60)
    
    visa_types = ["skilled_worker", "health_care_worker", "graduate", 
                  "global_talent", "student", "family"]
    
    all_passed = True
    for visa_type in visa_types:
        rules = rules_loader.get_all_rules(visa_type)
        metadata = rules_loader.get_metadata(visa_type)
        
        if rules:
            print(f"[PASS] {visa_type}: {len(rules)} rules loaded")
        else:
            print(f"[FAIL] {visa_type}: FAILED to load rules")
            all_passed = False
        
        if metadata:
            print(f"  - Visa Name: {metadata.get('visa_type', 'N/A')}")
        else:
            print(f"  - Metadata: Not available")
    
    return all_passed


def test_visa_recommendation():
    """Test the visa recommendation system with a sample profile."""
    print("\n" + "=" * 60)
    print("Testing Visa Recommendation System")
    print("=" * 60)
    
    # Create a sample profile for a skilled worker
    profile = ApplicantProfile(
        job_title="Software Engineer",
        salary_annual=55000,
        has_sponsor=True,
        country_of_origin="India",
        age=28,
        qualification="BSc Computer Science",
        english_proficiency="test_passed",
    )
    
    print(f"\nSample Profile:")
    print(f"  - Job: {profile.job_title}")
    print(f"  - Salary: GBP {profile.salary_annual:,}/year")
    print(f"  - Has Sponsor: {profile.has_sponsor}")
    print(f"  - Nationality: {profile.country_of_origin}")
    print(f"  - Age: {profile.age}")
    print(f"  - Education: {profile.qualification}")
    print(f"  - English: {profile.english_proficiency}")
    
    # Get recommendation
    recommendation = get_visa_recommendation(profile)
    
    print(f"\nVisa Recommendations:")
    print("-" * 40)
    
    all_options = recommendation.get("all_options", [])
    for option in all_options:
        if option.verdict == "eligible":
            status = "[ELIGIBLE]"
        elif option.verdict == "not_eligible":
            status = "[NOT ELIGIBLE]"
        else:
            status = "[INSUFFICIENT INFO]"
        print(f"{status} {option.visa_name}: {option.verdict.upper()}")
        print(f"   Score: {option.score}/100 | Priority: {option.priority}")
        if option.matched_criteria:
            print(f"   Matched: {', '.join(option.matched_criteria[:2])}")
        if option.missing_criteria:
            print(f"   Missing: {', '.join(option.missing_criteria[:2])}")
        print()
    
    # Check if Skilled Worker is eligible (should be for this profile)
    skilled_worker_eligible = any(
        opt.visa_type == "skilled_worker" and opt.verdict == "eligible"
        for opt in all_options
    )
    
    return skilled_worker_eligible


def test_rules_loader_api():
    """Test the rules loader API methods."""
    print("\n" + "=" * 60)
    print("Testing Rules Loader API")
    print("=" * 60)
    
    # Test get_rule
    rule = rules_loader.get_rule("skilled_worker", "sponsorship")
    if rule:
        print(f"[PASS] get_rule('skilled_worker', 'sponsorship'): {rule.get('rule_id')}")
    else:
        print("[FAIL] get_rule failed")
        return False
    
    # Test get_visa_config
    config = rules_loader.get_visa_config("family")
    if config:
        print(f"[PASS] get_visa_config('family'): Has {len(config.get('rules', {}))} rules")
    else:
        print("[FAIL] get_visa_config failed")
        return False
    
    # Test list_available_visa_types
    available = rules_loader.list_available_visa_types()
    print(f"[PASS] list_available_visa_types: {len(available)} visa types available")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ATLAS AI - RULES INTEGRATION TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Rules Loader
    results.append(("Rules Loader", test_rules_loader()))
    
    # Test 2: Rules Loader API
    results.append(("Rules Loader API", test_rules_loader_api()))
    
    # Test 3: Visa Recommendation
    results.append(("Visa Recommendation", test_visa_recommendation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())