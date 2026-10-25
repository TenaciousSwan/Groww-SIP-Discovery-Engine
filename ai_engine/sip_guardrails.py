"""
SIP Research Domain Guardrails & Schema Validator.
Ensures data consistency, validates verbatim evidence traceability, and normalizes category variants.
"""

from typing import Dict, Any

VALID_PRIMARY_CATEGORIES = {
    'SIP Initiation',
    'Expectations',
    'Post-Initiation Behaviour',
    'Continuation Barriers',
    'Pause, Reduction, or Cancellation',
    'Continuation Enablers',
    'External Workarounds',
    'Trust and Comprehension',
    'Unrelated / General Financial Noise'
}

VALID_JOURNEY_STAGES = {
    'Before starting a SIP',
    'Starting the first SIP',
    'Early months (1-3)',
    'Middle of first year (4-8)',
    'Approaching month 12',
    'Pausing, reducing, or stopping',
    'Continuing despite uncertainty',
    'Unclear / Unstated'
}

CATEGORY_SYNONYM_MAP = {
    'Initiation': 'SIP Initiation',
    'Starting': 'SIP Initiation',
    'Barriers': 'Continuation Barriers',
    'Friction': 'Continuation Barriers',
    'Obstacles': 'Continuation Barriers',
    'Cancellation': 'Pause, Reduction, or Cancellation',
    'Pause': 'Pause, Reduction, or Cancellation',
    'Enablers': 'Continuation Enablers',
    'Help': 'Continuation Enablers',
    'Workarounds': 'External Workarounds',
    'External Seeking': 'External Workarounds',
    'Trust': 'Trust and Comprehension',
    'Comprehension': 'Trust and Comprehension',
    'Confusion': 'Trust and Comprehension',
    'Noise': 'Unrelated / General Financial Noise',
    'Unrelated': 'Unrelated / General Financial Noise'
}

def validate_and_sanitize_sip_insight(insight_dict: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """
    Applies rigorous research guardrails to LLM output:
    1. Validates and normalizes primary taxonomy category.
    2. Enforces non-hallucination of verbatim quote.
    3. Prevents unsupported continuation claims.
    4. Automatically flags records requiring human review.
    """
    cleaned = dict(insight_dict)
    
    # 1. Normalize Primary Category
    p_cat = cleaned.get('primary_category', 'Unrelated / General Financial Noise')
    if p_cat not in VALID_PRIMARY_CATEGORIES:
        matched = False
        for syn, canon in CATEGORY_SYNONYM_MAP.items():
            if syn.lower() in str(p_cat).lower():
                cleaned['primary_category'] = canon
                matched = True
                break
        if not matched:
            cleaned['primary_category'] = 'Unrelated / General Financial Noise'
            cleaned['needs_human_review'] = True

    # 2. Reconcile relevance flag
    if cleaned['primary_category'] == 'Unrelated / General Financial Noise':
        cleaned['is_sip_continuation_relevant'] = False
    elif not cleaned.get('is_sip_continuation_relevant', True):
        cleaned['primary_category'] = 'Unrelated / General Financial Noise'

    # 3. Verify Verbatim Evidence Span
    quote = str(cleaned.get('supporting_quote', '')).strip()
    if quote and raw_text:
        # Check if quote is present in raw text (normalize whitespace)
        norm_raw = " ".join(raw_text.lower().split())
        norm_quote = " ".join(quote.lower().split())
        if norm_quote not in norm_raw:
            # Quote was summarized or hallucinated instead of verbatim
            cleaned['evidence_limitations'] = (
                str(cleaned.get('evidence_limitations', '')) + 
                " [Notice: Model generated synthesized quote rather than exact verbatim substring.]"
            ).strip()
            # If quote differs greatly, keep first 120 chars of raw text as safe fallback
            if len(norm_raw) > 0:
                cleaned['supporting_quote'] = raw_text[:150].strip() + "..."
            cleaned['needs_human_review'] = True

    # 4. Continuation Status Guardrail
    raw_lower = raw_text.lower() if raw_text else ""
    status = cleaned.get('continuation_status', 'Unclear / Not-Stated')
    
    # Explicit cancellation requires explicit language in raw text
    cancel_keywords = ['cancel', 'stopped my sip', 'closed the sip', 'discontinued', 'bandh kar diya']
    if status == 'Explicitly-Cancelled' and not any(kw in raw_lower for kw in cancel_keywords):
        cleaned['continuation_status'] = 'At-Risk (Hesitating/Failing)'
        cleaned['evidence_limitations'] = (
            str(cleaned.get('evidence_limitations', '')) + 
            " [Guardrail: Demoted from Explicitly-Cancelled to At-Risk due to lack of explicit cancellation verbs.]"
        ).strip()
        cleaned['needs_human_review'] = True

    # Explicit pause check
    pause_keywords = ['pause', 'paused', 'skip', 'skipped installment', 'hold pe']
    if status == 'Explicitly-Paused' and not any(kw in raw_lower for kw in pause_keywords):
        cleaned['continuation_status'] = 'At-Risk (Hesitating/Failing)'
        cleaned['evidence_limitations'] = (
            str(cleaned.get('evidence_limitations', '')) + 
            " [Guardrail: Demoted from Explicitly-Paused to At-Risk due to lack of explicit pause verbs.]"
        ).strip()

    # 5. Journey Stage Guardrail
    j_stage = cleaned.get('journey_stage', 'Unclear / Unstated')
    if j_stage not in VALID_JOURNEY_STAGES:
        cleaned['journey_stage'] = 'Unclear / Unstated'

    # 6. Clamp confidence
    conf = cleaned.get('confidence_score', 0.5)
    try:
        conf = float(conf)
        cleaned['confidence_score'] = max(0.0, min(1.0, round(conf, 2)))
    except (ValueError, TypeError):
        cleaned['confidence_score'] = 0.5

    return cleaned
