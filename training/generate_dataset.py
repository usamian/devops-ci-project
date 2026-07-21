"""
Atlas AI — Synthetic Conversational Dataset Generator
Generates 2,000+ training examples for intent classification and NER fine-tuning.
Structure: {user_input, intent, entities, expected_rule_outcome}

Run: python training/generate_dataset.py
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SYNTHETIC_DIR

random.seed(42)

# ── Template banks ────────────────────────────────────────────────────────────

JOBS = [
    ("software engineer", "2136", 49400),
    ("data scientist", "2425", 48000),
    ("nurse", "2225", 29000),
    ("doctor", "2211", 49923),
    ("civil engineer", "2121", 43600),
    ("mechanical engineer", "2122", 43600),
    ("pharmacist", "2213", 48900),
    ("teacher", "2314", 38700),
    ("solicitor", "2411", 48700),
    ("accountant", "2421", 42500),
    ("physiotherapist", "2221", 38700),
    ("architect", "2426", 42500),
    ("psychologist", "2212", 43900),
    ("web developer", "2137", 40700),
    ("it project manager", "2134", 52100),
    ("business analyst", "2422", 46600),
    ("social worker", "2442", 38700),
    ("paramedic", "2231", 29000),
    ("financial analyst", "3539", 44800),
    ("management consultant", "2422", 46600),
    ("electrical engineer", "2123", 44100),
    ("electronics engineer", "2124", 44100),
    ("biologist", "2112", 38700),
    ("chemical scientist", "2111", 38700),
    ("lab technician", "3111", 28500),
    ("speech therapist", "2223", 38700),
    ("occupational therapist", "2222", 38700),
    ("radiographer", "2217", 38700),
    ("it specialist manager", "2133", 55100),
    ("university lecturer", "2311", 38700),
]

SALARIES_LOW = [20000, 22000, 24000, 25000, 26000, 27000, 28000]
SALARIES_BORDERLINE = [30000, 32000, 35000, 38000, 38700, 39000, 40000]
SALARIES_HIGH = [45000, 50000, 55000, 60000, 70000, 80000, 100000]

COUNTRIES_EXEMPT = ["Australia", "USA", "Canada", "New Zealand", "Jamaica", "Ireland"]
COUNTRIES_NON_EXEMPT = ["India", "Pakistan", "Nigeria", "China", "Philippines",
                        "Bangladesh", "Sri Lanka", "Kenya", "Ghana", "Brazil",
                        "Colombia", "Ukraine", "Romania", "Turkey", "Iran"]
AGES = list(range(22, 55))
AGES_NEW_ENTRANT = list(range(18, 26))


# ── Intent: eligibility_check templates ──────────────────────────────────────
def gen_eligibility_check(i: int) -> dict:
    job, soc, going_rate = random.choice(JOBS)
    salary = random.choice(SALARIES_HIGH + SALARIES_BORDERLINE)
    country = random.choice(COUNTRIES_NON_EXEMPT + COUNTRIES_EXEMPT)
    age = random.choice(AGES)
    has_sponsor = random.choice([True, True, False])
    english = "test_passed" if country in COUNTRIES_NON_EXEMPT else "native"

    templates = [
        f"I am a {job} from {country} earning £{salary:,} a year. My employer will sponsor me. Am I eligible?",
        f"Can I apply for a skilled worker visa? I work as a {job}, salary £{salary:,}, based in {country}.",
        f"I have a job offer as a {job} in the UK paying £{salary:,}/year. Do I qualify for a skilled worker visa?",
        f"I'm {age} years old, a {job} from {country} with a salary of £{salary:,}. Will I get a skilled worker visa?",
        f"My employer is sponsoring me for a {job} role at £{salary:,} per annum. I'm from {country}. Am I eligible?",
        f"Skilled worker visa eligibility check: {job}, £{salary:,}/year, {country} national, {'has CoS' if has_sponsor else 'no CoS yet'}.",
        f"Do I meet the requirements for a skilled worker visa as a {job} earning £{salary:,}?",
        f"I got a job offer as {job} at £{salary:,} annual salary in London. Can I get a visa?",
        f"Checking if I qualify: {job} role, salary £{salary:,}, I'm from {country} and {age} years old.",
        f"Can a {job} from {country} earning £{salary:,} get a UK Skilled Worker Visa?",
    ]

    salary_ok = salary >= max(38700, going_rate)
    expected_outcome = "eligible" if (salary_ok and has_sponsor) else "not_eligible"

    return {
        "user_input": random.choice(templates),
        "intent": "eligibility_check",
        "entities": {
            "JOB_TITLE": job,
            "SOC_CODE": soc,
            "SALARY": salary,
            "COUNTRY": country,
            "AGE": age,
            "HAS_SPONSOR": has_sponsor,
            "ENGLISH": english,
        },
        "expected_rule_outcome": expected_outcome,
    }


# ── Intent: document_requirement templates ────────────────────────────────────
def gen_document_requirement(i: int) -> dict:
    templates = [
        "What documents do I need for a Skilled Worker visa?",
        "What paperwork is required for a UK work visa?",
        "Can you list the documents needed to apply for a skilled worker visa?",
        "I need to know what evidence to submit for my visa application.",
        "What proof do I need to provide for a Skilled Worker visa?",
        "Do I need an IELTS certificate for the visa?",
        "Is a TB test required for the skilled worker visa?",
        "What bank statements do I need for a UK work visa?",
        "Do I need to provide a degree certificate for the skilled worker visa?",
        "What is a Certificate of Sponsorship and how do I get one?",
        "My employer said I need a CoS — what is that?",
        "Does the skilled worker visa require a police clearance certificate?",
        "What English language tests are accepted for a Skilled Worker visa?",
        "Can I use my IELTS score of 6.5 for the Skilled Worker visa?",
        "I have a UK degree. Do I still need to take an English test?",
        "What financial documents do I need to show for a Skilled Worker visa?",
        "Is proof of salary needed when applying?",
        "How do I prove my qualifications for a Skilled Worker visa?",
        "What does 'certified maintenance' on the CoS mean?",
        "Do I need £1,270 in my bank account?",
    ]
    return {
        "user_input": random.choice(templates),
        "intent": "document_requirement",
        "entities": {},
        "expected_rule_outcome": None,
    }


# ── Intent: processing_time templates ────────────────────────────────────────
def gen_processing_time(i: int) -> dict:
    templates = [
        "How long does a skilled worker visa take?",
        "What is the processing time for a UK work visa?",
        "How many weeks does it take to get a decision on my visa?",
        "I applied for a skilled worker visa — when will I get a decision?",
        "Is there a way to speed up my visa application?",
        "What is priority service for UK visas?",
        "How long does it take to process a skilled worker visa from India?",
        "Can I get my visa in 5 days?",
        "What is the super priority service and how much does it cost?",
        "I'm applying from Nigeria — how long will the visa take?",
        "How long does in-country switching to a Skilled Worker visa take?",
        "Is the 3-week processing time guaranteed?",
        "What happens if my visa is taking longer than expected?",
        "When should I apply for my skilled worker visa before my start date?",
        "Can I travel to the UK before my visa decision?",
        "How soon can I start working after getting my skilled worker visa?",
        "Does the processing time vary by country?",
        "How long is the vignette valid for after visa approval?",
        "Processing time estimate for skilled worker visa applied from Pakistan?",
        "I need my visa urgently — what options do I have?",
    ]
    return {
        "user_input": random.choice(templates),
        "intent": "processing_time",
        "entities": {},
        "expected_rule_outcome": None,
    }


# ── Intent: general_query templates ──────────────────────────────────────────
def gen_general_query(i: int) -> dict:
    templates = [
        "What is a Skilled Worker visa?",
        "Tell me about UK immigration",
        "What visas are available for working in the UK?",
        "Is there a visa for nurses to work in the UK?",
        "What is the difference between a skilled worker visa and a tier 2 visa?",
        "What happened to the Tier 2 visa?",
        "Can my family come with me on a Skilled Worker visa?",
        "What is the Immigration Health Surcharge?",
        "How much does a skilled worker visa cost?",
        "What is ILR and can I get it on a Skilled Worker visa?",
        "Can I get British citizenship after a Skilled Worker visa?",
        "Can my wife work in the UK if I have a Skilled Worker visa?",
        "What are the settlement requirements for a Skilled Worker visa holder?",
        "What is the Health and Care Worker visa?",
        "Is the NHS hiring nurses from abroad?",
        "Can I extend my Skilled Worker visa?",
        "What happens if I change jobs on a Skilled Worker visa?",
        "Can I study in the UK on a Skilled Worker visa?",
        "What is a sponsor licence and how does a company get one?",
        "What are shortage occupations in the UK?",
        "How does the points-based immigration system work?",
        "What is the Immigration Skills Charge?",
        "Do I pay the Immigration Health Surcharge on a Health and Care visa?",
        "What does RQF level 3 mean for visa purposes?",
        "What is the going rate for a software engineer in the UK?",
        "Atlas AI what can you help me with?",
        "What questions can you answer about UK visas?",
        "Hello, I need help with UK visa information",
        "I want to work in the UK — what visa do I need?",
        "Is it hard to get a UK work visa?",
    ]
    return {
        "user_input": random.choice(templates),
        "intent": "general_query",
        "entities": {},
        "expected_rule_outcome": None,
    }


# ── Edge cases ────────────────────────────────────────────────────────────────
def gen_edge_cases() -> list[dict]:
    return [
        # Low salary — not eligible
        {
            "user_input": "I'm a software engineer from India earning £25,000. My employer will sponsor me. Am I eligible?",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "software engineer", "SALARY": 25000, "COUNTRY": "India", "HAS_SPONSOR": True},
            "expected_rule_outcome": "not_eligible",
        },
        # High salary — eligible
        {
            "user_input": "I'm a data scientist from China with a salary of £75,000 and a Certificate of Sponsorship. Do I qualify?",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "data scientist", "SALARY": 75000, "COUNTRY": "China", "HAS_SPONSOR": True},
            "expected_rule_outcome": "eligible",
        },
        # No sponsor — not eligible
        {
            "user_input": "I'm a nurse from the Philippines earning £35,000 but I haven't found a sponsor yet.",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "nurse", "SALARY": 35000, "COUNTRY": "Philippines", "HAS_SPONSOR": False},
            "expected_rule_outcome": "not_eligible",
        },
        # Doctor — eligible
        {
            "user_input": "I am a doctor from India, offered £55,000 by an NHS trust. Will I get a skilled worker visa?",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "doctor", "SALARY": 55000, "COUNTRY": "India", "HAS_SPONSOR": True},
            "expected_rule_outcome": "eligible",
        },
        # New entrant — borderline
        {
            "user_input": "I'm 23, just graduated as a civil engineer from Nigeria. Salary is £32,000 with sponsorship.",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "civil engineer", "SALARY": 32000, "COUNTRY": "Nigeria", "AGE": 23, "HAS_SPONSOR": True},
            "expected_rule_outcome": "eligible",  # New entrant rate for civil engineer = £30,520
        },
        # Eligible occupation search
        {
            "user_input": "Is chef an eligible occupation for Skilled Worker visa?",
            "intent": "general_query",
            "entities": {"JOB_TITLE": "chef"},
            "expected_rule_outcome": None,
        },
        # Australian national — English exempt
        {
            "user_input": "I'm Australian working as an accountant, salary £44,000 with a CoS. Am I eligible?",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "accountant", "SALARY": 44000, "COUNTRY": "Australia", "HAS_SPONSOR": True},
            "expected_rule_outcome": "eligible",
        },
        # Salary exactly at threshold
        {
            "user_input": "My salary offer is exactly £38,700 as a secondary school teacher. Will that be enough?",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "teacher", "SALARY": 38700, "COUNTRY": "unknown"},
            "expected_rule_outcome": "eligible",
        },
        # Missing info
        {
            "user_input": "Can I apply for a Skilled Worker visa?",
            "intent": "eligibility_check",
            "entities": {},
            "expected_rule_outcome": "insufficient_info",
        },
        # Shortage occupation
        {
            "user_input": "I'm a physiotherapist from South Africa, earning £38,000, employer sponsoring me.",
            "intent": "eligibility_check",
            "entities": {"JOB_TITLE": "physiotherapist", "SALARY": 38000, "COUNTRY": "South Africa", "HAS_SPONSOR": True},
            "expected_rule_outcome": "not_eligible",  # Below £38,700 general threshold
        },
    ]


# ── Main generator ─────────────────────────────────────────────────────────────
def generate_dataset(n_per_class: int = 500) -> list[dict]:
    dataset = []

    generators = [
        (gen_eligibility_check, n_per_class),
        (gen_document_requirement, n_per_class),
        (gen_processing_time, n_per_class),
        (gen_general_query, n_per_class),
    ]

    for gen_fn, n in generators:
        for i in range(n):
            item = gen_fn(i)
            dataset.append(item)

    # Add edge cases
    dataset.extend(gen_edge_cases())

    # Shuffle
    random.shuffle(dataset)
    return dataset


def split_dataset(dataset: list[dict], train_ratio=0.8, val_ratio=0.1):
    n = len(dataset)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    return (
        dataset[:n_train],
        dataset[n_train:n_train + n_val],
        dataset[n_train + n_val:],
    )


def save_dataset(dataset: list[dict], name: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(dataset)} examples → {path}")


def main():
    print("Generating Atlas AI synthetic dataset...")
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    # Full dataset
    full = generate_dataset(n_per_class=525)
    print(f"Total examples: {len(full)}")

    # Intent distribution
    from collections import Counter
    intent_counts = Counter(d["intent"] for d in full)
    print("Intent distribution:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")

    # Split
    train, val, test = split_dataset(full)
    save_dataset(full, "full_dataset", SYNTHETIC_DIR)
    save_dataset(train, "train", SYNTHETIC_DIR)
    save_dataset(val, "validation", SYNTHETIC_DIR)
    save_dataset(test, "test", SYNTHETIC_DIR)

    # Intent-only (for DistilBERT)
    intent_data = [{"text": d["user_input"], "label": d["intent"]} for d in full]
    save_dataset(intent_data, "intent_classification", SYNTHETIC_DIR)

    print(f"\n✅ Dataset generation complete. Files saved to {SYNTHETIC_DIR}")


if __name__ == "__main__":
    main()
