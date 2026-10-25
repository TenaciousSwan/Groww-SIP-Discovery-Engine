import pytest
import pandas as pd
from analytics.sip_opportunity_scorer import compute_sip_opportunity_scores

def test_opportunity_scorer_ranking():
    mock_data = pd.DataFrame([
        {
            'id': 'rec_1',
            'is_sip_continuation_relevant': 1,
            'source': 'Play Store (Groww)',
            'primary_category': 'Continuation Barriers',
            'sub_category': 'Bank Mandate / Autopay Failure',
            'journey_stage': 'Early months (1-3)',
            'continuation_status': 'At-Risk (Hesitating/Failing)',
            'severity': 'High',
            'confidence_score': 0.9,
            'potential_unmet_need': 'Proactive notification'
        },
        {
            'id': 'rec_2',
            'is_sip_continuation_relevant': 1,
            'source': 'Reddit (r/mutualfunds)',
            'primary_category': 'Continuation Barriers',
            'sub_category': 'Bank Mandate / Autopay Failure',
            'journey_stage': 'Early months (1-3)',
            'continuation_status': 'At-Risk (Hesitating/Failing)',
            'severity': 'High',
            'confidence_score': 0.95,
            'potential_unmet_need': 'One tap UPI retry'
        },
        {
            'id': 'rec_3',
            'is_sip_continuation_relevant': 0,
            'source': 'App Store',
            'primary_category': 'Unrelated / General Financial Noise',
            'sub_category': 'Other / Unclear',
            'journey_stage': 'Unclear / Unstated',
            'continuation_status': 'Unclear / Not-Stated',
            'severity': 'None',
            'confidence_score': 0.8,
            'potential_unmet_need': 'N/A'
        }
    ])

    opps = compute_sip_opportunity_scores(mock_data)
    assert not opps.empty
    top = opps.iloc[0]
    assert top['sub_category'] == 'Bank Mandate / Autopay Failure'
    assert top['record_count'] == 2
    assert top['distinct_sources'] == 2
    assert top['composite_score'] > 0
