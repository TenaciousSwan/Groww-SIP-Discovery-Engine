"""
12-Month SIP Continuation — AI-Powered Product Discovery Engine
A research workbench for Product Managers investigating first-time mutual fund investor continuation in India.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Path setup
sys.path.insert(0, os.path.dirname(__file__))

from analytics.sip_opportunity_scorer import load_sip_data, compute_sip_opportunity_scores, DEFAULT_WEIGHTS
from analytics.sip_themes import extract_sip_themes
from evaluation.golden_set import evaluate_golden_set, GOLDEN_SET_CASES, DOCUMENTED_HUMAN_CORRECTIONS
from ai_engine.sip_classifier import classify_single_record, save_sip_insight, setup_sip_tables
from ingestion.sip_cleaner import save_records, setup_db

DB_PATH = 'data/discovery.db'

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Groww SIP Continuation Discovery Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Okabe-Ito Colorblind-Safe Palette ───────────────────────────────────────────
CB_ORANGE    = "#E69F00"
CB_SKYBLUE   = "#56B4E9"
CB_GREEN     = "#009E73"
CB_YELLOW    = "#F0E442"
CB_BLUE      = "#0072B2"
CB_VERMILION = "#D55E00"
CB_PINK      = "#CC79A7"
CB_DARK      = "#1a1a2a"

OKABE_ITO = [CB_ORANGE, CB_SKYBLUE, CB_GREEN, CB_YELLOW, CB_BLUE, CB_VERMILION, CB_PINK]
SEV_COLORS = {"High": CB_VERMILION, "Medium": CB_ORANGE, "Low": CB_SKYBLUE, "None": "#6a6a8a"}

def base_layout(height=340):
    return dict(
        paper_bgcolor="#16161e",
        plot_bgcolor="#1e1e2e",
        font=dict(family="Inter, sans-serif", color="#e8e8e8", size=13),
        height=height,
        margin=dict(l=16, r=16, t=40, b=16),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
        xaxis=dict(gridcolor="#2e2e3e", linecolor="#3e3e4e"),
        yaxis=dict(gridcolor="#2e2e3e", linecolor="#3e3e4e"),
    )

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .metric-card {
        background: #1e1e2e;
        border: 1.5px solid #3a3a5e;
        border-radius: 10px;
        padding: 16px 14px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #E69F00;
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.76rem;
        color: #9a9ab0;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 5px;
        font-weight: 600;
    }
    .section-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        background: #1e1e2e;
        border-left: 4px solid #56B4E9;
        padding: 8px 14px;
        margin: 20px 0 12px 0;
        border-radius: 0 6px 6px 0;
    }
    .insight-box {
        background: #1e1e2e;
        border: 1.5px solid #3a3a5e;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        font-size: 0.9rem;
        color: #e8e8f0;
        line-height: 1.6;
    }
    .tag {
        display: inline-block;
        background: #2a2a40;
        color: #c8c8e0;
        border: 1px solid #4a4a6a;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 4px;
        margin-bottom: 3px;
    }
    .tag-hi  { background:#3d1f1a; color:#E69F00; border-color:#5a3020; }
    .tag-mid { background:#1e2a3a; color:#56B4E9; border-color:#2a3a50; }
    .tag-lo  { background:#1a2e2a; color:#009E73; border-color:#204840; }
    .quote-box {
        background: #14141f;
        border-left: 3px solid #E69F00;
        padding: 10px 14px;
        font-style: italic;
        color: #d8d8ea;
        margin: 8px 0;
        border-radius: 0 4px 4px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Data Loading & State Management ───────────────────────────────────────────
setup_db(DB_PATH)
setup_sip_tables(DB_PATH)

@st.cache_data(ttl=30)
def get_cached_sip_data():
    return load_sip_data(DB_PATH)

df = get_cached_sip_data()

# ── Sidebar Filters & Controls ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Groww SIP Engine")
    st.markdown("**12-Month SIP Continuation Study**")
    st.caption("Product Management Fellowship · Groww Teardown")
    st.divider()

    total_records = len(df)
    groww_records = int(df['source'].str.contains('Groww', case=False, na=False).sum()) if not df.empty else 0
    relevant_count = int(df['is_sip_continuation_relevant'].sum()) if not df.empty else 0
    
    st.metric("Total Records Imported", total_records)
    st.metric("Groww-Specific Signals", groww_records)
    st.metric("Relevant SIP Records", relevant_count)
    
    st.divider()
    st.markdown("### 🔍 Filters")
    
    # Source filter with Groww highlighted
    source_options = ['All', 'Play Store (Groww)', 'Reddit (r/mutualfunds · Groww)', 'Reddit (r/IndiaInvestments · Groww)', 'Reddit (r/personalfinanceindia · Groww)']
    if not df.empty and 'source' in df.columns:
        other_sources = sorted([s for s in df['source'].dropna().unique() if s and s not in source_options])
        source_options += other_sources
    sel_source = st.selectbox("Source Platform", source_options)

    # Category filter
    cat_options = ['All']
    if not df.empty and 'primary_category' in df.columns:
        cat_options += sorted([c for c in df['primary_category'].dropna().unique() if c])
    sel_category = st.selectbox("Taxonomy Category", cat_options)

    # Continuation Status filter
    status_options = ['All', 'Active-Continuing', 'At-Risk (Hesitating/Failing)', 'Explicitly-Paused', 'Explicitly-Cancelled', 'Explicitly-Reduced', 'Unclear / Not-Stated']
    sel_status = st.selectbox("Continuation Status", status_options)

    # Severity filter
    sev_options = ['All', 'High', 'Medium', 'Low', 'None']
    sel_severity = st.selectbox("Friction Severity", sev_options)

    st.divider()
    st.caption("Target App: Groww (com.nextbillion.groww)")
    st.caption("AI Model: Gemini 2.5 Flash + Deterministic Guardrails")
    st.caption("Strict Epistemic Humility Rules Active")

# Apply filters
fdf = df.copy()
if sel_source != 'All':
    fdf = fdf[fdf['source'] == sel_source]
if sel_category != 'All':
    fdf = fdf[fdf['primary_category'] == sel_category]
if sel_status != 'All':
    fdf = fdf[fdf['continuation_status'] == sel_status]
if sel_severity != 'All':
    fdf = fdf[fdf['severity'] == sel_severity]

# Relevant subset
rel_df = fdf[fdf['is_sip_continuation_relevant'] == 1].copy()

# ── Header & KPI Cards ────────────────────────────────────────────────────────
st.markdown("# 📈 Groww 12-Month SIP Continuation — AI Discovery Engine")
st.markdown("> **An evidence-grounded research engine investigating why first-time mutual fund investors on GROWW start SIPs but later pause, reduce, cancel, or abandon them.**")

st.divider()

col1, col2, col3, col4, col5 = st.columns(5)
total_imp = len(fdf)
total_rel = len(rel_df)
pct_rel = (total_rel / max(1, total_imp)) * 100
mandate_frictions = (rel_df['sub_category'] == 'Bank Mandate / Autopay Failure').sum() if not rel_df.empty else 0
cancelled_count = (rel_df['continuation_status'] == 'Explicitly-Cancelled').sum() if not rel_df.empty else 0
at_risk_count = (rel_df['continuation_status'] == 'At-Risk (Hesitating/Failing)').sum() if not rel_df.empty else 0
active_continuing = (rel_df['continuation_status'] == 'Active-Continuing').sum() if not rel_df.empty else 0

for col, val, label, sublabel in [
    (col1, str(total_rel), "Relevant SIP Signals", f"{pct_rel:.0f}% of imported records"),
    (col2, str(mandate_frictions), "Mandate/Autopay Issues", "#1 operational friction"),
    (col3, str(at_risk_count), "At-Risk Investors", "hesitating on dip/delays"),
    (col4, str(cancelled_count), "Explicit Cancellations", "stopped within 12M"),
    (col5, str(active_continuing), "Active Continuers", "evidence of habit"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
            <div style="font-size:0.68rem;color:#7a7a9a;margin-top:4px">{sublabel}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── Main Tabs ──────────────────────────────────────────────────────────────────
tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📋 Executive Overview",
    "🔬 Research Themes",
    "🗺️ 12-Month User Journey",
    "🎯 Opportunity Matrix",
    "🔎 Evidence Explorer",
    "✍️ Human Review & Audit",
    "🧪 AI Quality & Golden Set",
    "📥 Ingestion Workbench"
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 0: EXECUTIVE OVERVIEW
# ════════════════════════════════════════════════════════════════════════════════
with tab0:
    st.markdown('<div class="section-header">Executive Summary — Core Drop-Off Drivers for Groww SIP Investors</div>', unsafe_allow_html=True)
    st.caption("Based on verified public records from Groww Play Store reviews (com.nextbillion.groww), Reddit discussions (r/mutualfunds · Groww), and public fintech forums.")

    if rel_df.empty:
        st.info("No relevant SIP records match the current filters. Adjust sidebar filters to view insights.")
    else:
        col_a, col_b = st.columns([3, 2])
        
        with col_a:
            # Primary Category Distribution
            cat_counts = rel_df['primary_category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Count']
            cat_counts['%'] = (cat_counts['Count'] / len(rel_df) * 100).round(1)
            
            fig_cat = px.bar(
                cat_counts, x='%', y='Category', orientation='h',
                title=f'Friction & Behavioral Distribution (% of {len(rel_df)} SIP records)',
                color='Category', color_discrete_sequence=OKABE_ITO,
                text='%'
            )
            fig_cat.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_cat.update_layout(**base_layout(320), showlegend=False)
            st.plotly_chart(fig_cat, use_container_width=True)

        with col_b:
            # Continuation Status Distribution
            st.markdown('<div class="section-header">Verified Investor Status</div>', unsafe_allow_html=True)
            status_counts = rel_df['continuation_status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig_status = px.pie(
                status_counts, names='Status', values='Count',
                title='Continuation Status Breakdown (Strict Text Evidence)',
                color_discrete_sequence=OKABE_ITO, hole=0.35
            )
            fig_status.update_traces(textinfo='label+percent', textfont_size=11)
            fig_status.update_layout(**base_layout(320))
            st.plotly_chart(fig_status, use_container_width=True)

        # Key Findings Card Row
        st.markdown('<div class="section-header">Top 3 Critical Insights for Groww 12-Month Continuation</div>', unsafe_allow_html=True)
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        
        with rec_col1:
            st.markdown(f"""
            <div class="insight-box" style="border-left:4px solid {CB_VERMILION}">
                <strong style="color:{CB_VERMILION}">#1 Bank Mandate & Salary Delay Trap</strong><br>
                <span class="tag">Continuation Barrier</span>
                <span class="tag">High Severity</span><br><br>
                First-time Groww investors do not quit because they dislike wealth creation; they quit because rigid autopay debit dates fail when monthly salaries are delayed by 24–48 hours. Banks charge ₹250–₹350 punitive ECS bounce fees, triggering immediate autopay cancellation on Groww.
            </div>
            """, unsafe_allow_html=True)

        with rec_col2:
            st.markdown(f"""
            <div class="insight-box" style="border-left:4px solid {CB_ORANGE}">
                <strong style="color:{CB_ORANGE}">#2 First Market Dip Shock & Linear Bias</strong><br>
                <span class="tag">Expectation Gap</span>
                <span class="tag">Months 1–4</span><br><br>
                First-time investors enter with fixed-deposit mental models expecting steady upward gains. When Groww displays red negative returns during early months, anxiety triggers premature redemption before rupee-cost averaging can take effect.
            </div>
            """, unsafe_allow_html=True)

        with rec_col3:
            st.markdown(f"""
            <div class="insight-box" style="border-left:4px solid {CB_GREEN}">
                <strong style="color:{CB_GREEN}">#3 Groww 48-Hour Skip Rule & Missing Step-Down</strong><br>
                <span class="tag">Product Opportunity</span>
                <span class="tag">High Feasibility</span><br><br>
                Users complain that Groww's skip SIP option is blocked if attempted less than 48 hours before debit. When emergencies occur, this rigidity forces bank bounce fees or outright cancellation. Dynamic pause and step-down sliders preserve user folios.
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1: RESEARCH THEMES & COUNTEREXAMPLES
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Synthesized Research Themes & Evidence Provenance</div>', unsafe_allow_html=True)
    st.caption("Each theme aggregates independent public signals, quotes, and counterexamples without inflating evidence.")

    themes = extract_sip_themes(rel_df)
    if not themes:
        st.info("No themes extracted yet. Ingest records to see aggregated patterns.")
    else:
        for idx, th in enumerate(themes[:6], 1):
            accent = OKABE_ITO[(idx - 1) % len(OKABE_ITO)]
            with st.expander(f"#{idx} — {th['theme_name']} ({th['record_count']} records across {th['distinct_sources']} sources)", expanded=(idx <= 2)):
                st.markdown(f"""
                <div class="insight-box" style="border-left:4px solid {accent}">
                    <strong style="color:{accent};font-size:1.05rem;">{th['theme_name']}</strong> · <span class="tag">{th['primary_category']}</span><br><br>
                    <strong>Plain-Language Explanation:</strong><br>{th['explanation']}<br><br>
                    <strong>Common Associated Behaviors:</strong> {th['associated_behaviours']}<br>
                    <strong>Potential Unmet Need:</strong> <em style="color:#f0e442">"{th['potential_user_need']}"</em><br><br>
                    <strong>Source Distribution:</strong> {json.dumps(th['source_distribution'])}<br>
                    <span style="font-size:0.8rem;color:#8a8ab0;">Research Gap & Scope: {th['research_gap']}</span>
                </div>
                """, unsafe_allow_html=True)

                # Representative Excerpts
                st.markdown("**Representative Verbatim Evidence:**")
                for ex in th['representative_excerpts']:
                    st.markdown(f"""
                    <div class="quote-box">
                        "{ex['quote']}"<br>
                        <span style="font-size:0.75rem;color:#9a9ab0;">— Source: {ex['source']} | Status: {ex['status']} | ID: <code>{ex['record_id']}</code></span>
                    </div>
                    """, unsafe_allow_html=True)

                # Counterexample
                if th['counterexample']:
                    st.markdown(f"""
                    <div style="background:#1b2a22;border-left:3px solid {CB_GREEN};padding:10px 14px;border-radius:0 4px 4px 0;margin-top:8px;">
                        <strong style="color:{CB_GREEN}">Counterexample (Continuation Succeeded):</strong><br>
                        "{th['counterexample']['content']}"<br>
                        <span style="font-size:0.75rem;color:#a0d8b0;">Insight: {th['counterexample']['insight']}</span>
                    </div>
                    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2: 12-MONTH USER JOURNEY
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">12-Month Investor Journey & Drop-Off Friction Points</div>', unsafe_allow_html=True)
    st.caption("Temporal breakdown showing how investor expectations, behaviors, and drop-off risks shift across the first 12 months.")

    journey_stages = [
        ('Before starting a SIP', 'KYC doubts, selecting fund, fear of equity vs FD'),
        ('Starting the first SIP', 'Bank autopay setup, initial mandate confirmation'),
        ('Early months (1-3)', 'First market dip shock, frequent app checking, NAV lag confusion'),
        ('Middle of first year (4-8)', 'Salary delay collision, flat return fatigue, emergency expenses'),
        ('Approaching month 12', 'Annual review, tax return considerations, deciding to renew/cancel'),
        ('Pausing, reducing, or stopping', 'Explicit pause, reduction in instalment amount, or cancellation'),
        ('Continuing despite uncertainty', 'Formed automated habit, ignored short-term volatility')
    ]

    j_counts = rel_df['journey_stage'].value_counts().to_dict() if not rel_df.empty else {}

    col_j1, col_j2 = st.columns([3, 2])
    with col_j1:
        j_chart_data = []
        for stage, desc in journey_stages:
            cnt = j_counts.get(stage, 0)
            j_chart_data.append({'Stage': stage, 'Records': cnt, 'Description': desc})
        
        j_df = pd.DataFrame(j_chart_data)
        fig_j = px.bar(
            j_df, x='Records', y='Stage', orientation='h',
            title='Record Volume across 12-Month Journey Stages',
            color='Stage', color_discrete_sequence=OKABE_ITO,
            text='Records'
        )
        fig_j.update_traces(textposition='outside')
        fig_j.update_layout(**base_layout(380), showlegend=False)
        st.plotly_chart(fig_j, use_container_width=True)

    with col_j2:
        st.markdown("**Journey Stage Breakdown & Key Risk:**")
        for stage, desc in journey_stages:
            cnt = j_counts.get(stage, 0)
            st.markdown(f"""
            <div class="insight-box" style="padding:10px 14px;margin:6px 0;">
                <strong>{stage}</strong> <span class="tag">n={cnt}</span><br>
                <span style="font-size:0.8rem;color:#a0a0c0;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3: OPPORTUNITY PRIORITIZATION MATRIX
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Opportunity Prioritization Matrix (Editable Weights)</div>', unsafe_allow_html=True)
    st.caption("Multi-dimensional scoring framework ranking candidate PM interventions. Adjust weights in the expander below.")

    with st.expander("⚙️ Adjust Scoring Dimension Weights", expanded=False):
        w_cols = st.columns(4)
        with w_cols[0]:
            w_freq = st.slider("Frequency Weight", 0.5, 3.0, 1.5, 0.1)
            w_breadth = st.slider("Source Breadth Weight", 0.5, 3.0, 1.2, 0.1)
        with w_cols[1]:
            w_sev = st.slider("Severity Weight", 0.5, 3.0, 2.0, 0.1)
            w_12m = st.slider("12M Relevance Weight", 0.5, 3.0, 1.8, 0.1)
        with w_cols[2]:
            w_link = st.slider("Continuation Link Weight", 0.5, 3.0, 2.2, 0.1)
            w_evid = st.slider("Evidence Strength Weight", 0.5, 3.0, 1.0, 0.1)
        with w_cols[3]:
            w_addr = st.slider("Addressability Weight", 0.5, 3.0, 1.6, 0.1)
            w_feas = st.slider("MVP Feasibility Weight", 0.5, 3.0, 1.4, 0.1)

        custom_weights = {
            'w_frequency': w_freq,
            'w_breadth': w_breadth,
            'w_severity': w_sev,
            'w_relevance_12m': w_12m,
            'w_continuation_link': w_link,
            'w_evidence_strength': w_evid,
            'w_addressability': w_addr,
            'w_feasibility': w_feas
        }

    opp_df = compute_sip_opportunity_scores(df, custom_weights=custom_weights)

    if not opp_df.empty:
        col_m1, col_m2 = st.columns([3, 2])
        
        with col_m1:
            fig_opp = px.scatter(
                opp_df,
                x='pct_sample',
                y='addressability',
                size='composite_score',
                color='sub_category',
                text='sub_category',
                title='Opportunity Matrix: Frequency (%) vs. UX Addressability (Bubble = Composite Score)',
                labels={'pct_sample': 'Frequency (% of Sample)', 'addressability': 'UX Addressability (0-1)'},
                color_discrete_sequence=OKABE_ITO
            )
            fig_opp.update_traces(textposition='top center', marker=dict(opacity=0.85, line=dict(width=1.5, color='#16161e')))
            fig_opp.update_layout(**base_layout(400), showlegend=False)
            fig_opp.add_hline(y=0.75, line_dash='dot', line_color='#4a4a6a', annotation_text="High Addressability")
            st.plotly_chart(fig_opp, use_container_width=True)

        with col_m2:
            st.markdown("**Ranked Opportunity Priorities:**")
            for _, r in opp_df.head(4).iterrows():
                st.markdown(f"""
                <div class="insight-box">
                    <strong>#{int(r['rank'])} — {r['sub_category']}</strong><br>
                    <span class="tag">Score: {r['composite_score']}</span>
                    <span class="tag">{r['record_count']} records ({r['pct_sample']}%)</span>
                    <span class="tag">{r['distinct_sources']} sources</span><br><br>
                    <span style="font-size:0.83rem;color:#c0c0d8;"><strong>PM Rationale:</strong> {r['rationale']}</span><br>
                    <span style="font-size:0.8rem;color:#f0e442;"><strong>Unmet Need:</strong> "{r['example_unmet_need']}"</span>
                </div>
                """, unsafe_allow_html=True)

        # Full dimension table
        st.markdown('<div class="section-header">Complete Multi-Dimensional Score Breakdown</div>', unsafe_allow_html=True)
        display_opps = opp_df[['rank', 'sub_category', 'record_count', 'distinct_sources', 'avg_severity', 'relevance_12m', 'continuation_link', 'addressability', 'feasibility', 'composite_score']]
        st.dataframe(display_opps.set_index('rank'), use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4: EVIDENCE EXPLORER
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Evidence Explorer — Trace Insights to Raw Text & Provenance</div>', unsafe_allow_html=True)
    st.caption("Inspect individual quotes, source URLs, confidence scores, and limitations behind every classified signal.")

    if rel_df.empty:
        st.info("No records match the current filters.")
    else:
        # Search query within content
        search_query = st.text_input("Filter records by keyword (e.g. 'mandate', 'loss', 'groww', 'salary'):", "")
        exp_df = rel_df.copy()
        if search_query:
            exp_df = exp_df[exp_df['raw_text'].str.contains(search_query, case=False, na=False)]

        st.caption(f"Showing {len(exp_df)} records")

        for _, row in exp_df.head(15).iterrows():
            badge_class = "tag-hi" if row['severity'] == 'High' else "tag-mid" if row['severity'] == 'Medium' else "tag-lo"
            with st.container():
                st.markdown(f"""
                <div class="insight-box">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong>{row['primary_category']} · {row['sub_category']}</strong>
                        <div>
                            <span class="{badge_class}">{row['severity']} Severity</span>
                            <span class="tag">{row['continuation_status']}</span>
                            <span class="tag">Conf: {row['confidence_score']:.2f}</span>
                        </div>
                    </div>
                    <div class="quote-box">
                        "{row['raw_text']}"
                    </div>
                    <div style="display:flex;gap:12px;font-size:0.75rem;color:#8a8ab0;flex-wrap:wrap;margin-top:6px;">
                        <span><strong>Source:</strong> {row['source']}</span>
                        <span><strong>Journey:</strong> {row['journey_stage']}</span>
                        <span><strong>Trigger:</strong> {row['triggering_event']}</span>
                        <span><strong>Workaround:</strong> {row['external_workaround']}</span>
                        <span><strong>ID:</strong> <code>{row['id']}</code></span>
                        {f'<span><a href="{row["source_url"]}" target="_blank" style="color:#56B4E9;">Source Link</a></span>' if row.get("source_url") else ''}
                    </div>
                    <div style="margin-top:8px;font-size:0.82rem;color:#f0e442;">
                        <strong>Potential Unmet Need:</strong> {row['potential_unmet_need']}
                    </div>
                    {f'<div style="margin-top:4px;font-size:0.75rem;color:#e89090;"><strong>Evidence Note:</strong> {row["evidence_limitations"]}</div>' if row.get("evidence_limitations") else ''}
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 5: HUMAN REVIEW & AUDIT WORKBENCH
# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Human Review & Audit Workbench</div>', unsafe_allow_html=True)
    st.caption("Inspect, approve, correct, or reject AI outputs. Human adjustments are stored separately in `sip_human_reviews`.")

    review_needed_df = rel_df[rel_df['needs_human_review'] == 1].copy() if not rel_df.empty else pd.DataFrame()
    
    col_hr1, col_hr2 = st.columns([2, 1])
    with col_hr1:
        st.markdown(f"**Records Awaiting Review: {len(review_needed_df)}** (High severity, ambiguous, or flagged by guardrails)")
    with col_hr2:
        # Export CSV Button
        if not rel_df.empty:
            csv_data = rel_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Reviewed Findings to CSV",
                data=csv_data,
                file_name=f"sip_continuation_research_export_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    if not rel_df.empty:
        # Selector for record to review
        record_ids = rel_df['id'].tolist()
        selected_rec_id = st.selectbox("Select Record ID to Inspect & Audit:", record_ids)
        target_record = rel_df[rel_df['id'] == selected_rec_id].iloc[0]

        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### Original Evidence")
            st.markdown(f"""
            <div class="insight-box">
                <strong>Record ID:</strong> <code>{target_record['id']}</code><br>
                <strong>Source Platform:</strong> {target_record['source']}<br>
                <strong>Collection Date:</strong> {target_record.get('collection_date', 'N/A')}<br><br>
                <div class="quote-box">"{target_record['raw_text']}"</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### Current Model Prediction")
            st.markdown(f"""
            - **Primary Category:** `{target_record['primary_category']}`
            - **Sub-Category:** `{target_record['sub_category']}`
            - **Journey Stage:** `{target_record['journey_stage']}`
            - **Continuation Status:** `{target_record['continuation_status']}`
            - **Severity:** `{target_record['severity']}`
            - **Confidence:** `{target_record['confidence_score']:.2f}`
            """)

        with col_right:
            st.markdown("#### Researcher Audit Action")
            with st.form(f"audit_form_{selected_rec_id}"):
                rev_action = st.radio("Review Decision:", ["Approve AI Output", "Correct Classification", "Reject (Mark Irrelevant)"])
                
                # Correction fields
                new_cat = st.selectbox("Reviewed Primary Category:", [
                    'SIP Initiation', 'Expectations', 'Post-Initiation Behaviour',
                    'Continuation Barriers', 'Pause, Reduction, or Cancellation',
                    'Continuation Enablers', 'External Workarounds', 'Trust and Comprehension',
                    'Unrelated / General Financial Noise'
                ], index=3)
                
                new_status = st.selectbox("Reviewed Continuation Status:", [
                    'Active-Continuing', 'At-Risk (Hesitating/Failing)', 'Explicitly-Paused',
                    'Explicitly-Cancelled', 'Explicitly-Reduced', 'Unclear / Not-Stated'
                ])
                
                new_sev = st.selectbox("Reviewed Severity:", ['High', 'Medium', 'Low', 'None'])
                correction_notes = st.text_area("Audit Notes / Correction Rationale:", "Reviewed and validated against ground-truth evidence.")
                reviewer_name = st.text_input("Reviewer Name:", "Fellowship Researcher")

                submit_audit = st.form_submit_button("💾 Save Human Audit Decision")
                if submit_audit:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute('''
                        INSERT OR REPLACE INTO sip_human_reviews
                        (review_id, record_id, status, reviewed_category, reviewed_sub_category,
                         reviewed_journey_stage, reviewed_continuation_status, reviewed_severity,
                         correction_notes, reviewed_at, reviewer_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        f"rev_{selected_rec_id}_{datetime.now().strftime('%s')}",
                        selected_rec_id,
                        rev_action,
                        new_cat if rev_action == "Correct Classification" else target_record['primary_category'],
                        target_record['sub_category'],
                        target_record['journey_stage'],
                        new_status if rev_action == "Correct Classification" else target_record['continuation_status'],
                        new_sev if rev_action == "Correct Classification" else target_record['severity'],
                        correction_notes,
                        datetime.now().isoformat(),
                        reviewer_name
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"Audit decision saved for {selected_rec_id} as '{rev_action}'!")
                    st.cache_data.clear()

# ════════════════════════════════════════════════════════════════════════════════
# TAB 6: AI QUALITY & GOLDEN SET EVALUATION
# ════════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Golden Set AI Evaluation & Release Gate</div>', unsafe_allow_html=True)
    st.caption("Rigorous evaluation across 20 representative test cases representing all edge cases, ambiguous finance inputs, and sentiment vs behavior dilemmas.")

    if st.button("🚀 Re-Run Golden Set Evaluation Benchmark"):
        st.cache_data.clear()

    eval_results = evaluate_golden_set()

    # KPI row for Golden Set
    ek1, ek2, ek3, ek4, ek5 = st.columns(5)
    with ek1:
        st.metric("Overall Agreement", f"{eval_results['overall_case_agreement_pct']}%")
    with ek2:
        st.metric("Relevance Accuracy", f"{eval_results['relevance_accuracy_pct']}%")
    with ek3:
        st.metric("Relevance Precision", f"{eval_results['relevance_precision_pct']}%")
    with ek4:
        st.metric("Category Agreement", f"{eval_results['category_agreement_pct']}%")
    with ek5:
        st.metric("Status Agreement", f"{eval_results['continuation_status_agreement_pct']}%")

    st.markdown(f"**Release-Gate Status:** {'🟢 READY FOR PRODUCT DISCOVERY' if eval_results['overall_case_agreement_pct'] >= 80 else '🟡 REFINEMENT RECOMMENDED'}")
    st.caption(f"{eval_results['sample_limitations']}")

    # Documented Historical Corrections
    st.markdown('<div class="section-header">Documented Actual Model Corrections</div>', unsafe_allow_html=True)
    st.caption("Documented historical examples where model hallucinations were caught and corrected by human review.")
    for doc in DOCUMENTED_HUMAN_CORRECTIONS:
        st.markdown(f"""
        <div class="insight-box" style="border-left:4px solid {CB_VERMILION}">
            <strong>Record:</strong> <code>{doc.get('record_id', doc.get('case_id'))}</code><br>
            <div class="quote-box">"{doc['raw_text']}"</div>
            <strong style="color:#e89090;">Model Initial Classification:</strong> {json.dumps(doc['ai_initial_output'])}<br>
            <strong style="color:#a0d8b0;">Human Corrected Classification:</strong> {json.dumps(doc['human_corrected_output'])}<br>
            <strong>Correction Rationale:</strong> {doc['rejection_reason']}
        </div>
        """, unsafe_allow_html=True)

    # Detailed Golden Set Results Table
    st.markdown('<div class="section-header">Detailed 20-Case Benchmark Table</div>', unsafe_allow_html=True)
    cases_df = pd.DataFrame(eval_results['detailed_cases'])
    st.dataframe(cases_df[['case_id', 'edge_case_type', 'expected_category', 'ai_category', 'expected_status', 'ai_status', 'case_passed']], use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 7: INGESTION WORKBENCH
# ════════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown('<div class="section-header">Data Ingestion & Dataset Import Workbench</div>', unsafe_allow_html=True)
    st.caption("Upload CSV / JSON feedback spreadsheets, enter manual user feedback, or run scrapers.")

    ing_col1, ing_col2 = st.columns(2)
    
    with ing_col1:
        st.markdown("#### 📁 File Upload (CSV / JSON)")
        uploaded_file = st.file_uploader("Upload Public Feedback Spreadsheet (CSV or JSON):", type=['csv', 'json'])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    up_df = pd.read_csv(uploaded_file)
                else:
                    up_df = pd.read_json(uploaded_file)
                
                st.write(f"Preview ({len(up_df)} records):")
                st.dataframe(up_df.head(3))
                
                # Content column identification
                content_col = st.selectbox("Select column containing feedback text:", up_df.columns)
                source_val = st.text_input("Source label for this batch:", "CSV Import")
                
                if st.button("📥 Import & Classify File Records"):
                    imported_recs = []
                    for idx, r in up_df.iterrows():
                        txt = str(r[content_col])
                        imported_recs.append({
                            'id': f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx}",
                            'source': source_val,
                            'content': txt,
                            'timestamp': datetime.now().isoformat(),
                            'url': str(r.get('url', '')),
                            'metadata': {'imported_from': uploaded_file.name}
                        })
                    saved_n = save_records(imported_recs, db_path=DB_PATH)
                    st.success(f"Saved {saved_n} clean records. Now classifying...")
                    
                    for rec in imported_recs:
                        insight = classify_single_record(rec['content'])
                        insight['id'] = rec['id']
                        insight['source'] = rec['source']
                        save_sip_insight(insight, db_path=DB_PATH)
                    st.success("Classification complete! Refresh to see new data.")
                    st.cache_data.clear()
            except Exception as e:
                st.error(f"Error processing upload: {e}")

    with ing_col2:
        st.markdown("#### ✍️ Manual Text / Interview Ingestion")
        with st.form("manual_entry_form"):
            man_content = st.text_area("Enter user feedback / interview transcript excerpt:", placeholder="e.g. Started my SIP 3 months ago in Groww, but autopay bounced yesterday...")
            man_source = st.selectbox("Source Platform:", ["User Interview", "Reddit Discussion", "Play Store Review", "Twitter/X Post", "YouTube Comment", "Other Forum"])
            man_url = st.text_input("Source URL (optional):", "")
            submit_manual = st.form_submit_button("⚡ Ingest & Analyze Immediately")

            if submit_manual and man_content:
                man_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                rec_payload = [{
                    'id': man_id,
                    'source': man_source,
                    'content': man_content,
                    'timestamp': datetime.now().isoformat(),
                    'url': man_url,
                    'metadata': {'ingestion': 'manual_entry'}
                }]
                save_records(rec_payload, db_path=DB_PATH)
                insight = classify_single_record(man_content)
                insight['id'] = man_id
                insight['source'] = man_source
                save_sip_insight(insight, db_path=DB_PATH)
                st.success(f"Record {man_id} successfully classified as '{insight['primary_category']}' -> '{insight['sub_category']}'!")
                st.cache_data.clear()

    st.divider()
    st.markdown("#### 📄 Standard CSV Schema Template")
    sample_template = pd.DataFrame([
        {
            "id": "playstore_sample_01",
            "source": "Play Store (Groww)",
            "content": "Autopay failed when my salary was delayed by 2 days. Bank charged ₹295 penalty.",
            "timestamp": "2026-09-15T10:30:00",
            "url": "https://play.google.com/store/apps/details?id=com.nextbillion.groww",
            "metadata": '{"app": "Groww", "rating": 1}'
        }
    ])
    st.download_button(
        "Download Sample CSV Template",
        sample_template.to_csv(index=False).encode('utf-8'),
        "sip_feedback_sample_template.csv",
        "text/csv"
    )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(f"SIP Continuation Discovery Engine · {len(df)} total imported records · {relevant_count} relevant SIP signals · Product Management Fellowship Project")
