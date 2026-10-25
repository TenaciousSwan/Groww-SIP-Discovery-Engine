# Edge Cases & Failure Recovery Specification

This document defines corner scenarios, failure modes, data anomalies, and edge cases across the entire pipeline, along with explicit recovery mechanisms for each.

---

## 1. Phase 1: Data Ingestion & Pre-Filtering Edge Cases

### 1.1 Store Review / Platform Scraping API Rate Limits & Blocks
* **Scenario:** Google Play Store, Reddit API (PRAW), or YouTube API throttles requests or temporarily blocks IP due to volume limits.
* **Impact:** Ingestion fails mid-execution, leading to incomplete or biased dataset collection.
* **Handling Strategy:**
  * Implement exponential backoff retry logic (3 retries with random jitter between 2 to 10 seconds).
  * Enforce graceful degradation: If one platform fail-stops, log the error explicitly and proceed with available platforms. Do NOT fail the entire ETL run.
  * Store checkpoint state in SQLite (`ingestion_logs` table) so failed runs resume from the last successful timestamp/page.

### 1.2 Empty, Multilingual, or Emoji-Only User Feedback
* **Scenario:** Reviews containing only emojis (e.g., "🔥🔥🔥"), non-English/Hinglish text (e.g., "size fit nahi hua return kar diya"), or single-word entries ("nice", "bad").
* **Impact:** Downstream LLM token wastage or false-positive schema extractions.
* **Handling Strategy:**
  * **Text Length Threshold:** Drop any raw entry with character count < 15 characters before LLM processing.
  * **Language Normalization:** Retain Hinglish and vernacular inputs, as they contain high-intent friction signals ("size badla", "kapda patla hai"). Instruct the LLM prompt in Phase 2 to translate and process Hinglish natively into English taxonomy fields.
  * **Emoji Stripping:** Clean excessive repetitive emojis using regex while retaining text payload.

### 1.3 High-Volume Duplicate / Bot Feedback
* **Scenario:** Bot spam or identical duplicate reviews across multiple listings ("Great product buy now").
* **Impact:** Skews frequency metrics in the Pareto distribution.
* **Handling Strategy:**
  * Deduplicate raw entries by computing an MD5 content hash (`hashlib.md5(text.lower().strip().encode())`).
  * Reject duplicate content hashes within a 30-day sliding window in `raw_conversations`.

---

## 2. Phase 2: AI Enrichment & LLM Processing Edge Cases

### 2.1 User Explicitly Demands Monetary Incentives / Price Cuts
* **Scenario:** Raw user feedback explicitly states: "Give 50% discount", "Too expensive, make it cheaper", or "Provide promo codes".
* **Impact:** Violates the non-monetary constraint if passed through or recommended.
* **Handling Strategy:**
  * Apply the **Re-Attribution Guardrail Engine** (`ai_engine/guardrails.py`).
  * Price/Discount complaints MUST be mapped to non-monetary root causes:
    * *"Too expensive"* -> `Fabric / Quality Doubt` or `Unclear Value Proposition`.
    * *"Need discount"* -> `Comparison Friction` or `Lack of Social Proof`.
  * The guardrail logic strips monetary recommendations from final PM outputs.

### 2.2 LLM Output Schema Malformation / Invalid JSON
* **Scenario:** The LLM returns invalid JSON, missing required Pydantic keys (e.g., missing `friction_category`), or hallucinated keys.
* **Impact:** Schema validation failure (`pydantic.ValidationError`), causing processing script to crash.
* **Handling Strategy:**
  * Catch `ValidationError` explicitly.
  * Attempt one automated repair retry with a fallback prompt emphasizing strict JSON formatting.
  * If the retry fails, store the item in an `unparsed_logs` table with status `FAILED_SCHEMA` and continue batch execution.

### 2.3 Ambiguous or Multi-Friction Feedback
* **Scenario:** A user review mentions multiple friction points simultaneously (e.g., "Size S was too tight, material feels cheap, and styling looked totally different from model photo").
* **Impact:** Forcing a single categorical output loses critical sub-signals.
* **Handling Strategy:**
  * Define `primary_friction` (enum) AND `secondary_frictions` (list of enums) in the Pydantic schema (`ai_engine/schema.py`).
  * Calculate opportunity impact scores using weighted values: Primary Friction = 1.0, Secondary Friction = 0.5.

---

## 3. Phase 3: Analytics & Dashboard UI Edge Cases

### 3.1 Zero Data or Low Ingestion Sample Size
* **Scenario:** New pipeline setup or heavy filtering results in < 20 processed records in `enriched_insights`.
* **Impact:** Statistical metrics (Pareto distribution, External Dependency Index) become misleading or mathematically invalid.
* **Handling Strategy:**
  * Display a warning banner in Streamlit: *"Low sample size (< 50 items). Statistical confidence is low."*
  * Suppress percentage-based charts when N < 30; display absolute counts instead.

### 3.2 High Ratio of External Seeking Behavior (Outlier Spike)
* **Scenario:** A sudden viral Reddit thread or YouTube haul causes 90%+ of ingested records to report external platform reliance (YouTube/Reddit).
* **Impact:** Distorts baseline metrics for external dependency.
* **Handling Strategy:**
  * Calculate a 7-day rolling baseline for `External Dependency Index`.
  * Flag statistical anomalies (e.g., > 2 standard deviations from rolling mean) with an alert tag: *"Platform Spike Detected from Source: Reddit"*.

---

## 4. Summary Matrix of Edge Cases

| Phase | Edge Case Scenario | Risk Level | Mitigation Mechanism |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Scraper API Rate Throttling | Medium | Exponential backoff + per-source error boundaries |
| **Phase 1** | Bot Spam & Exact Duplicates | High | MD5 content hashing & sliding deduplication window |
| **Phase 2** | User Demands Discounts/Coupons | Critical | Re-attribution engine -> converts to Value/Quality/Fit gap |
| **Phase 2** | Malformed LLM JSON Output | Medium | Pydantic validation retry + fallback queue |
| **Phase 3** | Sample Size < 30 Items | Low | UI warning banner + absolute counts display |
