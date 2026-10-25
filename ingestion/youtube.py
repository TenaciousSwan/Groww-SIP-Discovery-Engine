import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN")

# Real Myntra haul / review YouTube video IDs (verified working)
MYNTRA_VIDEO_IDS = [
    "K7e-0FiLzR0",   # Myntra haul India
    "t7RFVDgbWQY",   # Myntra shopping haul
    "NLGszMHhfqQ",   # Myntra fashion review
    "WYvb7sgtxH4",   # Myntra try-on haul
    "pj9mfFi0R9s",   # Myntra wishlist haul
]

MOCK_COMMENTS = [
    "The fit on that Myntra dress looks weird, is it true to size?",
    "I added the second top to my wishlist, thanks for the review!",
    "Quality does not look that great for the price.",
    "I returned this exact item yesterday because of sizing issues.",
    "Still confused if I should buy from Myntra or somewhere else.",
    "The fabric looks thin in the video, can you confirm?",
    "Always hesitate before buying from Myntra because of wrong sizes.",
    "Been in my wishlist for 2 months, still not sure if worth it."
]


def _get_mock_records():
    print("  [YouTube] Returning mock YouTube data as fallback.")
    records = []
    for i, content in enumerate(MOCK_COMMENTS):
        records.append({
            "id": f"youtube_mock_{i}_{uuid.uuid4().hex[:8]}",
            "source": "youtube",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "url": "https://www.youtube.com/watch?v=mock",
            "metadata": "{\"video_id\": \"mock\"}"
        })
    return records


def get_youtube_comments(video_ids=None, limit_per_video=30):
    """
    Fetch real YouTube comments via Apify youtube-scraper actor.
    Falls back to mock data if APIFY_API_TOKEN is not set or actor fails.
    """
    if not APIFY_TOKEN:
        return _get_mock_records()

    target_ids = video_ids or MYNTRA_VIDEO_IDS

    try:
        from apify_client import ApifyClient
        client = ApifyClient(APIFY_TOKEN)

        print(f"[YouTube] Starting Apify scraper for {len(target_ids)} videos...")

        run_input = {
            "startUrls": [
                {"url": f"https://www.youtube.com/watch?v={vid}"}
                for vid in target_ids
            ],
            "maxComments": limit_per_video,
            "maxResultStreams": 0,
            "maxResults": limit_per_video * len(target_ids),
        }

        run = client.actor("streamers/youtube-scraper").call(run_input=run_input)

        # Fix: handle both dict and object response from Apify SDK versions
        if isinstance(run, dict):
            dataset_id = run.get("defaultDatasetId")
        else:
            dataset_id = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)

        if not dataset_id:
            raise ValueError("Could not retrieve dataset ID from Apify run.")

        records = []
        for item in client.dataset(dataset_id).iterate_items():
            comments = item.get("comments") or []
            video_id = item.get("id") or "unknown"

            for comment in comments:
                content = comment.get("text") or ""
                if not content.strip():
                    continue

                published_at = comment.get("date") or datetime.now().isoformat()
                comment_id = comment.get("id") or uuid.uuid4().hex

                records.append({
                    "id": f"youtube_{comment_id}",
                    "source": "youtube",
                    "content": content,
                    "timestamp": str(published_at),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "metadata": f"{{\"video_id\": \"{video_id}\"}}"
                })

        print(f"[YouTube] Apify scraping complete. Fetched {len(records)} comments.")
        return records if records else _get_mock_records()

    except Exception as e:
        print(f"[YouTube] Apify actor failed: {e}. Falling back to mock data.")
        return _get_mock_records()


if __name__ == "__main__":
    records = get_youtube_comments()
    for r in records[:3]:
        print(r)
