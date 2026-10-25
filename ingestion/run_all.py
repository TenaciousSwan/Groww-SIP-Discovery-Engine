from playstore import get_playstore_reviews
from reddit import get_reddit_posts
from youtube import get_youtube_comments
from cleaner import setup_db, save_records

def main():
    print("--- Phase 1: Data Ingestion & Pre-Filtering Engine ---")
    
    # 1. Setup DB
    setup_db()
    
    all_records = []
    
    # 2. Scrape Play Store
    try:
        playstore_data = get_playstore_reviews(limit=500, months_back=4)
        all_records.extend(playstore_data)
    except Exception as e:
        print(f"Error scraping Play Store: {e}")
        
    # 3. Scrape Reddit (Mock)
    try:
        reddit_data = get_reddit_posts(limit=100)
        all_records.extend(reddit_data)
    except Exception as e:
        print(f"Error scraping Reddit: {e}")
        
    # 4. Scrape YouTube (Basic/Mock)
    try:
        youtube_data = get_youtube_comments()
        all_records.extend(youtube_data)
    except Exception as e:
        print(f"Error scraping YouTube: {e}")
        
    # 5. Clean and Save Data
    if all_records:
        print(f"\nTotal raw records collected: {len(all_records)}")
        saved_count = save_records(all_records)
        print(f"Successfully saved {saved_count} clean records to data/discovery.db")
    else:
        print("No records were collected.")

if __name__ == '__main__':
    main()
