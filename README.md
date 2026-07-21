# 🗺️ Atlas AI - UK Immigration Guidance Assistant

A full-fledged AI chatbot for UK immigration guidance, featuring natural conversation, smart decision-making, and professional responses based on official GOV.UK guidance.

## ✨ Features

### 🤖 Intelligent Conversation
- **Natural, casual conversation style** - Chat like you would with a human assistant
- **Smart intent detection** - Understands what you're asking with confidence scoring
- **Context awareness** - Remembers your conversation and builds on previous messages
- **Multi-turn dialogue** - Handles complex conversations that span multiple topics

### 🎯 Core Capabilities
- **Visa eligibility assessment** - Check if you qualify for various UK visas
- **Document requirements** - Get detailed checklists for your application
- **Processing times** - Know how long your application might take
- **Fee breakdowns** - Understand all costs involved
- **Salary thresholds** - Check if your salary meets requirements
- **Visa comparisons** - Understand differences between visa types

### 🚀 AI Enhancements
- **Query expansion** - Automatically expands queries with synonyms for better search
- **Smart RAG retrieval** - Advanced vector search with intent-aware filtering
- **FAQ matching** - Pre-built FAQ system for common questions
- **Entity extraction** - Automatically extracts job titles, salaries, countries, etc.
- **Professional fallbacks** - Honest responses when unsure, with guidance to official sources

### 🔄 Auto-Update System
- **1-click updates** - Update data from GOV.UK with a single click
- **Smart change detection** - Only updates when content has actually changed
- **Hash-based comparison** - Uses SHA256 to detect content changes
- **Efficient updates** - Skips unchanged pages to save time

### 🛡️ Professional Standards
- **Accurate information** - Based on official GOV.UK guidance
- **Professional fallback** - Honestly admits when unsure and directs to official sources
- **Clear disclaimers** - Always reminds users this is guidance, not legal advice
- **GDPR compliant** - No personal data retained beyond session

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A free Groq API key (see below)

---

### 🔑 Groq API Key Setup (Required for AI Responses)

Atlas AI uses **Groq's free API** to power its AI responses. Groq provides fast inference using models like `llama-3.3-70b-versatile` — completely free on their free tier.

#### Step 1: Get Your Free Groq API Key
1. Go to [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign up or log in (free account)
3. Click **"Create API Key"**
4. Copy the generated key (starts with `gsk_...`)

#### Step 2: Add the Key to the Project
Open `groq_config.py` in the project root and replace the placeholder:

```python
# groq_config.py
GROQ_API_KEY = "gsk_your_actual_key_here"   # ← paste your key here
```

> ⚠️ **Never share your API key or commit it to a public repo.** The `.gitignore` already excludes `.env` files, but `groq_config.py` is tracked — so keep your key private or use a `.env` file instead.

#### Groq Free Tier Limits
| Limit | Value |
|-------|-------|
| Requests per minute | 30 |
| Requests per day | 14,400 |
| Tokens per minute | 6,000 |
| Cost | **Free** |

These limits are more than enough for personal use and portfolio demos.

#### What Happens Without a Key?
The app still works — it falls back to the rule-based engine and knowledge base for responses. You just won't get the enhanced AI-generated answers.

---

### Step 1: Setup (First Time Only)

Run the setup script to create a virtual environment and install dependencies:

```bash
python setup.py
```

### Step 2: Configure Groq API Key

```bash
# Copy the config template
cp groq_config.example.py groq_config.py
```

Then open `groq_config.py` and paste your key:
```python
GROQ_API_KEY = "gsk_your_actual_key_here"
```

Or set it in your `.env` file:
```bash
cp .env.example .env
# then edit .env and set GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 3: Start the Application

```bash
python start.py
```

Then open your browser to: `http://localhost:5000`

```bash
# Full setup and start (auto-runs setup if needed)
python start.py

# CLI mode
python start.py --mode cli

# Custom port
python start.py --port 8080

# Debug mode
python start.py --debug

# Skip auto-setup check (if already set up)
python start.py --no-auto-setup
```

### All Available Options for start.py
```bash
python start.py                    # Web interface (default)
python start.py --mode cli         # CLI interface
python start.py --port 8080        # Custom port
python start.py --host 127.0.0.1   # Localhost only
python start.py --debug            # Enable debug mode
python start.py --no-auto-setup    # Skip automatic setup check
```

### All Available Options for setup.py
```bash
python setup.py                    # Full setup with venv
python setup.py --no-venv          # Install to system Python (not recommended)
python setup.py --force            # Force reinstallation
```

### Manual Installation (Optional)
If you prefer to manage dependencies manually:
```bash
# Create virtual environment
python -m venv .atlas_venv

# Activate it
# Windows: .atlas_venv\Scripts\activate
# Linux/Mac: source .atlas_venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m src.api.app
```

### Optional: Install Full spaCy Transformer Model
The large spaCy transformer model is not included by default (457MB). If you need it:
```bash
# Install from GitHub URL (not from PyPI)
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.7.3/en_core_web_trf-3.7.3-py3-none-any.whl
```

## 📁 Project Structure

```
01-Final-AtlasAI/
├── src/
│   ├── api/              # Flask web API
│   │   └── app.py        # Main Flask application
│   ├── dialogue/         # Conversation management
│   │   ├── enhanced_manager.py  # 🆕 New enhanced dialogue manager
│   │   └── manager.py    # Original dialogue manager
│   ├── nlp/              # Natural language processing
│   │   ├── intent_classifier.py
│   │   ├── ner_extractor.py
│   │   └── confidence_handler.py
│   ├── rag/              # Retrieval-Augmented Generation
│   │   ├── gov_uk_scraper.py
│   │   ├── retriever.py
│   │   └── embedder.py
│   ├── rule_engine/      # Eligibility checking
│   │   ├── skilled_worker.py
│   │   ├── health_care_worker.py
│   │   └── rules_base.py
│   ├── gpt/              # LLM integration
│   │   └── local_llm.py  # Ollama integration
│   ├── core/             # Core utilities
│   │   ├── config.py
│   │   ├── audit.py
│   │   └── canonicalizer.py
│   └── responses/        # Response templates
├── data/                 # Data files
│   ├── rules/            # Visa rules data
│   └── synthetic/        # Training data
├── models/               # ML models
│   └── faiss_index/      # Vector search index
├── frontend/             # Web UI templates
├── tests/                # Unit tests
├── main.py               # 🚀 Unified launcher (web + CLI)
├── config.py             # Configuration
└── requirements.txt      # Dependencies
```

## 💬 Conversation Examples

### Casual Greeting
```
You: Hey there!
Atlas: Hey! I'm Atlas, your friendly UK visa expert. Ready to help you navigate the immigration system. What would you like to know?
```

### Eligibility Check
```
You: Can I apply for a Skilled Worker visa?
Atlas: I'd be happy to help you check your eligibility! To give you an accurate assessment, I'll need a few details:

1. What's your job title or the role you've been offered?
2. What's the annual salary in GBP?
3. Do you have a Certificate of Sponsorship from a UK employer?
4. Which country are you from?

Feel free to provide all the information at once, or we can go through it step by step!
```

### Professional Fallback
```
You: What's the latest immigration policy change?
Atlas: I appreciate you asking, but I want to be completely honest — I'm not entirely sure about that specific detail. For the most accurate and up-to-date information, I'd recommend checking the official GOV.UK website or consulting with a qualified immigration adviser. That said, I'd be happy to help with anything related to visa eligibility, requirements, or the application process!
```

## 🔧 Configuration

Edit `config.py` or create a `.env` file to customize:

```env
# Flask settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Ollama settings (for LLM features)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

## 👤 Author

**Usama Shafiq**
- GitHub: [@usamian](https://github.com/usamian)
- Email: [usamian.dev@gmail.com](mailto:usamian.dev@gmail.com)

## 📄 License

**All Rights Reserved.**

Copyright (c) 2026 Usama Shafiq.

This project is created for portfolio demonstration purposes only. Unauthorized use, reproduction, or distribution of this code, in part or in whole, is strictly prohibited. For inquiries, please contact the author directly.
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# Session settings
SESSION_TIMEOUT_MINUTES=60
```

## 🎯 Key Features Explained

### Enhanced Intent Classification
The chatbot uses pattern matching and keyword analysis to understand user intent with confidence scoring:
- **Pattern matching** - Regex patterns for common queries
- **Keyword analysis** - Fallback keyword matching
- **Confidence scoring** - Each classification includes a confidence level
- **Context awareness** - Uses conversation history for disambiguation

### Entity Extraction
Automatically extracts relevant information from user messages:
- Job titles and occupations
- Salary figures (handles various formats: £45,000, 45k, etc.)
- Countries and nationalities
- Visa types
- Sponsorship status
- English proficiency
- Qualifications
- Age

### Smart Response Generation
- **Casual greetings** - Multiple varied greeting responses
- **Informational responses** - Accurate, sourced information
- **Eligibility assessments** - Structured evaluation with clear results
- **Professional fallbacks** - Honest admission when unsure
- **Context-aware replies** - Builds on previous conversation

### Multi-Turn Conversation
- Maintains conversation history
- Remembers extracted entities
- Builds user profile over time
- Handles topic switches gracefully

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Test the enhanced dialogue manager directly:
```bash
python -m src.dialogue.enhanced_manager
```

## 📊 API Reference

### Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "message": "Can I apply for a Skilled Worker visa?"
}
```

Response:
```json
{
  "response": "I'd be happy to help you check your eligibility!...",
  "session_id": "uuid",
  "intent": "eligibility_check",
  "confidence": 0.95,
  "entities": {
    "visa_type": "skilled worker"
  },
  "profile": {},
  "processing_time_ms": 45.2,
  "timestamp": "2024-01-01 12:00:00"
}
```

### Other Endpoints
- `GET /api/health` - Health check
- `GET /api/greeting` - Get welcome message
- `POST /api/reset` - Clear session
- `GET /api/visas` - List supported visas
- `POST /api/eligibility` - Check eligibility
- `GET /api/occupations/search?q=engineer` - Search occupations

## 🔒 Privacy & Security

- **No data retention** - Sessions expire after 60 minutes
- **GDPR compliant** - No personal data stored permanently
- **Local processing** - Can run entirely offline (without LLM)
- **Audit logging** - Optional logging for compliance

## 🛠️ Advanced Features

### RAG Integration
The system can integrate with GOV.UK scraping for retrieval-augmented generation:
```python
from src.rag.gov_uk_scraper import scraper

# Scrape GOV.UK pages
pages = scraper.scrape_all()

# Build knowledge base
kb = scraper.build_knowledge_base()
```

### Rule Engine
Deterministic eligibility checking based on UK immigration rules:
```python
from src.rule_engine.skilled_worker import SkilledWorkerRuleEngine
from src.rule_engine.rules_base import ApplicantProfile

engine = SkilledWorkerRuleEngine()
profile = ApplicantProfile(
    job_title="Software Engineer",
    salary_annual=50000,
    has_sponsor=True,
    country_of_origin="India",
)
result = engine.check_eligibility(profile)
```

### LLM Integration
Optional integration with Ollama for natural language generation:
```bash
# Install Ollama
# Download model: ollama pull mistral
```

## ⚠️ Disclaimer

**This tool provides informational guidance only, not legal advice.** Immigration rules change frequently. Always consult a qualified immigration solicitor or check official GOV.UK sources before making any decisions.

## 🙏 Acknowledgments

- Information sourced from official GOV.UK guidance
- Built with Flask, Python, and modern web technologies

---

> **Note:** This project is shared for portfolio viewing purposes only. Unauthorized use, copying, modification, or distribution is strictly prohibited. See [LICENSE](LICENSE) for details.