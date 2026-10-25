import pytest
from ai_engine.sip_classifier import classify_single_record
from ai_engine.sip_guardrails import validate_and_sanitize_sip_insight

def test_explicit_cancellation_extraction():
    text = "I explicitly cancelled my ₹5,000 SIP yesterday due to fear of market crash."
    res = classify_single_record(text)
    assert res['is_sip_continuation_relevant'] is True
    assert res['primary_category'] == 'Pause, Reduction, or Cancellation'
    assert res['continuation_status'] == 'Explicitly-Cancelled'

def test_negative_sentiment_does_not_infer_cancellation():
    text = "Market fell 3% today, my folio is in red. Terrible day."
    res = classify_single_record(text)
    assert res['is_sip_continuation_relevant'] is True
    # Should NOT be classified as cancelled
    assert res['continuation_status'] != 'Explicitly-Cancelled'
    assert res['continuation_status'] == 'At-Risk (Hesitating/Failing)'

def test_positive_sentiment_does_not_infer_continuation():
    text = "Awesome app design! Very fast interface and dark mode looks cool."
    res = classify_single_record(text)
    assert res['is_sip_continuation_relevant'] is False
    assert res['primary_category'] == 'Unrelated / General Financial Noise'

def test_mandate_failure_extraction():
    text = "My SIP autopay failed because salary was delayed and bank charged ₹295 bounce fee."
    res = classify_single_record(text)
    assert res['primary_category'] == 'Continuation Barriers'
    assert res['sub_category'] == 'Bank Mandate / Autopay Failure'
    assert res['severity'] == 'High'

def test_unrelated_apparel_filtered():
    text = "The red dress I bought from Myntra was size S and too small."
    res = classify_single_record(text)
    assert res['is_sip_continuation_relevant'] is False
    assert res['primary_category'] == 'Unrelated / General Financial Noise'
