# Implementation Plan: AI-Powered Discovery Engine (Phased Build)

## Project Overview
This document serves as the execution roadmap for building the **Myntra Wishlist Conversion AI Discovery Engine**. The build is divided into 3 modular, testable phases. Each phase has a self-contained deliverable that can be tested in isolation before moving to the next.

---

## Phase 1: Data Ingestion & Pre-Filtering Engine
**Goal:** Build and validate the multi-source data extraction pipeline that pulls raw public feedback (Play Store, Reddit, YouTube) and filters for wishlist conversion signals.

### Tasks & Deliverables:
1. **Play Store Scraper Module (`ingestion/playstore.py`):**
   * Implement `google-play-scraper` to pull recent Myntra app reviews.
   * Filter reviews based on key intent terms (`wishlist`, `saved`, `size`, `fit`, `quality`, `confused`, `doubt`, `return`).
2. **Reddit Scraper Module (`ingestion/reddit.py`):**
   * Integrate Reddit PRAW / API to fetch posts and comments from `r/IndianFashionAddicts`, `r/ShoppingDeals`, and `r/DesiFragranceAddicts`.
   * Search for threads discussing Myntra hauls, sizing issues, and decision hesitation.
3. **Data Normalization & Anonymization (`ingestion/cleaner.py`):**
   * Strip PII (usernames, emails, links).
   * Save raw structured records into SQLite database (`data/discovery.db` -> table `raw_conversations`).

### Phase 1 Verification Checklist:
* [ ] Can run `python ingestion/run_all.py` and output 200+ clean, pre-filtered records into `data/discovery.db`.
* [ ] Zero PII present in output records.
* [ ] Raw feedback covers all target channels (Play Store, Reddit, YouTube).

---

## Phase 2: AI Enrichment Pipeline & Schema Mapping
**Goal:** Build the LLM classification engine that processes raw feedback and structures it into actionable PM taxonomy attributes (Intent, Friction Category, External Seeking Behavior, Severity).

### Tasks & Deliverables:
1. **Taxonomy Schema & Prompt Definition (`ai_engine/schema.py` & `ai_engine/prompts.py`):**
   * Define Pydantic schema for structured output (JSON Mode / Function Calling).
   * Formulate system prompt instructing LLM to extract intent, friction cause, decision outcome, and external validation behavior.
2. **LLM Execution Engine (`ai_engine/classifier.py`):**
   * Connect OpenAI API (`gpt-4o` / `gpt-4o-mini`) or Claude API to process batch records.
   * Store structured results into SQLite (`data/discovery.db` -> table `enriched_insights`).
3. **Non-Monetary Guardrail Filter (`ai_engine/guardrails.py`):**
   * Ensure any feedback or generated suggestion strictly excludes discount/coupon/monetary requests, re-attributing friction to clarity, trust, fit, or UX gaps.

### Phase 2 Verification Checklist:
* [ ] Run `python ai_engine/classifier.py` on 100 sample raw entries.
* [ ] Achieve >85% accuracy on schema classification evaluated on a 20-sample spot check.
* [ ] Verify that non-monetary attribution properly translates price resistance into value/trust/fit uncertainty.

---

## Phase 3: Analytics Workbench & PM Insights Dashboard
**Goal:** Deliver an interactive Streamlit dashboard that synthesizes all extracted data into visual charts, opportunity matrices, and prioritized non-monetary product concepts.

### Tasks & Deliverables:
1. **Analytics Engine (`analytics/metrics.py`):**
   * Compute Pareto distribution of primary friction causes.
   * Calculate External Seeking Index (% of users leaving Myntra for external validation like YouTube/Reddit).
   * Calculate Severity Score x Frequency matrix to highlight top opportunity areas.
2. **Streamlit UI (`app.py`):**
   * **Tab 1: Executive Summary:** Top friction points, wishlist intent split (genuine purchase vs. bookmarking).
   * **Tab 2: Deep Dive Friction Explorer:** Filter feedback by category (e.g., Fit/Size Uncertainty, Fabric Doubt, Style Mismatch).
   * **Tab 3: Non-Monetary Product Solutions:** Automated mapping of top friction areas to candidate non-monetary UX/product features.

### Phase 3 Verification Checklist:
* [ ] Launch Streamlit dashboard (`streamlit run app.py`).
* [ ] Filter insights by friction category and source.
* [ ] Produce top 3 non-monetary growth recommendations backed by raw user evidence.

---

## Summary Roadmap

```
+------------------------------------+
|  Phase 1: Ingestion & Filtering    |  <-- Pull 200+ raw records from Play Store, Reddit, YouTube
+------------------------------------+
                  |
                  v
+------------------------------------+
|  Phase 2: AI Enrichment Pipeline   |  <-- Extract JSON schema (Friction, Intent, External Seeking)
+------------------------------------+
                  |
                  v
+------------------------------------+
|  Phase 3: PM Analytics Workbench   |  <-- Interactive Streamlit UI with Non-Monetary Solutions
+------------------------------------+
```
