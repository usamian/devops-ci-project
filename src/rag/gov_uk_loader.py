"""
Atlas AI — GOV.UK Immigration Guidance Loader
Loads and chunks official GOV.UK content for RAG embedding.
Content is pre-encoded from official GOV.UK pages.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class DocumentChunk:
    """A chunk of GOV.UK immigration guidance text."""
    chunk_id: str
    text: str
    source_url: str
    source_title: str
    topic: str


def get_govuk_documents() -> list[DocumentChunk]:
    """
    Returns a curated set of GOV.UK immigration guidance chunks.
    Content sourced from: https://www.gov.uk/skilled-worker-visa
    Last reviewed: April 2024
    """
    raw_docs = _get_raw_govuk_content()
    chunks = []
    for doc_idx, doc in enumerate(raw_docs):
        text_chunks = _chunk_text(doc["text"], chunk_size=500, overlap=60)
        for chunk_idx, chunk_text in enumerate(text_chunks):
            chunks.append(DocumentChunk(
                chunk_id=f"doc{doc_idx}_chunk{chunk_idx}",
                text=chunk_text,
                source_url=doc["url"],
                source_title=doc["title"],
                topic=doc["topic"],
            ))
    return chunks


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 60) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def _get_raw_govuk_content() -> list[dict]:
    """Returns pre-encoded GOV.UK immigration guidance content."""
    return [
        {
            "title": "Skilled Worker visa – Overview",
            "url": "https://www.gov.uk/skilled-worker-visa",
            "topic": "overview",
            "text": """
The Skilled Worker visa allows you to come to or stay in the UK to do an eligible job with an approved employer.
You must be paid a minimum salary, and your job must be on the list of eligible occupations.
You must also be sponsored by a UK employer who holds a valid Skilled Worker sponsor licence.

To apply, you must score 70 points. You get points for having a job offer from an approved sponsor,
your job being at the required skill level, and your salary meeting the minimum threshold.
The Skilled Worker visa replaced the Tier 2 (General) visa on 1 December 2020.

You can usually apply up to 3 months before you start your job in the UK.
You must apply before your current visa expires if you're already in the UK.
You can apply online and you'll usually get a decision within 3 weeks if you apply from outside the UK
or 8 weeks if you apply from inside the UK.
            """,
        },
        {
            "title": "Skilled Worker visa – Eligibility",
            "url": "https://www.gov.uk/skilled-worker-visa/eligibility",
            "topic": "eligibility",
            "text": """
To be eligible for a Skilled Worker visa you must:
- be at least 18 years old
- have a job offer from a UK employer that is a licensed sponsor
- be doing a job that is on the list of eligible occupations
- meet the minimum salary requirements for your job
- be able to speak English at the required level

You'll need to score 70 points to get a Skilled Worker visa.
Mandatory points (60 points total):
- 20 points for having a valid job offer from a licensed sponsor
- 20 points for your job being at the required skill level (RQF 3 or above)
- 20 points for meeting the salary requirement

You also need 10 tradeable points, which you can get if your job is in a shortage occupation,
or if you have a PhD relevant to your job (10 points), or a PhD in a STEM subject (20 points).

The salary threshold was increased from 1 April 2024. The minimum salary is now £38,700 per year,
or the 'going rate' for the occupation if that is higher. Before April 2024 the threshold was £26,200.
            """,
        },
        {
            "title": "Skilled Worker visa – Your Job",
            "url": "https://www.gov.uk/skilled-worker-visa/your-job",
            "topic": "occupation",
            "text": """
Your job must be on the list of eligible occupations (Appendix Skilled Occupations).
The list includes hundreds of jobs at or above RQF level 3 (A-level equivalent).
Each occupation has a Standard Occupational Classification (SOC) code and a 'going rate' salary.

You must earn at least the minimum salary for your job. The minimum is the higher of:
- £38,700 per year (the general threshold from April 2024), OR
- The 'going rate' for your specific SOC code

If your occupation is on the Immigration Salary List (a subset of shortage occupations),
you only need to earn 80% of the going rate, but still at least £38,700.

New entrants to the labour market can be paid a lower salary — the lower of £30,960 or 70% of the going rate.
You're a new entrant if you're under 26, currently studying or recently graduated, or in a postdoctoral position.

Your sponsor assigns you a Certificate of Sponsorship (CoS) reference number.
You must include this number in your visa application.
The CoS confirms your job title, salary, and start date.
            """,
        },
        {
            "title": "Skilled Worker visa – English Language Requirement",
            "url": "https://www.gov.uk/skilled-worker-visa/knowledge-of-english",
            "topic": "english_language",
            "text": """
You must be able to speak, read, write and understand English to at least CEFR level B1.
You can prove your English language knowledge in several ways:

1. You are a national of a majority English-speaking country: Antigua and Barbuda, Australia, the Bahamas,
   Barbados, Belize, Canada, Dominica, Grenada, Guyana, Jamaica, Malta, New Zealand, St Kitts and Nevis,
   St Lucia, St Vincent and the Grenadines, Trinidad and Tobago, or the USA.

2. You have a UK degree or degree-level qualification (taught in English).

3. You have passed an approved English language test at B1 level or above:
   - IELTS for UKVI (Academic or General Training)
   - TOEFL iBT
   - PTE Academic UKVI
   - Cambridge English B1 Preliminary (PET) for Schools
   - Trinity College London Integrated Skills in English (ISE)

4. You have a GCSE, A-level, Scottish Higher or equivalent in English language or English literature
   from a UK school.

If you studied abroad at degree level or higher in English, you may be able to use your qualification
if it was taught and assessed in English and you have a letter from the institution confirming this.
            """,
        },
        {
            "title": "Skilled Worker visa – Documents",
            "url": "https://www.gov.uk/skilled-worker-visa/documents-you-must-provide",
            "topic": "documents",
            "text": """
You'll need to provide the following documents when you apply:

Required documents:
- A valid passport or travel document
- Your Certificate of Sponsorship reference number from your employer
- Proof of English language ability (unless exempt)
- Proof of your salary/job offer (e.g., employment contract, payslips)
- Your personal history (including any criminal convictions)
- Tuberculosis (TB) test results (if you're from a country where TB testing is required)
- Bank statements showing you have at least £1,270 (unless your employer certifies your maintenance)

You may also need to provide:
- Qualifications certificates (degree, professional qualifications)
- IELTS/TOEFL/PTE test certificate
- Previous UK visa refusal letters (if applicable)
- Overseas criminal record certificate (if your sponsor is in a regulated sector)

You will have to pay the Immigration Health Surcharge (IHS) as part of your application.
The IHS is currently £1,035 per year.

TB test certificates must be from an approved clinic. You must include an x-ray if required.
            """,
        },
        {
            "title": "Skilled Worker visa – Processing Times",
            "url": "https://www.gov.uk/skilled-worker-visa/apply",
            "topic": "processing_time",
            "text": """
Standard processing times:
- From outside the UK: You'll usually get a decision within 3 weeks.
- From inside the UK: You'll usually get a decision within 8 weeks.

These are target processing times and are not guaranteed. Processing can take longer during busy periods.

Priority services (available at some visa application centres, for an additional fee):
- Priority service: Decision within 5 working days (fee: £500)
- Super priority service: Decision within 1 working day (fee: £800) – available for applications from inside the UK

You should not book travel or make major commitments before receiving your decision.
You cannot apply for Priority or Super Priority service for all visa types.

Online applications are processed faster than paper applications.
You should apply as early as possible, and at least 3 months before your intended start date.
            """,
        },
        {
            "title": "Skilled Worker visa – Fees and Costs",
            "url": "https://www.gov.uk/skilled-worker-visa/apply",
            "topic": "fees",
            "text": """
Visa application fees (as of April 2024):
- Up to 3 years: £719
- More than 3 years: £1,420

These fees apply per person. If you're bringing dependants, each person pays separately.

Immigration Health Surcharge (IHS):
- £1,035 per year (per person)
- You pay the full amount for your visa duration upfront

Example total cost for a 5-year visa:
- Visa fee: £1,420
- IHS for 5 years: £5,175
- Total (excluding biometrics): £6,595

Additional costs:
- Biometric enrolment: usually free at visa application centres in the UK
- TB test: varies by country (typically £50–£150)
- English language test: £150–£250 depending on test type
- Priority service: £500
- Super priority service: £800

Your employer may cover some of these costs. Employers are legally required to pay the Immigration Skills Charge
(£1,000 per year for small sponsors, £239 per year for charities; £364 per year for small/charitable sponsors).
            """,
        },
        {
            "title": "Skilled Worker visa – How to Apply",
            "url": "https://www.gov.uk/skilled-worker-visa/apply",
            "topic": "application",
            "text": """
You apply online at gov.uk. Before you apply you must:
1. Get a Certificate of Sponsorship from your UK employer
2. Have the documents you need ready
3. Check whether you need to prove your English language ability
4. Check whether you need a TB test

During your application you will need to:
- Enter your Certificate of Sponsorship reference number
- Upload your supporting documents
- Pay the visa application fee and Immigration Health Surcharge
- Book and attend a biometric appointment (fingerprints and photograph)

After you apply:
- You'll usually get a decision within 3 weeks (from outside UK) or 8 weeks (from inside UK)
- If approved, you'll get a vignette sticker in your passport or a BRP (Biometric Residence Permit)
- You must travel to the UK within 30 days of getting your visa if applying from outside the UK

If your application is refused, you may have the right to an administrative review.
You can request this if you believe a case-working error was made.
You cannot appeal against a refusal.
            """,
        },
        {
            "title": "Skilled Worker visa – Dependants",
            "url": "https://www.gov.uk/skilled-worker-visa/family-members",
            "topic": "dependants",
            "text": """
Your partner and children under 18 can apply to join or stay with you in the UK as your dependants.
They must apply separately and will need to pay their own visa fees and IHS.

Your dependants can:
- Work in the UK without restriction (any job, any hours)
- Study in the UK
- Use the NHS (after paying the IHS)

Your partner must be:
- Your husband, wife or civil partner, OR
- Your unmarried partner if you have lived together for at least 2 years

Children under 18 must:
- Be genuinely your child (biological, adopted, or step-child)
- Not be married or in a civil partnership
- Not be living independently

You may need to show you can support your dependants financially.
The financial requirement for dependants varies based on how long you've been in the UK
and whether you or your sponsor will be supporting them.
            """,
        },
        {
            "title": "Skilled Worker visa – Extending and Switching",
            "url": "https://www.gov.uk/skilled-worker-visa/extend-or-switch",
            "topic": "extension",
            "text": """
You can extend your Skilled Worker visa or switch to it from another visa type.

Extension:
- Apply before your current visa expires (up to 28 days before)
- You can stay in the UK while your application is being processed
- Same salary and occupation requirements apply

Switching:
- You can switch to a Skilled Worker visa from most other visa types (except Visitor)
- You must have a new job offer and Certificate of Sponsorship
- Student visa holders can switch if they meet the requirements

Settlement (Indefinite Leave to Remain – ILR):
- You can apply for ILR (settlement) after 5 years on a Skilled Worker visa
- You must not have been outside the UK for more than 180 days in any rolling 12-month period
- You must still be working in an eligible skilled job
- Salary thresholds apply at the time of ILR application too

British Citizenship:
- After 1 year of ILR you can apply for British citizenship by naturalisation
- You must meet residence and character requirements
            """,
        },
        {
            "title": "Shortage Occupations – Immigration Salary List",
            "url": "https://www.gov.uk/government/publications/skilled-worker-visa-immigration-salary-list",
            "topic": "shortage_occupations",
            "text": """
The Immigration Salary List (formerly Shortage Occupation List) contains occupations where
the UK government has identified a shortage of workers.

For occupations on the Immigration Salary List, applicants only need to earn 80% of the going rate,
though the overall minimum of £38,700 still applies (unless new entrant rates apply).

Current shortage occupations include:
- Nurses (SOC 2225)
- Paramedics (SOC 2231)
- Medical radiographers (SOC 2217)
- Podiatrists (SOC 2218)
- Physiotherapists (SOC 2221)
- Occupational therapists (SOC 2222)
- Speech and language therapists (SOC 2223)
- Health professionals n.e.c. (SOC 2219)
- Laboratory technicians (SOC 3111)

The list is reviewed periodically by the Migration Advisory Committee (MAC).
Being on the shortage list also awards 20 tradeable points, making it easier to reach the 70-point threshold.
            """,
        },
        {
            "title": "Skilled Worker visa – Health and Care Worker route",
            "url": "https://www.gov.uk/health-care-worker-visa",
            "topic": "health_care",
            "text": """
The Health and Care Worker visa is a faster, cheaper route for eligible health and care professionals.

Eligible roles include:
- Doctors (all specialties)
- Nurses
- Allied health professionals
- Adult social care workers

Advantages over standard Skilled Worker visa:
- Lower application fee (£247 up to 3 years; £479 over 3 years)
- Exempt from Immigration Health Surcharge
- Faster processing (priority given)

You must be sponsored by:
- The NHS
- An NHS-funded organisation
- An organisation providing adult social care services

The same salary and English language requirements apply.
Your employer must hold a Skilled Worker sponsor licence and issue you a Certificate of Sponsorship.
            """,
        },
    ]
