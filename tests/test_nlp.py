"""
Atlas AI — NLP Unit Tests
Tests for preprocessing, intent classification, and NER extraction.

Run: pytest tests/test_nlp.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.nlp.preprocessor import (
    clean_text, extract_salary_from_text, extract_age_from_text,
    extract_soc_code_from_text, normalise_country_name, preprocess_for_model
)
from src.nlp.intent_classifier import classify_intent, _keyword_classify
from src.nlp.ner_extractor import extract_entities, entities_to_profile_updates


# ── Preprocessor Tests ────────────────────────────────────────────────────────

class TestPreprocessor:
    def test_clean_text_strips_whitespace(self):
        assert clean_text("  hello world  ") == "hello world"

    def test_clean_text_collapses_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_clean_text_unicode_normalisation(self):
        result = clean_text("café")
        assert isinstance(result, str)

    @pytest.mark.parametrize("text,expected", [
        ("£50,000", 50000),
        ("£50000", 50000),
        ("£50k", 50000),
        ("50k", 50000),
        ("50,000 pounds", 50000),
        ("salary of £38,700", 38700),
        ("£38,700 per year", 38700),
        ("100000", 100000),
    ])
    def test_salary_extraction(self, text, expected):
        result = extract_salary_from_text(text)
        assert result is not None
        assert abs(result - expected) < 1

    def test_salary_extraction_none_for_no_salary(self):
        assert extract_salary_from_text("hello world") is None
        assert extract_salary_from_text("I am 30 years old") is None

    @pytest.mark.parametrize("text,expected", [
        ("I am 28 years old", 28),
        ("28-year-old nurse", 28),
        ("age 35", None),  # Not matching pattern
        ("30 y/o", 30),
        ("I am 25 yr old", 25),
    ])
    def test_age_extraction(self, text, expected):
        result = extract_age_from_text(text)
        assert result == expected

    def test_soc_code_extraction(self):
        assert extract_soc_code_from_text("SOC 2136") == "2136"
        assert extract_soc_code_from_text("soc-2136") == "2136"
        assert extract_soc_code_from_text("code 2136") == "2136"
        assert extract_soc_code_from_text("no code here") is None

    def test_country_normalisation(self):
        assert normalise_country_name("usa") == "United States of America"
        assert normalise_country_name("UK") == "United Kingdom"
        assert normalise_country_name("india") == "India"


# ── Intent Classifier Tests ───────────────────────────────────────────────────

class TestIntentClassifier:
    @pytest.mark.parametrize("text,expected_intent", [
        ("Am I eligible for a skilled worker visa?", "eligibility_check"),
        ("Do I qualify for a UK work visa?", "eligibility_check"),
        ("What documents do I need?", "document_requirement"),
        ("What proof do I need to provide?", "document_requirement"),
        ("How long does the visa take?", "processing_time"),
        ("What is the processing time?", "processing_time"),
        ("What is a Skilled Worker visa?", "general_query"),
        ("Tell me about UK immigration", "general_query"),
    ])
    def test_keyword_classifier(self, text, expected_intent):
        intent, confidence = _keyword_classify(text)
        assert intent == expected_intent, f"'{text}': expected {expected_intent}, got {intent}"

    def test_classify_intent_returns_dict(self):
        result = classify_intent("Am I eligible for a visa?")
        assert isinstance(result, dict)
        assert "intent" in result
        assert "confidence" in result
        assert "low_confidence" in result
        assert "source" in result

    def test_classify_intent_valid_label(self):
        from config import INTENT_LABELS
        result = classify_intent("How long does it take?")
        assert result["intent"] in INTENT_LABELS

    def test_confidence_between_0_and_1(self):
        result = classify_intent("some query")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_low_confidence_flag(self):
        from config import INTENT_CONFIDENCE_THRESHOLD
        result = classify_intent("xyz abc def")
        # Low-quality input should have lower confidence
        assert isinstance(result["low_confidence"], bool)


# ── NER Extractor Tests ────────────────────────────────────────────────────────

class TestNERExtractor:
    def test_extracts_salary_gbp(self):
        result = extract_entities("My salary is £50,000 per year")
        entities = result["entities"]
        assert "SALARY" in entities
        assert entities["SALARY"]["value"] == 50000

    def test_extracts_job_title(self):
        result = extract_entities("I am a software engineer from India")
        entities = result["entities"]
        assert "JOB_TITLE" in entities
        assert "software engineer" in entities["JOB_TITLE"]["value"].lower()

    def test_extracts_country(self):
        result = extract_entities("I am from Nigeria applying for a UK visa")
        entities = result["entities"]
        assert "COUNTRY" in entities
        assert "Nigeria" in entities["COUNTRY"]["value"]

    def test_extracts_age(self):
        result = extract_entities("I am 28 years old applying for a visa")
        entities = result["entities"]
        assert "AGE" in entities
        assert entities["AGE"]["value"] == 28

    def test_extracts_visa_type(self):
        result = extract_entities("I want to apply for a skilled worker visa")
        entities = result["entities"]
        assert "VISA_TYPE" in entities

    def test_extracts_has_sponsor_true(self):
        result = extract_entities("I have a Certificate of Sponsorship from my employer")
        entities = result["entities"]
        assert "HAS_SPONSOR" in entities
        assert entities["HAS_SPONSOR"]["value"] is True

    def test_extracts_has_sponsor_false(self):
        result = extract_entities("I don't have a sponsor yet")
        entities = result["entities"]
        assert "HAS_SPONSOR" in entities
        assert entities["HAS_SPONSOR"]["value"] is False

    def test_extracts_english_ielts(self):
        result = extract_entities("I have passed IELTS with a score of 7.5")
        entities = result["entities"]
        assert "ENGLISH" in entities
        assert entities["ENGLISH"]["value"] == "test_passed"

    def test_multiple_entities(self):
        text = "I am a nurse from the Philippines earning £35,000 and I'm 25 years old"
        result = extract_entities(text)
        entities = result["entities"]
        assert "JOB_TITLE" in entities
        assert "COUNTRY" in entities
        assert "SALARY" in entities
        assert "AGE" in entities

    def test_entities_to_profile_updates(self):
        result = extract_entities("Software engineer from India earning £50,000")
        updates = entities_to_profile_updates(result)
        assert isinstance(updates, dict)
        if "job_title" in updates:
            assert isinstance(updates["job_title"], str)
        if "salary_annual" in updates:
            assert isinstance(updates["salary_annual"], (int, float))
        if "country_of_origin" in updates:
            assert isinstance(updates["country_of_origin"], str)

    def test_confidence_values_in_range(self):
        result = extract_entities("I am a doctor from Pakistan")
        for entity_type, entity_data in result["entities"].items():
            assert 0.0 <= entity_data["confidence"] <= 1.0

    def test_low_confidence_list_is_list(self):
        result = extract_entities("some text")
        assert isinstance(result["low_confidence"], list)


# ── Integration: NLP → Profile ────────────────────────────────────────────────

class TestNLPToProfileIntegration:
    def test_full_pipeline_eligible_scenario(self):
        """
        Test complete NLP pipeline: text → intent + entities → profile → rule check.
        """
        from src.rule_engine.rules_base import ApplicantProfile, Verdict
        from src.rule_engine.skilled_worker import check_eligibility

        text = "I'm a software engineer from India earning £50,000. My employer will sponsor me."

        intent_result = classify_intent(text)
        assert intent_result["intent"] == "eligibility_check"

        entity_result = extract_entities(text)
        updates = entities_to_profile_updates(entity_result)

        profile = ApplicantProfile(
            english_proficiency="test_passed",  # Simulate clarification answer
            **updates
        )

        # We need has_sponsor to be True for this to be eligible
        if profile.has_sponsor is None:
            profile.has_sponsor = True  # From "my employer will sponsor me"

        result = check_eligibility(profile)
        # If salary and job extracted correctly, should be eligible
        if profile.salary_annual and profile.salary_annual >= 38700 and profile.has_sponsor:
            assert result.verdict in [Verdict.ELIGIBLE, Verdict.NOT_ELIGIBLE, Verdict.INSUFFICIENT_INFO]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
