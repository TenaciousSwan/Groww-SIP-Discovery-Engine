import pytest
import sqlite3
import os
from ingestion.sip_cleaner import remove_pii, save_records, setup_db
from ingestion.sip_seed_data import SIP_PUBLIC_RECORDS

TEST_DB = 'data/test_discovery.db'

def test_pii_redaction():
    text = "Contact rahul@gmail.com or call 9876543210 regarding my SIP folio 12345678."
    cleaned = remove_pii(text)
    assert "@gmail.com" not in cleaned
    assert "[EMAIL]" in cleaned
    assert "9876543210" not in cleaned
    assert "[PHONE]" in cleaned
    assert "folio 12345678" not in cleaned
    assert "[ACCOUNT_REDACTED]" in cleaned

def test_financial_terms_preserved():
    text = "My ₹5,000 SIP in Parag Parikh Flexi Cap lost -4.5% NAV on Nifty drop."
    cleaned = remove_pii(text)
    assert "₹5,000" in cleaned
    assert "-4.5%" in cleaned
    assert "Parag Parikh" in cleaned

def test_db_persistence_and_provenance():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    setup_db(TEST_DB)
    
    count = save_records(SIP_PUBLIC_RECORDS[:5], db_path=TEST_DB)
    assert count == 5
    
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM raw_conversations')
    row_count = cursor.fetchone()[0]
    conn.close()
    
    assert row_count == 5
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
