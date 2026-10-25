"""
Myntra Wishlist Conversion — AI Discovery Engine Dashboard (V2)
AI-powered friction discovery engine for Myntra wishlist-to-purchase conversion.
"""

import sys
import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Add analytics to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analytics'))
from opportunity_scorer import (
    load_enriched_data,
    compute_opportunity_scores,
    compute_friction_matrix,
    compute_segment_breakdown,
    compute_external_seeking_breakdown,
    compute_decision_factor_frequency,
    get_top_unmet_needs,
    SEVERITY_WEIGHTS,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Myntra AI Discovery Engine",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Colorblind-safe Okabe-Ito palette (distinguishable by all CVD types) ──────
# Ref: https://jfly.uni-koeln.de/color/
CB_ORANGE    = "#E69F00"
CB_SKYBLUE   = "#56B4E9"
CB_GREEN     = "#009E73"
CB_YELLOW    = "#F0E442"
CB_BLUE      = "#0072B2"
CB_VERMILION = "#D55E00"
CB_PINK      = "#CC79A7"
CB_DARK      = "#1a1a2a"

OKABE_ITO = [CB_ORANGE, CB_SKYBLUE, CB_GREEN, CB_YELLOW, CB_BLUE, CB_VERMILION, CB_PINK]

# Severity — shape + color (never rely on color alone)
SEV_COLORS = {"High": CB_VERMILION, "Medium": CB_ORANGE, "Low": CB_SKYBLUE}

# ── Plotly base layout (reused on every chart) ────────────────────────────────
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

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Base ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    /* ── Metric card — neutral dark, high contrast text ── */
    .metric-card {
        background: #1e1e2e;
        border: 1.5px solid #3a3a5e;
        border-radius: 10px;
        padding: 20px 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #E69F00;          /* CB orange — visible to all CVD types */
        letter-spacing: -0.02em;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #9a9ab0;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 6px;
        font-weight: 500;
    }
    /* ── Section header — strong contrast, no color-coding ── */
    .section-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;                  /* pure white — max contrast on dark bg */
        background: #1e1e2e;
        border-left: 4px solid #56B4E9; /* CB sky-blue — visible to all CVD */
        padding: 8px 12px;
        margin: 24px 0 12px 0;
        border-radius: 0 6px 6px 0;
        letter-spacing: -0.01em;
    }
    /* ── Insight card — clean, readable, enough contrast ── */
    .insight-box {
        background: #1e1e2e;
        border: 1.5px solid #3a3a5e;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        font-size: 0.9rem;
        color: #e8e8f0;                  /* near-white — not grey */
        line-height: 1.65;
    }
    /* ── Tag pills — neutral so they never conflict with chart colors ── */
    .tag {
        display: inline-block;
        background: #2a2a40;
        color: #c8c8e0;
        border: 1px solid #4a4a6a;
        border-radius: 4px;
        padding: 2px 9px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 4px;
        margin-bottom: 2px;
    }
    .tag-hi  { background:#3d1f1a; color:#E69F00; border-color:#5a3020; }  /* orange */
    .tag-mid { background:#1e2a3a; color:#56B4E9; border-color:#2a3a50; }  /* sky blue */
    .tag-lo  { background:#1a2e2a; color:#009E73; border-color:#204840; }  /* green */
    /* ── Tab bar ── */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.85rem;
        font-weight: 500;
        color: #c8c8e0;          /* readable on dark bg */
    }
    .stTabs [aria-selected="true"] {
        color: #E69F00 !important;
        border-bottom-color: #E69F00 !important;
        font-weight: 700 !important;
    }
    /* ── Dataframe — boost readability ── */
    .stDataFrame td { font-size: 0.85rem !important; }
    .stDataFrame th { font-size: 0.8rem !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_data():
    try:
        df = load_enriched_data()
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛍️ Myntra Discovery Engine")
    st.markdown("**V2 — PM Opportunity Discovery**")
    st.divider()

    if df.empty:
        st.error("No data. Run classifier first.")
        st.stop()

    st.success(f"{len(df)} records classified")

    # Filters
    sources = ['All'] + sorted(df['source'].unique().tolist())
    sel_source = st.selectbox("Source", sources)

    severities = ['All', 'High', 'Medium', 'Low']
    sel_severity = st.selectbox("Severity", severities)

    st.divider()
    st.caption("Built with Gemini 3.6 Flash + Ollama Fallback")
    st.caption("Data: Play Store · Reddit · YouTube")

# Apply filters
fdf = df.copy()
if sel_source != 'All':
    fdf = fdf[fdf['source'] == sel_source]
if sel_severity != 'All':
    fdf = fdf[fdf['severity'] == sel_severity]

# ── Header metrics ────────────────────────────────────────────────────────────

st.markdown("# 🛍️ Myntra Wishlist Conversion — AI Discovery Engine")
st.markdown("> **An AI-powered discovery system that converts unstructured user evidence into prioritised behavioural insights and testable Growth opportunities.**")
st.markdown(f"*Powered by Gemini 3.6 Flash · {len(fdf)} user signals analysed · Evidence: Play Store, Reddit & YouTube*")
st.divider()

# Top KPI row
col1, col2, col3, col4, col5 = st.columns(5)

genuine_intent_pct = (fdf['wishlist_mode'] == 'Genuine-Intent').mean() * 100 if not fdf.empty else 0
high_sev_pct = (fdf['severity'] == 'High').mean() * 100 if not fdf.empty else 0
size_doubt_pct = (fdf['postponement_trigger'] == 'Size-Doubt').mean() * 100 if not fdf.empty else 0
external_pct = (fdf['external_source'] != 'None').mean() * 100 if 'external_source' in fdf.columns and not fdf.empty else 0
deferred_count = (fdf['intent'] == 'Deferred-Intent').sum() if not fdf.empty else 0

for col, val, label, sublabel in [
    (col1, f"{genuine_intent_pct:.0f}%", "Genuine Purchase Intent", "will buy · blocked by friction"),
    (col2, f"{high_sev_pct:.0f}%",       "High Severity Friction",   "actively prevents checkout"),
    (col3, f"{size_doubt_pct:.0f}%",     "Size-Doubt Blocked",       "#1 postponement trigger"),
    (col4, f"{external_pct:.0f}%",       "Seek External Info",       "leave Myntra to validate"),
    (col5, str(deferred_count),           "Deferred-Intent Users",    "real intent, fixable friction"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{val}</div>
            <div class="metric-label">{label}</div>
            <div style="font-size:0.68rem;color:#6a6a8a;margin-top:4px">{sublabel}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Executive Brief",
    "🎯 Opportunity Matrix",
    "🛒 Wishlist Behavior",
    "🚧 Postponement Triggers",
    "🔍 External Seeking",
    "👤 Segment Analysis",
    "💡 Unmet Needs"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 0 — EXECUTIVE BRIEF (Quantified Summary for PM submission)
# ════════════════════════════════════════════════════════════════════════════
with tab0:
    st.markdown('<div class="section-header">AI Discovery Engine — Quantified Findings</div>', unsafe_allow_html=True)
    st.caption(f"Based on {len(fdf)} classified user signals scraped from Play Store, Reddit & YouTube.")

    if not fdf.empty:
        total = len(fdf)

        # ── Top Friction Breakdown ───────────────────────────────────────────
        st.markdown('<div class="section-header">🔥 Top Friction Categories — Why Users Don\'t Buy</div>', unsafe_allow_html=True)
        friction_df = fdf[fdf['friction_category'] != 'None']['friction_category'].value_counts().reset_index()
        friction_df.columns = ['Friction Category', 'Count']
        friction_df['% of All Users'] = (friction_df['Count'] / total * 100).round(1)
        friction_df['Rank'] = range(1, len(friction_df) + 1)

        col_a, col_b = st.columns([2, 3])
        with col_a:
            rank_colors = [CB_ORANGE, CB_SKYBLUE, CB_GREEN, CB_BLUE, CB_PINK]
            for _, row in friction_df.head(5).iterrows():
                idx = int(row['Rank']) - 1
                color = rank_colors[min(idx, len(rank_colors)-1)]
                st.markdown(f"""
                <div class="insight-box">
                    <strong style="color:{color}">#{row['Rank']} {row['Friction Category']}</strong><br>
                    <span class="tag">{row['Count']} users</span>
                    <span class="tag">{row['% of All Users']}% of total</span>
                </div>
                """, unsafe_allow_html=True)
        with col_b:
            fig_f = px.bar(
                friction_df.head(5), x='% of All Users', y='Friction Category',
                orientation='h', text='% of All Users',
                title=f'Friction Distribution (% of {total} users)',
                color='Friction Category',
                color_discrete_sequence=OKABE_ITO,
            )
            fig_f.update_traces(texttemplate='%{text:.1f}%', textposition='outside',
                                marker_line_color='#16161e', marker_line_width=1.5)
            fig_f.update_layout(**base_layout(300), showlegend=False)
            st.plotly_chart(fig_f, use_container_width=True)

        # ── Postponement Triggers ────────────────────────────────────────────
        st.markdown('<div class="section-header">⏸️ Why Purchases Are Postponed — Ranked</div>', unsafe_allow_html=True)
        trig_df = fdf[fdf['postponement_trigger'] != 'None']['postponement_trigger'].value_counts().reset_index()
        trig_df.columns = ['Trigger', 'Count']
        trig_df['% of All Users'] = (trig_df['Count'] / total * 100).round(1)
        high_sev = fdf[fdf['severity'] == 'High']['postponement_trigger'].value_counts()
        trig_df['High Severity Count'] = trig_df['Trigger'].map(high_sev).fillna(0).astype(int)
        trig_df['% High Severity'] = (trig_df['High Severity Count'] / trig_df['Count'] * 100).round(1)

        col_c, col_d = st.columns([3, 2])
        with col_c:
            fig_t = px.bar(
                trig_df, x='Trigger', y='% of All Users',
                text='% of All Users',
                title='Postponement Triggers — % Users Affected',
                color='Trigger',
                color_discrete_sequence=OKABE_ITO,
            )
            fig_t.update_traces(
                texttemplate='%{text:.1f}%', textposition='outside',
                marker_line_color='#16161e', marker_line_width=1.5
            )
            fig_t.update_layout(**base_layout(320))
            # Annotate severity inline so no separate color needed
            for _, r in trig_df.iterrows():
                fig_t.add_annotation(
                    x=r['Trigger'], y=r['% of All Users'],
                    text=f"{r['% High Severity']:.0f}% high-sev",
                    showarrow=False, yshift=22,
                    font=dict(size=10, color='#9a9ab0')
                )
            st.plotly_chart(fig_t, use_container_width=True)
        with col_d:
            st.dataframe(
                trig_df[['Trigger', '% of All Users', '% High Severity']].set_index('Trigger'),
                use_container_width=True
            )

        # ── Wishlist Intent Split ────────────────────────────────────────────
        st.markdown('<div class="section-header">🛒 Wishlist Intent — Purchase vs. Bookmarking</div>', unsafe_allow_html=True)
        col_e, col_f = st.columns(2)
        with col_e:
            wm = fdf['wishlist_mode'].value_counts().reset_index()
            wm.columns = ['Mode', 'Count']
            wm['%'] = (wm['Count'] / total * 100).round(1)
            fig_w = px.pie(wm, names='Mode', values='Count',
                           title='Wishlist Mode Split',
                           color_discrete_sequence=OKABE_ITO,
                           hole=0.35)
            fig_w.update_traces(textinfo='label+percent', textfont_size=12)
            fig_w.update_layout(**base_layout(300))
            st.plotly_chart(fig_w, use_container_width=True)
        with col_f:
            genuine_pct = (fdf['wishlist_mode'] == 'Genuine-Intent').mean() * 100
            browse_pct  = (fdf['wishlist_mode'] == 'Browse-Saving').mean() * 100
            price_pct   = (fdf['wishlist_mode'] == 'Price-Waiting').mean() * 100
            ext_pct     = (fdf['external_source'] != 'None').mean() * 100 if 'external_source' in fdf.columns else 0
            st.markdown(f"""
            <div class="insight-box">
                <strong style="color:{CB_ORANGE}">Key Numbers</strong><br><br>
                ■ <strong>{genuine_pct:.1f}%</strong> Genuine Purchase Intent (blocked by friction)<br>
                ■ <strong>{browse_pct:.1f}%</strong> Browse-Saving / mood-board behaviour<br>
                ■ <strong>{price_pct:.1f}%</strong> Waiting for a discount/sale<br>
                ■ <strong>{ext_pct:.1f}%</strong> Leaving Myntra to validate elsewhere<br><br>
                <span style="color:#6a6a8a;font-size:0.8rem">Based on {total} classified records</span>
            </div>
            """, unsafe_allow_html=True)

        # ── Top 3 PM Recommendations ─────────────────────────────────────────
        st.markdown('<div class="section-header">🚀 Top 3 Non-Monetary Product Opportunities</div>', unsafe_allow_html=True)
        top_friction = friction_df.head(3)['Friction Category'].tolist()
        recommendations = {
            'Fit/Size':           ('📏 Interactive Fit Assistant', 'Size confidence tool — body-measurement-based size predictor with model-type photos for each product. Eliminates #1 reason users don\'t convert.'),
            'Fabric/Material':    ('🧵 Verified Fabric Reviews', 'User-submitted texture/feel ratings + short video clips. Addresses material doubt without returning items.'),
            'Styling/Occasion':   ('👗 Occasion Styling Guide', 'AI-powered "How to wear this" card on each product page — shows 3 outfit pairings for context (work, casual, festive).'),
            'Trust/Authenticity': ('⭐ Verified Buyer Badges', 'Highlight reviews from verified purchasers with photo proof. Builds trust without discount signals.'),
            'Social-Validation':  ('👥 Community Try-On Feed', 'User-submitted try-on photos/reels per product. Replaces the need to check Instagram/YouTube.'),
            'Delivery/Return':    ('🔄 Instant Exchange Promise', 'One-tap size exchange with 24hr turnaround promise — removes return anxiety as a blocker.'),
        }
        for i, cat in enumerate(top_friction, 1):
            if cat in recommendations:
                title, desc = recommendations[cat]
                pct_val = friction_df[friction_df['Friction Category']==cat]['% of All Users'].values[0]
                accent = OKABE_ITO[(i - 1) % len(OKABE_ITO)]
                st.markdown(f"""
                <div class="insight-box" style="border-color:{accent}60;border-left:3px solid {accent}">
                    <strong style="color:{accent}">#{i} — {title}</strong><br>
                    <span class="tag">Addresses: {cat}</span>
                    <span class="tag">{pct_val}% of users</span><br><br>
                    {desc}
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — OPPORTUNITY MATRIX (Q10, Q11)
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Opportunity Matrix — Frequency vs. Conversion Impact</div>', unsafe_allow_html=True)
    st.caption("Friction areas ranked by how often they appear, how badly they block purchase, and how fixable they are through product changes.")

    scores = compute_opportunity_scores(fdf)

    if not scores.empty:
        col_a, col_b = st.columns([3, 2])

        with col_a:
            # Bubble chart: x=pct_of_total, y=conversion_impact, size=total_opportunity
            fig = px.scatter(
                scores,
                x='pct_of_total',
                y='conversion_impact',
                size='total_opportunity',
                color='postponement_trigger',
                text='postponement_trigger',
                title='Opportunity Matrix — Bubble size = Opportunity Score',
                labels={
                    'pct_of_total': '% of Users Affected',
                    'conversion_impact': 'Conversion Impact (Fixability)',
                    'total_opportunity': 'Opportunity Score'
                },
                color_discrete_sequence=OKABE_ITO,
            )
            fig.update_traces(textposition='top center', marker=dict(opacity=0.85,
                              line=dict(width=1.5, color='#16161e')))
            fig.update_layout(**base_layout(380), showlegend=False)
            fig.add_hline(y=0.5, line_dash='dot', line_color='#4a4a6a',
                          annotation_text="Fix threshold", annotation_font_color='#9a9ab0')
            fig.add_vline(x=scores['pct_of_total'].median(), line_dash='dot', line_color='#4a4a6a')
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown('<div class="section-header">Ranked Opportunities</div>', unsafe_allow_html=True)
            for _, row in scores.iterrows():
                impact_cls = "tag-hi" if row['conversion_impact'] > 0.7 else "tag-mid" if row['conversion_impact'] > 0.4 else "tag-lo"
                impact_label = "High" if row['conversion_impact'] > 0.7 else "Medium" if row['conversion_impact'] > 0.4 else "Low"
                st.markdown(f"""
                <div class="insight-box">
                    <strong>{row['postponement_trigger']}</strong><br>
                    <span class="tag">{row['pct_of_total']:.0f}% of users</span>
                    <span class="tag">Score: {row['total_opportunity']:.0f}</span>
                    <span class="{impact_cls}">{impact_label} impact</span><br>
                    <span style="color:#6a6a8a;font-size:0.8rem">{row['pct_genuine_intent']:.0f}% genuine intent · {row['conversion_impact']:.0%} fixable</span>
                </div>
                """, unsafe_allow_html=True)

        # Friction category heatmap
        st.markdown('<div class="section-header">Friction Category × Severity Heatmap</div>', unsafe_allow_html=True)
        matrix = compute_friction_matrix(fdf)
        if not matrix.empty:
            heat_data = matrix.drop(columns=['weighted_score'], errors='ignore')
            fig2 = px.imshow(
                heat_data,
                text_auto=True,
                color_continuous_scale='Blues',
                title='Count of records by Friction × Severity',
            )
            fig2.update_layout(**base_layout(320))
            st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — WISHLIST BEHAVIOR (Q1, Q8)
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Wishlist Mode Breakdown</div>', unsafe_allow_html=True)
    st.caption("Identifies whether users add items with genuine purchase intent or as mood-board saving — and which group is blocked by friction.")

    col_a, col_b = st.columns(2)

    with col_a:
        if 'wishlist_mode' in fdf.columns:
            wm_counts = fdf['wishlist_mode'].value_counts().reset_index()
            wm_counts.columns = ['mode', 'count']
            fig = px.pie(
                wm_counts, names='mode', values='count',
                title='Wishlist Mode Distribution',
                color_discrete_sequence=OKABE_ITO,
                hole=0.35,
            )
            fig.update_traces(textinfo='label+percent', textfont_size=12)
            fig.update_layout(**base_layout(340))
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if 'intent' in fdf.columns:
            intent_counts = fdf['intent'].value_counts().reset_index()
            intent_counts.columns = ['intent', 'count']
            fig2 = px.bar(
                intent_counts, x='count', y='intent', orientation='h',
                title='User Intent Distribution',
                color='intent',
                color_discrete_sequence=OKABE_ITO,
                text='count',
            )
            fig2.update_traces(textposition='outside', marker_line_color='#16161e', marker_line_width=1.5)
            fig2.update_layout(**base_layout(340), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    # Wishlist mode vs intent cross-tab
    st.markdown('<div class="section-header">Intent × Wishlist Mode Cross-Tab</div>', unsafe_allow_html=True)
    if 'wishlist_mode' in fdf.columns and 'intent' in fdf.columns:
        cross = pd.crosstab(fdf['intent'], fdf['wishlist_mode'])
        fig3 = px.imshow(
            cross, text_auto=True, color_continuous_scale='Blues',
            title='How intent maps to wishlist behavior'
        )
        fig3.update_layout(**base_layout(300))
        st.plotly_chart(fig3, use_container_width=True)

    # Key decision factors identified from user language
    st.markdown('<div class="section-header">Identified Decision Factors — What Users Weigh Before Buying</div>', unsafe_allow_html=True)
    factor_freq = compute_decision_factor_frequency(fdf)
    if not factor_freq.empty:
        fig4 = px.bar(
            x=factor_freq.values, y=factor_freq.index, orientation='h',
            title='How often each factor is mentioned',
            color=factor_freq.index,
            color_discrete_sequence=OKABE_ITO,
            labels={'x': 'Mentions', 'y': 'Factor'},
            text=factor_freq.values,
        )
        fig4.update_traces(textposition='outside', marker_line_color='#16161e', marker_line_width=1.5)
        fig4.update_layout(**base_layout(320), showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — POSTPONEMENT TRIGGERS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Predicted Friction — Why Wishlisted Items Are Not Purchased</div>', unsafe_allow_html=True)
    st.caption("Ranked by frequency and severity. The triggers at the top are the highest-priority product interventions to unblock conversion.")

    if 'postponement_trigger' in fdf.columns:
        col_a, col_b = st.columns([2, 1])

        with col_a:
            trigger_counts = fdf.groupby(['postponement_trigger', 'severity']).size().reset_index(name='count')
            fig = px.bar(
                trigger_counts,
                x='count', y='postponement_trigger',
                color='severity',
                orientation='h',
                title='Postponement Triggers by Severity',
                color_discrete_map=SEV_COLORS,
                barmode='stack',
                text='count',
            )
            fig.update_traces(textposition='inside', textfont_size=11)
            fig.update_layout(**base_layout(360))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            scores = compute_opportunity_scores(fdf)
            if not scores.empty:
                st.markdown("**Opportunity Scores**")
                for _, r in scores.iterrows():
                    pct = r['pct_of_total']
                    score = r['total_opportunity']
                    st.metric(
                        label=r['postponement_trigger'],
                        value=f"{pct:.0f}% of users",
                        delta=f"Score: {score:.0f}",
                        delta_color="normal"
                    )

        # Comparison dimension breakdown (Q5)
        st.markdown('<div class="section-header">How Users Compare — Identified Comparison Dimensions</div>', unsafe_allow_html=True)
        if 'comparison_dimension' in fdf.columns:
            comparers = fdf[fdf['comparison_dimension'] != 'Not-Comparing']
            if not comparers.empty:
                comp_counts = comparers['comparison_dimension'].value_counts().reset_index()
                comp_counts.columns = ['dimension', 'count']
                fig2 = px.pie(
                    comp_counts, names='dimension', values='count',
                    title=f'Comparison Dimensions ({len(comparers)} users comparing)',
                    color_discrete_sequence=OKABE_ITO,
                    hole=0.35,
                )
                fig2.update_traces(textinfo='label+percent', textfont_size=12)
                fig2.update_layout(**base_layout(300))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No comparison behavior detected in filtered data.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — EXTERNAL SEEKING (Q6)
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Detected Platform Leakage — Where Users Go to Validate</div>', unsafe_allow_html=True)
    st.caption("High-intent users who leave Myntra to verify on YouTube, Reddit or Instagram before deciding — a trust and information gap.")

    ext_breakdown = compute_external_seeking_breakdown(fdf)

    if not ext_breakdown.empty:
        col_a, col_b = st.columns(2)

        with col_a:
            fig = px.bar(
                ext_breakdown,
                x='external_source', y='count',
                color='external_source',
                title='External Sources Used',
                color_discrete_sequence=OKABE_ITO,
                labels={'count': 'Users', 'external_source': 'Platform'},
                text='count',
            )
            fig.update_traces(textposition='outside', marker_line_color='#16161e', marker_line_width=1.5)
            fig.update_layout(**base_layout(340))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("**Why they go external**")
            for i, (_, row) in enumerate(ext_breakdown.iterrows()):
                accent = OKABE_ITO[i % len(OKABE_ITO)]
                st.markdown(f"""
                <div class="insight-box">
                    <strong style="color:{accent}">{row['external_source']}</strong>
                    <span class="tag">{row['pct_of_seekers']:.0f}% of seekers</span><br>
                    Main trigger: <strong>{row['top_trigger']}</strong><br>
                    <span style="color:#9a9ab0;font-size:0.82rem">{row['pct_high_severity']:.0f}% high severity</span>
                </div>
                """, unsafe_allow_html=True)

        # External vs non-external friction comparison
        st.markdown('<div class="section-header">External Seekers vs. Non-Seekers — Friction Comparison</div>', unsafe_allow_html=True)
        if 'external_source' in fdf.columns:
            fdf['seeks_external'] = fdf['external_source'] != 'None'
            ext_friction = fdf.groupby(['seeks_external', 'friction_category']).size().reset_index(name='count')
            ext_friction['seeks_external'] = ext_friction['seeks_external'].map({True: 'Seeks External Info', False: 'Stays on Myntra'})
            fig2 = px.bar(
                ext_friction, x='friction_category', y='count',
                color='seeks_external', barmode='group',
                title='What drives users to seek info externally?',
                color_discrete_map={'Seeks External Info': CB_ORANGE, 'Stays on Myntra': CB_SKYBLUE},
                text='count',
            )
            fig2.update_traces(textposition='outside')
            fig2.update_layout(**base_layout(320))
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No external seeking detected in filtered records.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — SEGMENT ANALYSIS (Q9)
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Behavioural Signals — How Purchase Patterns Differ by User Type</div>', unsafe_allow_html=True)
    st.caption("Segments inferred from language signals in each record.")

    seg_breakdown = compute_segment_breakdown(fdf)

    if not seg_breakdown.empty and len(seg_breakdown) > 1:
        col_a, col_b = st.columns([3, 2])

        with col_a:
            fig = px.bar(
                seg_breakdown,
                x='user_segment_signal', y='count',
                color='user_segment_signal',
                title='User Segments by Volume',
                color_discrete_sequence=OKABE_ITO,
                labels={'count': 'Records', 'user_segment_signal': 'Segment'},
                text='count',
            )
            fig.update_traces(textposition='outside', marker_line_color='#16161e', marker_line_width=1.5)
            fig.update_layout(**base_layout(340), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("**Segment Profiles**")
            for i, (_, row) in enumerate(seg_breakdown.iterrows()):
                if row['user_segment_signal'] == 'Unclear':
                    continue
                accent = OKABE_ITO[i % len(OKABE_ITO)]
                st.markdown(f"""
                <div class="insight-box">
                    <strong style="color:{accent}">{row['user_segment_signal']}</strong>
                    <span class="tag">n={row['count']}</span><br>
                    Top trigger: <strong>{row['top_trigger']}</strong><br>
                    Top friction: <strong>{row['top_friction']}</strong><br>
                    <span class="tag">{row['pct_external_seeking']:.0f}% seek external info</span>
                    <span class="tag">{row['pct_genuine_intent']:.0f}% genuine intent</span>
                </div>
                """, unsafe_allow_html=True)

        # Segment × wishlist mode heatmap
        st.markdown('<div class="section-header">Segment × Wishlist Mode</div>', unsafe_allow_html=True)
        seg_wm = pd.crosstab(fdf['user_segment_signal'], fdf['wishlist_mode'])
        fig2 = px.imshow(
            seg_wm, text_auto=True, color_continuous_scale='Blues',
            title='How each segment uses the wishlist'
        )
        fig2.update_layout(**base_layout(300))
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("Segment signals are 'Unclear' for most records — this is expected with Play Store review data. Richer sources (Reddit posts, interviews) would improve signal.")
        # Still show overall breakdown
        if 'user_segment_signal' in fdf.columns:
            seg_counts = fdf['user_segment_signal'].value_counts().reset_index()
            fig = px.pie(seg_counts, names='user_segment_signal', values='count',
                         title='Segment Signal Distribution',
                         color_discrete_sequence=OKABE_ITO,
                         hole=0.35)
            fig.update_traces(textinfo='label+percent', textfont_size=12)
            fig.update_layout(**base_layout(360))
            st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — UNMET NEEDS
# ════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Unmet Needs — Patterns That Predict Non-Purchase</div>', unsafe_allow_html=True)
    st.caption("Recurring unmet needs clustered by friction type and trigger — each cluster is a direct product opportunity.")

    unmet = get_top_unmet_needs(fdf, n=15)

    if not unmet.empty:
        for _, row in unmet.iterrows():
            freq_cls = "tag-hi" if row['count'] >= 10 else "tag-mid" if row['count'] >= 5 else "tag-lo"
            freq_label = "High freq" if row['count'] >= 10 else "Med freq" if row['count'] >= 5 else "Low freq"
            st.markdown(f"""
            <div class="insight-box">
                <span class="{freq_cls}">n={row['count']} · {freq_label}</span>
                <span class="tag">{row['friction_category']}</span>
                <span class="tag">{row['postponement_trigger']}</span><br><br>
                <em style="color:#e8e8e8">"{row['example_need']}"</em>
            </div>
            """, unsafe_allow_html=True)

        # Full unmet needs table
        st.markdown('<div class="section-header">Full Unmet Needs Explorer</div>', unsafe_allow_html=True)
        if 'unmet_need' in fdf.columns:
            display_df = fdf[['source', 'intent', 'friction_category', 'postponement_trigger', 'severity', 'unmet_need']]\
                .sort_values('severity', ascending=False)\
                .head(50)
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "unmet_need": st.column_config.TextColumn("Unmet Need", width="large"),
                    "severity": st.column_config.TextColumn("Severity", width="small"),
                }
            )
    else:
        st.info("No unmet needs extracted yet. Run the classifier with V2 schema.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Myntra AI Discovery Engine · 455 signals · Play Store · Reddit · YouTube · Classified with Gemini 3.6 Flash")
