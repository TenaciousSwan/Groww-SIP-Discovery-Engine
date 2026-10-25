import os
import sys
from ingestion.sip_cleaner import setup_db, save_records
from ingestion.sip_seed_data import SIP_PUBLIC_RECORDS
from ingestion.sip_reddit import get_groww_reddit_posts
from ingestion.sip_consumer_forums import get_groww_consumer_grievances
from ingestion.sip_playstore import get_groww_playstore_reviews
from ai_engine.sip_classifier import run_sip_classification

def run_all_sip_ingestion(fetch_live_playstore=True, fetch_live_reddit=True, fetch_consumer_grievances=True, run_enrichment=True, db_path='data/discovery.db'):
    print("==========================================================================")
    print("  GROWW 12-Month SIP Continuation — Comprehensive Online Data Pipeline   ")
    print("==========================================================================")
    
    # 1. Setup DB
    setup_db(db_path)
    all_records = []

    # 2. Add high-integrity benchmark SIP records
    print(f"\n[1/4] Loading {len(SIP_PUBLIC_RECORDS)} verified benchmark SIP records...")
    all_records.extend(SIP_PUBLIC_RECORDS)

    # 3. Collect Groww community discussions from Reddit
    if fetch_live_reddit:
        print("\n[2/4] Collecting Groww community discussions from Reddit...")
        try:
            reddit_posts = get_groww_reddit_posts(limit=100)
            all_records.extend(reddit_posts)
            print(f"  -> Successfully gathered {len(reddit_posts)} Groww Reddit discussions.")
        except Exception as e:
            print(f"  -> Reddit fetch note: {e}")

    # 4. Collect public consumer grievance forum records (MouthShut, ConsumerComplaints, Trustpilot, YouTube)
    if fetch_consumer_grievances:
        print("\n[3/4] Collecting public consumer grievance records (MouthShut, ConsumerComplaints, Trustpilot, YouTube)...")
        try:
            grievance_records = get_groww_consumer_grievances()
            all_records.extend(grievance_records)
            print(f"  -> Successfully gathered {len(grievance_records)} public grievance records.")
        except Exception as e:
            print(f"  -> Consumer grievance fetch note: {e}")

    # 5. Deep Play Store collection for Groww (1★ through 5★, multiple pages)
    if fetch_live_playstore:
        print("\n[4/4] Deep scraping real Groww Google Play Store reviews (App ID: com.nextbillion.groww)...")
        try:
            # 8 pages per score rating, covering MOST_RELEVANT and NEWEST across all 5 ratings
            playstore_reviews = get_groww_playstore_reviews(limit_per_score=200, pages_per_score=8, months_back=24)
            all_records.extend(playstore_reviews)
            print(f"  -> Successfully added {len(playstore_reviews)} Groww Play Store reviews.")
        except Exception as e:
            print(f"  -> Play Store fetch note: {e}")

    # 6. Clean, sanitize PII, deduplicate, and persist
    print(f"\nPersisting, scrubbing PII, and deduplicating {len(all_records)} total records...")
    saved_count = save_records(all_records, db_path=db_path)
    print(f"SUCCESS: Total records saved/synchronized in {db_path}.")

    # 7. Automatically classify and enrich any unclassified records
    if run_enrichment:
        print("\nRunning dual-backend AI classification on newly ingested records...")
        enriched_count = run_sip_classification(db_path=db_path)
        print(f"Enrichment pipeline complete. Total enriched records: {enriched_count}")

    return saved_count

if __name__ == '__main__':
    run_all_sip_ingestion()
