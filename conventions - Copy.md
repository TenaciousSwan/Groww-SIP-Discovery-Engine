# System Conventions & Code Guidelines

This document serves as the single source of truth for architectural style, directory structure, coding standards, error handling patterns, and banned antipatterns. Every module developed for the **AI Discovery Engine** must adhere strictly to these conventions.

---

## 1. Directory & File Structure

```
myntra_discovery_engine/
│
├── data/                       # Local SQLite database & raw output exports
│   └── discovery.db            # Primary persistent database
│
├── ingestion/                  # Phase 1: Data Scrapers & Ingestion Modules
│   ├── __init__.py
│   ├── playstore.py            # Google Play Store reviews ingestion
│   ├── reddit.py               # Reddit post & comment crawler (PRAW)
│   ├── youtube.py              # YouTube comments & transcript fetcher
│   ├── cleaner.py              # PII stripping & text normalization
│   └── run_all.py              # Single entry point for Phase 1 pipeline
│
├── ai_engine/                  # Phase 2: LLM Classification & Schema Engine
│   ├── __init__.py
│   ├── schema.py               # Pydantic models for structured outputs
│   ├── prompts.py              # System & user prompt templates
│   ├── classifier.py           # LLM API orchestration & schema mapping
│   └── guardrails.py           # Non-monetary validation & price filter
│
├── analytics/                  # Phase 3: Aggregation & Metrics Calculation
│   ├── __init__.py
│   └── metrics.py              # Pareto, Severity Score & External Index logic
│
├── app.py                      # Phase 3: Streamlit UI Dashboard Entrypoint
│
├── PROBLEM_STATEMENT.md        # Plain English problem scope & objectives
├── ARCHITECTURE.md             # System design & data flow diagram
├── implementationPlan.md       # Phased execution roadmap
├── conventions.md              # System conventions & coding standards
└── requirements.txt            # Python dependencies
```

---

## 2. Naming Conventions

* **Files & Folders:** Lowercase with underscores (`snake_case`). Example: `playstore.py`, `ai_engine/schema.py`.
* **Variables & Functions:** `snake_case`. Example: `fetch_playstore_reviews()`, `clean_raw_text()`.
* **Classes:** `PascalCase`. Example: `WishlistInsightSchema`, `PlayStoreIngestor`.
* **Constants:** `UPPER_SNAKE_CASE`. Example: `MAX_RETRIES = 3`, `KEYWORDS_FILTER = ['wishlist', 'size', 'fit']`.
* **Database Tables & Columns:** `snake_case`. Example: `raw_conversations`, `enriched_insights`, `friction_category`.

---

## 3. Allowed Tech Stack & Core Libraries

To ensure stability, simplicity, and speed, **only** use the following approved libraries:

| Purpose | Approved Library | Notes |
| :--- | :--- | :--- |
| **Data Manipulation** | `pandas` (v2.0+) | For dataframe aggregations and CSV dumps |
| **Database** | `sqlite3` / `SQLAlchemy` | Local SQLite file storage (`data/discovery.db`) |
| **Store Ingestion** | `google-play-scraper` | For Google Play Store reviews |
| **Reddit Ingestion** | `praw` | Official Reddit API Wrapper |
| **YouTube Ingestion**| `youtube-transcript-api` | Extract transcripts & video comments |
| **Data Validation** | `pydantic` (v2.0+) | Enforce structured JSON schema from LLMs |
| **AI / LLM Integration**| `openai` / `anthropic` | Structured outputs & function calling |
| **Dashboard UI** | `streamlit` | Interactive PM UI & visualization |
| **HTTP Requests** | `httpx` / `requests` | For external endpoints |

---

## 4. Error Handling Patterns

1. **Graceful Degraded Ingestion:**
   * If a single source (e.g., Reddit API) fails due to rate limits or network issues, log the error and continue executing the remaining scrapers. Never crash the entire ETL run for one failing feed.
2. **Explicit Exception Logging:**
   * Always wrap scraper and API calls in `try-except` blocks with informative error logging:
     ```python
     import logging
     
     try:
         results = fetch_reviews(...)
     except Exception as e:
         logging.error(f"[PlayStore Ingestion Error] Failed to fetch reviews: {str(e)}")
         results = []
     ```
3. **LLM Schema Fallback & Validation:**
   * Validate LLM JSON outputs using Pydantic `ValidationError`.
   * If LLM returns an invalid payload, retry once with a retry-prompt or log to an `unparsed_logs` table rather than stopping the batch.

---

## 5. Non-Monetary Guardrail Policy (BANNED PATTERNS)

This project has a strict **zero monetary incentive** constraint.

* **BANNED IN LLM OUTPUTS:** Never classify solutions or root causes as "Give a 10% discount", "Issue a coupon", "Price too high", "Offer cashback", or "Drop prices".
* **RE-ATTRIBUTION PATTERN:** If a user complains about price in raw text (e.g. *"Too expensive for this top"*), the AI classifier MUST re-attribute the friction to **Value Perception / Quality Doubt / Lack of Fabric Clarity** rather than price itself.
  * *Raw:* "Not worth 1500 rupees for this polyester shirt."
  * *Correct Classification:* `Fabric / Quality Doubt` + `Unclear Value Proposition`.

---

## 6. Code Style & Antipatterns

* **NO Hardcoded Credentials:** Store API keys in environment variables or `.env` file (`OPENAI_API_KEY`, `REDDIT_CLIENT_ID`).
* **NO Raw Unstructured Text in DB:** All stored insights must pass through the cleaner and schema validator.
* **NO Over-Complicated Orchestrators:** Do NOT introduce complex multi-agent frameworks (e.g. AutoGen, CrewAI) if standard Python functions with Pydantic + OpenAI calls suffice. Keep the execution linear and predictable.
* **NO Silent Failures:** Never write empty `except:` blocks (`pass`). Always log or handle exceptions explicitly.
