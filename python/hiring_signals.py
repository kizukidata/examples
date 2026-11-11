"""New LinkedIn jobs and changed company pages in one pass.

Price at the Free tier, per returned row: linkedin-jobs-feed $0.0012,
linkedin-company-monitor $0.0020. No per-item charge when an input yields
nothing; Apify's run start fee still applies.

Run (APIFY_TOKEN set): python hiring_signals.py

Writes out/jobs.csv and prints the company fields that moved.
"""

import csv
import os
from pathlib import Path

from apify_client import ApifyClient

OUT = Path(__file__).parent / "out"

JOBS_INPUT = {
    "keywords": "data engineer",
    "location": "Berlin, Germany",
    "daysSincePosted": 7,
    "onlyNewItems": True,  # only what an earlier run with the same search did not return
    "includeDetails": True,
    "maxItems": 20,
}

COMPANY_INPUT = {
    "companies": ["apify", "google"],
    "onlyChanges": True,  # only companies whose fields differ from the previous run
    "maxItems": 5,
}

PRICE_PER_ROW = {
    "kizukidata/linkedin-jobs-feed": 0.0012,
    "kizukidata/linkedin-company-monitor": 0.0020,
}


def run_actor(client, actor, run_input, charged):
    run = client.actor(actor).call(run_input=run_input)
    if run is None:
        raise SystemExit(f"{actor}: the run did not start")
    rows = client.dataset(run.default_dataset_id).list_items().items
    billable = [r for r in rows if charged(r)]
    print(f"{actor}: {len(rows)} rows, {len(billable)} charged, about ${len(billable) * PRICE_PER_ROW[actor]:.4f}")
    return rows


def pay(row):
    if row.get("compensationSummary"):
        return row["compensationSummary"]
    low, high = row.get("salaryMin"), row.get("salaryMax")
    if low is None and high is None:
        return ""
    span = f"{low}-{high}" if low is not None and high is not None else str(low if low is not None else high)
    return " ".join(part for part in (row.get("salaryCurrency"), span, row.get("salaryPeriod")) if part)


def main():
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("APIFY_TOKEN is not set")
    client = ApifyClient(token)
    OUT.mkdir(exist_ok=True)

    jobs = run_actor(
        client,
        "kizukidata/linkedin-jobs-feed",
        JOBS_INPUT,
        lambda r: r.get("detailsStatus") != "blocked",
    )
    columns = ["postedAt", "title", "companyName", "location", "employmentType", "seniority", "pay", "url"]
    with (OUT / "jobs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in jobs:
            writer.writerow(
                {
                    "postedAt": row.get("postedAt") or "",
                    "title": row.get("title") or "",
                    "companyName": row.get("companyName") or "",
                    "location": row.get("location") or "",
                    "employmentType": row.get("employmentType") or "",
                    "seniority": row.get("seniority") or "",
                    "pay": pay(row),
                    "url": row.get("url") or "",
                }
            )
    print(f"{len(jobs)} jobs written to {OUT / 'jobs.csv'}")

    companies = run_actor(
        client,
        "kizukidata/linkedin-company-monitor",
        COMPANY_INPUT,
        lambda r: r.get("status") == "ok",
    )
    for row in companies:
        if row.get("status") != "ok":
            print(f"  {row.get('slug')}: {row.get('errorCode')} (not charged)")
            continue
        changes = row.get("changes") or {}
        if changes.get("baseline"):
            print(f"  {row.get('name')}: first run, the current values are the baseline")
            continue
        diffs = changes.get("diffs") or []
        print(f"  {row.get('name')}: {len(diffs)} fields changed")
        for diff in diffs:
            print(f"    {diff['field']}: {diff['from']} -> {diff['to']}")


if __name__ == "__main__":
    main()
