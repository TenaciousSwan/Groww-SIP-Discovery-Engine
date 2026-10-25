# Problem Statement & Engine Goals: Groww 12-Month SIP Continuation

## 1. Executive Summary & Core Challenge
* **Product Initiative:** Groww Mutual Funds Squad Initiative — Diagnosing and Improving 12-Month SIP Continuation Among First-Time Mutual Fund Investors.
* **Target Application:** Groww (`com.nextbillion.groww` — India's largest retail investment platform).
* **The Business Objective:** Increase the percentage of first-time mutual fund investors on Groww who still maintain an active SIP 12 months after starting their first SIP.
* **Metric Definition of Active SIP:** At least one successful monthly SIP instalment completed in the last 30 days.

---

## 2. Research Hypothesis & Problem Investigation
Conventional fintech thinking assumes retail investors drop out because "the market fell." This AI discovery engine investigates the authentic root causes from real public evidence across:
* **Google Play Store Reviews for Groww** (`com.nextbillion.groww`)
* **Reddit Communities** (`r/mutualfunds`, `r/IndiaInvestments`, `r/personalfinanceindia`)
* **Public Investor Forums & Financial Discussion Threads**

### Critical Research Questions Addressed
1. **Why do investors start their first SIP on Groww?** (Habit goal, family/peer influence, social media influencers, tax-saving ELSS).
2. **What expectations do they enter with?** (Expectation of quick linear growth, predictability, easy withdrawal vs long-term equity compounding).
3. **What happens post-initiation?** (Checking Groww portfolio 4–5 times a day, panic on first red market dip, NAV allotment confusion).
4. **Why do they pause, reduce, or cancel?** (Salary delay colliding with fixed SIP date, bank ECS bounce penalties of ₹250–₹350, unexpected emergency expenses, rigid 48-hour skip rule).
5. **Where do they seek workarounds?** (Leaving Groww to ask on Reddit, searching YouTube explainers, moving to direct AMC portals/MF Central).
6. **What enables long-term continuation?** (Salary-aligned debit dates, automated habit discipline, turning off daily market notification noise).

---

## 3. Product & Non-Monetary Guardrails
* **No Reliance on Artificial Cashbacks or Subsidies:** The solution must be product-led, educational, and operational.
* **Strict Epistemic Humility:** Negative sentiment must NOT be assumed to be cancellation unless explicitly stated in text.
* **Full Verbatim Traceability:** Every insight links directly to raw user quotes, source URLs, timestamps, and confidence scores.

---

## 4. Current Dataset Footprint (data/discovery.db)
* **Total Records Ingested:** 1,873 records (scrubbed of PII and deduplicated).
* **Relevant Groww SIP Signals:** 887 verified records across 1★ to 5★ ratings and community discussions.
* **Primary Drop-off Friction:** Bank Mandate / Autopay Failures and Salary Delay Penalties (#1 operational blocker).
* **Golden Set Agreement:** 95.0% agreement against 20 ground-truth edge case benchmarks.
