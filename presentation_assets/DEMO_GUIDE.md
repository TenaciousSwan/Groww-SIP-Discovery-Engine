# AI Discovery Engine - Demo Guide

## Problem
Millions of users browse fashion products and save them to their wishlists, but fail to purchase them within 30 days. As a PM, understanding the *non-monetary* reasons behind this drop-off (wishlist → purchase conversion) is critical for driving Growth without relying on discounts.

## Input
The engine ingests unstructured, user-generated evidence. Currently, this includes:
- App Store / Play Store Reviews
- Reddit Conversations
- YouTube Comments

## Processing
The system acts as a structured discovery pipeline:
1. **Extract:** AI identifies relevant behavioural signals from raw text.
2. **Classify:** AI maps these signals to abandonment barriers (e.g., Size-Doubt, Occasion-Not-Yet).
3. **Cluster:** Recurring themes are grouped together.
4. **Prioritise:** The Opportunity Scorer ranks these barriers based on frequency and severity.

## Output
The PM receives a prioritised list of Growth hypotheses backed by user evidence, highlighting exactly what behavioural friction is preventing purchases.

---

## Demo Journey
*Follow these exact steps when presenting the dashboard:*

1. **Open the Dashboard:** Start at the top of the page. Point to the header text: *"An AI-powered discovery system that converts unstructured user evidence into prioritised behavioural insights and testable Growth opportunities."*
2. **Explain the Funnel:** Scroll to the top metrics. Show how we started with hundreds of raw signals, and the AI distilled them down to genuine behavioural insights.
3. **Highlight the Opportunity Scorer:** Scroll down to the **"Top Unmet Needs & Feature Opportunities"** section. Explain that the AI isn't just listing complaints; it is grouping them and suggesting product gaps.
4. **Focus on Non-Monetary Friction:** Scroll to the **"Postponement Triggers"** chart. Point out the behavioural triggers like `Size-Doubt` or `Wants-More-Reviews` as clear examples of Product Confidence Gaps.
5. **Read the Raw Evidence:** Expand one of the dataframes or look at the recent signals table at the bottom to prove that the AI classification matches real user statements.

---

## Strongest Insight (Example)

**The Barrier:** Product Confidence Gap / Lack of Social Proof
- **Evidence:** Users frequently indicate they are waiting to see more reviews or are unsure about the fit ("Size-Doubt", "Wants-More-Reviews").
- **PM Interpretation:** Wishlisting represents high interest, but the user lacks the necessary context to feel confident in the purchase. The barrier is informational and psychological, not financial.
- **Opportunity:** The Growth team should test improving product visualization, adding fit-context information, or highlighting user-generated reviews directly in the wishlist view to bridge the confidence gap.
