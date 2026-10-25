import os
import uuid
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

TARGET_SUBREDDITS = [
    "india",
    "IndiaSpeaks",
    "IndianConsumer",
    "IndianStockMarket"
]

SEARCH_QUERY = 'Blinkit wallet OR Blinkit cashback OR Blinkit refund'

MOCK_TOPICS = [
    "Blinkit wallet balance issue",
    "Blinkit cashback not received",
    "Blinkit wallet refund pending",
    "Blinkit money deducted from wallet"
]
MOCK_COMMENTS = [
    "Blinkit wallet money was deducted but the order was cancelled.",
    "My Blinkit cashback has not appeared in the wallet.",
    "Blinkit wallet refund is still pending after the order was cancelled.",
    "Where can I check my Blinkit wallet balance?"
]


def _get_mock_records(limit=100):
    import random
    print(f"  [Reddit] Generating {limit} mock records as fallback.")
    records = []
    for _ in range(limit):
        is_post = random.choice([True, False])
        content = random.choice(MOCK_TOPICS) if is_post else random.choice(MOCK_COMMENTS)
        subreddit = random.choice(TARGET_SUBREDDITS)
        days_ago = random.randint(0, 30)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
        record_id = str(uuid.uuid4())
        post_type = "post" if is_post else "comment"
        records.append({
            "id": f"reddit_{record_id}",
            "source": "reddit",
            "content": content,
            "timestamp": timestamp,
            "url": f"https://reddit.com/r/{subreddit}/comments/{record_id[:8]}",
            "metadata": f'{{"subreddit": "{subreddit}", "type": "{post_type}"}}'
        })
    return records


def _fetch_subreddit(subreddit, query, limit=25):
    """Fetch posts from Reddit public JSON API (no auth required)."""
    query_params = urllib.parse.urlencode({
        "q": query,
        "sort": "new",
        "limit": limit,
        "restrict_sr": 1
    })
    url = f"https://www.reddit.com/r/{subreddit}/search.json?{query_params}"
    headers = {"User-Agent": "BlinkitWalletInsightBot/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data.get("data", {}).get("children", [])
    except Exception as e:
        print(f"  [Reddit] Failed to fetch r/{subreddit}: {e}")
        return []


def get_reddit_posts(limit=150):
    """
    Fetch real Reddit posts via Reddit public JSON API (completely free, no auth).
    Falls back to mock data only if all requests fail.
    """
    print(f"[Reddit] Fetching real posts from {len(TARGET_SUBREDDITS)} subreddits via Reddit JSON API...")
    records = []
    per_sub = max(25, limit // len(TARGET_SUBREDDITS))

    for subreddit in TARGET_SUBREDDITS:
        posts = _fetch_subreddit(subreddit, SEARCH_QUERY, per_sub)
        for post in posts:
            d = post.get("data", {})
            # Use selftext (body) or title
            content = d.get("selftext", "").strip()
            if not content or content == "[removed]" or content == "[deleted]":
                content = d.get("title", "").strip()
            if not content:
                continue

            created_utc = d.get("created_utc", 0)
            try:
                timestamp = datetime.utcfromtimestamp(created_utc).isoformat()
            except Exception:
                timestamp = datetime.now().isoformat()

            post_id = d.get("id") or str(uuid.uuid4())
            records.append({
                "id": f"reddit_{post_id}",
                "source": "reddit",
                "content": content,
                "timestamp": timestamp,
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "metadata": f'{{"subreddit": "{subreddit}", "type": "post", "score": {d.get("score", 0)}}}'
            })
        time.sleep(1)  # Be polite to Reddit API

    if not records:
        print("[Reddit] No records fetched, using mock fallback.")
        return _get_mock_records(limit)

    print(f"[Reddit] Fetched {len(records)} real posts from Reddit.")
    return records[:limit]


if __name__ == "__main__":
    records = get_reddit_posts(limit=20)
    for r in records[:3]:
        print(r)
