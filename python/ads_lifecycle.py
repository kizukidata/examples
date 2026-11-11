"""Ad lifecycle for a few EU TikTok advertisers: what is new, scaling or stopped.

Price at the Free tier, per returned row: tiktok-ads-monitor $0.0018.
No per-item charge when an input yields nothing; Apify's run start fee still
applies. With onlyChanges on, ACTIVE ads are skipped and not charged.

Run (APIFY_TOKEN set): python ads_lifecycle.py

Run it on a schedule. The first run returns every listed ad as NEW and charges
for it, and records the state; from the second run the rows say NEW, SCALING or
STOPPED against the previous run.
"""

import os

from apify_client import ApifyClient

ADS_INPUT = {
    "queries": ["Nike"],
    "regions": ["DE", "FR"],
    "days": 30,
    "onlyChanges": True,
    "includeDetails": True,  # adds adText, the ad's own copy
    "maxItems": 30,
}

PRICE_PER_AD = 0.0018


def main():
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        raise SystemExit("APIFY_TOKEN is not set")
    client = ApifyClient(token)

    run = client.actor("kizukidata/tiktok-ads-monitor").call(run_input=ADS_INPUT)
    if run is None:
        raise SystemExit("the run did not start")
    rows = client.dataset(run.default_dataset_id).list_items().items
    charged = [r for r in rows if not r.get("error") and r.get("lifecycle") != "ACTIVE"]
    print(f"{len(charged)} ads changed, about ${len(charged) * PRICE_PER_AD:.4f} at the Free tier")

    order = {"NEW": 0, "SCALING": 1, "STOPPED": 2, "ACTIVE": 3}
    for row in sorted(rows, key=lambda r: order.get(r.get("lifecycle"), 9)):
        if row.get("error"):
            print(f"  {row.get('adId')}: {(row.get('error') or {}).get('type', 'error')} (not charged)")
            continue
        print(
            f"  {row.get('lifecycle', '?'):8} {row.get('advertiser') or '?':20} "
            f"{row.get('firstShownAt')} to {row.get('lastShownAt')} "
            f"({row.get('daysRunning')} days, reach {row.get('reachChange') or 'no comparison'})"
        )
        if row.get("adText"):
            print(f"           {row['adText'][:120]}")
        print(f"           {row.get('libraryUrl')}")


if __name__ == "__main__":
    main()
