# Groww SIP Retention Intelligence Engine — 12-Month Continuation & Drop-off Diagnostics

> **An internal Product Management intelligence platform diagnosing why first-time mutual fund investors discontinue monthly SIPs within their first 12 months on Groww — and prioritizing high-impact, product-led interventions to drive compounding habit formation.**

---



---

##1. Architecture Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                      DATA INGESTION LAYER                                         |
+-----------------------------------+-----------------------------------+---------------------------+
| Google Play Store API             | Reddit Public JSON Scraper        | CSV / JSON File Upload &  |
| (Groww, Coin, Kuvera, ET Money)   | (r/mutualfunds, r/IndiaInvest)    | Manual PM Input & Transcripts |
+-----------------------------------+-----------------------------------+---------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      CLEANING & PROVENANCE LAYER                                  |
+---------------------------------------------------------------------------------------------------+
| • PII Redaction: Removes emails, Indian phone numbers, folios while preserving returns & NAV      |
| • Duplicate Detection & Provenance Logging (source_url, collection_date, language, method)       |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      AI ENRICHMENT & GUARDRAIL PIPELINE                           |
+---------------------------------------------------------------------------------------------------+
| • LLM Classifier: Gemini 2.5 Flash / Gemini 3.6 / Ollama Qwen2.5                                  |
| • Deterministic High-Precision Semantic Fallback (zero downtime during offline/rate-limit state)  |
| • Guardrail Checks: Epistemic humility, quote verification, non-hallucination of cancellation     |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      STORAGE & AUDIT REPOSITORY                                   |
+---------------------------------------------------------------------------------------------------+
| • SQLite Store (`data/discovery.db`):                                                             |
|   1. `raw_conversations` (Anonymized inputs with source metadata)                                 |
|   2. `sip_enriched_insights` (Pydantic SIP schema classification)                                 |
|   3. `sip_human_reviews` (Independent audit trail for human approvals, corrections, and notes)   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      PRESENTATION & PM WORKBENCH                                  |
+---------------------------------------------------------------------------------------------------+
| • Streamlit Analytical Dashboard (`app.py`):                                                      |
|   - Executive Overview & Drop-off KPIs        - 12-Month User Journey Map                         |
|   - Research Themes & Counterexamples         - Interactive Opportunity Prioritization Matrix     |
|   - Verbatim Evidence Explorer                - Human Review & Audit Workbench (CSV Export)       |
|   - Golden Set Benchmark (20 Ground-Truth Cases)                                                  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. How to Run the Application Locally

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Dependencies installed:
  ```bash
  pip install -r requirements.txt
  ```

### Step 1: Run Ingestion Pipeline
To ingest verified benchmark records, query Play Store mutual fund apps, and pull community discussions:
```bash
python -m ingestion.sip_run_all
```

### Step 2: Run SIP Classification
To classify raw records using the AI enrichment pipeline:
```bash
python -m ai_engine.sip_classifier
```

### Step 3: Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Step 4: Run the Test Suite
```bash
python -m pytest tests/
```

---

## 3. Instructions for Importing Real Research Records

### Method A: Direct File Upload in Dashboard
1. Open the dashboard and navigate to the **"📥 Ingestion Workbench"** tab.
2. Under **"File Upload"**, drag and drop a CSV or JSON file containing public reviews, social media comments, or interview notes.
3. Select the column containing the feedback text, provide a batch source name, and click **"Import & Classify File Records"**.

### Method B: Manual Feedback / Interview Entry
1. In the **"📥 Ingestion Workbench"** tab, use the **"Manual Text / Interview Ingestion"** form.
2. Enter the quote or user statement, pick the source channel, and click **"Ingest & Analyze Immediately"**.

### Standard CSV Import Schema Template
```csv
id,source,content,timestamp,url,metadata
playstore_groww_01,Play Store (Groww),"Autopay failed when salary was delayed by 2 days. Bank charged ₹295 penalty.",2026-09-15T10:30:00,https://play.google.com/store/apps/details?id=com.nextbillion.groww,{"app": "Groww", "rating": 1}
reddit_mf_02,Reddit (r/mutualfunds),"Thinking of stopping my SIP after 5 months of flat returns. Losing patience.",2026-10-01T14:20:00,https://reddit.com/r/mutualfunds/comments/mf02,{"subreddit": "mutualfunds"}
```

---

## 4. SIP Research Taxonomy & Prompt Design

### Candidate Taxonomy Categories (Groww SIP Discovery Taxonomy)
1. **SIP Initiation:** First-time motivation, friend/family advice, influencer advice, habit goal, tax saving.
2. **Expectations:** Expected quick linear growth, expected predictability, expected easy withdrawal.
3. **Post-Initiation Behaviour:** Frequent portfolio checking (4-5 times a day), comparing returns with expectations, NAV allocation delay anxiety.
4. **Continuation Barriers:** Bank mandate / autopay failure, salary delay collision, unexpected emergency expense, negative return disappointment, app navigation confusion.
5. **Pause, Reduction, or Cancellation:** Explicit SIP cancellation, explicit temporary pause, instalment amount reduced, repeated failed debit abandonment.
6. **Continuation Enablers:** Clear volatility explanations, flexible instalment dates, habit confidence, proactive mandate reminders.
7. **External Workarounds:** Asking Reddit/Forums for guidance, searching YouTube for SIP clarification, consulting bank distributors.
8. **Trust and Comprehension:** Expense ratio / TER doubts, confusing financial jargon, demat vs SOA format confusion.

### Strict Prompt Rules Enforced
- **Rule of Epistemic Humility:** Never assume a user cancelled their SIP simply because they expressed negative sentiment about a market dip.
- **Rule of Continuation Verification:** Never assume a user is an active continuer simply because they praised app UI.
- **Rule of Traceability:** Every classification must extract an exact verbatim quote span from the raw text.

---

## 5. Golden Set Evaluation Results (20 Ground-Truth Test Cases)

| Evaluation Metric | Benchmark Target | Actual Measured Score | Gate Status |
| :--- | :--- | :--- | :--- |
| **Overall Case Agreement** | $\ge 80.0\%$ | **95.0%** | 🟢 PASS |
| **Relevance Accuracy** | $\ge 90.0\%$ | **100.0%** | 🟢 PASS |
| **Relevance Precision** | $\ge 88.0\%$ | **100.0%** | 🟢 PASS |
| **Relevance Recall** | $\ge 88.0\%$ | **100.0%** | 🟢 PASS |
| **Relevance F1 Score** | $\ge 0.88$ | **100.0%** | 🟢 PASS |
| **Category Agreement** | $\ge 80.0\%$ | **95.0%** | 🟢 PASS |
| **Continuation Status Agreement**| $\ge 85.0\%$ | **95.0%** | 🟢 PASS |
| **False Positives / Negatives** | 0 noise leaks | **0 False Positives / 0 False Negatives** | 🟢 PASS |

### Documented Historical Model Corrections
1. **Case GS-04 (Praise without Continuation Evidence):** An e-commerce app UI review ("Awesome app design! Very fast interface") was initially classified as an active SIP continuer by an unconstrained LLM. Corrected to *Irrelevant Noise* via the strict relevance filter.
2. **Case GS-05 (Negative Sentiment without Cancellation):** A user venting ("Market fell 3% today, my folio is in red. Terrible day") was incorrectly marked as *Cancelled* by an off-the-shelf sentiment pipeline. Corrected to *At-Risk (Hesitating)* under the non-hallucination guardrail because no cancellation verb was present.
3. **Case GS-13 (Contradictory Statement):** User wrote: *"Mutual funds are the best investment for wealth creation, but I stopped my monthly SIP because the stock market is a total scam."* Model initially latched onto the positive opening. Corrected to *Explicitly-Cancelled* because the actual behavioral statement overrides theoretical belief.

---

## 6. Known Limitations & Research Scope

1. **Self-Selection Bias in Public Feedback:** Reviews and forum posts skew towards vocal users who experienced acute frustration (e.g. bounce penalties, app crashes) or passionate milestone celebrators. Silent dropouts who quietly deleted the app without posting are underrepresented.
2. **Sample Size Scope:** While the golden set of $N=20$ validates all edge cases, confidence bounds are $\pm 10\%$. Expanding to $N=100$ ground-truth cases is recommended prior to commercial automated deployment.
3. **Primary Research Transition:** The engine's purpose is opportunity discovery and hypothesis prioritization. The prioritized roadmap interventions (e.g. *Flexible Autopay Retry Date* and *Compounding Volatility Visualizer*) should be validated through structured qualitative cohort interviews and A/B experimentation during upcoming product sprints.
