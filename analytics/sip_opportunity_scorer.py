"""
Opportunity Prioritization Framework for 12-Month SIP Continuation.
Transparent, multi-dimensional scoring for Groww Mutual Funds Product Prioritization.
"""

import sqlite3
import pandas as pd
import numpy as np

DB_PATH = 'data/discovery.db'

# Predefined domain addressability and feasibility scores for common SIP friction areas
DOMAIN_FACTORS = {
    'Bank Mandate / Autopay Failure': {
        'addressability': 0.92, # Very high — in-app UPI retry, advance balance alert, grace window
        'feasibility': 0.88,    # High — standard payment SDK / webhook workflow
        'rationale': "Directly fixable in app: notify 24h before debit, provide 1-tap UPI mandate fallback."
    },
    'Salary Delay / Variable Income': {
        'addressability': 0.88, # High — flexible debit dates, monthly date shift
        'feasibility': 0.85,    # High — user-configurable SIP execution dates
        'rationale': "Addressable by allowing investors to shift monthly debit date by up to 10 days."
    },
    'Unexpected Emergency Expense': {
        'addressability': 0.75, # Medium-high — 1-tap pause button without cancellation
        'feasibility': 0.90,    # High — AMC pause API already exists in most platforms
        'rationale': "High feasibility: promote 1-to-3 month 'Pause SIP' instead of outright cancellation."
    },
    'Negative Return Disappointment': {
        'addressability': 0.70, # Medium — visual contextual compounding education
        'feasibility': 0.85,    # High — portfolio UI tweak showing units accumulated vs NAV
        'rationale': "Can be addressed by showing Rupee-Cost Averaging progress during market dips."
    },
    'Nav / Units Allocation Confusion': {
        'addressability': 0.85, # High — instant allotment timeline progress bar
        'feasibility': 0.90,    # High — UI order tracking timeline (D+1, D+2 expectations)
        'rationale': "Solvable via transparency: order tracking bar showing 'Money debited -> AMC confirmed -> Units allotted'."
    },
    'Daily/Frequent Portfolio Checking': {
        'addressability': 0.65, # Medium — anti-anxiety UX modes
        'feasibility': 0.80,    # High — 'zen mode' hiding day P&L in favor of milestone goals
        'rationale': "Addressable by defaulting home screen to goal milestones rather than daily red/green fluctuations."
    },
    'Expense Ratio / Hidden Charge Doubt': {
        'addressability': 0.85, # High — transparent cost calculator
        'feasibility': 0.90,    # High — straightforward fee breakdown card
        'rationale': "Solvable with clear fee disclosure showing ₹0 platform commission and exact TER."
    },
    'Asking Reddit/Forums for Guidance': {
        'addressability': 0.78, # Medium-high — in-app verified Q&A
        'feasibility': 0.75,    # Medium — curated community or AMA with SEBI registered advisors
        'rationale': "Addressable by embedding verified answers to common beginner SIP questions inside app."
    }
}

DEFAULT_WEIGHTS = {
    'w_frequency': 1.5,
    'w_breadth': 1.2,
    'w_severity': 2.0,
    'w_relevance_12m': 1.8,
    'w_continuation_link': 2.2,
    'w_evidence_strength': 1.0,
    'w_addressability': 1.6,
    'w_feasibility': 1.4
}

def load_sip_data(db_path=DB_PATH):
    """Loads joined raw, enriched, and human-reviewed SIP records."""
    conn = sqlite3.connect(db_path)
    try:
        # Load enriched insights joined with raw conversations and latest human reviews
        query = '''
            SELECT 
                e.*,
                r.content as raw_text,
                r.url as source_url,
                r.collection_date,
                r.language,
                h.status as human_review_status,
                h.reviewed_category,
                h.reviewed_sub_category,
                h.correction_notes
            FROM sip_enriched_insights e
            LEFT JOIN raw_conversations r ON e.id = r.id
            LEFT JOIN sip_human_reviews h ON e.id = h.record_id
        '''
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error loading SIP data: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def compute_sip_opportunity_scores(df: pd.DataFrame, custom_weights=None) -> pd.DataFrame:
    """
    Computes transparent multi-dimensional opportunity scores for each sub-category.
    Returns ranked DataFrame with individual dimension values and human-readable rationales.
    """
    if df.empty:
        return pd.DataFrame()

    weights = dict(DEFAULT_WEIGHTS)
    if custom_weights:
        weights.update(custom_weights)

    # Filter to relevant records
    rel_df = df[df['is_sip_continuation_relevant'] == 1].copy()
    if rel_df.empty:
        return pd.DataFrame()

    # Map severity to numeric scale
    sev_map = {'High': 3, 'Medium': 2, 'Low': 1, 'None': 0}
    rel_df['num_severity'] = rel_df['severity'].map(sev_map).fillna(1)

    # Relevance to 12-Month Journey (higher if in Early Months, Mid-Year, Approaching 12M, or Pausing)
    j_weights = {
        'Early months (1-3)': 1.0,
        'Middle of first year (4-8)': 1.0,
        'Approaching month 12': 0.9,
        'Pausing, reducing, or stopping': 1.0,
        'Starting the first SIP': 0.7,
        'Continuing despite uncertainty': 0.8,
        'Before starting a SIP': 0.4,
        'Unclear / Unstated': 0.3
    }
    rel_df['j_relevance'] = rel_df['journey_stage'].map(j_weights).fillna(0.3)

    # Connection to continuation (1.0 if cancelled, paused, or at-risk)
    c_status_weights = {
        'Explicitly-Cancelled': 1.0,
        'Explicitly-Paused': 0.9,
        'Explicitly-Reduced': 0.8,
        'At-Risk (Hesitating/Failing)': 0.85,
        'Active-Continuing': 0.3,
        'Unclear / Not-Stated': 0.2
    }
    rel_df['c_link'] = rel_df['continuation_status'].map(c_status_weights).fillna(0.3)

    opportunities = []
    total_relevant = len(rel_df)

    for sub_cat, group in rel_df.groupby('sub_category'):
        count = len(group)
        pct_of_sample = round((count / total_relevant) * 100, 1)
        distinct_sources = group['source'].nunique()
        avg_sev = group['num_severity'].mean()
        avg_12m_rel = group['j_relevance'].mean()
        avg_continuation_link = group['c_link'].mean()
        avg_confidence = group['confidence_score'].mean()

        # Lookup addressability and feasibility
        domain_info = DOMAIN_FACTORS.get(sub_cat, {
            'addressability': 0.70,
            'feasibility': 0.75,
            'rationale': "Standard product and educational intervention."
        })

        addr = domain_info['addressability']
        feas = domain_info['feasibility']
        rationale = domain_info['rationale']

        # Composite opportunity score formula:
        # Sum of weighted normalized dimensions
        raw_score = (
            (count * weights['w_frequency']) +
            (distinct_sources * 2.0 * weights['w_breadth']) +
            (avg_sev * 10.0 * weights['w_severity']) +
            (avg_12m_rel * 25.0 * weights['w_relevance_12m']) +
            (avg_continuation_link * 30.0 * weights['w_continuation_link']) +
            (avg_confidence * 15.0 * weights['w_evidence_strength']) +
            (addr * 25.0 * weights['w_addressability']) +
            (feas * 20.0 * weights['w_feasibility'])
        )

        # Primary parent category
        parent_cat = group['primary_category'].value_counts().index[0]

        opportunities.append({
            'sub_category': sub_cat,
            'primary_category': parent_cat,
            'record_count': count,
            'pct_sample': pct_of_sample,
            'distinct_sources': distinct_sources,
            'avg_severity': round(avg_sev, 2),
            'relevance_12m': round(avg_12m_rel, 2),
            'continuation_link': round(avg_continuation_link, 2),
            'evidence_strength': round(avg_confidence, 2),
            'addressability': round(addr, 2),
            'feasibility': round(feas, 2),
            'composite_score': round(raw_score, 1),
            'rationale': rationale,
            'example_unmet_need': group['potential_unmet_need'].dropna().iloc[0] if not group['potential_unmet_need'].dropna().empty else "N/A"
        })

    opp_df = pd.DataFrame(opportunities)
    if not opp_df.empty:
        opp_df = opp_df.sort_values('composite_score', ascending=False).reset_index(drop=True)
        opp_df['rank'] = range(1, len(opp_df) + 1)
    return opp_df

if __name__ == '__main__':
    df = load_sip_data()
    print(f"Loaded {len(df)} records.")
    opps = compute_sip_opportunity_scores(df)
    print("=== TOP OPPORTUNITIES ===")
    if not opps.empty:
        print(opps[['rank', 'sub_category', 'record_count', 'composite_score', 'rationale']].head(5).to_string())
