import sqlite3
import re
import os
import json
from datetime import datetime

DB_PATH = 'data/discovery.db' if os.path.exists('data') else '../data/discovery.db'

def setup_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_conversations (
            id                TEXT PRIMARY KEY,
            source            TEXT,
            content           TEXT,
            timestamp         TEXT,
            url               TEXT,
            metadata          TEXT,
            collection_date   TEXT,
            language          TEXT,
            collection_method TEXT
        )
    ''')
    # Check and migrate columns if existing table was from previous version
    cursor.execute("PRAGMA table_info(raw_conversations)")
    existing_cols = {col[1] for col in cursor.fetchall()}
    for col_name in ['collection_date', 'language', 'collection_method']:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE raw_conversations ADD COLUMN {col_name} TEXT")
            except Exception:
                pass
    conn.commit()
    conn.close()

def remove_pii(text: str) -> str:
    """
    Anonymizes sensitive PII while preserving financial figures, fund names, and percentage returns.
    """
    if not text:
        return ""
    # Remove email addresses
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL]', text)
    # Remove Indian phone numbers (10 digits starting with 6, 7, 8, or 9 with optional +91)
    text = re.sub(r'(?:\+?91[\-\s]?)?[6789]\d{9}', '[PHONE]', text)
    # Remove full URLs but preserve domain context if needed
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)
    # Remove account/folio-like numbers (e.g. A/C 1234567890 or Folio 98765432)
    text = re.sub(r'\b(?:folio|a/c|acc|account|bank)\s*(?:no|number|#)?\s*[:\-\s]?\s*\d{6,16}\b', '[ACCOUNT_REDACTED]', text, flags=re.IGNORECASE)
    # Clean excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_language(text: str) -> str:
    """Basic language/vernacular heuristic (English, Hinglish)."""
    text_lower = text.lower()
    hinglish_words = ['kare', 'karna', 'hai', 'nhi', 'nahi', 'raha', 'paisa', 'rupaye', 'bhai', 'bandh', 'rok', 'diya', 'gaya', 'kyun']
    if any(re.search(r'\b' + re.escape(w) + r'\b', text_lower) for w in hinglish_words):
        return "Hinglish"
    return "English"

def save_records(records, db_path=DB_PATH):
    """
    Saves and deduplicates incoming raw records with provenance tracking.
    """
    setup_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    clean_records = []
    seen_hashes = set()

    for record in records:
        content = record.get('content', '').strip()
        if not content:
            continue
            
        clean_content = remove_pii(content)
        if len(clean_content) < 15:  # skip empty or single-word noise
            continue

        # Content hash for deduplication
        norm_content = " ".join(clean_content.lower().split())
        if norm_content in seen_hashes:
            continue
        seen_hashes.add(norm_content)

        rec_id = str(record.get('id', ''))
        source = record.get('source', 'user_import')
        timestamp = record.get('timestamp') or datetime.now().isoformat()
        url = record.get('url', '')
        
        meta = record.get('metadata', {})
        if isinstance(meta, dict):
            meta_str = json.dumps(meta)
        else:
            meta_str = str(meta)
            
        coll_date = record.get('collection_date') or datetime.now().isoformat()
        lang = record.get('language') or detect_language(clean_content)
        method = record.get('collection_method', 'automated_scraper')

        clean_records.append((
            rec_id, source, clean_content, timestamp, url, meta_str,
            coll_date, lang, method
        ))
    
    cursor.executemany('''
        INSERT OR REPLACE INTO raw_conversations 
        (id, source, content, timestamp, url, metadata, collection_date, language, collection_method)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', clean_records)
    
    conn.commit()
    conn.close()
    return len(clean_records)

if __name__ == '__main__':
    setup_db()
    print("SIP database table ready.")
