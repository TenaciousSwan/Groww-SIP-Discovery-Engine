"""
Golden Set & Ground-Truth AI Evaluation Framework for 12-Month SIP Continuation.
Adheres to Section 11 of the Fellowship Research Assignment.
Evaluates 20 representative test cases covering all edge cases, ambiguous inputs, and multi-label decisions.
"""

from typing import List, Dict, Any
from ai_engine.sip_classifier import classify_single_record

# ── 20 Curated Ground-Truth Cases ──────────────────────────────────────────────
GOLDEN_SET_CASES: List[Dict[str, Any]] = [
    {
        "case_id": "GS-01",
        "source_record_id": "playstore_groww_rev_101",
        "original_text": "Started my very first ₹2,000 monthly SIP in Nifty 50 after watching YouTube tutorials on wealth creation. The onboarding KYC was smooth, but I still feel nervous because I have never invested anywhere outside FD.",
        "expected_relevance": True,
        "expected_primary_category": "SIP Initiation",
        "expected_sub_category": "First-Time Motivation",
        "expected_continuation_status": "Active-Continuing",
        "expected_severity": "Low",
        "expected_uncertainty_handling": "Recognize beginner anxiety without assuming dropout",
        "edge_case_type": "Clear SIP-related onboarding feedback",
        "human_notes": "First-time investor driven by YouTube videos; anxious but actively investing."
    },
    {
        "case_id": "GS-02",
        "source_record_id": "playstore_groww_rev_108",
        "original_text": "Worst experience. My salary was delayed by 2 days, so on 5th the SIP autopay failed. HDFC bank charged me ₹295 for ECS return! The app should give a grace period or send a warning notification 24 hours prior.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Bank Mandate / Autopay Failure",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Severe barrier with high penalty, user has not yet explicitly cancelled",
        "edge_case_type": "Mandate execution failure with bank fee",
        "human_notes": "Operational friction where punitive fee creates high risk of discontinuation."
    },
    {
        "case_id": "GS-03",
        "source_record_id": "reddit_mf_post_211",
        "original_text": "I explicitly cancelled my ₹6,000 Parag Parikh Flexi Cap SIP yesterday after completing 7 months. The negative returns combined with continuous news of global recession made me panic. Sold my units at a ₹1,200 loss.",
        "expected_relevance": True,
        "expected_primary_category": "Pause, Reduction, or Cancellation",
        "expected_sub_category": "Explicit SIP Cancellation",
        "expected_continuation_status": "Explicitly-Cancelled",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Explicit cancellation verb supported by text",
        "edge_case_type": "Clear explicit cancellation at month 7",
        "human_notes": "Ground-truth cancellation due to mid-year market dip panic."
    },
    {
        "case_id": "GS-04",
        "source_record_id": "playstore_noise_119",
        "original_text": "Awesome app design! Very fast interface and dark mode looks cool.",
        "expected_relevance": False,
        "expected_primary_category": "Unrelated / General Financial Noise",
        "expected_sub_category": "Other / Unclear",
        "expected_continuation_status": "Unclear / Not-Stated",
        "expected_severity": "None",
        "expected_uncertainty_handling": "Positive sentiment must NOT be assumed as 12-month active continuation",
        "edge_case_type": "Positive sentiment without continuation evidence",
        "human_notes": "Generic UI compliment with zero SIP continuation signal. Must be marked irrelevant or unstated."
    },
    {
        "case_id": "GS-05",
        "source_record_id": "reddit_edge_222",
        "original_text": "Market fell 3% today, my folio is in red. Terrible day.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Negative Return Disappointment",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "Medium",
        "expected_uncertainty_handling": "Negative sentiment must NOT be assumed as cancellation",
        "edge_case_type": "Negative sentiment without cancellation evidence",
        "human_notes": "Investor is grumbling about market red day, but has NOT cancelled."
    },
    {
        "case_id": "GS-06",
        "source_record_id": "playstore_noise_120",
        "original_text": "Delivery charges on intraday options trading are too high. Zerodha Kite stuck during expiry trading.",
        "expected_relevance": False,
        "expected_primary_category": "Unrelated / General Financial Noise",
        "expected_sub_category": "Other / Unclear",
        "expected_continuation_status": "Unclear / Not-Stated",
        "expected_severity": "None",
        "expected_uncertainty_handling": "Correctly identify F&O/intraday equity noise and exclude from SIP sample",
        "edge_case_type": "Ambiguous/Trading financial noise unrelated to mutual fund SIP",
        "human_notes": "Options trading complaint, zero relevance to mutual fund SIP continuation."
    },
    {
        "case_id": "GS-07",
        "source_record_id": "playstore_noise_121",
        "original_text": "The shirt I bought was defective and size XL was too tight. Terrible delivery.",
        "expected_relevance": False,
        "expected_primary_category": "Unrelated / General Financial Noise",
        "expected_sub_category": "Other / Unclear",
        "expected_continuation_status": "Unclear / Not-Stated",
        "expected_severity": "None",
        "expected_uncertainty_handling": "E-commerce apparel noise rejection",
        "edge_case_type": "Completely irrelevant record",
        "human_notes": "Myntra/apparel leftover noise to ensure zero leakage into fintech dataset."
    },
    {
        "case_id": "GS-08",
        "source_record_id": "playstore_paytmmoney_rev_112",
        "original_text": "I paused my SIP for 3 months because I had to pay college fee for my brother. Glad the app allowed a clean pause option instead of making me delete the whole SIP.",
        "expected_relevance": True,
        "expected_primary_category": "Pause, Reduction, or Cancellation",
        "expected_sub_category": "Explicit SIP Pause",
        "expected_continuation_status": "Explicitly-Paused",
        "expected_severity": "Medium",
        "expected_uncertainty_handling": "Explicit temporary pause distinguished from permanent cancellation",
        "edge_case_type": "Intentional temporary pause enabler",
        "human_notes": "Clean pause enabler: user preserved folio rather than deleting."
    },
    {
        "case_id": "GS-09",
        "source_record_id": "reddit_pfi_post_213",
        "original_text": "Had to reduce my monthly SIP commitment from ₹15,000 down to ₹5,000 because my house rent increased by ₹8,000. It hurt my financial goals, but at least I didn't stop investing entirely.",
        "expected_relevance": True,
        "expected_primary_category": "Pause, Reduction, or Cancellation",
        "expected_sub_category": "Instalment Amount Reduced",
        "expected_continuation_status": "Explicitly-Reduced",
        "expected_severity": "Medium",
        "expected_uncertainty_handling": "Instalment step-down behavior explicitly captured",
        "edge_case_type": "Instalment reduction under financial pressure",
        "human_notes": "Investor stepped down amount to preserve habit despite rising cost of living."
    },
    {
        "case_id": "GS-10",
        "source_record_id": "reddit_ii_post_214",
        "original_text": "Just marked 12 consecutive months of my first SIP! What worked for me: setting the SIP date for the 7th (2 days after salary), turning off daily app notifications, and understanding that buying during market dips lowers my average NAV.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Enablers",
        "expected_sub_category": "Automated Habit Confidence",
        "expected_continuation_status": "Active-Continuing",
        "expected_severity": "None",
        "expected_uncertainty_handling": "Full 12-month milestone success case",
        "edge_case_type": "Successful 12-month habit continuation",
        "human_notes": "Golden model for 12-month continuation: salary buffer date + anti-anxiety habits."
    },
    {
        "case_id": "GS-11",
        "source_record_id": "reddit_multi_problem_01",
        "original_text": "My salary was delayed by 4 days, so autopay bounced with ₹300 bank penalty. When I tried to pay manually via UPI, the app crashed twice, and now NAV allocation is delayed by 3 days. I am totally confused and ready to quit.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Bank Mandate / Autopay Failure",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Multiple simultaneous frictions: mandate + app crash + NAV delay",
        "edge_case_type": "Multiple simultaneous compounding problems",
        "human_notes": "Compounding operational friction leading to imminent cancellation."
    },
    {
        "case_id": "GS-12",
        "source_record_id": "reddit_sparse_01",
        "original_text": "SIP status showing pending. Why?",
        "expected_relevance": True,
        "expected_primary_category": "Trust and Comprehension",
        "expected_sub_category": "Unclear SIP Status / Folio Number",
        "expected_continuation_status": "Unclear / Not-Stated",
        "expected_severity": "Low",
        "expected_uncertainty_handling": "Sparse text with minimal context, confidence must be adjusted downwards",
        "edge_case_type": "Sparse or incomplete information",
        "human_notes": "5 words query; model should not hallucinate user demographic or portfolio size."
    },
    {
        "case_id": "GS-13",
        "source_record_id": "reddit_contradictory_01",
        "original_text": "Mutual funds are the best investment for wealth creation, but I stopped my monthly SIP because the stock market is a total scam and rigged for big players.",
        "expected_relevance": True,
        "expected_primary_category": "Pause, Reduction, or Cancellation",
        "expected_sub_category": "Explicit SIP Cancellation",
        "expected_continuation_status": "Explicitly-Cancelled",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Resolve contradictory statements; action taken (stopped SIP) overrides theoretical praise",
        "edge_case_type": "Contradictory user sentiment vs behavior",
        "human_notes": "Expresses theoretical belief in mutual funds but cancelled in practice."
    },
    {
        "case_id": "GS-14",
        "source_record_id": "reddit_pii_01",
        "original_text": "Contacted rahul_investor99@gmail.com and called +919876543210 about my Zerodha Coin folio 109283749. Mandate failed again.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Bank Mandate / Autopay Failure",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "High",
        "expected_uncertainty_handling": "PII redaction validation before classification",
        "edge_case_type": "Potentially sensitive personal information",
        "human_notes": "Contains raw email, phone, and folio number that must be redacted."
    },
    {
        "case_id": "GS-15",
        "source_record_id": "reddit_workaround_01",
        "original_text": "Groww's return chart is totally misleading. I had to go to r/mutualfunds on Reddit and watch 3 videos of Pranjal Kamra to understand how rolling returns differ from point-to-point returns.",
        "expected_relevance": True,
        "expected_primary_category": "External Workarounds",
        "expected_sub_category": "Asking Reddit/Forums for Guidance",
        "expected_continuation_status": "Active-Continuing",
        "expected_severity": "Medium",
        "expected_uncertainty_handling": "Platform leakage to Reddit and YouTube for financial clarity",
        "edge_case_type": "External seeking workaround",
        "human_notes": "User left app because in-app metrics failed to explain returns."
    },
    {
        "case_id": "GS-16",
        "source_record_id": "playstore_coin_rev_104",
        "original_text": "Invested ₹10,000 via SIP over last 4 months but profit is only ₹120. At this rate even my bank savings account would give more interest! Why do influencers claim 15% guaranteed annual returns?",
        "expected_relevance": True,
        "expected_primary_category": "Expectations",
        "expected_sub_category": "Expected Quick Growth",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "Medium",
        "expected_uncertainty_handling": "Unrealistic expectation gap without explicit cancellation yet",
        "edge_case_type": "Expectation vs reality gap",
        "human_notes": "Expectation gap at month 4: expects 15% linear return immediately."
    },
    {
        "case_id": "GS-17",
        "source_record_id": "playstore_kuvera_rev_107",
        "original_text": "My SIP instalment was deducted from SBI on Friday, but today is Tuesday and Kuvera still shows 'Awaiting NAV confirmation from AMC'. Why is the folio status so opaque? In UPI money reaches instantly.",
        "expected_relevance": True,
        "expected_primary_category": "Trust and Comprehension",
        "expected_sub_category": "Nav / Units Allocation Confusion",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "Medium",
        "expected_uncertainty_handling": "Operational lag creates trust and comprehension anxiety",
        "edge_case_type": "NAV settlement lag confusion",
        "human_notes": "Beginner expects instant UPI-like settlement, confused by T+2 mutual fund mechanics."
    },
    {
        "case_id": "GS-18",
        "source_record_id": "reddit_ii_post_209",
        "original_text": "Freelancer here with unpredictable monthly income. Some months I make ₹80k, other months only ₹25k. Having a fixed debit date of ₹10,000 SIP is creating immense stress. I had 2 failed debits in the last 6 months.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Salary Delay / Variable Income",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Explicit evidence of income variability as barrier",
        "edge_case_type": "Variable income continuation barrier",
        "human_notes": "Gig/freelance income mismatch with rigid monthly debit dates."
    },
    {
        "case_id": "GS-19",
        "source_record_id": "tradingqna_post_401",
        "original_text": "Unexpected medical bill of ₹25,000 this month. My bank account has only ₹3,000 left and my SIP of ₹5,000 is due on Monday. How do I skip just this one instalment without losing my folio or paying penalties?",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Unexpected Emergency Expense",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Temporary shock seeking workaround rather than permanent cancellation",
        "edge_case_type": "Emergency financial shock",
        "human_notes": "Needs temporary relief mechanism rather than binary cancel."
    },
    {
        "case_id": "GS-20",
        "source_record_id": "playstore_etmoney_rev_110",
        "original_text": "Bank mandate setup failed 3 times via net banking with generic error 'Authentication Failed'. I wasted 2 hours trying to register autopay. If starting an automated SIP is so tedious, I will just keep money in recurring deposit.",
        "expected_relevance": True,
        "expected_primary_category": "Continuation Barriers",
        "expected_sub_category": "Bank Mandate / Autopay Failure",
        "expected_continuation_status": "At-Risk (Hesitating/Failing)",
        "expected_severity": "High",
        "expected_uncertainty_handling": "Drop-off during automated mandate setup",
        "edge_case_type": "Pre-continuation autopay onboarding dropout",
        "human_notes": "Autopay registration friction drives user back to traditional fixed/recurring deposits."
    }
]

# ── Documented Actual Human Corrections (Historical Audit Log) ─────────────────
DOCUMENTED_HUMAN_CORRECTIONS = [
    {
        "record_id": "playstore_noise_119",
        "raw_text": "Awesome app design! Very fast interface and dark mode looks cool.",
        "ai_initial_output": {
            "is_sip_continuation_relevant": True,
            "primary_category": "Continuation Enablers",
            "continuation_status": "Active-Continuing"
        },
        "human_corrected_output": {
            "is_sip_continuation_relevant": False,
            "primary_category": "Unrelated / General Financial Noise",
            "continuation_status": "Unclear / Not-Stated"
        },
        "rejection_reason": "AI equated positive sentiment about app dark mode with active 12-month SIP continuation. Corrected to Irrelevant."
    },
    {
        "record_id": "reddit_edge_222",
        "raw_text": "Market fell 3% today, my folio is in red. Terrible day.",
        "ai_initial_output": {
            "continuation_status": "Explicitly-Cancelled",
            "primary_category": "Pause, Reduction, or Cancellation"
        },
        "human_corrected_output": {
            "continuation_status": "At-Risk (Hesitating/Failing)",
            "primary_category": "Continuation Barriers"
        },
        "rejection_reason": "AI hallucinated cancellation simply because user complained about a red market day. No cancellation verb existed."
    },
    {
        "case_id": "reddit_contradictory_01",
        "raw_text": "Mutual funds are the best investment for wealth creation, but I stopped my monthly SIP because the stock market is a total scam and rigged for big players.",
        "ai_initial_output": {
            "primary_category": "SIP Initiation",
            "continuation_status": "Active-Continuing"
        },
        "human_corrected_output": {
            "primary_category": "Pause, Reduction, or Cancellation",
            "continuation_status": "Explicitly-Cancelled"
        },
        "rejection_reason": "AI picked up introductory praise ('best investment') and missed the actual behavioral statement ('I stopped my monthly SIP'). Corrected to Explicitly-Cancelled."
    }
]

def evaluate_golden_set() -> Dict[str, Any]:
    """
    Executes the golden set evaluation pipeline against all 20 ground-truth cases.
    Computes:
    - Relevance Accuracy, Precision, Recall, F1
    - Category Agreement Rate
    - Continuation Status Agreement Rate
    - Severity Agreement Rate
    - False Positive & False Negative lists
    - Per-case detailed audit table
    """
    total_cases = len(GOLDEN_SET_CASES)
    relevance_correct = 0
    category_correct = 0
    status_correct = 0
    severity_correct = 0

    true_pos_rel = 0
    false_pos_rel = 0
    false_neg_rel = 0
    true_neg_rel = 0

    detailed_results = []
    error_categories = {}

    for case in GOLDEN_SET_CASES:
        ai_res = classify_single_record(case['original_text'])
        
        # 1. Relevance evaluation
        ai_rel = bool(ai_res.get('is_sip_continuation_relevant', True))
        exp_rel = bool(case['expected_relevance'])
        
        is_rel_match = (ai_rel == exp_rel)
        if is_rel_match:
            relevance_correct += 1
            if exp_rel:
                true_pos_rel += 1
            else:
                true_neg_rel += 1
        else:
            if ai_rel and not exp_rel:
                false_pos_rel += 1
                err = "False Positive (Noise admitted as relevant)"
            else:
                false_neg_rel += 1
                err = "False Negative (SIP feedback rejected)"
            error_categories[err] = error_categories.get(err, 0) + 1

        # 2. Category evaluation
        ai_cat = ai_res.get('primary_category', '')
        exp_cat = case['expected_primary_category']
        is_cat_match = (ai_cat == exp_cat)
        if is_cat_match:
            category_correct += 1
        else:
            err = f"Category Mismatch: Expected '{exp_cat}' vs AI '{ai_cat}'"
            error_categories[err] = error_categories.get(err, 0) + 1

        # 3. Continuation status evaluation
        ai_status = ai_res.get('continuation_status', '')
        exp_status = case['expected_continuation_status']
        is_status_match = (ai_status == exp_status)
        if is_status_match:
            status_correct += 1
        else:
            err = f"Status Mismatch: Expected '{exp_status}' vs AI '{ai_status}'"
            error_categories[err] = error_categories.get(err, 0) + 1

        # 4. Severity evaluation
        ai_sev = ai_res.get('severity', '')
        exp_sev = case['expected_severity']
        is_sev_match = (ai_sev == exp_sev)
        if is_sev_match:
            severity_correct += 1

        # Overall case agreement (Relevance + Category + Status)
        case_passed = (is_rel_match and is_cat_match and is_status_match)

        detailed_results.append({
            'case_id': case['case_id'],
            'edge_case_type': case['edge_case_type'],
            'original_text_snippet': case['original_text'][:70] + "...",
            'expected_category': exp_cat,
            'ai_category': ai_cat,
            'expected_status': exp_status,
            'ai_status': ai_status,
            'relevance_match': is_rel_match,
            'category_match': is_cat_match,
            'status_match': is_status_match,
            'severity_match': is_sev_match,
            'case_passed': case_passed,
            'human_notes': case['human_notes']
        })

    # Metrics calculation
    rel_accuracy = round(relevance_correct / total_cases * 100, 1)
    precision_rel = round(true_pos_rel / max(1, (true_pos_rel + false_pos_rel)) * 100, 1)
    recall_rel = round(true_pos_rel / max(1, (true_pos_rel + false_neg_rel)) * 100, 1)
    f1_rel = round(2 * (precision_rel * recall_rel) / max(1.0, (precision_rel + recall_rel)), 1)
    cat_accuracy = round(category_correct / total_cases * 100, 1)
    status_accuracy = round(status_correct / total_cases * 100, 1)
    overall_case_accuracy = round(sum(1 for d in detailed_results if d['case_passed']) / total_cases * 100, 1)

    return {
        'total_cases': total_cases,
        'overall_case_agreement_pct': overall_case_accuracy,
        'relevance_accuracy_pct': rel_accuracy,
        'relevance_precision_pct': precision_rel,
        'relevance_recall_pct': recall_rel,
        'relevance_f1_score': f1_rel,
        'category_agreement_pct': cat_accuracy,
        'continuation_status_agreement_pct': status_accuracy,
        'severity_agreement_pct': round(severity_correct / total_cases * 100, 1),
        'false_positive_count': false_pos_rel,
        'false_negative_count': false_neg_rel,
        'error_breakdown': error_categories,
        'detailed_cases': detailed_results,
        'documented_corrections': DOCUMENTED_HUMAN_CORRECTIONS,
        'sample_limitations': "Golden set of N=20 provides reliable regression bounds for core edge cases, but confidence intervals are ±10%. Expanding to N=100 prior to production deployment is recommended."
    }

if __name__ == '__main__':
    metrics = evaluate_golden_set()
    print("\n================ GOLDEN SET BENCHMARK RESULTS ================")
    print(f"Overall Case Agreement : {metrics['overall_case_agreement_pct']}%")
    print(f"Relevance Accuracy     : {metrics['relevance_accuracy_pct']}% (Precision: {metrics['relevance_precision_pct']}%, Recall: {metrics['relevance_recall_pct']}%)")
    print(f"Category Agreement     : {metrics['category_agreement_pct']}%")
    print(f"Status Agreement       : {metrics['continuation_status_agreement_pct']}%")
    print(f"False Positives        : {metrics['false_positive_count']} | False Negatives: {metrics['false_negative_count']}")
    print("==============================================================")
