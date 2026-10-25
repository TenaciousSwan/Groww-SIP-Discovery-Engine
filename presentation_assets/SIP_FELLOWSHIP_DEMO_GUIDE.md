# 12-Month SIP Continuation AI Discovery Engine — PM Fellowship Demo Guide

## 1. Problem & Objective
* **Business Objective:** Increase the percentage of first-time mutual fund investors in India who maintain an active SIP 12 months after starting their first SIP (defined as having at least one successful instalment in the last 30 days).
* **Research Core Question:** Why do first-time investors start SIPs with good intentions, but later pause, reduce, cancel, or abandon them?
* **Common Misconception vs Reality:** Industry observers assume dropouts occur solely because "markets fell." Our research engine reveals operational friction, rigid mandate dates, ECS penalty traps, and settlement confusion often cause discontinuation before market returns even matter.

---

## 2. Walkthrough & Demo Script (Tab by Tab)

### Tab 0: Executive Overview
* **Point out:** The KPI banner showing total signals, mandate failure proportion, at-risk investors, and explicit dropouts.
* **Highlight:** The top friction categories chart (Continuation Barriers vs Expectations vs Trust & Comprehension).
* **Key Finding:** *The Bank Mandate & Salary Delay Trap* — salaries arrive 24–48 hours late, causing fixed autopay debits to bounce, triggering ₹250–₹350 bank penalties. This administrative shock directly drives investors to cancel their SIPs.

### Tab 1: Research Themes & Counterexamples
* **Point out:** The synthesized themes aggregated across distinct platforms.
* **Highlight:** The **Counterexample box** for each major theme (e.g., investors who completed 12 months by scheduling SIP debits 2 days after salary and turning off daily portfolio notifications).
* **Emphasize Epistemic Humility:** The research notes explain the limitations of public feedback without overgeneralizing to all Indian investors.

### Tab 2: 12-Month User Journey
* **Point out:** The chronological map from *Before starting* $\rightarrow$ *Early months (1–3)* $\rightarrow$ *Mid-year (4–8)* $\rightarrow$ *Approaching month 12* $\rightarrow$ *Continuation / Cancellation*.
* **Highlight:** How friction changes over time: Early months suffer from daily NAV check anxiety; mid-year suffers from emergency cashflow shocks.

### Tab 3: Opportunity Prioritization Matrix
* **Point out:** The interactive bubble chart plotting Frequency (%) vs UX Addressability, with bubble size indicating the multi-dimensional Composite Score.
* **Demonstrate:** Expand the weight sliders (`w_severity`, `w_12m`, `w_addressability`) and show how PM priorities can be tested dynamically.
* **Top Opportunity:** *Proactive Mandate Failure Alert & 1-Tap UPI Re-authorization* with zero penalty reassurance.

### Tab 4: Evidence Explorer
* **Point out:** The search bar and live cards tracing every insight back to verbatim quotes, source URLs, timestamps, and confidence scores.
* **Highlight:** No fabricated quotes or phantom demographic claims.

### Tab 5: Human Review & Audit Workbench
* **Point out:** How a PM fellow can inspect records flagged with `needs_human_review = True`, approve, correct category or status, and log reviewer notes.
* **Demonstrate:** Show the separate storage of human corrections in `sip_human_reviews` table and the "Export Reviewed Findings to CSV" button.

### Tab 6: AI Quality & Golden Set
* **Point out:** The 20-case ground-truth benchmark covering edge cases (ambiguous finance, positive praise without continuation evidence, negative sentiment without cancellation, compounding problems).
* **Highlight:** 95.0% Overall Case Agreement, 100% Relevance Accuracy, 0 False Positives, and documented actual human corrections.

### Tab 7: Ingestion Workbench
* **Demonstrate:** The drag-and-drop CSV / JSON uploader, the instant manual text entry form, and the downloadable sample CSV template.
