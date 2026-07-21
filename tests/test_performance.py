"""
Atlas AI — Performance Benchmark Suite
Tests response times and query coverage for the optimized system.
"""

import time
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.nlp.intent_classifier_v2 import classify_intent_enhanced
from src.responses.knowledge_base import get_response, get_fallback_response
from src.core.cache_manager import get_query_cache, generate_cache_key
from src.dialogue.manager_v2 import process_message, reset_session


# ── Test Queries ─────────────────────────────────────────────────────────────

TEST_QUERIES = [
    # Eligibility queries
    ("I'm a software engineer from India earning £50,000. Can I get a Skilled Worker visa?", "eligibility_check"),
    ("Do I qualify for a skilled worker visa as a nurse?", "eligibility_check"),
    ("What are the requirements for a Skilled Worker visa?", "eligibility_check"),
    
    # Processing time queries
    ("How long does it take to get a decision?", "processing_time"),
    ("What is the processing time for Skilled Worker visa?", "processing_time"),
    ("Can I get a priority decision?", "processing_time"),
    
    # Fees and costs queries
    ("How much does the visa cost?", "fees_and_costs"),
    ("What are the application fees?", "fees_and_costs"),
    ("What is the Immigration Health Surcharge?", "fees_and_costs"),
    
    # Document queries
    ("What documents do I need?", "document_requirement"),
    ("Do I need a TB test?", "document_requirement"),
    ("What proof of English do I need?", "document_requirement"),
    
    # Dependants queries
    ("Can I bring my family?", "dependants_query"),
    ("Can my spouse work in the UK?", "dependants_query"),
    ("What about my children?", "dependants_query"),
    
    # Extension/switching queries
    ("Can I extend my visa?", "extension_switching"),
    ("Can I switch from a Student visa?", "extension_switching"),
    ("How do I change my visa?", "extension_switching"),
    
    # Settlement queries
    ("How do I apply for ILR?", "settlement_ilr"),
    ("When can I apply for settlement?", "settlement_ilr"),
    ("What are the requirements for British citizenship?", "settlement_ilr"),
    
    # Health and Care Worker queries
    ("What is the Health and Care Worker visa?", "health_care_worker"),
    ("I'm a nurse, can I get a cheaper visa?", "health_care_worker"),
    ("Do doctors pay lower fees?", "health_care_worker"),
    
    # Shortage occupation queries
    ("Is nursing on the shortage list?", "shortage_occupation"),
    ("What is the Immigration Salary List?", "shortage_occupation"),
    ("Do I get a lower salary threshold?", "shortage_occupation"),
    
    # English language queries
    ("What is the English requirement?", "english_language"),
    ("Do I need IELTS?", "english_language"),
    ("Am I exempt from English?", "english_language"),
    
    # Salary threshold queries
    ("What is the minimum salary?", "salary_threshold"),
    ("What is the going rate for software engineers?", "salary_threshold"),
    ("I'm under 26, do I get a lower salary?", "salary_threshold"),
    
    # General queries
    ("Hello", "general_query"),
    ("Thank you", "general_query"),
    ("Goodbye", "general_query"),
    ("What is Skilled Worker visa?", "general_query"),
    
    # Fallback queries (out of scope)
    ("What is the weather in London?", "fallback"),
    ("How do I apply for asylum?", "fallback"),
    ("Tell me a joke", "fallback"),
]


def test_intent_classification_speed(iterations: int = 100):
    """Test intent classification speed."""
    print("\n" + "="*60)
    print("INTENT CLASSIFICATION SPEED TEST")
    print("="*60)
    
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        classify_intent_enhanced("I'm a software engineer from India earning £50,000")
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\nResults ({iterations} iterations):")
    print(f"  Average: {avg_time:.2f} ms")
    print(f"  Min: {min_time:.2f} ms")
    print(f"  Max: {max_time:.2f} ms")
    status = "PASS" if avg_time < 50 else "FAIL"
    print(f"  Status: [{status}] (< 50ms target)")
    
    return avg_time < 50


def test_intent_classification_accuracy():
    """Test intent classification accuracy."""
    print("\n" + "="*60)
    print("INTENT CLASSIFICATION ACCURACY TEST")
    print("="*60)
    
    correct = 0
    total = len(TEST_QUERIES)
    
    for query, expected_intent in TEST_QUERIES:
        result = classify_intent_enhanced(query)
        actual_intent = result["intent"]
        
        # For fallback queries, any non-specific intent is acceptable
        if expected_intent == "fallback":
            if actual_intent == "general_query":
                correct += 1
        elif actual_intent == expected_intent:
            correct += 1
    
    accuracy = (correct / total) * 100
    
    print(f"\nResults ({total} queries):")
    print(f"  Correct: {correct}/{total}")
    print(f"  Accuracy: {accuracy:.1f}%")
    status = "PASS" if accuracy >= 90 else "FAIL"
    print(f"  Status: [{status}] (>= 90% target)")
    
    return accuracy >= 90


def test_knowledge_base_coverage():
    """Test knowledge base response generation."""
    print("\n" + "="*60)
    print("KNOWLEDGE BASE COVERAGE TEST")
    print("="*60)
    
    intents = [
        "processing_time", "fees_and_costs", "document_requirement",
        "dependants_query", "extension_switching", "settlement_ilr",
        "health_care_worker", "shortage_occupation", "english_language",
        "salary_threshold", "general_query",
    ]
    
    all_valid = True
    for intent in intents:
        response = get_response(intent)
        has_response = bool(response.get("response"))
        has_followup = bool(response.get("follow_up"))
        valid = has_response and has_followup
        
        status = "[OK]" if valid else "[FAIL]"
        resp_status = "YES" if has_response else "NO"
        follow_status = "YES" if has_followup else "NO"
        print(f"  {status} {intent}: response={resp_status}, follow_up={follow_status}")
        
        if not valid:
            all_valid = False
    
    # Test fallback
    fallback = get_fallback_response()
    fallback_valid = bool(fallback.get("response"))
    fb_status = "[OK]" if fallback_valid else "[FAIL]"
    fb_resp = "YES" if fallback_valid else "NO"
    print(f"  {fb_status} fallback: response={fb_resp}")
    
    if not fallback_valid:
        all_valid = False
    
    status = "PASS" if all_valid else "FAIL"
    print(f"\n  Status: [{status}]")
    return all_valid


def test_caching_performance():
    """Test caching system performance."""
    print("\n" + "="*60)
    print("CACHING PERFORMANCE TEST")
    print("="*60)
    
    cache = get_query_cache()
    cache.clear()
    
    # Test write performance
    write_times = []
    for i in range(1000):
        start = time.perf_counter()
        cache.set(f"key_{i}", f"value_{i}")
        end = time.perf_counter()
        write_times.append((end - start) * 1000)
    
    avg_write = sum(write_times) / len(write_times)
    
    # Test read performance
    read_times = []
    for i in range(1000):
        start = time.perf_counter()
        cache.get(f"key_{i}")
        end = time.perf_counter()
        read_times.append((end - start) * 1000)
    
    avg_read = sum(read_times) / len(read_times)
    
    print(f"\nResults (1000 operations):")
    print(f"  Average Write: {avg_write:.4f} ms")
    print(f"  Average Read: {avg_read:.4f} ms")
    print(f"  Cache Stats: {cache.stats()}")
    status = "PASS" if avg_read < 1 else "FAIL"
    print(f"  Status: [{status}] (< 1ms read target)")
    
    return avg_read < 1


def test_end_to_end_response_time():
    """Test end-to-end response time for various query types."""
    print("\n" + "="*60)
    print("END-TO-END RESPONSE TIME TEST")
    print("="*60)
    
    test_session_id = "perf_test_session"
    reset_session(test_session_id)
    
    test_cases = [
        ("Hello", "Greeting"),
        ("How long does processing take?", "Processing Time"),
        ("What are the fees?", "Fees Query"),
        ("Can I bring my family?", "Dependants Query"),
        ("I'm a software engineer from India earning £50,000 with a sponsor", "Eligibility Check"),
    ]
    
    results = []
    for query, description in test_cases:
        start = time.perf_counter()
        result = process_message(test_session_id, query)
        end = time.perf_counter()
        
        response_time = (end - start) * 1000
        results.append((description, response_time))
        
        if response_time < 1000:
            status = "[OK]"
        elif response_time < 3000:
            status = "[SLOW]"
        else:
            status = "[FAIL]"
        print(f"  {status} {description}: {response_time:.0f} ms")
    
    avg_time = sum(r[1] for r in results) / len(results)
    max_time = max(r[1] for r in results)
    
    print(f"\nSummary:")
    print(f"  Average Response Time: {avg_time:.0f} ms")
    print(f"  Max Response Time: {max_time:.0f} ms")
    status = "PASS" if avg_time < 2000 else "FAIL"
    print(f"  Status: [{status}] (< 2000ms target)")
    
    return avg_time < 2000


def run_all_tests():
    """Run all performance tests."""
    print("\n" + "="*70)
    print("  ATLAS AI — PERFORMANCE BENCHMARK SUITE")
    print("="*70)
    
    results = {
        "Intent Classification Speed": test_intent_classification_speed(),
        "Intent Classification Accuracy": test_intent_classification_accuracy(),
        "Knowledge Base Coverage": test_knowledge_base_coverage(),
        "Caching Performance": test_caching_performance(),
        "End-to-End Response Time": test_end_to_end_response_time(),
    }
    
    print("\n" + "="*70)
    print("  FINAL RESULTS")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    overall = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    print(f"  OVERALL: {overall}")
    print("="*70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)