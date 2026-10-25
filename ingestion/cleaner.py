import sqlite3
import re
import os

DB_PATH = 'data/discovery.db'

def setup_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    conn.commit()
    conn.close()

def remove_pii(text):
    if not text:
        return text
    # Remove email addresses
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL]', text)
    # Remove phone numbers (simple pattern for Indian numbers)
    text = re.sub(r'(?:\+?91[\-\s]?)?[789]\d{9}', '[PHONE]', text)
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)
    return text

def save_records(records):
    """
    Save a list of records to the database.
    Each record should be a dict with keys: id, source, content, timestamp, url, metadata
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    clean_records = []
    for record in records:
        clean_content = remove_pii(record.get('content', ''))
        clean_records.append((
            str(record.get('id', '')),
            record.get('source', ''),
            clean_content,
            record.get('timestamp', ''),
            record.get('url', ''),
            str(record.get('metadata', '{}'))
        ))
    
    cursor.executemany('''
        INSERT OR REPLACE INTO raw_conversations 
        (id, source, content, timestamp, url, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', clean_records)
    
    conn.commit()
    conn.close()
    return len(clean_records)

if __name__ == '__main__':
    setup_db()
    print("Database setup complete.")
