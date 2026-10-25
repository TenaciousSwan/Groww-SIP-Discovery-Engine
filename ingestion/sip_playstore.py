from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import uuid

TARGET_APPS = {
    'Groww': 'com.nextbillion.groww',
    'Coin by Zerodha': 'com.zerodha.coin',
    'Kuvera': 'com.kuvera.app',
    'ET Money': 'com.etmoney.android',
    'Paytm Money': 'com.paytmmoney'
}

SIP_KEYWORDS = [
    'sip', 'autopay', 'mandate', 'instalment', 'installment',
    'cancel', 'pause', 'stopped', 'failed', 'deducted', 'allotment',
    'nav', 'negative return', 'loss', 'first time', 'beginner'
]

def get_sip_playstore_reviews(limit_per_app=40, months_back=6):
    """
    Fetches real public Play Store reviews from leading Indian mutual fund apps.
    Filters for discussions mentioning SIP mechanics, friction, and continuation issues.
    """
    cutoff_date = datetime.now() - timedelta(days=30 * months_back)
    all_filtered = []

    for app_name, app_id in TARGET_APPS.items():
        print(f"Fetching Play Store reviews for {app_name} ({app_id})...")
        try:
            result, _ = reviews(
                app_id,
                lang='en',
                country='in',
                sort=Sort.NEWEST,
                count=limit_per_app * 2
            )
            
            for rev in result:
                rev_date = rev['at']
                if rev_date < cutoff_date:
                    continue
                
                content = rev.get('content', '')
                if not content:
                    continue

                content_lower = content.lower()
                if any(kw in content_lower for kw in SIP_KEYWORDS):
                    review_id = rev.get('reviewId') or str(uuid.uuid4())
                    all_filtered.append({
                        'id': f"playstore_{app_name.lower().replace(' ', '_')}_{review_id}",
                        'source': f"Play Store ({app_name})",
                        'content': content,
                        'timestamp': rev_date.isoformat(),
                        'url': f"https://play.google.com/store/apps/details?id={app_id}&reviewId={review_id}",
                        'metadata': {
                            'app': app_name,
                            'score': rev.get('score'),
                            'thumbsUpCount': rev.get('thumbsUpCount', 0)
                        },
                        'collection_date': datetime.now().isoformat(),
                        'collection_method': 'google_play_scraper'
                    })
                    if len(all_filtered) >= limit_per_app * len(TARGET_APPS):
                        break
        except Exception as e:
            print(f"  Warning: could not fetch Play Store reviews for {app_name}: {e}")

    print(f"Play Store collection finished: {len(all_filtered)} relevant SIP reviews found.")
    return all_filtered

if __name__ == '__main__':
    records = get_sip_playstore_reviews(limit_per_app=5)
    print(f"Fetched {len(records)} sample records.")
