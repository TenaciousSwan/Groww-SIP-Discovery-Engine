# Architecture Specification: AI-Powered Discovery Engine

## 1. Executive Summary
This document outlines the technical architecture for the **Myntra Wishlist Conversion AI Discovery Engine**. The system continuously ingests unstructured feedback across public digital channels (Play Store, Reddit, YouTube), processes the data through an LLM classification pipeline, and renders actionable, non-monetary growth insights into an analytical dashboard.

---

## 2. System Architecture Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                      DATA INGESTION LAYER                                         |
+-----------------------------------+-----------------------------------+---------------------------+
| Google Play Store API             | Reddit API / PRAW Scraper         | YouTube Data API v3       |
| (App Reviews & Ratings)           | (r/IndianFashionAddicts, etc.)    | (Comment Threads & Hauls) |
+-----------------------------------+-----------------------------------+---------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      INGESTION & QUEUE LAYER                                      |
+---------------------------------------------------------------------------------------------------+
| • Python / FastApi ETL Workers                                                                    |
| • Pre-filtering Engine (Keyword Matching: 'wishlist', 'size', 'fit', 'quality', 'confused')       |
| • Deduplication & Anonymization Engine (PII Removal)                                             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      AI ENRICHMENT PIPELINE                                       |
+---------------------------------------------------------------------------------------------------+
| • Primary Classifier: OpenAI GPT-4o / Claude 3.5 Sonnet API                                       |
| • Prompt Template Engine (Structured JSON Output via Function Calling)                            |
| • Schema Mapping: Intent, Friction Category, Decision Stage, External Search Triggers             |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                       STORAGE & ANALYTICS                                         |
+---------------------------------------------------------------------------------------------------+
| • Relational Store: PostgreSQL / SQLite (Structured Feedbacks & Classified Schema)                 |
| • Analytics Store: DuckDB / Pandas DataFrames (Aggregated Metrics & Opportunity Scoring)          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      PRESENTATION & CONSUMPTION                                   |
+---------------------------------------------------------------------------------------------------+
| • Interactive Dashboard: Streamlit / React Web App                                                |
| • PM Insights Workbench: Root Cause Breakdown, Opportunity Frequency Chart, Non-Monetary Ideation |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Layer-by-Layer Technical Stack

### A. Data Ingestion Layer
* **Sources:**
  * **Play Store:** `google-play-scraper` (Python library for fetching official store reviews).
  * **Reddit:** `PRAW` (Python Reddit API Wrapper) targeting channels like `r/IndianFashionAddicts`, `r/DesiFragranceAddicts`, `r/ShoppingDeals`.
  * **YouTube:** `youtube-transcript-api` and `google-api-python-client` targeting popular Myntra try-on hauls and review channels.
* **Pre-Processing Rules:**
  * Clean whitespace, remove emojis/links, drop duplicates by content hash.
  * Keyword filter: Must match intent keywords (`wishlist`, `saved`, `buy later`, `confused`, `fit`, `size`, `return`, `quality`, `fabric`, `try-on`).

### B. AI Enrichment Pipeline
* **LLM Engine:** OpenAI API (`gpt-4o-mini` for batch pre-filtering, `gpt-4o` / `claude-3-5-sonnet` for deep semantic schema mapping).
* **Taxonomy Schema Mapping:**
  ```json
  {
    "feedback_id": "STRING",
    "source": "PlayStore | Reddit | YouTube",
    "wishlist_intent": "Genuine Purchase Intent | Bookmarking / Inspiration | Price Tracking",
    "friction_category": "Fit / Size Uncertainty | Fabric / Quality Doubt | Styling / Occasion Mismatch | Lack of Social Validation | Choice Overload",
    "external_seeking_behavior": true,
    "external_platform_mentioned": "YouTube | Reddit | Instagram | None",
    "decision_outcome": "Postponed | Abandoned | Bought Elsewhere",
    "quote_summary": "STRING",
    "severity_score": "1-5"
  }
  ```

### C. Database & Data Model
* **Database System:** PostgreSQL (Production) / SQLite (Local MVP).
* **Core Tables:**
  1. `raw_conversations`: ID, Source, Timestamp, Raw Text, Author Hash.
  2. `enriched_insights`: ID, RawID, Intent, FrictionCategory, ExternalSeeking, Outcome, Severity, ProcessedAt.
  3. `opportunity_aggregates`: FrictionCategory, OccurrenceCount, AverageSeverity, TrendDirection.

### D. Presentation & User Interface
* **Frontend Framework:** Streamlit (Python-native rapid prototyping) or React dashboard.
* **Key Visualizations:**
  * **Friction Breakdown:** Pareto chart showing top reasons users stall on wishlisted items.
  * **External Dependency Index:** Percentage of users who leave Myntra to validate fit/quality before buying.
  * **Opportunity Prioritization Matrix:** Frequency vs. Impact grid for PM feature planning.

---

## 4. Key Data Flows

1. **Ingestion Flow:** Cron job triggers ingestion scrapers every 24 hours -> Fetches raw posts/reviews -> Filters for relevant keywords -> Saves to `raw_conversations`.
2. **AI Enrichment Flow:** Ingestion pipeline triggers batch job -> Batches 50 raw items -> Sends prompt payload to LLM -> Receives structured JSON -> Validates against Pydantic schema -> Saves to `enriched_insights`.
3. **Analytics Flow:** PM opens Streamlit dashboard -> Dashboard queries aggregated SQL metrics -> Displays real-time charts and top non-monetary leverage points.

---

## 5. Security, Constraints & Non-Monetary Scope Boundaries

* **Privacy & Compliance:** Strips all PII (user names, handles, locations, emails) prior to sending text to LLM endpoints.
* **Cost Efficiency:** Uses lightweight model (`gpt-4o-mini`) for initial keyword relevance scoring; reserves high-tier LLM for structured schema classification.
* **Non-Monetary Guardrail:** The system rejects inputs or proposals that suggest discounts, coupons, or price drops, filtering explicitly for product UX, information layout, fit clarity, and social proof.
