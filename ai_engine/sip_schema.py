from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class SIPPresetCategory:
    """Canonical SIP Taxonomy Categories matching Fellowship Assignment Section 6."""
    INITIATION = "SIP Initiation"
    EXPECTATIONS = "Expectations"
    POST_INITIATION_BEHAVIOUR = "Post-Initiation Behaviour"
    CONTINUATION_BARRIERS = "Continuation Barriers"
    PAUSE_REDUCE_CANCEL = "Pause, Reduction, or Cancellation"
    CONTINUATION_ENABLERS = "Continuation Enablers"
    EXTERNAL_WORKAROUNDS = "External Workarounds"
    TRUST_COMPREHENSION = "Trust and Comprehension"
    UNRELATED_NOISE = "Unrelated / General Financial Noise"

class SIPInsightSchema(BaseModel):
    """
    PM-grade classification schema for 12-Month SIP Continuation Discovery.
    Focuses on understanding WHY first-time mutual fund investors continue or drop out.
    """

    # ── 1. Relevance Filter ───────────────────────────────────────────────────
    is_sip_continuation_relevant: bool = Field(
        description="True if the text relates to starting, holding, managing, pausing, failing, or cancelling a mutual fund SIP. False if purely stock trading, crypto, or unrelated."
    )

    relevance_reason: str = Field(
        description="Brief explanation of why this record is or is not relevant to SIP continuation research."
    )

    # ── 2. Primary Research Taxonomy Category (Section 6) ─────────────────────
    primary_category: Literal[
        'SIP Initiation',
        'Expectations',
        'Post-Initiation Behaviour',
        'Continuation Barriers',
        'Pause, Reduction, or Cancellation',
        'Continuation Enablers',
        'External Workarounds',
        'Trust and Comprehension',
        'Unrelated / General Financial Noise'
    ] = Field(description="The primary category representing the core user challenge or observation.")

    # ── 3. Granular Sub-Category Label ────────────────────────────────────────
    sub_category: Literal[
        # A. Initiation
        'First-Time Motivation',
        'Friend/Family Advice',
        'Influencer/Social Media Advice',
        'Habit Formation Goal',
        'Tax Saving (ELSS)',
        'Pre-Start Confusion',

        # B. Expectations
        'Expected Quick Growth',
        'Expected Predictability/Safety',
        'Expected Easy Withdrawal',
        'Misunderstood Compounding/Time Horizon',

        # C. Post-Initiation Behaviour
        'Daily/Frequent Portfolio Checking',
        'Comparing Returns with Expectation',
        'Panic on First Market Dip',
        'Instalment Verification Checking',

        # D. Continuation Barriers
        'Bank Mandate / Autopay Failure',
        'Salary Delay / Variable Income',
        'Unexpected Emergency Expense',
        'Negative Return Disappointment',
        'App/Folio Navigation Confusion',
        'Nav / Units Allocation Confusion',
        'Competing Financial Priority',

        # E. Pause, Reduction, Cancellation
        'Explicit SIP Cancellation',
        'Explicit SIP Pause',
        'Instalment Amount Reduced',
        'Repeated Failed Debit Abandonment',

        # F. Continuation Enablers
        'Clear Growth Explanations',
        'Flexible Instalment Date/Amount',
        'Prompt Mandate Issue Recovery',
        'Automated Habit Confidence',

        # G. External Workarounds
        'Asking Reddit/Forums for Guidance',
        'Searching YouTube for SIP Clarification',
        'Consulting Bank/Distributor/Agent',
        'Searching Google for Fund Performance',

        # H. Trust & Comprehension
        'Expense Ratio / Hidden Charge Doubt',
        'Confusing Financial Jargon',
        'Unclear SIP Status / Folio Number',
        'Platform Trust / Glitch Concern',

        # Fallback
        'General Investing Discussion',
        'Other / Unclear'
    ] = Field(description="Granular taxonomy label. Choose the most specific supported label.")

    # ── 4. User Journey Stage (Section 12) ────────────────────────────────────
    journey_stage: Literal[
        'Before starting a SIP',
        'Starting the first SIP',
        'Early months (1-3)',
        'Middle of first year (4-8)',
        'Approaching month 12',
        'Pausing, reducing, or stopping',
        'Continuing despite uncertainty',
        'Unclear / Unstated'
    ] = Field(description="Assign a journey stage ONLY when temporal or stage evidence exists in text.")

    # ── 5. Continuation Status (Strict Evidence Rule) ─────────────────────────
    continuation_status: Literal[
        'Active-Continuing',
        'Explicitly-Paused',
        'Explicitly-Cancelled',
        'Explicitly-Reduced',
        'At-Risk (Hesitating/Failing)',
        'Unclear / Not-Stated'
    ] = Field(description="CRITICAL: Do NOT infer cancellation from negative sentiment or continuation from positive sentiment. Assign explicit status only if text states it.")

    # ── 6. Severity of Friction ───────────────────────────────────────────────
    severity: Literal['Low', 'Medium', 'High', 'None'] = Field(
        description="High = explicitly stopped or failed SIP. Medium = confusion, panic, hesitating. Low = minor query. None = positive/neutral."
    )

    # ── 7. Evidence-Backed Extractions ────────────────────────────────────────
    stated_user_goal: str = Field(
        description="User's explicit or strongly implied investment goal (e.g. 'wealth creation', 'tax saving', 'emergency fund', 'unstated')."
    )

    triggering_event: str = Field(
        description="What specific event triggered this thought/action (e.g. 'salary delayed', 'market dropped 5%', 'mandate rejected by bank', 'first SIP debit notification', 'none')."
    )

    observed_behavior: str = Field(
        description="Specific behavior described (e.g. 'checked app daily', 'cancelled autopay', 'posted query on forum', 'ignored notification')."
    )

    emotional_or_practical_concern: str = Field(
        description="Core anxiety or operational blocker (e.g. 'fear of losing capital', 'confusion over deduction without allotment', 'distrust in app')."
    )

    external_workaround: Literal[
        'Reddit',
        'YouTube',
        'Google Search',
        'Friends / Family',
        'Customer Support',
        'Financial Advisor',
        'None'
    ] = Field(description="Where did the user seek help outside the platform?")

    potential_unmet_need: str = Field(
        description="Actionable PM opportunity: 'Investor would continue if the platform provided ___'. Be concrete and specific."
    )

    # ── 8. Traceability & Epistemic Humility ──────────────────────────────────
    supporting_quote: str = Field(
        description="Exact verbatim excerpt from the user text that substantiates this classification. Never fabricate quotes."
    )

    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Confidence between 0.0 and 1.0. Lower when text is ambiguous or short."
    )

    evidence_limitations: str = Field(
        description="State what is missing or ambiguous (e.g. 'User does not state whether SIP was actually stopped', 'Income and investment duration unknown')."
    )

    needs_human_review: bool = Field(
        description="True if record contains contradictory statements, borderline relevance, or low confidence."
    )

    summary: str = Field(
        description="One crisp sentence summarizing the user's situation and barrier to 12-month continuation."
    )
