import sqlite3
import os
import json
import time
import re
import random
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
from schema import InsightSchemaV2 as InsightSchema
from prompts import SYSTEM_PROMPT
from guardrails import enforce_non_monetary_guardrail

OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
GEMINI_MODEL    = "gemini-3.6-flash"
PREFER_BACKEND  = os.environ.get("PREFER_BACKEND", "ollama").lower()  # "gemini" or "ollama"
GEMINI_SLEEP    = 5           # seconds between Gemini calls (safe for 15 RPM free tier)
OLLAMA_TIMEOUT  = 90          # seconds — skip record if Ollama hangs
MAX_CONTENT_LEN = 600         # chars — truncate very long reviews
DB_PATH = 'data/discovery.db' if os.path.exists('data') else '../data/discovery.db'

INSIGHT_JSON_SCHEMA = InsightSchema.model_json_schema()

# ── DB helpers ────────────────────────────────────────────────────────────────

def setup_enriched_table():
    """Create table if it doesn't exist. Do NOT drop — preserves progress on resume."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enriched_insights (
            id                   TEXT PRIMARY KEY,
            source               TEXT,
            intent               TEXT,
            friction_category    TEXT,
            severity             TEXT,
            wishlist_mode        TEXT,
            postponement_trigger TEXT,
            comparison_dimension TEXT,
            external_source      TEXT,
            decision_factors     TEXT,
            unmet_need           TEXT,
            user_segment_signal  TEXT,
            summary              TEXT,
            FOREIGN KEY(id) REFERENCES raw_conversations(id)
        )
    ''')
    conn.commit()
    conn.close()


def get_already_processed_ids():
    """Return set of IDs already in enriched_insights (for resume support)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM enriched_insights')
    ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return ids


def get_raw_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, source, content FROM raw_conversations')
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_insight(r):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO enriched_insights
        (id, source, intent, friction_category, severity,
         wishlist_mode, postponement_trigger, comparison_dimension,
         external_source, decision_factors, unmet_need,
         user_segment_signal, summary)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        r['id'], r['source'], r['intent'], r['friction_category'], r['severity'],
        r['wishlist_mode'], r['postponement_trigger'], r['comparison_dimension'],
        r['external_source'], r['decision_factors'], r['unmet_need'],
        r['user_segment_signal'], r['summary']
    ))
    conn.commit()
    conn.close()


def truncate_content(content: str) -> str:
    """Truncate very long content to prevent Ollama from hanging."""
    if len(content) > MAX_CONTENT_LEN:
        return content[:MAX_CONTENT_LEN] + '...[truncated]'
    return content

# ── Ollama backend ────────────────────────────────────────────────────────────

def _call_ollama_raw(content):
    response = ollama_lib.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": content}
        ],
        format=INSIGHT_JSON_SCHEMA,
        options={"temperature": 0.1, "num_predict": 512}
    )
    raw = response["message"]["content"]
    data = json.loads(raw)
    validated = InsightSchema(**data)
    return {
        "intent":               validated.intent,
        "friction_category":    validated.friction_category,
        "severity":             validated.severity,
        "wishlist_mode":        validated.wishlist_mode,
        "postponement_trigger": validated.postponement_trigger,
        "comparison_dimension": validated.comparison_dimension,
        "external_source":      validated.external_source,
        "decision_factors":     validated.decision_factors,
        "unmet_need":           validated.unmet_need,
        "user_segment_signal":  validated.user_segment_signal,
        "summary":              validated.summary,
    }


def _call_ollama(content):
    """Ollama call with hard timeout — skips stuck records."""
    content = truncate_content(content)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call_ollama_raw, content)
        try:
            return future.result(timeout=OLLAMA_TIMEOUT)
        except FuturesTimeoutError:
            raise Exception(f"Ollama timed out after {OLLAMA_TIMEOUT}s — skipping record")

# ── Gemini backend ────────────────────────────────────────────────────────────

def _call_gemini_with_retry(client, content, max_retries=3):
    content = truncate_content(content)
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=InsightSchema,
                    temperature=0.1
                )
            )
            parsed = response.parsed
            return {
                "intent":               parsed.intent,
                "friction_category":    parsed.friction_category,
                "severity":             parsed.severity,
                "wishlist_mode":        parsed.wishlist_mode,
                "postponement_trigger": parsed.postponement_trigger,
                "comparison_dimension": parsed.comparison_dimension,
                "external_source":      parsed.external_source,
                "decision_factors":     parsed.decision_factors,
                "unmet_need":           parsed.unmet_need,
                "user_segment_signal":  parsed.user_segment_signal,
                "summary":              parsed.summary,
            }
        except Exception as e:
            err_str = str(e)
            if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                match = re.search(r'retry in (\d+\.?\d*)s', err_str)
                wait = float(match.group(1)) + 2 if match else 30
                print(f"  [Gemini] Rate limited. Waiting {wait:.0f}s...", flush=True)
                time.sleep(wait)
            else:
                raise
    raise Exception("Gemini failed after max retries.")

# ── Mock fallback ─────────────────────────────────────────────────────────────

def _mock_result(reason="No backend"):
    return {
        "intent":               random.choice(['Deferred-Intent', 'Browse-Saving', 'Complaint', 'Comparison']),
        "friction_category":    random.choice(['Fit/Size', 'Fabric/Material', 'Trust/Authenticity', 'Styling/Occasion']),
        "severity":             random.choice(['Low', 'Medium', 'High']),
        "wishlist_mode":        random.choice(['Genuine-Intent', 'Browse-Saving', 'Price-Waiting', 'Unclear']),
        "postponement_trigger": random.choice(['Size-Doubt', 'Price-Wait', 'Wants-More-Reviews', 'None']),
        "comparison_dimension": 'Not-Comparing',
        "external_source":      'None',
        "decision_factors":     random.choice(['Fit,Size', 'Price,Reviews', 'Styling,Occasion']),
        "unmet_need":           f"[Mock - {reason}]",
        "user_segment_signal":  'Unclear',
        "summary":              f"Mock summary - {reason}",
    }

# ── Main classification loop ──────────────────────────────────────────────────

def run_classification():
    setup_enriched_table()

    all_rows = get_raw_records()
    already_done = get_already_processed_ids()
    pending = [(rid, src, content) for rid, src, content in all_rows if rid not in already_done]

    total = len(all_rows)
    done_before = len(already_done)
    print(f"Total records : {total}", flush=True)
    print(f"Already done  : {done_before} (resuming)", flush=True)
    print(f"To process    : {len(pending)}", flush=True)

    if not pending:
        print("All records already classified. Nothing to do.", flush=True)
        return

    gemini_key = os.environ.get("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None

    # Determine backend based on PREFER_BACKEND setting
    ollama_ready = False
    if PREFER_BACKEND == "gemini" and gemini_client:
        print(f"[Backend] Gemini {GEMINI_MODEL} PRIMARY (PREFER_BACKEND=gemini) | {GEMINI_SLEEP}s between calls", flush=True)
    else:
        if OLLAMA_AVAILABLE:
            try:
                models = ollama_lib.list()
                available = [m.model for m in models.models]
                if any(OLLAMA_MODEL in m for m in available):
                    print(f"[Backend] Ollama + {OLLAMA_MODEL} | timeout={OLLAMA_TIMEOUT}s | max_content={MAX_CONTENT_LEN}c", flush=True)
                    ollama_ready = True
                else:
                    print(f"[Backend] Ollama running but '{OLLAMA_MODEL}' not pulled.", flush=True)
            except Exception as e:
                print(f"[Backend] Ollama not reachable: {e}", flush=True)

        if not ollama_ready:
            if gemini_client:
                print(f"[Backend] Gemini {GEMINI_MODEL} fallback | {GEMINI_SLEEP}s between calls", flush=True)
            else:
                print("[Backend] No AI backend — using mock data.", flush=True)

    processed = 0
    skipped   = 0
    global_idx = done_before

    for row_id, source, content in pending:
        global_idx += 1
        print(f"[{global_idx}/{total}] {row_id[:45]}...", end=" ", flush=True)

        try:
            if PREFER_BACKEND == "gemini" and gemini_client:
                result = _call_gemini_with_retry(gemini_client, content)
                backend = "Gemini"
                if global_idx < total:
                    time.sleep(GEMINI_SLEEP)
            elif ollama_ready:
                result = _call_ollama(content)
                backend = "Ollama"
            elif gemini_client:
                result = _call_gemini_with_retry(gemini_client, content)
                backend = "Gemini-fallback"
                if global_idx < total:
                    time.sleep(GEMINI_SLEEP)
            else:
                raise ValueError("No backend")

            result['friction_category'] = enforce_non_monetary_guardrail(result['friction_category'])
            save_insight({'id': row_id, 'source': source, **result})
            processed += 1
            print(f"[{backend}] {result['intent']} | {result['postponement_trigger']} | {result['severity']}", flush=True)

        except Exception as e:
            err_msg = str(e)[:80]
            print(f"[ERROR] {err_msg}", flush=True)
            
            fallback_success = False
            if backend != "Ollama" and ollama_ready:
                try:
                    print("[Fallback] Attempting Ollama due to failure...", flush=True)
                    result = _call_ollama(content)
                    backend = "Ollama-fallback"
                    result['friction_category'] = enforce_non_monetary_guardrail(result['friction_category'])
                    save_insight({'id': row_id, 'source': source, **result})
                    processed += 1
                    print(f"[{backend}] {result['intent']} | {result['postponement_trigger']} | {result['severity']}", flush=True)
                    fallback_success = True
                except Exception as ollama_e:
                    print(f"[Fallback ERROR] Ollama also failed: {str(ollama_e)[:80]}", flush=True)
                    err_msg = str(ollama_e)[:80]
            
            if not fallback_success:
                print(f"[SKIP] Using Mock data", flush=True)
                # Use mock for failed/timed-out records so they don't block future runs
                result = _mock_result(reason=err_msg[:40])
                result['friction_category'] = enforce_non_monetary_guardrail(result['friction_category'])
                save_insight({'id': row_id, 'source': source, **result})
                skipped += 1

    final_count = done_before + processed + skipped
    print(f"\nDone! {final_count}/{total} records in DB ({skipped} mocked due to timeout/error).", flush=True)
    print("Run: streamlit run app.py", flush=True)


if __name__ == '__main__':
    run_classification()
