"""Turn two YouTube talks, one PDF and one web page into Markdown and RAG chunks.

Price at the Free tier, per returned row: youtube-transcripts $0.0010,
pdf-to-markdown $0.0016, url-to-markdown $0.00033. No per-item charge when an
input yields nothing; Apify's run start fee still applies.

Run:
    python -m pip install -r requirements.txt
    $env:APIFY_TOKEN = "<your token>"     # PowerShell
    python rag_ingest.py

Writes out/*.md and out/chunks.jsonl next to this file.
"""

import json
import os
from pathlib import Path

from apify_client import ApifyClient

OUT = Path(__file__).parent / "out"

# one row per video, per PDF and per page; maxItems caps what a run can cost
TRANSCRIPTS_INPUT = {
    "videos": [
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "https://www.youtube.com/watch?v=kCc8FmEb1nY",
    ],
    "languages": ["en"],
    "output": "both",
    "chunkSize": 1200,
    "maxItems": 2,
}

PDF_INPUT = {
    "pdfUrls": ["https://arxiv.org/pdf/1706.03762"],
    "maxItems": 1,
}

PAGE_INPUT = {
    "urls": ["https://apify.com/kizukidata"],
    "maxItems": 1,
    "maxCharsPerPage": 20000,
}

PRICE_PER_ROW = {
    "kizukidata/youtube-transcripts": 0.0020,
    "kizukidata/pdf-to-markdown": 0.0022,
    "kizukidata/url-to-markdown": 0.0014,
}


def run_actor(client, actor, run_input):
    """Run one Actor and return its dataset rows, with the rows we were charged for."""
    run = client.actor(actor).call(run_input=run_input)
    if run is None:
        raise SystemExit(f"{actor}: the run did not start")
    rows = client.dataset(run.default_dataset_id).list_items().items
    # A row that only records a failure is in the dataset but is not charged.
    charged = [r for r in rows if not r.get("error") and r.get("status") in (None, "ok")]
    cost = len(charged) * PRICE_PER_ROW[actor]
    print(f"{actor}: {len(rows)} rows, {len(charged)} charged, about ${cost:.4f}")
    return rows


def main():
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("APIFY_TOKEN is not set")
    client = ApifyClient(token)
    OUT.mkdir(exist_ok=True)
    chunks = []

    for row in run_actor(client, "kizukidata/youtube-transcripts", TRANSCRIPTS_INPUT):
        if row.get("error") or not row.get("markdown"):
            reason = (row.get("error") or {}).get("type", "no markdown")
            print(f"  {row.get('videoId')}: skipped, {reason}")
            continue
        target = OUT / f"transcript-{row['videoId']}.md"
        target.write_text(row["markdown"], encoding="utf-8")
        for chunk in row.get("chunks") or []:
            chunks.append(
                {
                    "source": row["url"],
                    "title": row["title"],
                    "start": chunk["start"],
                    "text": chunk["text"],
                }
            )

    for row in run_actor(client, "kizukidata/pdf-to-markdown", PDF_INPUT):
        if row.get("status") != "ok" or not row.get("markdown"):
            # scan or failed: no row content, not charged
            print(f"  {row.get('url')}: {row.get('status')}, not charged")
            continue
        name = row["url"].rstrip("/").rsplit("/", 1)[-1].removesuffix(".pdf") or "document"
        (OUT / f"{name}.md").write_text(row["markdown"], encoding="utf-8")

    for row in run_actor(client, "kizukidata/url-to-markdown", PAGE_INPUT):
        if not row.get("markdown"):
            continue
        (OUT / "page.md").write_text(row["markdown"], encoding="utf-8")

    with (OUT / "chunks.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"{len(chunks)} chunks written to {OUT / 'chunks.jsonl'}")
    print(f"Markdown files written to {OUT}")


if __name__ == "__main__":
    main()
