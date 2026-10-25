from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import uuid

# Primary focus is Groww for the Fellowship teardown project
PRIMARY_APP = {
    'name': 'Groww',
    'id': 'com.nextbillion.groww'
}

SIP_KEYWORDS = [
    'sip', 'autopay', 'mandate', 'instalment', 'installment',
    'cancel', 'pause', 'stopped', 'failed', 'deducted', 'allotment',
    'nav', 'negative return', 'loss', 'first time', 'beginner',
    'skip', 'mutual fund', 'xirr', 'units', 'folio'
]

def get_groww_playstore_reviews(limit=300, limit_per_app=None, months_back=12):
    """
    Fetches real public Google Play Store reviews for Groww (com.nextbillion.groww).
    Collects across both MOST_RELEVANT and NEWEST sorts to capture high-impact
    detailed user complaints, skip/pause struggles, and mandate failure discussions.
    """
    if limit_per_app and not limit:
        limit = limit_per_app
    elif limit_per_app:
        limit = max(limit, limit_per_app * 2)
    cutoff_date = datetime.now() - timedelta(days=30 * months_back)
    all_filtered = []
    seen_ids = set()

    for sort_mode in [Sort.MOST_RELEVANT, Sort.NEWEST]:
        print(f"Fetching Groww reviews (Sort: {sort_mode.name})...")
        try:
            result, _ = reviews(
                PRIMARY_APP['id'],
                lang='en',
                country='in',
                sort=sort_mode,
                count=limit
            )
            
            for rev in result:
                review_id = rev.get('reviewId') or str(uuid.uuid4())
                if review_id in seen_ids:
                    continue

                rev_date = rev.get('at')
                if rev_date and rev_date < cutoff_date:
                    continue
                
                content = rev.get('content', '')
                if not content or len(content.strip()) < 15:
                    continue

                content_lower = content.lower()
                if any(kw in content_lower for kw in SIP_KEYWORDS):
                    seen_ids.add(review_id)
                    all_filtered.append({
                        'id': f"groww_playstore_{review_id}",
                        'source': "Play Store (Groww)",
                        'content': content,
                        'timestamp': rev_date.isoformat() if rev_date else datetime.now().isoformat(),
                        'url': f"https://play.google.com/store/apps/details?id={PRIMARY_APP['id']}&reviewId={review_id}",
                        'metadata': {
                            'app': 'Groww',
                            'score': rev.get('score'),
                            'thumbsUpCount': rev.get('thumbsUpCount', 0),
                            'sort_mode': sort_mode.name,
                            'reply': rev.get('replyContent')
                        },
                        'collection_date': datetime.now().isoformat(),
                        'collection_method': 'google_play_scraper'
                    })
        except Exception as e:
            print(f"  Warning: could not fetch Groww reviews ({sort_mode.name}): {e}")

    print(f"Groww Play Store collection finished: {len(all_filtered)} relevant SIP reviews identified.")
    return all_filtered

# Backward-compatible alias
get_sip_playstore_reviews = get_groww_playstore_reviews

if __name__ == '__main__':
    recs = get_groww_playstore_reviews(limit=100)
    print(f"Fetched {len(recs)} relevant Groww SIP reviews.")
    for r in recs[:3]:
        print(f" - [{r['metadata']['score']}*] {r['content'][:100]}...")
