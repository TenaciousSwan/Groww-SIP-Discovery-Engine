from google_play_scraper import Sort, reviews
from datetime import datetime, timedelta
import uuid

PRIMARY_APP = {
    'name': 'Groww',
    'id': 'com.nextbillion.groww'
}

SIP_KEYWORDS = [
    'sip', 'autopay', 'mandate', 'nach', 'instalment', 'installment',
    'cancel', 'cancelling', 'cancelled', 'pause', 'pausing', 'paused',
    'stopped', 'failed', 'deducted', 'allotment', 'allotted',
    'nav', 'negative return', 'loss', 'first time', 'beginner',
    'skip', 'skipping', 'mutual fund', 'xirr', 'units', 'folio',
    'bounce', 'penalty', 'delay', 'delayed', 'salary', 'auto debit',
    'auto-debit', 'ecs', 'step up', 'step-up', 'insufficient',
    'cams', 'kfintech', 'amc', 'redemption', 'crash', 'market fall',
    'portfolio', 'cut off', 'cut-off', 'due date', '250', '350', '48 hours'
]

def get_groww_playstore_reviews(limit_per_score=200, pages_per_score=3, months_back=18):
    """
    Deep-scrapes real public Google Play Store reviews for Groww (com.nextbillion.groww).
    Iterates across all 5 star ratings (1★ through 5★) and both MOST_RELEVANT and NEWEST
    sort orders with token pagination to maximize the discovery of real user experiences:
    - 1★ & 2★: Critical friction, bank bounce charges, mandate failures, skip blocks, cancellation.
    - 3★: Hesitation, confusion over NAV date, XIRR vs absolute returns, comparison.
    - 4★ & 5★: Long-term continuation enablers, successful habit formation, salary-day alignments.
    """
    cutoff_date = datetime.now() - timedelta(days=30 * months_back)
    all_filtered = []
    seen_ids = set()
    app_id = PRIMARY_APP['id']

    print(f"Starting deep collection of Groww Play Store reviews (App ID: {app_id})...")

    for sort_type in [Sort.MOST_RELEVANT, Sort.NEWEST]:
        sort_name = "MOST_RELEVANT" if sort_type == Sort.MOST_RELEVANT else "NEWEST"
        print(f"\n--- Scraping Groww Reviews [{sort_name}] ---")

        for score in [1, 2, 3, 4, 5]:
            token = None
            for page in range(pages_per_score):
                try:
                    res, token = reviews(
                        app_id,
                        lang='en',
                        country='in',
                        sort=sort_type,
                        filter_score_with=score,
                        count=limit_per_score,
                        continuation_token=token
                    )
                    if not res:
                        break

                    matched_in_page = 0
                    for r in res:
                        rid = r.get('reviewId') or str(uuid.uuid4())
                        if rid in seen_ids:
                            continue

                        rev_date = r.get('at')
                        if rev_date and rev_date < cutoff_date:
                            continue

                        content = r.get('content', '')
                        if not content or len(content.strip()) < 12:
                            continue

                        content_lower = content.lower()
                        if any(kw in content_lower for kw in SIP_KEYWORDS):
                            seen_ids.add(rid)
                            matched_in_page += 1
                            all_filtered.append({
                                'id': f"groww_ps_{rid}",
                                'source': "Play Store (Groww)",
                                'content': content,
                                'timestamp': rev_date.isoformat() if rev_date else datetime.now().isoformat(),
                                'url': f"https://play.google.com/store/apps/details?id={app_id}&reviewId={rid}",
                                'metadata': {
                                    'app': 'Groww',
                                    'score': r.get('score', score),
                                    'thumbsUpCount': r.get('thumbsUpCount', 0),
                                    'sort_mode': sort_name,
                                    'page': page + 1,
                                    'appVersion': r.get('appVersion', '')
                                },
                                'collection_date': datetime.now().isoformat(),
                                'collection_method': 'google_play_scraper_deep'
                            })

                    print(f"  [{sort_name} | Score {score}* | Page {page+1}]: {len(res)} reviews scanned -> {matched_in_page} SIP matched (Total so far: {len(all_filtered)})")
                    if not token:
                        break
                except Exception as e:
                    print(f"  Notice on {sort_name} Score {score}* page {page+1}: {e}")
                    break

    print(f"\nCompleted Groww Play Store deep ingestion: {len(all_filtered)} unique, verified SIP reviews extracted.")
    return all_filtered

# Backward-compatible alias
get_sip_playstore_reviews = get_groww_playstore_reviews

if __name__ == '__main__':
    recs = get_groww_playstore_reviews(limit_per_score=100, pages_per_score=1)
    print(f"Sample count: {len(recs)}")
