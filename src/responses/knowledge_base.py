"""
Atlas AI — Comprehensive Knowledge Base
Professional, detailed responses for all UK immigration query types.
All information is sourced from official GOV.UK guidance.
"""

from config import DISCLAIMER

# ── Comprehensive Response Templates ─────────────────────────────────────────

KNOWLEDGE_BASE = {
    "processing_time": {
        "response": (
            "## ⏱️ Skilled Worker Visa Processing Times\n\n"
            "**Standard Processing:**\n"
            "- **From outside the UK:** Usually within **3 weeks** (15 working days)\n"
            "- **From inside the UK (switching/extending):** Usually within **8 weeks** (40 working days)\n\n"
            "**Priority Services (Additional Fee):**\n"
            "- **Priority Service:** Decision within **5 working days** (+£500)\n"
            "- **Super Priority Service:** Decision within **1 working day** (+£800) — "
            "Available for in-country applications only\n\n"
            "**Important Notes:**\n"
            "- These are target times, not guarantees\n"
            "- Processing can take longer during peak periods (summer, holidays)\n"
            "- Complex applications may take longer\n"
            "- Do not book non-refundable travel before receiving your decision\n"
            "- You can usually apply up to 3 months before your start date\n\n"
            f"*Source: [GOV.UK – Skilled Worker Visa Processing Times]"
            f"(https://www.gov.uk/skilled-worker-visa/apply)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to know about priority service options?",
            "Do you need information about applying from inside or outside the UK?",
        ],
    },
    "fees_and_costs": {
        "response": (
            "## 💰 Skilled Worker Visa Fees and Costs (2024)\n\n"
            "**Visa Application Fees:**\n"
            "| Duration | Standard Fee | Health & Care Worker |\n"
            "|----------|-------------|---------------------|\n"
            "| Up to 3 years | £719 | £284 |\n"
            "| More than 3 years | £1,420 | £551 |\n\n"
            "**Immigration Health Surcharge (IHS):**\n"
            "- **Standard rate:** £1,035 per year (per person)\n"
            "- **Health & Care workers:** EXEMPT (no IHS)\n"
            "- Must be paid upfront for entire visa duration\n\n"
            "**Example Total Cost (Standard Route, 5 years):**\n"
            "- Visa fee: £1,420\n"
            "- IHS (5 years): £5,175\n"
            "- **Total (excluding extras): £6,595**\n\n"
            "**Additional Costs:**\n"
            "- TB test: £50–£150 (if required)\n"
            "- English language test: £150–£250\n"
            "- Priority service: +£500\n"
            "- Super Priority: +£800\n"
            "- Biometric enrolment: Usually free\n\n"
            "**Employer Costs:**\n"
            "- Immigration Skills Charge: £364–£1,000 per year (paid by sponsor)\n\n"
            f"*Source: [GOV.UK – Visa Fees]"
            f"(https://www.gov.uk/skilled-worker-visa/apply)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to know about the Health and Care Worker visa (lower fees)?",
            "Do you need information about who pays these costs?",
        ],
    },
    "dependants_query": {
        "response": (
            "## 👨‍👩‍👧‍👦 Bringing Dependants to the UK\n\n"
            "**Who Can Come as Your Dependant?**\n"
            "- **Partner:** Husband, wife, civil partner, or unmarried partner "
            "(living together for 2+ years)\n"
            "- **Children:** Under 18 (or over 18 if currently in UK as your dependant)\n\n"
            "**Dependant Rights:**\n"
            "- ✅ Work in the UK (any job, any hours)\n"
            "- ✅ Study in the UK\n"
            "- ✅ Use the NHS (after paying IHS)\n"
            "- ✅ Travel freely in and out of the UK\n\n"
            "**Requirements:**\n"
            "- You must be able to support them financially\n"
            "- They must apply separately and pay their own fees\n"
            "- Each dependant pays the full visa fee + IHS\n"
            "- You may need to show additional maintenance funds\n\n"
            "**Financial Requirement for Dependants:**\n"
            "- Partner: £285 in savings (28+ days)\n"
            "- First child: £315 in savings (28+ days)\n"
            "- Each additional child: £200 in savings (28+ days)\n"
            "- These are waived if your sponsor certifies maintenance\n\n"
            "**Application Process:**\n"
            "1. Dependants can apply at the same time as you or join later\n"
            "2. They need to provide relationship evidence\n"
            "3. Children need birth certificates showing both parents' names\n\n"
            f"*Source: [GOV.UK – Family Members]"
            f"(https://www.gov.uk/skilled-worker-visa/family-members)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to know about school options for children?",
            "Do you need information about applying for dependants?",
        ],
    },
    "extension_switching": {
        "response": (
            "## 🔄 Extending or Switching Your Skilled Worker Visa\n\n"
            "**Extending Your Visa:**\n"
            "- Apply before your current visa expires\n"
            "- Can apply up to 28 days before expiry\n"
            "- Same requirements apply (sponsor, salary, occupation)\n"
            "- You can stay in the UK while application is processed\n"
            "- No limit on number of extensions\n\n"
            "**Switching to Skilled Worker Visa:**\n"
            "You can switch from most visa types, including:\n"
            "- ✅ Student visa (after completing studies)\n"
            "- ✅ Graduate visa\n"
            "- ✅ Tier 2 (General) visa\n"
            "- ✅ Global Talent visa\n"
            "- ✅ Family visa\n"
            "- ❌ Visitor visa (cannot switch)\n\n"
            "**Requirements for Switching:**\n"
            "- New job offer from licensed sponsor\n"
            "- New Certificate of Sponsorship\n"
            "- Meet all standard eligibility criteria\n"
            "- Pay full application fee and IHS\n\n"
            "**Student to Skilled Worker:**\n"
            "- Can switch after completing your degree\n"
            "- No need to return to home country\n"
            "- Must meet salary and occupation requirements\n\n"
            "**Important:**\n"
            "- Your new sponsor must be different from your current one (usually)\n"
            "- You can start working for new sponsor once visa is granted\n"
            "- Previous time in UK counts towards ILR (5 years)\n\n"
            f"*Source: [GOV.UK – Extend or Switch]"
            f"(https://www.gov.uk/skilled-worker-visa/extend-or-switch)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to know about switching from a Student visa?",
            "Do you need information about the extension process?",
        ],
    },
    "settlement_ilr": {
        "response": (
            "## 🏠 Settlement (Indefinite Leave to Remain) After Skilled Worker Visa\n\n"
            "**Eligibility for ILR:**\n"
            "- You must have spent **5 continuous years** in the UK on a Skilled Worker visa\n"
            "- You must still be working in an eligible skilled job\n"
            "- You must meet the salary threshold at the time of ILR application\n"
            "- You must not have been outside the UK for more than **180 days** in any "
            "rolling 12-month period during those 5 years\n\n"
            "**ILR Requirements:**\n"
            "1. **Continuous residence:** No more than 180 days absence in any 12-month period\n"
            "2. **Employment:** Still working in eligible job with sponsor\n"
            "3. **Salary:** Meeting current threshold (usually £38,700 or going rate)\n"
            "4. **Life in the UK test:** Pass the official test\n"
            "5. **English language:** B1 CEFR level (if not already proven)\n"
            "6. **Good character:** No serious criminal convictions\n\n"
            "**ILR Application:**\n"
            "- Can apply 28 days before completing 5 years\n"
            "- Fee: £2,885 (as of 2024)\n"
            "- Decision usually within 6 months\n"
            "- Priority service available (5 working days) for +£800\n\n"
            "**After ILR:**\n"
            "- Live and work in the UK without restriction\n"
            "- No immigration time limits\n"
            "- Access to public funds (benefits)\n"
            "- Can apply for British citizenship after 12 months\n\n"
            "**British Citizenship:**\n"
            "- Apply after 1 year of ILR (total 6 years in UK)\n"
            "- Must meet residence and character requirements\n"
            "- Fee: £1,580 (plus £80 ceremony fee)\n\n"
            f"*Source: [GOV.UK – Settlement]"
            f"(https://www.gov.uk/settled-status-eu-citizens-families/applying/eligibility)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to know about the 180-day absence rule?",
            "Do you need information about the Life in the UK test?",
        ],
    },
    "health_care_worker": {
        "response": (
            "## 🏥 Health and Care Worker Visa\n\n"
            "**What is it?**\n"
            "A faster, cheaper route for eligible health and care professionals "
            "working in the UK's health and social care sector.\n\n"
            "**Eligible Roles:**\n"
            "- **Doctors:** All specialties (GPs, consultants, surgeons, etc.)\n"
            "- **Nurses:** All nursing roles (RNs, mental health, learning disabilities)\n"
            "- **Allied Health Professionals:** Physiotherapists, radiographers, "
            "paramedics, occupational therapists, etc.\n"
            "- **Adult Social Care Workers:** Care workers, senior care workers, "
            "support workers\n"
            "- **Health Professionals:** Psychologists, pharmacists, midwives, etc.\n\n"
            "**Key Advantages Over Standard Skilled Worker Visa:**\n"
            "| Benefit | Standard SW | Health & Care |\n"
            "|---------|------------|---------------|\n"
            "| Application Fee (3+ years) | £1,420 | £551 |\n"
            "| IHS (per year) | £1,035 | EXEMPT |\n"
            "| Processing Time | Standard | Priority given |\n"
            "| Total Savings (5 years) | - | ~£6,000+ |\n\n"
            "**Eligibility Requirements:**\n"
            "- Job must be with an eligible employer (NHS, NHS foundation trust, "
            "adult social care provider)\n"
            "- Employer must hold a Skilled Worker sponsor licence\n"
            "- Same salary and English language requirements as Skilled Worker\n"
            "- Job must be on the eligible occupations list\n\n"
            "**Who Can't Use This Route?**\n"
            "- Those working in non-clinical roles (admin, management without clinical duties)\n"
            "- Those working for private healthcare providers not contracted with NHS\n"
            "- Those in dentistry or ophthalmology (unless NHS-employed)\n\n"
            f"*Source: [GOV.UK – Health and Care Worker Visa]"
            f"(https://www.gov.uk/health-care-worker-visa)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to check if your specific role qualifies?",
            "Do you need information about eligible employers?",
        ],
    },
    "shortage_occupation": {
        "response": (
            "## 📋 Shortage Occupations (Immigration Salary List)\n\n"
            "**What is the Immigration Salary List?**\n"
            "A list of occupations where the UK has identified a shortage of workers. "
            "These roles get special treatment in the immigration system.\n\n"
            "**Benefits for Shortage Occupations:**\n"
            "- Salary threshold: Only need to earn **80% of the going rate**\n"
            "- Still must meet the general threshold of £38,700 (unless new entrant)\n"
            "- 20 tradeable points towards the 70-point requirement\n"
            "- Easier to meet the points-based system criteria\n\n"
            "**Current Shortage Occupations Include:**\n"
            "- **Healthcare:** Nurses (SOC 2225), Paramedics (2231), Medical Radiographers (2217), "
            "Podiatrists (2218), Physiotherapists (2221), Occupational Therapists (2222), "
            "Speech and Language Therapists (2223)\n"
            "- **Science & Tech:** Laboratory Technicians (3111), Biological Scientists (2111), "
            "Physical Scientists (2112), Social Workers (2232)\n"
            "- **Engineering:** Civil Engineers (2121), Mechanical Engineers (2122), "
            "Electrical Engineers (2123), Electronics Engineers (2124)\n"
            "- **Education:** Secondary Education Teachers (2311), Special Needs Teachers (2312)\n"
            "- **Arts:** Dancers, Choreographers (3411), Actors, Musicians (3412)\n\n"
            "**How to Check if Your Job is on the List:**\n"
            "1. Find your SOC code (Standard Occupational Classification)\n"
            "2. Check if it appears in the Immigration Salary List\n"
            "3. Verify the going rate for your specific code\n\n"
            "**Important:** The list is reviewed periodically by the Migration Advisory Committee (MAC). "
            "Always check the latest version on GOV.UK.\n\n"
            f"*Source: [GOV.UK – Immigration Salary List]"
            f"(https://www.gov.uk/government/publications/skilled-worker-visa-immigration-salary-list)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like me to check if your occupation is on the shortage list?",
            "Do you need information about going rates for specific jobs?",
        ],
    },
    "english_language": {
        "response": (
            "## 📝 English Language Requirement for Skilled Worker Visa\n\n"
            "**Required Level:** CEFR B1 (Intermediate) in all four skills:\n"
            "- Speaking\n"
            "- Listening\n"
            "- Reading\n"
            "- Writing\n\n"
            "**How to Prove English Proficiency:**\n\n"
            "**1. Nationality Exemption** — If you're a citizen of a majority English-speaking country:\n"
            "   - Antigua and Barbuda, Australia, Bahamas, Barbados, Belize, Canada, Dominica, "
            "   Grenada, Guyana, Jamaica, Malta, New Zealand, St Kitts and Nevis, St Lucia, "
            "   St Vincent and the Grenadines, Trinidad and Tobago, USA\n\n"
            "**2. UK Degree** — A UK bachelor's, master's, or PhD degree (taught in English)\n\n"
            "**3. Approved English Test** — Pass one of these at B1 level or above:\n"
            "   - IELTS for UKVI (Academic or General Training)\n"
            "   - TOEFL iBT\n"
            "   - PTE Academic UKVI\n"
            "   - Cambridge English B1 Preliminary (PET)\n"
            "   - Trinity College London ISE\n\n"
            "**4. GCSE/A-Level** — GCSE, A-level, Scottish Higher in English language or literature\n\n"
            "**5. Overseas Degree** — Degree taught in English (requires ECCTIS verification)\n\n"
            "**Test Validity:**\n"
            "- IELTS/TOEFL/PTE: Valid for 2 years from test date\n"
            "- Degree certificates: No expiry\n"
            "- Must be from an approved test provider\n\n"
            "**Exemptions:**\n"
            "- Nationals of majority English-speaking countries\n"
            "- Those with a UK degree\n"
            "- Those who previously demonstrated English for a UK visa\n"
            "- Those with a physical or mental condition preventing testing\n\n"
            f"*Source: [GOV.UK – English Language Requirement]"
            f"(https://www.gov.uk/skilled-worker-visa/knowledge-of-english)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like information about English test preparation?",
            "Do you need to know about ECCTIS verification for overseas degrees?",
        ],
    },
    "salary_threshold": {
        "response": (
            "## 💷 Salary Thresholds for Skilled Worker Visa (April 2024)\n\n"
            "**General Salary Threshold:** £38,700 per year\n\n"
            "**Going Rate:** Each occupation has a specific 'going rate' salary. "
            "You must earn the **higher** of:\n"
            "- The general threshold (£38,700), OR\n"
            "- The going rate for your specific SOC code\n\n"
            "**New Entrant Salary Threshold:** Lower rates for new entrants:\n"
            "- General new entrant threshold: £30,960 per year\n"
            "- Or 70% of the going rate for your occupation (whichever is higher)\n"
            "- Absolute minimum: £26,200 per year\n\n"
            "**Who Qualifies as a New Entrant?**\n"
            "- Under 26 years old\n"
            "- Currently studying (switching from Student visa)\n"
            "- Recently graduated (within 2 years)\n"
            "- In professional training\n"
            "- Working towards full registration for regulated profession\n"
            "- Postdoctoral position (in specific roles)\n\n"
            "**Shortage Occupation Salary:**\n"
            "- Only need to earn 80% of the going rate\n"
            "- General threshold of £38,700 still applies (unless new entrant)\n\n"
            "**What Counts as Salary?**\n"
            "- Basic gross salary (before tax)\n"
            "- Allowances that are guaranteed\n"
            "- UK location allowances\n"
            "- Does NOT include: bonuses, commission, overtime, accommodation allowances\n\n"
            "**Examples:**\n"
            "| Occupation | Going Rate | Required Salary |\n"
            "|------------|------------|----------------|\n"
            "| Software Developer | £38,700 | £38,700 |\n"
            "| Nurse | £29,900 | £38,700 (general threshold) |\n"
            "| Doctor (specialist) | £50,000+ | £50,000+ |\n"
            "| Teacher | £32,000 | £38,700 (general threshold) |\n\n"
            f"*Source: [GOV.UK – Salary Requirements]"
            f"(https://www.gov.uk/skilled-worker-visa/eligibility)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like me to check the going rate for your specific occupation?",
            "Do you need information about new entrant status?",
        ],
    },
    "document_requirement": {
        "response": (
            "## 📋 Documents Required for Skilled Worker Visa\n\n"
            "**Mandatory Documents:**\n"
            "1. **Valid Passport or Travel Document**\n"
            "   - Must be valid for entire stay\n"
            "   - Must have at least one blank page\n\n"
            "2. **Certificate of Sponsorship (CoS) Reference Number**\n"
            "   - Provided by your UK employer\n"
            "   - Contains your job details, salary, and start date\n"
            "   - Valid for 3 months from date of issue\n\n"
            "3. **Proof of English Language**\n"
            "   - IELTS/TOEFL/PTE certificate, OR\n"
            "   - UK degree certificate, OR\n"
            "   - Evidence of nationality from English-speaking country\n\n"
            "4. **Proof of Salary/Employment**\n"
            "   - Employment contract, OR\n"
            "   - Payslips showing salary, OR\n"
            "   - Letter from employer confirming salary\n\n"
            "5. **Financial Evidence**\n"
            "   - Bank statements showing £1,270 held for 28+ days, OR\n"
            "   - Sponsor certification of maintenance on CoS (A-rated sponsors)\n\n"
            "**Additional Documents (If Applicable):**\n"
            "- **TB Test Certificate** — If from a listed country\n"
            "- **Academic Qualifications** — Degree certificates, transcripts\n"
            "- **Previous UK Visa Refusals** — Full details and refusal letters\n"
            "- **Criminal Record Certificate** — If working in regulated sectors\n"
            "- **ATAS Certificate** — For certain sensitive research areas\n"
            "- **Dependants' Documents** — Birth certificates, marriage certificates\n\n"
            "**Document Format:**\n"
            "- All documents must be originals or certified copies\n"
            "- Non-English documents need certified translations\n"
            "- Translations must include translator credentials and confirmation of accuracy\n\n"
            "**Biometric Information:**\n"
            "- Fingerprints and photograph at visa application centre\n"
            "- Usually free at UK centres\n\n"
            f"*Source: [GOV.UK – Documents You Must Provide]"
            f"(https://www.gov.uk/skilled-worker-visa/documents-you-must-provide)*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like a personalized document checklist?",
            "Do you need information about TB test requirements for your country?",
        ],
    },
    "general_query": {
        "response": (
            "## 🗺️ Welcome to Atlas AI — Your UK Immigration Guide\n\n"
            "I can help you with comprehensive information about UK immigration, "
            "particularly the **Skilled Worker Visa**. Here's what I can assist with:\n\n"
            "**📋 Visa Information:**\n"
            "- Eligibility assessment for Skilled Worker visa\n"
            "- Salary and occupation requirements\n"
            "- English language requirements\n"
            "- Document checklists\n\n"
            "**💰 Costs & Timeline:**\n"
            "- Visa fees and total costs\n"
            "- Processing times and priority services\n"
            "- Immigration Health Surcharge (IHS)\n\n"
            "**👨‍👩‍👧‍👦 Family & Settlement:**\n"
            "- Bringing dependants (partner and children)\n"
            "- Extending or switching visas\n"
            "- Settlement (ILR) after 5 years\n"
            "- British citizenship pathway\n\n"
            "**🏥 Special Routes:**\n"
            "- Health and Care Worker visa (lower fees)\n"
            "- Shortage occupations (lower salary threshold)\n"
            "- New entrant provisions\n\n"
            "**How to Use This Tool:**\n"
            "Simply type your question in natural language. For example:\n"
            "- *\"I'm a software engineer from India earning £50,000. Can I get a Skilled Worker visa?\"*\n"
            "- *\"How much does the visa cost?\"*\n"
            "- *\"Can I bring my family?\"*\n"
            "- *\"What documents do I need?\"*\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to check your eligibility for a Skilled Worker visa?",
            "Do you have a specific question about UK immigration?",
        ],
    },
}


def get_response(intent: str, context: dict = None) -> dict:
    """
    Get the appropriate response for an intent.
    
    Args:
        intent: The detected intent category
        context: Optional context dict with user profile info
    
    Returns:
        dict with 'response', 'follow_up', and 'sources'
    """
    if intent in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[intent]
    
    # Default fallback for unknown intents
    return get_fallback_response()


def get_fallback_response() -> dict:
    """
    Professional fallback response for queries outside system scope.
    """
    return {
        "response": (
            "I apologize, but I'm currently unable to provide specific guidance on that topic. "
            "My expertise is focused on UK Skilled Worker visa eligibility and related immigration matters.\n\n"
            "**What I Can Help With:**\n"
            "- Skilled Worker visa eligibility assessment\n"
            "- Salary and occupation requirements\n"
            "- Document checklists and processing times\n"
            "- Fees and costs breakdown\n"
            "- Bringing dependants to the UK\n"
            "- Extension, switching, and settlement (ILR)\n"
            "- Health and Care Worker visa\n"
            "- English language requirements\n\n"
            "**For Other Immigration Matters:**\n"
            "I recommend consulting:\n"
            "- Official [GOV.UK](https://www.gov.uk) website for comprehensive guidance\n"
            "- A qualified immigration solicitor for personalized advice\n"
            "- OISC-registered immigration advisers\n\n"
            "Is there anything about Skilled Worker visas I can help you with instead?\n\n"
            f"*{DISCLAIMER}*"
        ),
        "follow_up": [
            "Would you like to check your Skilled Worker visa eligibility?",
            "Do you have questions about Skilled Worker visa requirements?",
        ],
    }


def get_suggestion_for_intent(intent: str) -> list:
    """Get suggested follow-up questions for an intent."""
    if intent in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[intent].get("follow_up", [])
    return ["Is there anything else I can help you with?"]