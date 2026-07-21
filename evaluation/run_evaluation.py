"""
Atlas AI — Evaluation Suite
Generates automated evaluation reports for all metrics:
  1. Intent Classification Accuracy + Confusion Matrix
  2. NER F1 Score per entity type  
  3. Rule Engine Correctness (benchmark scenarios)
  4. Safety Score (hallucination detection)
  5. SUS Score template (manual input)

Run: python evaluation/run_evaluation.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from config import SYNTHETIC_DIR

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"


# ── 1. Intent Classification Evaluation ──────────────────────────────────────

def evaluate_intent_classification() -> dict:
    from sklearn.metrics import (
        accuracy_score, f1_score, classification_report, confusion_matrix
    )
    from src.nlp.intent_classifier import classify_intent
    from config import INTENT_LABELS

    print("\n[1/5] Evaluating Intent Classification...")

    # Load test set
    test_path = SYNTHETIC_DIR / "test.json"
    if not test_path.exists():
        print("  ⚠️  Test dataset not found. Run: python training/generate_dataset.py")
        return {}

    with open(test_path) as f:
        test_data = json.load(f)

    y_true = []
    y_pred = []
    low_conf_count = 0

    for item in test_data:
        true_label = item.get("intent", item.get("label", "general_query"))
        text = item.get("user_input", item.get("text", ""))
        if not text:
            continue

        result = classify_intent(text)
        pred_label = result["intent"]

        y_true.append(true_label)
        y_pred.append(pred_label)
        if result["low_confidence"]:
            low_conf_count += 1

    accuracy = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro", labels=INTENT_LABELS, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, average=None, labels=INTENT_LABELS, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=INTENT_LABELS).tolist()

    report = classification_report(
        y_true, y_pred, target_names=INTENT_LABELS, output_dict=True, zero_division=0
    )

    metrics = {
        "accuracy": round(accuracy, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_per_class": {INTENT_LABELS[i]: round(f1_per_class[i], 4) for i in range(len(INTENT_LABELS))},
        "confusion_matrix": cm,
        "classification_report": report,
        "total_samples": len(y_true),
        "low_confidence_rate": round(low_conf_count / max(len(y_true), 1), 4),
        "target_met": accuracy >= 0.95,
    }

    print(f"  Accuracy: {accuracy:.2%} {'✅' if accuracy >= 0.95 else '⚠️'} (target ≥ 95%)")
    print(f"  F1 (macro): {f1_macro:.4f}")
    print(f"  Per-class F1:")
    for intent, score in metrics["f1_per_class"].items():
        print(f"    {intent}: {score:.4f}")
    print(f"  Low-confidence rate: {metrics['low_confidence_rate']:.1%}")

    return metrics


# ── 2. NER F1 Evaluation ──────────────────────────────────────────────────────

def evaluate_ner() -> dict:
    from src.nlp.ner_extractor import extract_entities

    print("\n[2/5] Evaluating NER Extractor...")

    # Annotated test cases
    ner_test_cases = [
        ("I am a software engineer from India earning £50,000 a year",
         {"JOB_TITLE": "software engineer", "COUNTRY": "India", "SALARY": 50000}),
        ("Nurse from Philippines salary £35,000",
         {"JOB_TITLE": "nurse", "COUNTRY": "Philippines", "SALARY": 35000}),
        ("Civil engineer aged 28 from Nigeria earning £44,000",
         {"JOB_TITLE": "civil engineer", "AGE": 28, "COUNTRY": "Nigeria", "SALARY": 44000}),
        ("I am a 30 year old doctor from Pakistan earning £55,000",
         {"JOB_TITLE": "doctor", "AGE": 30, "COUNTRY": "Pakistan", "SALARY": 55000}),
        ("Applying for skilled worker visa, accountant from Australia",
         {"VISA_TYPE": "skilled_worker", "JOB_TITLE": "accountant", "COUNTRY": "Australia"}),
        ("I passed IELTS and I'm a physiotherapist earning £40,000",
         {"JOB_TITLE": "physiotherapist", "SALARY": 40000, "ENGLISH": "test_passed"}),
        ("Data scientist from China, salary £60,000",
         {"JOB_TITLE": "data scientist", "COUNTRY": "China", "SALARY": 60000}),
        ("I have a Certificate of Sponsorship as a solicitor",
         {"JOB_TITLE": "solicitor", "HAS_SPONSOR": True}),
        ("No sponsor yet, teacher from Kenya earning £38,700",
         {"JOB_TITLE": "teacher", "COUNTRY": "Kenya", "SALARY": 38700, "HAS_SPONSOR": False}),
        ("web developer UK job offer salary 41000",
         {"JOB_TITLE": "web developer", "SALARY": 41000}),
    ]

    entity_types = ["JOB_TITLE", "SALARY", "AGE", "COUNTRY", "VISA_TYPE"]
    true_positives = Counter()
    false_positives = Counter()
    false_negatives = Counter()

    for text, expected_entities in ner_test_cases:
        result = extract_entities(text)
        extracted = result["entities"]

        for etype in entity_types:
            expected = expected_entities.get(etype)
            predicted = extracted.get(etype)

            if expected is not None and predicted is not None:
                # Check if value roughly matches
                if etype == "SALARY":
                    match = abs(predicted["value"] - expected) < 500
                elif etype == "AGE":
                    match = predicted["value"] == expected
                elif etype == "JOB_TITLE":
                    match = expected.lower() in predicted["value"].lower() or \
                            predicted["value"].lower() in expected.lower()
                elif etype == "COUNTRY":
                    match = expected.lower() in predicted["value"].lower() or \
                            predicted["value"].lower() in expected.lower()
                else:
                    match = str(predicted["value"]).lower() == str(expected).lower()

                if match:
                    true_positives[etype] += 1
                else:
                    false_positives[etype] += 1
                    false_negatives[etype] += 1
            elif expected is not None and predicted is None:
                false_negatives[etype] += 1
            elif expected is None and predicted is not None:
                false_positives[etype] += 1

    f1_per_entity = {}
    for etype in entity_types:
        tp = true_positives[etype]
        fp = false_positives[etype]
        fn = false_negatives[etype]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        f1_per_entity[etype] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn,
        }

    all_f1 = [v["f1"] for v in f1_per_entity.values()]
    macro_f1 = sum(all_f1) / len(all_f1) if all_f1 else 0

    print(f"  Macro F1: {macro_f1:.4f} {'✅' if macro_f1 >= 0.90 else '⚠️'} (target ≥ 0.90)")
    print(f"  Per-entity F1:")
    for etype, scores in f1_per_entity.items():
        print(f"    {etype}: F1={scores['f1']:.4f} (P={scores['precision']:.4f}, R={scores['recall']:.4f})")

    return {
        "macro_f1": round(macro_f1, 4),
        "f1_per_entity": f1_per_entity,
        "total_test_cases": len(ner_test_cases),
        "target_met": macro_f1 >= 0.90,
    }


# ── 3. Rule Engine Correctness ────────────────────────────────────────────────

def evaluate_rule_engine() -> dict:
    from src.rule_engine.rules_base import ApplicantProfile, Verdict
    from src.rule_engine.skilled_worker import check_eligibility

    print("\n[3/5] Evaluating Rule Engine Correctness...")

    benchmark_scenarios = [
        # (description, profile_kwargs, expected_verdict)
        ("Eligible: SW standard case", 
         {"job_title": "Software Engineer", "salary_annual": 50000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
         "eligible"),
        ("Not eligible: salary below threshold",
         {"job_title": "Software Engineer", "salary_annual": 20000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
         "not_eligible"),
        ("Not eligible: no sponsor",
         {"job_title": "Civil Engineer", "salary_annual": 45000, "has_sponsor": False,
          "country_of_origin": "Nigeria", "english_proficiency": "test_passed", "age": 25},
         "not_eligible"),
        ("Eligible: doctor NHS salary",
         {"job_title": "Doctor", "salary_annual": 52000, "has_sponsor": True,
          "country_of_origin": "Pakistan", "english_proficiency": "test_passed", "age": 35},
         "eligible"),
        ("Not eligible: nurse salary below general threshold",
         {"job_title": "Nurse", "salary_annual": 28000, "has_sponsor": True,
          "country_of_origin": "Philippines", "english_proficiency": "test_passed", "age": 29},
         "not_eligible"),
        ("Eligible: Australian (English exempt)",
         {"job_title": "Accountant", "salary_annual": 44000, "has_sponsor": True,
          "country_of_origin": "Australia", "age": 32},
         "eligible"),
        ("Insufficient: missing salary",
         {"job_title": "Software Engineer", "has_sponsor": True, "country_of_origin": "India"},
         "insufficient_info"),
        ("Insufficient: missing job",
         {"salary_annual": 50000, "has_sponsor": True, "country_of_origin": "India"},
         "insufficient_info"),
        ("Not eligible: no English evidence",
         {"job_title": "Management Consultant", "salary_annual": 48000, "has_sponsor": True,
          "country_of_origin": "China", "english_proficiency": "none", "age": 28},
         "not_eligible"),
        ("Eligible: new entrant lower salary",
         {"job_title": "Civil Engineer", "salary_annual": 32000, "has_sponsor": True,
          "country_of_origin": "Nigeria", "english_proficiency": "test_passed",
          "age": 23, "is_new_entrant": True},
         "eligible"),
        ("Eligible: pharmacist",
         {"job_title": "Pharmacist", "salary_annual": 50000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
         "eligible"),
        ("Not eligible: age < 18",
         {"job_title": "Software Engineer", "salary_annual": 50000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 17},
         "not_eligible"),
        ("Eligible: salary exactly at general threshold",
         {"job_title": "Teacher", "salary_annual": 38700, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
         "eligible"),
        ("Not eligible: salary 1 below threshold",
         {"job_title": "Teacher", "salary_annual": 38699, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 30},
         "not_eligible"),
        ("Eligible: USA citizen (English exempt)",
         {"job_title": "Software Engineer", "salary_annual": 55000, "has_sponsor": True,
          "country_of_origin": "United States of America", "age": 28},
         "eligible"),
        ("Not eligible: salary below going rate for role",
         {"job_title": "IT Specialist Manager", "salary_annual": 40000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 35},
         "not_eligible"),  # Going rate 55100, threshold 38700, need max = 55100
        ("Eligible: IT specialist manager above going rate",
         {"job_title": "IT Specialist Manager", "salary_annual": 60000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 35},
         "eligible"),
        ("Not eligible: no info at all",
         {},
         "insufficient_info"),
        ("Eligible: physiotherapist above threshold",
         {"job_title": "Physiotherapist", "salary_annual": 40000, "has_sponsor": True,
          "country_of_origin": "Nigeria", "english_proficiency": "test_passed", "age": 30},
         "eligible"),
        ("Eligible: social worker",
         {"job_title": "Social Worker", "salary_annual": 40000, "has_sponsor": True,
          "country_of_origin": "India", "english_proficiency": "test_passed", "age": 32},
         "eligible"),
    ]

    passed = 0
    failed = 0
    failures = []

    for desc, kwargs, expected in benchmark_scenarios:
        profile = ApplicantProfile(**kwargs)
        result = check_eligibility(profile)
        verdict = result.verdict.value

        if verdict == expected:
            passed += 1
        else:
            failed += 1
            failures.append({
                "scenario": desc,
                "expected": expected,
                "got": verdict,
                "summary": result.summary,
            })

    total = len(benchmark_scenarios)
    correctness = passed / total

    print(f"  Passed: {passed}/{total} ({correctness:.1%}) {'✅' if correctness >= 0.98 else '⚠️'} (target ≥ 98%)")
    if failures:
        print(f"  Failed scenarios:")
        for f in failures:
            print(f"    ✗ {f['scenario']}: expected {f['expected']}, got {f['got']}")

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "correctness": round(correctness, 4),
        "failures": failures,
        "target_met": correctness >= 0.98,
    }


# ── 4. Safety Evaluation ──────────────────────────────────────────────────────

def evaluate_safety() -> dict:
    from src.gpt.explainer import generate_explanation, _detect_hallucination
    from src.rule_engine.rules_base import EligibilityResult, RuleResult, Verdict

    print("\n[4/5] Evaluating Safety (Anti-Hallucination)...")

    test_cases = [
        (Verdict.ELIGIBLE, "Eligible applicant explanation"),
        (Verdict.NOT_ELIGIBLE, "Not eligible — should not flip to eligible"),
        (Verdict.NOT_ELIGIBLE, "Not eligible — low salary"),
        (Verdict.INSUFFICIENT_INFO, "Missing information case"),
    ]

    hallucination_count = 0
    total = len(test_cases)
    verdict_flips = 0

    for verdict, desc in test_cases:
        mock_result = EligibilityResult(
            verdict=verdict,
            visa_type="skilled_worker",
            summary=f"Test: {desc}",
        )

        explanation = generate_explanation(
            result=mock_result,
            original_query=f"Am I eligible? ({desc})",
            retrieved_context="",
            profile_summary="",
        )

        # Check 1: Verdict must be preserved
        if explanation["verdict"] != verdict.value:
            verdict_flips += 1
            print(f"  ⚠️ Verdict flip detected: {verdict.value} → {explanation['verdict']}")

        # Check 2: No hallucination patterns in output
        if explanation["hallucination_detected"]:
            hallucination_count += 1
            print(f"  ⚠️ Hallucination detected in: {desc}")
            for pattern in explanation["hallucination_patterns"]:
                print(f"     Pattern: {pattern}")

        # Check 3: Disclaimer present
        exp_text = explanation["explanation"]
        if "informational" not in exp_text.lower() and "legal advice" not in exp_text.lower():
            print(f"  ⚠️ Disclaimer missing: {desc}")

    safety_score = 1.0 - (hallucination_count / total)
    verdict_preservation_rate = 1.0 - (verdict_flips / total)

    print(f"  Safety Score: {safety_score:.2%} {'✅' if safety_score == 1.0 else '⚠️'} (target: 100%)")
    print(f"  Verdict Preservation: {verdict_preservation_rate:.2%} {'✅' if verdict_preservation_rate == 1.0 else '⚠️'}")

    return {
        "total_tests": total,
        "hallucinations_detected": hallucination_count,
        "verdict_flips": verdict_flips,
        "safety_score": round(safety_score, 4),
        "verdict_preservation_rate": round(verdict_preservation_rate, 4),
        "target_met": safety_score == 1.0 and verdict_preservation_rate == 1.0,
    }


# ── 5. SUS Score Template ─────────────────────────────────────────────────────

def sus_score_template() -> dict:
    """
    System Usability Scale (SUS) template.
    This requires manual input from 20-30 users.
    Returns the empty template structure.
    """
    print("\n[5/5] SUS Score (Manual Collection Required)")
    print("  ℹ️  The SUS questionnaire should be administered to 20-30 users.")
    print("  ℹ️  Target: SUS score ≥ 75 (Good usability).")

    sus_questions = [
        "I think that I would like to use this system frequently.",
        "I found the system unnecessarily complex.",
        "I thought the system was easy to use.",
        "I think that I would need the support of a technical person to use this system.",
        "I found the various functions in this system were well integrated.",
        "I thought there was too much inconsistency in this system.",
        "I would imagine that most people would learn to use this system very quickly.",
        "I found the system very cumbersome to use.",
        "I felt very confident using the system.",
        "I needed to learn a lot of things before I could get going with this system.",
    ]

    template = {
        "instructions": (
            "Rate each statement 1-5: "
            "1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree"
        ),
        "questions": [{
            "id": i + 1,
            "text": q,
            "scoring": "positive" if (i % 2 == 0) else "negative",
        } for i, q in enumerate(sus_questions)],
        "scoring_formula": (
            "SUS = 2.5 * sum(("
            "  (odd_question_score - 1) + (5 - even_question_score)"
            "))"
        ),
        "example_scores": {"poor": "< 51", "ok": "51-68", "good": "68-80", "excellent": "> 80"},
        "user_responses": [],
        "computed_sus_score": None,
        "target": 75,
        "status": "PENDING — requires manual data collection from 20-30 users",
    }
    return template


# ── Report Generator ──────────────────────────────────────────────────────────

def generate_report(all_metrics: dict) -> str:
    report = f"""# Atlas AI — Evaluation Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---

## Summary

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| Intent Classification Accuracy | {all_metrics.get('intent', {}).get('accuracy', 'N/A')} | ≥ 95% | {'✅ MET' if all_metrics.get('intent', {}).get('target_met') else '⚠️ PENDING'} |
| NER F1 Score (macro) | {all_metrics.get('ner', {}).get('macro_f1', 'N/A')} | ≥ 0.90 | {'✅ MET' if all_metrics.get('ner', {}).get('target_met') else '⚠️ PENDING'} |
| Rule Engine Correctness | {all_metrics.get('rules', {}).get('correctness', 'N/A')} | ≥ 98% | {'✅ MET' if all_metrics.get('rules', {}).get('target_met') else '⚠️ PENDING'} |
| Safety Score | {all_metrics.get('safety', {}).get('safety_score', 'N/A')} | 100% | {'✅ MET' if all_metrics.get('safety', {}).get('target_met') else '⚠️ PENDING'} |
| SUS Score | Pending | ≥ 75 | ⏳ Requires user study |

---

## 1. Intent Classification

{json.dumps(all_metrics.get('intent', {}), indent=2)}

---

## 2. NER F1 Scores

{json.dumps(all_metrics.get('ner', {}), indent=2)}

---

## 3. Rule Engine Correctness

{json.dumps(all_metrics.get('rules', {}), indent=2)}

---

## 4. Safety Evaluation

{json.dumps(all_metrics.get('safety', {}), indent=2)}

---

## 5. SUS Score (Pending)

{json.dumps(all_metrics.get('sus', {}), indent=2)}

---

*Atlas AI — UK Immigration Guidance Assistant | MSc Research Project*
"""
    return report


def run_all():
    print("=" * 70)
    print("Atlas AI — Full Evaluation Suite")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_metrics = {}

    # Run each evaluation
    all_metrics["intent"] = evaluate_intent_classification()
    all_metrics["ner"] = evaluate_ner()
    all_metrics["rules"] = evaluate_rule_engine()
    all_metrics["safety"] = evaluate_safety()
    all_metrics["sus"] = sus_score_template()

    # Save raw metrics
    metrics_path = OUTPUT_DIR / f"metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)

    # Generate and save report
    report = generate_report(all_metrics)
    report_path = OUTPUT_DIR / f"evaluation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w") as f:
        f.write(report)

    # Summary
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"Report saved to: {report_path}")
    print(f"Metrics saved to: {metrics_path}")

    targets = {
        "Intent Accuracy ≥ 95%": all_metrics.get("intent", {}).get("target_met", False),
        "NER F1 ≥ 0.90": all_metrics.get("ner", {}).get("target_met", False),
        "Rule Correctness ≥ 98%": all_metrics.get("rules", {}).get("target_met", False),
        "Safety Score 100%": all_metrics.get("safety", {}).get("target_met", False),
    }

    all_met = all(targets.values())
    for label, met in targets.items():
        print(f"  {'✅' if met else '⚠️'} {label}")

    print(f"\n{'✅ All automated targets met!' if all_met else '⚠️ Some targets require model training to meet.'}")
    return all_metrics


if __name__ == "__main__":
    run_all()
