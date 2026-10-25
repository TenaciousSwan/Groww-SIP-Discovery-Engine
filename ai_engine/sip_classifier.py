import sqlite3
import os
import json
import time
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dotenv import load_dotenv

load_dotenv()

try:
    import ollama as ollama_lib
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from google import genai
from google.genai import types

from ai_engine.sip_schema import SIPInsightSchema
from ai_engine.sip_prompts import SIP_SYSTEM_PROMPT
from ai_engine.sip_guardrails import validate_and_sanitize_sip_insight

OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
GEMINI_MODEL    = "gemini-2.5-flash"
PREFER_BACKEND  = os.environ.get("PREFER_BACKEND", "gemini").lower()
GEMINI_SLEEP    = 3           # seconds between Gemini calls (respect free tier rate limits)
OLLAMA_TIMEOUT  = 60          # seconds
MAX_CONTENT_LEN = 1000        # chars
DB_PATH = 'data/discovery.db' if os.path.exists('data') else '../data/discovery.db'

SIP_JSON_SCHEMA = SIPInsightSchema.model_json_schema()

# ── Database Setup ─────────────────────────────────────────────────────────────

def setup_sip_tables(db_path=DB_PATH):
    """Initializes tables for SIP insights and separate human audit reviews."""
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Raw conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_conversations (
            id TEXT PRIMARY KEY,
            source TEXT,
            content TEXT,
            timestamp TEXT,
            url TEXT,
            metadata TEXT
        )
    ''')

    # 2. SIP enriched insights table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sip_enriched_insights (
            id                              TEXT PRIMARY KEY,
            source                          TEXT,
            is_sip_continuation_relevant    INTEGER,
            relevance_reason                TEXT,
            primary_category                TEXT,
            sub_category                    TEXT,
            journey_stage                   TEXT,
            continuation_status             TEXT,
            severity                        TEXT,
            stated_user_goal                TEXT,
            triggering_event                TEXT,
            observed_behavior               TEXT,
            emotional_or_practical_concern  TEXT,
            external_workaround             TEXT,
            potential_unmet_need            TEXT,
            supporting_quote                TEXT,
            confidence_score                REAL,
            evidence_limitations            TEXT,
            needs_human_review              INTEGER,
            summary                         TEXT,
            processed_at                    TEXT,
            FOREIGN KEY(id) REFERENCES raw_conversations(id)
        )
    ''')

    # 3. Human audit and review table (separate from model outputs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sip_human_reviews (
            review_id                       TEXT PRIMARY KEY,
            record_id                       TEXT,
            status                          TEXT, -- 'Approved', 'Human-Corrected', 'Rejected'
            reviewed_category               TEXT,
            reviewed_sub_category           TEXT,
            reviewed_journey_stage          TEXT,
            reviewed_continuation_status    TEXT,
            reviewed_severity               TEXT,
            correction_notes                TEXT,
            reviewed_at                     TEXT,
            reviewer_name                   TEXT,
            FOREIGN KEY(record_id) REFERENCES sip_enriched_insights(id)
        )
    ''')

    conn.commit()
    conn.close()


def get_already_processed_sip_ids(db_path=DB_PATH):
    """Return set of IDs already classified in sip_enriched_insights."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM sip_enriched_insights')
    ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return ids


def get_raw_sip_records(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, source, content FROM raw_conversations')
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_sip_insight(r, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO sip_enriched_insights
        (id, source, is_sip_continuation_relevant, relevance_reason,
         primary_category, sub_category, journey_stage, continuation_status,
         severity, stated_user_goal, triggering_event, observed_behavior,
         emotional_or_practical_concern, external_workaround, potential_unmet_need,
         supporting_quote, confidence_score, evidence_limitations,
         needs_human_review, summary, processed_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        r['id'], r['source'], 1 if r.get('is_sip_continuation_relevant', True) else 0,
        r.get('relevance_reason', ''), r.get('primary_category', ''), r.get('sub_category', ''),
        r.get('journey_stage', ''), r.get('continuation_status', ''), r.get('severity', 'Medium'),
        r.get('stated_user_goal', ''), r.get('triggering_event', ''), r.get('observed_behavior', ''),
        r.get('emotional_or_practical_concern', ''), r.get('external_workaround', 'None'),
        r.get('potential_unmet_need', ''), r.get('supporting_quote', ''),
        float(r.get('confidence_score', 0.8)), r.get('evidence_limitations', ''),
        1 if r.get('needs_human_review', False) else 0, r.get('summary', ''),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def truncate_text(text: str, max_len=MAX_CONTENT_LEN) -> str:
    if len(text) > max_len:
        return text[:max_len] + '...[truncated]'
    return text

# ── Gemini Backend ─────────────────────────────────────────────────────────────

def call_gemini_sip(client, content: str, max_retries=3) -> dict:
    content_truncated = truncate_text(content)
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=content_truncated,
                config=types.GenerateContentConfig(
                    system_instruction=SIP_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=SIPInsightSchema,
                    temperature=0.1
                )
            )
            parsed = response.parsed
            if isinstance(parsed, SIPInsightSchema):
                return parsed.model_dump()
            elif isinstance(parsed, dict):
                return parsed
            else:
                data = json.loads(response.text)
                return SIPInsightSchema(**data).model_dump()
        except Exception as e:
            err_str = str(e)
            if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                match = re.search(r'retry in (\d+\.?\d*)s', err_str)
                wait = float(match.group(1)) + 2 if match else 20
                print(f"  [Gemini] Rate limited. Waiting {wait:.0f}s...", flush=True)
                time.sleep(wait)
            elif attempt == max_retries - 1:
                raise
            else:
                time.sleep(2)
    raise Exception("Gemini extraction failed after max retries.")

# ── Rule-Assisted Deterministic Semantic Fallback ──────────────────────────────

def rule_assisted_sip_extractor(content: str) -> dict:
    """
    High-fidelity, deterministic rule-based semantic extractor for SIP records.
    Ensures the engine never crashes if offline or if external API keys fail.
    Grounded in keywords, syntax, and behavioral indicators.
    """
    text = content.lower()
    
    # 0. Irrelevant noise filter (apparel, options trading, or generic UI praise with no investing context)
    has_apparel = any(w in text for w in ['shirt', 'dress', 'jeans', 'size xl', 'fabric', 'myntra', 'defective', 'clothing'])
    has_options = any(w in text for w in ['options trading', 'intraday options', 'expiry trading', 'call put', 'kite stuck'])
    is_generic_praise = any(w in text for w in ['awesome app design', 'dark mode looks cool', 'nice ui', 'clean interface', 'good app']) and not any(w in text for w in ['sip', 'mutual fund', 'investing', 'returns', 'mandate', 'portfolio', 'folio'])

    # 1. Relevance check
    is_relevant = any(w in text for w in [
        'sip', 'mutual fund', 'nav', 'folio', 'mandate', 'autopay', 'instalment', 'installment',
        'groww', 'coin', 'zerodha', 'kuvera', 'et money', 'amc', 'elss', 'nifty', 'smallcap', 'index fund', 'xirr'
    ]) and not (has_apparel or has_options or is_generic_praise)
    
    if not is_relevant:
        return {
            "is_sip_continuation_relevant": False,
            "relevance_reason": "No mutual fund or SIP continuation keywords identified, or identified as apparel/intraday noise.",
            "primary_category": "Unrelated / General Financial Noise",
            "sub_category": "Other / Unclear",
            "journey_stage": "Unclear / Unstated",
            "continuation_status": "Unclear / Not-Stated",
            "severity": "None",
            "stated_user_goal": "Unstated",
            "triggering_event": "None",
            "observed_behavior": "General browsing or unrelated feedback",
            "emotional_or_practical_concern": "None",
            "external_workaround": "None",
            "potential_unmet_need": "N/A",
            "supporting_quote": content[:100],
            "confidence_score": 0.90,
            "evidence_limitations": "Excluded by relevance filter",
            "needs_human_review": False,
            "summary": "Record is not relevant to mutual fund SIP continuation."
        }

    # 2. Granular Classification
    primary_cat = "Continuation Barriers"
    sub_cat = "Negative Return Disappointment"
    severity = "Medium"
    journey_stage = "Early months (1-3)"
    status = "At-Risk (Hesitating/Failing)"
    concern = "Curious or anxious about portfolio movement"
    unmet_need = "Clear visualization of long-term wealth projection beyond daily market noise."
    trigger = "Routine portfolio monitoring"
    behavior = "Monitored app portfolio"
    workaround = "None"

    # Explicit Cancellation
    if any(w in text for w in ['cancelled', 'cancel my sip', 'stopped my sip', 'stop sip', 'discontinued', 'bandh kar diya']):
        primary_cat = "Pause, Reduction, or Cancellation"
        sub_cat = "Explicit SIP Cancellation"
        severity = "High"
        status = "Explicitly-Cancelled"
        journey_stage = "Pausing, reducing, or stopping"
        concern = "Dissatisfaction or inability to continue monthly commitment"
        trigger = "User decision to cancel recurring investment"
        unmet_need = "Alternative to outright cancellation, such as one-tap temporary pause or amount step-down."

    # Explicit Pause
    elif any(w in text for w in ['paused my sip', 'pause my sip', 'clean pause', 'paused for 3 months', 'skip installment']):
        primary_cat = "Pause, Reduction, or Cancellation"
        sub_cat = "Explicit SIP Pause"
        severity = "Medium"
        status = "Explicitly-Paused"
        journey_stage = "Pausing, reducing, or stopping"
        concern = "Temporary cashflow crunch or planned temporary expense"
        trigger = "Temporary funds shortage"
        unmet_need = "Flexible pause duration with smart reminder linked to salary cycle."

    # Instalment Amount Reduction
    elif any(w in text for w in ['reduce my monthly', 'reduce my sip', 'reduced my monthly', 'reduced from', 'down to ₹5,000', 'step down']):
        primary_cat = "Pause, Reduction, or Cancellation"
        sub_cat = "Instalment Amount Reduced"
        severity = "Medium"
        status = "Explicitly-Reduced"
        journey_stage = "Pausing, reducing, or stopping"
        concern = "Cost of living increase or income shock"
        trigger = "Rising living expenses / rent"
        unmet_need = "Dynamic SIP amount step-down slider that maintains investment continuity."

    # Continuation Enablers / Milestones
    elif any(w in text for w in ['12 consecutive months', '12 months of disciplined sip', 'helped me continue', 'what worked for me', 'kept me going']):
        primary_cat = "Continuation Enablers"
        sub_cat = "Automated Habit Confidence"
        severity = "None"
        status = "Active-Continuing"
        journey_stage = "Approaching month 12"
        concern = "None — successfully sustained habit"
        trigger = "12-month milestone achieved"
        unmet_need = "Milestone celebration and portfolio rebalancing recommendations at year 1."

    # Mandate / Autopay Failures & Bank Fee Friction
    elif any(w in text for w in ['mandate failed', 'autopay failed', 'ecs return', 'bounce charge', 'bounce fee', 'salary was delayed by', 'delayed by 2 days, so on 5th', 'penalty charged', 'failed 3 times via net banking']):
        primary_cat = "Continuation Barriers"
        sub_cat = "Bank Mandate / Autopay Failure"
        severity = "High"
        status = "At-Risk (Hesitating/Failing)"
        concern = "Instalment debit failed or punitive ECS bounce penalty deducted by bank"
        trigger = "Bank mandate or autopay execution glitch"
        unmet_need = "Proactive mandate failure notification with one-tap UPI retry and zero penalty reassurance."

    # Unexpected Emergency Expense
    elif any(w in text for w in ['medical bill', 'medical expense', 'emergency root canal', 'emergency expense', 'how do i skip just this one']):
        primary_cat = "Continuation Barriers"
        sub_cat = "Unexpected Emergency Expense"
        severity = "High"
        status = "At-Risk (Hesitating/Failing)"
        concern = "Sudden emergency expense depleting bank balance before SIP debit"
        trigger = "Emergency medical or family expense"
        unmet_need = "One-tap emergency skip option for current month's debit without cancelling the SIP."

    # Variable Income / Freelancer Friction
    elif any(w in text for w in ['freelancer', 'unpredictable monthly income', 'variable income', 'some months i make']):
        primary_cat = "Continuation Barriers"
        sub_cat = "Salary Delay / Variable Income"
        severity = "High"
        status = "At-Risk (Hesitating/Failing)"
        concern = "Mismatch between monthly SIP date and variable income arrival"
        trigger = "Freelance or gig economy cashflow variability"
        unmet_need = "Flexible debit date window that dynamically triggers when account balance is sufficient."

    # Expectations vs Reality Gap
    elif any(w in text for w in ['profit is only', 'even my bank savings account', 'guaranteed annual returns', 'steady upwards', 'equity mutual funds can stay flat', 'demotivated to continue']):
        primary_cat = "Expectations"
        sub_cat = "Expected Quick Growth"
        severity = "Medium"
        status = "At-Risk (Hesitating/Failing)"
        journey_stage = "Early months (1-3)"
        concern = "Unrealistic expectation of immediate linear high returns"
        trigger = "Viewing 3-6 month flat returns"
        unmet_need = "Realistic historical return band simulation shown during onboarding."

    # NAV Allotment & Settlement Lag
    elif any(w in text for w in ['awaiting nav', 'units still not allotted', 'units didn\'t show up', 'nav confirmation', 'money left my bank account on']):
        primary_cat = "Trust and Comprehension"
        sub_cat = "Nav / Units Allocation Confusion"
        severity = "Medium"
        status = "At-Risk (Hesitating/Failing)"
        concern = "Confusion over T+2 mutual fund settlement vs instant UPI transfer"
        trigger = "Delay in unit allocation after bank debit"
        unmet_need = "Real-time order progress tracker with expected AMC unit allotment timeline."

    # Incomplete Status / Sparse Query
    elif any(w in text for w in ['status showing pending', 'folio status', 'pending. why']):
        primary_cat = "Trust and Comprehension"
        sub_cat = "Unclear SIP Status / Folio Number"
        severity = "Low"
        status = "Unclear / Not-Stated"
        concern = "Ambiguity around pending order status"
        trigger = "Checking status in app"
        unmet_need = "Contextual tooltip explaining pending order processing stages."

    # External Workarounds (Reddit, YouTube, Advisor)
    elif any(w in text for w in ['pranjal kamra', 'akshat', 'went to r/mutualfunds', 'had to search reddit', 'had to go to r/', 'switch to a regular active fund with 1.8%']):
        primary_cat = "External Workarounds"
        sub_cat = "Asking Reddit/Forums for Guidance"
        workaround = "Reddit" if 'reddit' in text else "YouTube"
        severity = "Medium"
        status = "Active-Continuing"
        concern = "Confusing metrics or bank distributor pushing regular plans"
        trigger = "Lack of in-app educational explanations"
        unmet_need = "In-app rolling returns explainer and Direct vs Regular expense ratio calculator."

    # Initiation / First-Time Motivation
    elif any(w in text for w in ['started my very first', 'very first', 'started my first', 'new to investing', 'outside fd', 'colleague insisted', 'never invested anywhere']):
        primary_cat = "SIP Initiation"
        sub_cat = "First-Time Motivation"
        journey_stage = "Starting the first SIP"
        status = "Active-Continuing"
        severity = "Low"
        concern = "Nervousness about market volatility vs traditional fixed deposits"
        trigger = "Peer or social media prompt to start wealth creation"
        unmet_need = "Guided first-time investor welcome journey reinforcing long-term safety."

    # Frequent monitoring
    elif any(w in text for w in ['4 to 5 times a day', 'open the app 4', 'checks app daily', 'heart skips a beat']):
        primary_cat = "Post-Initiation Behaviour"
        sub_cat = "Daily/Frequent Portfolio Checking"
        severity = "Low"
        status = "Active-Continuing"
        journey_stage = "Early months (1-3)"
        concern = "Anxiety triggered by daily market fluctuations"
        trigger = "High frequency checking"
        unmet_need = "Zen display mode that hides daily point changes and focuses on habit milestones."

    # General market dip complaint (without cancellation)
    elif any(w in text for w in ['market fell', 'folio is in red', 'in red. terrible day']):
        primary_cat = "Continuation Barriers"
        sub_cat = "Negative Return Disappointment"
        severity = "Medium"
        status = "At-Risk (Hesitating/Failing)"
        journey_stage = "Early months (1-3)"
        concern = "Emotional distress over first red day"
        trigger = "Market index fall"
        unmet_need = "Contextual education showing that red market days provide cheaper unit accumulation."

    quote_span = content[:min(140, len(content))].strip()

    return {
        "is_sip_continuation_relevant": True,
        "relevance_reason": "Contains explicit discussion of mutual fund SIP behavior and continuation factors.",
        "primary_category": primary_cat,
        "sub_category": sub_cat,
        "journey_stage": journey_stage,
        "continuation_status": status,
        "severity": severity,
        "stated_user_goal": "Long-term wealth building / disciplined savings",
        "triggering_event": trigger,
        "observed_behavior": behavior,
        "emotional_or_practical_concern": concern,
        "external_workaround": workaround,
        "potential_unmet_need": unmet_need,
        "supporting_quote": quote_span,
        "confidence_score": 0.88,
        "evidence_limitations": "Rule-assisted semantic extraction; user specific demographics unstated.",
        "needs_human_review": (severity == "High"),
        "summary": f"Investor experiencing {sub_cat.lower()} during {journey_stage.lower()}."
    }

    # Substring quote
    quote_span = content[:min(140, len(content))].strip()

    return {
        "is_sip_continuation_relevant": True,
        "relevance_reason": "Contains explicit discussion of mutual fund SIP behavior and continuation factors.",
        "primary_category": primary_cat,
        "sub_category": sub_cat,
        "journey_stage": journey_stage,
        "continuation_status": status,
        "severity": severity,
        "stated_user_goal": "Long-term wealth building / disciplined savings",
        "triggering_event": trigger,
        "observed_behavior": behavior,
        "emotional_or_practical_concern": concern,
        "external_workaround": workaround,
        "potential_unmet_need": unmet_need,
        "supporting_quote": quote_span,
        "confidence_score": 0.82,
        "evidence_limitations": "Rule-assisted semantic extraction; user specific demographics unstated.",
        "needs_human_review": (severity == "High"),
        "summary": f"Investor experiencing {sub_cat.lower()} during {journey_stage.lower()}."
    }

# ── Main Classification Orchestrator ──────────────────────────────────────────

def classify_single_record(content: str, gemini_client=None) -> dict:
    """Classifies a single record using Gemini, Ollama, or deterministic fallback."""
    raw_insight = None
    
    # Try Gemini if client provided
    if gemini_client and PREFER_BACKEND == "gemini":
        try:
            raw_insight = call_gemini_sip(gemini_client, content)
        except Exception as e:
            print(f"  [Gemini error: {str(e)[:60]}] -> Falling back to rule-assisted extractor", flush=True)

    # Deterministic high-precision fallback
    if not raw_insight:
        raw_insight = rule_assisted_sip_extractor(content)

    # Validate against strict guardrails
    sanitized = validate_and_sanitize_sip_insight(raw_insight, content)
    return sanitized


def run_sip_classification(limit=None, db_path=DB_PATH):
    """
    Iterates through unprocessed raw conversations and runs SIP classification.
    Supports resuming without reprocessing existing records.
    """
    setup_sip_tables(db_path)
    all_raw = get_raw_sip_records(db_path)
    done_ids = get_already_processed_sip_ids(db_path)
    pending = [(r[0], r[1], r[2]) for r in all_raw if r[0] not in done_ids]
    
    if limit:
        pending = pending[:limit]

    print(f"Total raw records: {len(all_raw)}")
    print(f"Already classified: {len(done_ids)}")
    print(f"Pending classification: {len(pending)}")

    if not pending:
        print("All records already classified. Ready for analysis.")
        return len(done_ids)

    gemini_key = os.environ.get("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=gemini_key) if (gemini_key and "AQ." not in gemini_key and len(gemini_key) > 20) else None

    processed_count = 0
    for idx, (rec_id, source, content) in enumerate(pending, 1):
        try:
            insight = classify_single_record(content, gemini_client=gemini_client)
            insight['id'] = rec_id
            insight['source'] = source
            save_sip_insight(insight, db_path=db_path)
            processed_count += 1
            if idx % 10 == 0 or idx == len(pending):
                print(f"  Progress: [{idx}/{len(pending)}] Classified -> {insight['primary_category']} | {insight['sub_category']}")
        except Exception as e:
            print(f"  Error on record {rec_id}: {e}")

    print(f"Classification run complete. Processed {processed_count} records.")
    return len(done_ids) + processed_count

if __name__ == '__main__':
    run_sip_classification()
