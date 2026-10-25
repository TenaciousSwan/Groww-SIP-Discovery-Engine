import pytest
from evaluation.golden_set import evaluate_golden_set, GOLDEN_SET_CASES

def test_golden_set_benchmark_execution():
    assert len(GOLDEN_SET_CASES) == 20
    results = evaluate_golden_set()
    assert results['total_cases'] == 20
    assert results['relevance_accuracy_pct'] >= 90.0
    assert results['overall_case_agreement_pct'] >= 80.0
    assert 'documented_corrections' in results
    assert len(results['documented_corrections']) >= 2
