"""
Opportunity Scorer — converts classified records into quantified PM opportunity areas.

Opportunity Score = Frequency × Severity Weight × Conversion Impact Factor

This answers Q10 + Q11: What unmet needs emerge consistently, and how do we
quantify/compare opportunity areas to prioritize against the business metric?
"""

import sqlite3
import pandas as pd

DB_PATH = '../data/discovery.db' if __name__ == '__main__' else 'data/discovery.db'

# How much each postponement trigger blocks conversion (0-1 scale)
# High = fixable by product/UX; Low = external/intentional, hard to fix
CONVERSION_IMPACT = {
    'Size-Doubt':          0.92,  # #1 fixable — better size tools = direct conversion
    'Wants-More-Reviews':  0.82,  # High — social proof features unlock this
    'Comparing-Options':   0.70,  # High — better comparison UX, wishlist features
    'Occasion-Not-Yet':    0.35,  # Low — time-based, not a UX gap
    'Price-Wait':          0.20,  # Low — intentional wait, not solvable by UX
    'None':                0.10,
}

SEVERITY_WEIGHTS = {'High': 3, 'Medium': 2, 'Low': 1}

WISHLIST_INTENT_SCORE = {
    'Genuine-Intent':   1.0,  # These users WILL buy if friction is removed
    'Price-Waiting':    0.8,
    'Occasion-Waiting': 0.6,
    'Browse-Saving':    0.2,  # Low — may never convert regardless
    'Unclear':          0.5,
}


def load_enriched_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM enriched_insights", conn)
    conn.close()
    return df


def compute_opportunity_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame of opportunity areas ranked by composite score.
    """
    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Map severity to weight
    df['severity_weight'] = df['severity'].map(SEVERITY_WEIGHTS).fillna(1)

    # Map postponement trigger to conversion impact
    df['conversion_impact'] = df['postponement_trigger'].map(CONVERSION_IMPACT).fillna(0.1)

    # Wishlist intent score — how likely is conversion if friction is removed?
    df['intent_score'] = df['wishlist_mode'].map(WISHLIST_INTENT_SCORE).fillna(0.5)

    # Composite opportunity score per record
    df['opportunity_score'] = df['severity_weight'] * df['conversion_impact'] * df['intent_score']

    # Group by postponement trigger → aggregate opportunity
    trigger_scores = (
        df.groupby('postponement_trigger')
        .agg(
            count=('id', 'count'),
            avg_severity_weight=('severity_weight', 'mean'),
            conversion_impact=('conversion_impact', 'first'),
            total_opportunity=('opportunity_score', 'sum'),
            high_severity_count=('severity', lambda x: (x == 'High').sum()),
            pct_genuine_intent=('intent_score', lambda x: (x >= 0.8).mean() * 100),
        )
        .reset_index()
    )
    trigger_scores['pct_of_total'] = (trigger_scores['count'] / len(df) * 100).round(1)
    trigger_scores = trigger_scores.sort_values('total_opportunity', ascending=False)

    return trigger_scores


def compute_friction_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Friction category × severity matrix for the Pareto/heatmap view.
    """
    if df.empty:
        return pd.DataFrame()
    matrix = df.groupby(['friction_category', 'severity']).size().unstack(fill_value=0)
    # Add weighted score
    weights = {'High': 3, 'Medium': 2, 'Low': 1}
    matrix['weighted_score'] = sum(
        matrix.get(s, 0) * w for s, w in weights.items()
    )
    return matrix.sort_values('weighted_score', ascending=False)


def compute_segment_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Answers Q9: How do behaviors differ across user segments?
    Rewritten to avoid pandas named-agg + lambda compatibility issues.
    """
    if df.empty or 'user_segment_signal' not in df.columns:
        return pd.DataFrame()

    sev_map = {'High': 3, 'Medium': 2, 'Low': 1}
    rows = []
    for seg, grp in df.groupby('user_segment_signal'):
        rows.append({
            'user_segment_signal':  seg,
            'count':                len(grp),
            'top_trigger':          grp['postponement_trigger'].value_counts().index[0] if len(grp) > 0 else 'None',
            'top_friction':         grp['friction_category'].value_counts().index[0] if len(grp) > 0 else 'None',
            'pct_external_seeking': (grp['external_source'] != 'None').mean() * 100,
            'pct_genuine_intent':   (grp['wishlist_mode'] == 'Genuine-Intent').mean() * 100,
            'avg_severity':         grp['severity'].map(sev_map).fillna(1).mean(),
        })
    return pd.DataFrame(rows).sort_values('count', ascending=False).reset_index(drop=True)


def compute_external_seeking_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Answers Q6: Where do users go outside Myntra for validation?
    """
    if df.empty or 'external_source' not in df.columns:
        return pd.DataFrame()
    seekers = df[df['external_source'] != 'None']
    if seekers.empty:
        return pd.DataFrame()
    breakdown = (
        seekers.groupby('external_source')
        .agg(
            count=('id', 'count'),
            pct_high_severity=('severity', lambda x: (x == 'High').mean() * 100),
            top_trigger=('postponement_trigger', lambda x: x.value_counts().index[0] if len(x) > 0 else 'None'),
        )
        .reset_index()
        .sort_values('count', ascending=False)
    )
    breakdown['pct_of_seekers'] = (breakdown['count'] / len(seekers) * 100).round(1)
    return breakdown


def compute_decision_factor_frequency(df: pd.DataFrame) -> pd.Series:
    """
    Answers Q7: What role do fit/size/styling/price/reviews/occasion/social play?
    """
    if df.empty or 'decision_factors' not in df.columns:
        return pd.Series()
    all_factors = []
    for factors_str in df['decision_factors'].dropna():
        factors = [f.strip() for f in factors_str.split(',') if f.strip() and f.strip() != 'None']
        all_factors.extend(factors)
    if not all_factors:
        return pd.Series()
    return pd.Series(all_factors).value_counts()


def get_top_unmet_needs(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Answers Q10: What unmet needs emerge consistently?
    Returns the most frequently occurring unmet need summaries.
    """
    if df.empty or 'unmet_need' not in df.columns:
        return pd.DataFrame()
    # Group by friction + trigger to surface pattern clusters
    return (
        df[df['unmet_need'].notna() & (df['unmet_need'] != '')]
        .groupby(['friction_category', 'postponement_trigger'])
        .agg(
            count=('id', 'count'),
            example_need=('unmet_need', 'first'),
        )
        .reset_index()
        .sort_values('count', ascending=False)
        .head(n)
    )


if __name__ == '__main__':
    df = load_enriched_data()
    print(f"\nLoaded {len(df)} records.")
    print("\n=== TOP OPPORTUNITY AREAS ===")
    scores = compute_opportunity_scores(df)
    print(scores[['postponement_trigger', 'count', 'pct_of_total', 'total_opportunity', 'pct_genuine_intent']].to_string())

    print("\n=== DECISION FACTORS ===")
    print(compute_decision_factor_frequency(df).head(10))

    print("\n=== SEGMENT BREAKDOWN ===")
    print(compute_segment_breakdown(df).to_string())
