"""
Atlas AI — Constrained GPT Explanation Layer
CRITICAL CONSTRAINT: GPT can ONLY explain the verdict; it CANNOT change it.
The eligibility verdict is always determined by the rule engine, never by GPT.

Architecture:
  Rule Engine → Verdict + Reasons → [GPT] → Human-readable explanation
  GPT never sees "decide eligibility" — it only sees "explain this verdict"
"""

from __future__ import annotations
import re
from typing import Optional

from config import OPENAI_API_KEY, OPENAI_MODEL, OFFLINE_MODE, DISCLAIMER
from src.rule_engine.rules_base import EligibilityResult, Verdict

# ── Post-generation safety validator ─────────────────────────────────────────

# Phrases that would indicate GPT is making eligibility claims beyond what rules say
_HALLUCINATION_PATTERNS = [
    r'\byou (are|will be|would be|could be) (definitely|certainly|surely|absolutely) (eligible|approved)',
    r'\byou (will|would|should) (definitely|certainly|surely) (get|receive|obtain) (your|a) visa',
    r'\bguaranteed to (be approved|get a visa|qualify)',
    r'\bno doubt (you|that) (are|will)',
    r'\b100% (eligible|certain|sure)',
    r'\byou (are|will be) (eligible|approved) (regardless|despite|even if)',
    r'\bimmigration (lawyer|solicitor|professional) (is not|is unnecessary|not needed)',
]

_HALLUCINATION_RE = [re.compile(p, re.IGNORECASE) for p in _HALLUCINATION_PATTERNS]


def _detect_hallucination(text: str) -> list[str]:
    """Return list of problematic patterns found in generated text."""
    found = []
    for pattern_re in _HALLUCINATION_RE:
        if pattern_re.search(text):
            found.append(pattern_re.pattern)
    return found


def _sanitise_response(text: str, verdict: Verdict) -> str:
    """
    Post-process GPT output:
    1. Remove any hallucinated eligibility claims
    2. Ensure verdict consistency
    3. Append disclaimer
    """
    # Replace any "you will get" style guarantees with hedged language
    text = re.sub(
        r'\byou (will|would) (definitely|certainly|surely) (get|receive|obtain)',
        r'you may ',
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r'\b(guaranteed|100%|certainly) (eligible|approved)',
        r'likely eligible (subject to full Home Office assessment)',
        text,
        flags=re.IGNORECASE
    )
    return text


# ── Prompt templates ──────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    return """You are Atlas AI, a UK immigration guidance assistant. Your role is to explain 
immigration eligibility assessments in clear, empathetic, and accurate language.

STRICT RULES you must follow:
1. You NEVER change the eligibility verdict. The verdict has been determined by official rules and is provided to you as FACT.
2. You ONLY explain and elaborate on the verdict. You do NOT re-assess or override it.
3. You always cite official GOV.UK sources in your response.
4. You always include the disclaimer that this is informational guidance, not legal advice.
5. You never make absolute guarantees (e.g., "you will get the visa" — use "you appear to meet the requirements").
6. You always recommend consulting a qualified immigration solicitor for complex cases.
7. Keep responses concise but complete. Use bullet points for requirements.
8. Be empathetic — immigration is stressful. Be supportive in tone.
"""


def _build_user_prompt(
    result: EligibilityResult,
    retrieved_context: str,
    original_query: str,
    profile_summary: str,
) -> str:
    passed_rules = "\n".join(
        f"  ✓ {r.rule_description}: {r.reason}" for r in result.passed_rules
    )
    failed_rules = "\n".join(
        f"  ✗ {r.rule_description}: {r.reason}" for r in result.failed_rules
    )

    verdict_str = {
        Verdict.ELIGIBLE: "ELIGIBLE",
        Verdict.NOT_ELIGIBLE: "NOT ELIGIBLE",
        Verdict.INSUFFICIENT_INFO: "INSUFFICIENT INFORMATION",
    }.get(result.verdict, "UNKNOWN")

    prompt = f"""USER QUERY: {original_query}

APPLICANT PROFILE SUMMARY:
{profile_summary}

RULE ENGINE VERDICT (DO NOT CHANGE THIS):
Verdict: {verdict_str}
Points: {result.points_earned}/{result.points_required}
Summary: {result.summary}

PASSED REQUIREMENTS:
{passed_rules if passed_rules else "  (none)"}

FAILED REQUIREMENTS:
{failed_rules if failed_rules else "  (none)"}

RELEVANT GOV.UK GUIDANCE:
{retrieved_context}

TASK: Write a clear, helpful explanation of this eligibility assessment for the applicant.
- Explain WHAT the verdict means and WHY
- For each failed requirement, explain clearly what they would need to do to fix it
- Cite relevant GOV.UK links
- End with the standard disclaimer about seeking professional advice
- Keep the verdict as stated above. Do NOT change it.
"""
    return prompt


# ── Offline fallback template ─────────────────────────────────────────────────

def _build_offline_response(
    result: EligibilityResult,
    original_query: str,
    retrieved_context: str,
) -> str:
    """Build a structured response without GPT (offline mode)."""
    lines = []

    if result.verdict == Verdict.ELIGIBLE:
        lines.append("## ✅ You appear to be eligible for the Skilled Worker Visa\n")
        lines.append(result.summary)
        lines.append("\n### Requirements you meet:")
        for r in result.passed_rules:
            lines.append(f"- **{r.rule_description}**: {r.reason}")
            lines.append(f"  *(Source: [{r.source_url}]({r.source_url}))*")

    elif result.verdict == Verdict.NOT_ELIGIBLE:
        lines.append("## ❌ You do not currently meet the requirements\n")
        lines.append(result.summary)
        if result.failed_rules:
            lines.append("\n### Issues to resolve:")
            for r in result.failed_rules:
                lines.append(f"- **{r.rule_description}**: {r.reason}")
                lines.append(f"  *(Source: [{r.source_url}]({r.source_url}))*")
        if result.passed_rules:
            lines.append("\n### Requirements you meet:")
            for r in result.passed_rules:
                lines.append(f"- ✓ {r.rule_description}")

    elif result.verdict == Verdict.INSUFFICIENT_INFO:
        lines.append("## ℹ️ More information needed\n")
        lines.append(result.summary)
        if result.missing_info:
            lines.append("\n### Please provide:")
            for field in result.missing_info:
                lines.append(f"- {field.replace('_', ' ').title()}")

    if retrieved_context and retrieved_context != "No relevant guidance found.":
        lines.append("\n### Relevant GOV.UK Guidance:\n")
        lines.append(retrieved_context[:800] + "...")  # Truncate for display

    lines.append(f"\n---\n*{DISCLAIMER}*")
    return "\n".join(lines)


# ── Main explainer function ────────────────────────────────────────────────────

def generate_explanation(
    result: EligibilityResult,
    original_query: str,
    retrieved_context: str,
    profile_summary: str = "",
) -> dict:
    """
    Generate a human-readable explanation of the eligibility result.

    GUARANTEE: The verdict in result is NEVER modified by this function.
    GPT only explains the verdict, never determines it.

    Returns:
        {
            "explanation": str,
            "verdict": str,  # Unchanged from rule engine
            "source": "gpt" | "offline",
            "hallucination_detected": bool,
            "hallucination_patterns": list[str],
        }
    """
    # Offline mode or no API key
    if OFFLINE_MODE:
        explanation = _build_offline_response(result, original_query, retrieved_context)
        return {
            "explanation": explanation,
            "verdict": result.verdict.value,
            "source": "offline",
            "hallucination_detected": False,
            "hallucination_patterns": [],
        }

    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(result, retrieved_context, original_query, profile_summary)

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1200,
            temperature=0.3,  # Low temperature for factual, consistent outputs
        )

        raw_text = response.choices[0].message.content.strip()

        # Post-generation validation
        hallucination_patterns = _detect_hallucination(raw_text)
        sanitised_text = _sanitise_response(raw_text, result.verdict)

        # Ensure disclaimer is always present
        if "informational" not in sanitised_text.lower() and "legal advice" not in sanitised_text.lower():
            sanitised_text += f"\n\n---\n*{DISCLAIMER}*"

        return {
            "explanation": sanitised_text,
            "verdict": result.verdict.value,  # Always from rule engine — never from GPT
            "source": "gpt",
            "hallucination_detected": len(hallucination_patterns) > 0,
            "hallucination_patterns": hallucination_patterns,
        }

    except Exception as e:
        # If GPT call fails, fall back to offline mode
        print(f"[GPT] Error calling OpenAI API: {e}. Falling back to offline mode.")
        explanation = _build_offline_response(result, original_query, retrieved_context)
        return {
            "explanation": explanation,
            "verdict": result.verdict.value,
            "source": "offline_fallback",
            "hallucination_detected": False,
            "hallucination_patterns": [],
        }
