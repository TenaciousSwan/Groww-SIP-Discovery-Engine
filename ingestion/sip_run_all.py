import os
from ingestion.sip_cleaner import setup_db, save_records
from ingestion.sip_seed_data import SIP_PUBLIC_RECORDS
from ingestion.sip_reddit import get_sip_reddit_posts
from ingestion.sip_playstore import get_sip_playstore_reviews

def run_all_sip_ingestion(fetch_live_playstore=True, fetch_live_reddit=True, db_path='data/discovery.db'):
    print("================================================================")
    print("  SIP Continuation Discovery Engine — Public Ingestion Pipeline ")
    print("================================================================")
    
    # 1. Setup DB
    setup_db(db_path)
    all_records = []

    # 2. Add high-integrity public research dataset
    print(f"\n[1/3] Loading {len(SIP_PUBLIC_RECORDS)} verified benchmark SIP records...")
    all_records.extend(SIP_PUBLIC_RECORDS)

    # 3. Collect from Reddit
    if fetch_live_reddit:
        print("\n[2/3] Collecting discussions from r/mutualfunds, r/IndiaInvestments...")
        try:
            reddit_posts = get_sip_reddit_posts(limit=25)
            all_records.extend(reddit_posts)
            print(f"  -> Added {len(reddit_posts)} Reddit discussions.")
        except Exception as e:
            print(f"  -> Reddit fetch error: {e}")

    # 4. Collect from Google Play Store (Groww, Coin, Kuvera, etc.)
    if fetch_live_playstore:
        print("\n[3/3] Fetching public Play Store reviews from Indian investing apps...")
        try:
            playstore_reviews = get_sip_playstore_reviews(limit_per_app=15, months_back=4)
            all_records.extend(playstore_reviews)
            print(f"  -> Added {len(playstore_reviews)} Play Store reviews.")
        except Exception as e:
            print(f"  -> Play Store fetch note: {e}")

    # 5. Clean, sanitize PII, deduplicate, and persist
    print(f"\nPersisting and anonymizing {len(all_records)} total records...")
    saved_count = save_records(all_records, db_path=db_path)
    print(f"SUCCESS: {saved_count} unique, anonymized SIP records saved to {db_path}.")
    return saved_count

if __name__ == '__main__':
    run_all_sip_ingestion()
