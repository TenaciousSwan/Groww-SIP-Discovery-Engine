import sqlite3
conn = sqlite3.connect('data/discovery.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', c.fetchall())
c.execute('SELECT COUNT(*) FROM raw_conversations')
print('Raw records:', c.fetchone()[0])
try:
    c.execute('SELECT COUNT(*) FROM enriched_insights')
    print('Enriched records:', c.fetchone()[0])
    c.execute('PRAGMA table_info(enriched_insights)')
    cols = [r[1] for r in c.fetchall()]
    print('Enriched cols:', cols)
    # Sample a few rows
    c.execute('SELECT intent, friction_category, severity, wishlist_mode, postponement_trigger, user_segment_signal, external_source FROM enriched_insights LIMIT 3')
    rows = c.fetchall()
    print('Sample rows:')
    for r in rows:
        print(' ', r)
except Exception as e:
    print('enriched_insights error:', e)
conn.close()
