"""A morning digest from Google News, Telegram channels and YouTube channels.

Price at the Free tier, per returned row: google-news-feed $0.00136,
telegram-channel-feed $0.00028, youtube-channel-monitor $0.00024. No per-item
charge when an input yields nothing; Apify's run start fee still applies.

Run (APIFY_TOKEN set): python news_digest.py

Prints one block per source. Run it twice: the second run returns only what is
new, because every Actor here keeps its own state per input for 90 days.
"""

import os

from apify_client import ApifyClient

NEWS_INPUT = {
    "queries": ["electric vehicles", '"grid storage"'],
    "edition": "US:en",
    "timespan": "24h",
    "onlyNewItems": True,
    "resolveArticleUrls": True,
    "maxItems": 25,
}

TELEGRAM_INPUT = {
    "channels": ["durov"],
    "maxPostsPerChannel": 20,
    "onlyNewItems": True,
    "maxItems": 20,
}

YOUTUBE_INPUT = {
    "channels": ["@AndrejKarpathy"],
    "mode": "videos",
    "maxVideosPerChannel": 3,
    "onlyNewItems": True,
    "maxItems": 20,
}

PRICE_PER_ROW = {
    "kizukidata/google-news-feed": 0.0017,
    "kizukidata/telegram-channel-feed": 0.0020,
    "kizukidata/youtube-channel-monitor": 0.0011,
}


def run_actor(client, actor, run_input):
    run = client.actor(actor).call(run_input=run_input)
    if run is None:
        raise SystemExit(f"{actor}: the run did not start")
    rows = client.dataset(run.default_dataset_id).list_items().items
    charged = [r for r in rows if not r.get("error")]
    print(f"{actor}: {len(rows)} rows, about ${len(charged) * PRICE_PER_ROW[actor]:.4f}")
    return rows


def main():
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("APIFY_TOKEN is not set")
    client = ApifyClient(token)

    print("\nGoogle News")
    for row in run_actor(client, "kizukidata/google-news-feed", NEWS_INPUT):
        link = row.get("articleUrl") or row.get("googleNewsUrl")
        print(f"  {(row.get('publishedAt') or '')[:16]}  {row.get('outlet')}: {row.get('title')}\n    {link}")

    print("\nTelegram")
    for row in run_actor(client, "kizukidata/telegram-channel-feed", TELEGRAM_INPUT):
        if row.get("error"):
            print(f"  {row.get('channel')}: {(row.get('error') or {}).get('type', 'error')} (not charged)")
            continue
        first_line = (row.get("text") or "").strip().splitlines()[0] if row.get("text") else ""
        print(f"  {(row.get('publishedAt') or '')[:16]}  {row.get('channel')}: {first_line[:120]}\n    {row.get('url')}")

    print("\nYouTube")
    for row in run_actor(client, "kizukidata/youtube-channel-monitor", YOUTUBE_INPUT):
        if row.get("error"):
            print(f"  {row.get('channelId')}: {(row.get('error') or {}).get('type', 'error')} (not charged)")
            continue
        if row.get("type") != "video":
            continue  # channel and comment rows are in the same dataset
        print(f"  {row.get('publishedAt')}  {row.get('title')} ({row.get('views')} views)\n    {row.get('url')}")


if __name__ == "__main__":
    main()
