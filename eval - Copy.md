# Evaluation Framework & Test Metrics (`eval.md`)

This document defines the evaluation criteria, validation benchmarks, test suites, and target accuracy metrics for each phase of the **Myntra Wishlist Conversion AI Discovery Engine**.

---

## Evaluation Philosophy
To ensure the AI Discovery Engine generates reliable, high-integrity product insights for Growth Product Managers, every phase must pass strict automated tests and qualitative spot-checks before proceeding to the next.

```
+--------------------------+      +--------------------------+      +--------------------------+
|      PHASE 1 EVAL        |      |      PHASE 2 EVAL        |      |      PHASE 3 EVAL        |
| Data Ingestion Quality   | ---> |  LLM Schema Precision    | ---> | PM Dashboard Integrity   |
| • Noise & PII Filtering  |      | • Accuracy & Precision   |      | • Pareto & Opportunity   |
| • Multi-Channel Yield    |      | • Non-Monetary Guardrail |      | • UX Responsiveness      |
+--------------------------+      +--------------------------+      +--------------------------+
```

---

## Phase 1 Evaluation: Data Ingestion & Pre-Filtering Engine

### 1. Key Performance Indicators (KPIs)

| Evaluation Metric | Target Benchmark | Verification Method |
| :--- | :--- | :--- |
| **Ingestion Yield** | ≥ 200 clean entries per pipeline run | Row count query in `data/discovery.db` (`raw_conversations`) |
| **Keyword Relevance Rate** | ≥ 90% relevant to fashion hesitation | Manual spot check of 30 random raw records |
| **PII Anonymization** | 100% zero usernames, emails, or links | Regex audit scanner looking for `@`, `http://`, `https://` |
| **Deduplication Rate** | 100% unique MD5 content hashes | `COUNT(DISTINCT content_hash) == COUNT(*)` test in SQLite |
| **Graceful Degradation** | 100% uptime when 1 source API fails | Mock API timeout test on Reddit scraper; verify PlayStore succeeds |

### 2. Automated Test Suite (`tests/test_phase1_eval.py`)

```python
def test_pii_removal():
    raw_text = "Check out my review @john_doe on http://myntrasite.com! Size M was too tight."
    cleaned_text = clean_raw_text(raw_text)
    assert "@" not in cleaned_text
    assert "http" not in cleaned_text
    assert "Size M was too tight." in cleaned_text

def test_deduplication_hash():
    entry1 = "Size S was too tight on Myntra top"
    entry2 = "size s was too tight on myntra top"  # Same normalized text
    assert compute_content_hash(entry1) == compute_content_hash(entry2)
```

---

## Phase 2 Evaluation: AI Enrichment & Schema Mapping

### 1. Key Performance Indicators (KPIs)

| Evaluation Metric | Target Benchmark | Verification Method |
| :--- | :--- | :--- |
| **Schema Extraction Precision** | ≥ 88% overall precision | Benchmark against 50 manually human-annotated sample feedback entries |
| **Intent Classification Accuracy** | ≥ 90% accuracy | Intent split accuracy (Genuine Purchase vs. Bookmarking/Inspiration) |
| **Non-Monetary Guardrail Compliance** | **100% Zero monetary suggestions** | Automated audit script scanning `enriched_insights` for banned keywords |
| **Schema Validation Rate** | ≥ 98% valid Pydantic outputs | Ratio of successfully parsed JSON vs. `unparsed_logs` |
| **Hinglish Understanding Rate** | ≥ 85% correct categorization | Test suite containing 20 vernacular Hinglish inputs |

### 2. Non-Monetary Guardrail Audit Script (`tests/test_guardrails_eval.py`)

```python
BANNED_MONETARY_TERMS = ["discount", "coupon", "price drop", "cashback", "cheaper", "offer code"]

def test_non_monetary_guardrail_enforcement():
    raw_input = "The price is 2000 INR, too expensive, give 20% discount!"
    enriched_output = run_llm_classifier(raw_input)
    
    # Verify primary friction is re-attributed to quality/value, NOT price
    assert enriched_output.primary_friction in ["Fabric / Quality Doubt", "Unclear Value Proposition"]
    
    # Verify no monetary terms are present in the quote summary or recommendation
    for term in BANNED_MONETARY_TERMS:
        assert term not in enriched_output.quote_summary.lower()
```

### 3. Precision Matrix Benchmark (Human Annotated Ground Truth)

```
                       Predicted: Fit Uncertainty   Predicted: Fabric Doubt
Actual: Fit Uncertainty           42                            3
Actual: Fabric Doubt               2                           38
```

---

## Phase 3 Evaluation: PM Analytics Workbench & Dashboard

### 1. Key Performance Indicators (KPIs)

| Evaluation Metric | Target Benchmark | Verification Method |
| :--- | :--- | :--- |
| **Pareto Distribution Integrity** | 100% mathematical accuracy | SQL aggregation check: Sum of top 20% categories == reported Pareto cumulative % |
| **External Dependency Index** | Accurate % calculation | Verification of formula: `(Count(External Seeking == True) / Total) * 100` |
| **Dashboard UI Latency** | < 1.5 seconds rendering time | Streamlit execution profiler (`streamlit run app.py --logger.level=debug`) |
| **Actionable Concept Quality** | Top 3 non-monetary PM concepts | Qualitative PM review against Myntra strategic goals |

### 2. End-to-End Evaluation Test Suite (`tests/test_phase3_eval.py`)

```python
def test_external_dependency_index_calculation():
    # Insert 10 mock records (4 with external_seeking = True)
    df = load_mock_enriched_insights(total=10, external_seeking_count=4)
    index = calculate_external_dependency_index(df)
    assert index == 40.0  # Must equal exactly 40.0%

def test_pareto_sum():
    df = load_mock_enriched_insights()
    pareto_df = compute_pareto_distribution(df)
    assert pareto_df['cumulative_percentage'].iloc[-1] == 100.0
```

---

## Phase-by-Phase Sign-Off Gate

Before promoting code from one phase to the next, the team must run and pass the evaluation gate:

```bash
# Phase 1 Gate
python -m pytest tests/test_phase1_eval.py

# Phase 2 Gate
python -m pytest tests/test_phase2_eval.py

# Phase 3 Gate
python -m pytest tests/test_phase3_eval.py
```
