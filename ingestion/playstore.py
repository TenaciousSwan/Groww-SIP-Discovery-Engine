from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import uuid

# Target app
APP_ID = 'com.grofers.customerapp'
KEYWORDS = [
    'wallet', 'blinkit wallet', 'wallet balance', 'wallet money',
    'wallet payment', 'wallet refund', 'wallet cashback'
]

def get_playstore_reviews(limit=500, months_back=4):
    """
    Fetch all reviews in the lookback window and filter based on wallet keywords.
    """
    print(f"Fetching all Play Store reviews from the last {months_back} months...")
    cutoff_date = datetime.now() - timedelta(days=30 * months_back)
    filtered_records = []
    continuation_token = None
    seen_continuation_tokens = set()
    seen_review_ids = set()
    total_fetched = 0

    while True:
        if continuation_token in seen_continuation_tokens:
            break
        if continuation_token:
            seen_continuation_tokens.add(continuation_token)

        request_args = {
            'lang': 'en',
            'country': 'in',
            'sort': Sort.NEWEST,
            'count': limit
        }
        if continuation_token:
            request_args['continuation_token'] = continuation_token

        result, continuation_token = reviews(APP_ID, **request_args)
        if not result:
            break

        total_fetched += len(result)
        for rev in result:
            rev_date = rev['at']
            if rev_date < cutoff_date:
                continue

            review_id = rev['reviewId']
            if review_id in seen_review_ids:
                continue
            seen_review_ids.add(review_id)

            content = rev['content']
            if not content:
                continue

            content_lower = content.lower()
            if any(keyword in content_lower for keyword in KEYWORDS):
                filtered_records.append({
                    'id': f"playstore_{review_id}",
                    'source': 'playstore',
                    'content': content,
                    'timestamp': rev_date.isoformat(),
                    'url': f"https://play.google.com/store/apps/details?id={APP_ID}&reviewId={review_id}",
                    'metadata': f'{{"score": {rev["score"]}}}'
                })

        oldest_review_date = min(rev['at'] for rev in result)
        if oldest_review_date < cutoff_date or not continuation_token:
            break

    print(f"Play Store scraping completed. Fetched {total_fetched} reviews; found {len(filtered_records)} relevant reviews.")
    return filtered_records

if __name__ == '__main__':
    records = get_playstore_reviews()
    for r in records[:2]:
        print(r)
