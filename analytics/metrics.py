import sqlite3
import pandas as pd
import os

DB_PATH = 'data/discovery.db' if os.path.exists('data/discovery.db') else '../data/discovery.db'

def get_dataframe():
    """Fetches enriched insights and raw conversations, joining them into a single DataFrame."""
    try:
        conn = sqlite3.connect(DB_PATH)
        query = '''
            SELECT e.id, e.source, e.intent, e.friction_category, 
                   e.external_seeking, e.severity, e.summary, r.content as raw_feedback
            FROM enriched_insights e
            LEFT JOIN raw_conversations r ON e.id = r.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def compute_pareto_friction(df):
    """Calculates the frequency of each friction_category."""
    if df.empty:
        return pd.DataFrame()
    return df['friction_category'].value_counts().reset_index().rename(columns={'friction_category': 'Category', 'count': 'Frequency'})

def compute_external_seeking_index(df):
    """Calculates the percentage of records where external_seeking is True."""
    if df.empty:
        return 0.0
    total = len(df)
    external_seekers = df['external_seeking'].sum() # True counts as 1
    return (external_seekers / total) * 100

def compute_severity_matrix(df):
    """Groups data by friction_category and severity."""
    if df.empty:
        return pd.DataFrame()
    matrix = df.groupby(['friction_category', 'severity']).size().unstack(fill_value=0)
    # Ensure all severity columns exist
    for sev in ['Low', 'Medium', 'High']:
        if sev not in matrix.columns:
            matrix[sev] = 0
    # Add a weighted score
    matrix['Opportunity_Score'] = (matrix['High'] * 3) + (matrix['Medium'] * 2) + (matrix['Low'] * 1)
    matrix = matrix.sort_values(by='Opportunity_Score', ascending=False)
    return matrix.reset_index()

def get_wishlist_intent_split(df):
    """Computes the distribution of intent (Purchase vs. Bookmarking)."""
    if df.empty:
        return pd.DataFrame()
    return df['intent'].value_counts().reset_index().rename(columns={'intent': 'Intent', 'count': 'Frequency'})
