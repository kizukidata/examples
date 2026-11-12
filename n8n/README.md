# n8n

One node per Actor. The Apify community node `@apify/n8n-nodes-apify` runs an Actor and returns its dataset as items, so the next node in the flow gets rows, not a run ID.

## Add a node

1. In n8n, install the community node `@apify/n8n-nodes-apify` (Settings > Community nodes) and create an **Apify API** credential with your token from [Apify Console > Settings > API & Integrations](https://console.apify.com/settings/integrations).
2. Add an **Apify** node and set **Resource** = `Actors`, **Operation** = `Run actor and get dataset`.
3. Pick the Actor from Apify Store, then set **Actor input** = `JSON` and paste one of the bodies below.
4. Keep a cap on the run: set **Max total charge (USD)** to a value such as `0.25`. It stops the run before it can spend more, whatever the row count turns out to be.
5. Run it once by hand. The first run of an `onlyNewItems` / `onlyChanges` Actor returns everything in the window and records the state; the next run returns only what changed.

## Bodies

| Actor | Actor ID | Input |
|---|---|---|
| `kizukidata/youtube-transcripts` | `SfgmJC41bVTTEcH7H` | `bodies/youtube-transcripts.json` |
| `kizukidata/pdf-to-markdown` | `9vYNAb4obRGlqPBwH` | `bodies/pdf-to-markdown.json` |
| `kizukidata/url-to-markdown` | `OjoTmqGeAQVv9BBR6` | `bodies/url-to-markdown.json` |
| `kizukidata/linkedin-jobs-feed` | `xZfQb5hYCO3omCKj8` | `bodies/linkedin-jobs-feed.json` |
| `kizukidata/linkedin-company-monitor` | `7wLKOq6tNeoKnvhoe` | `bodies/linkedin-company-monitor.json` |
| `kizukidata/google-news-feed` | `6G99DZ5S5Pj5V8yGB` | `bodies/google-news-feed.json` |
| `kizukidata/telegram-channel-feed` | `snxdKxjzNVWPcA88F` | `bodies/telegram-channel-feed.json` |
| `kizukidata/youtube-channel-monitor` | `PqDFuCIowEy50TfMO` | `bodies/youtube-channel-monitor.json` |
| `kizukidata/note-articles-feed` | `Un2LHIdrpO5weDDwh` | `bodies/note-articles-feed.json` |
| `kizukidata/tiktok-ads-monitor` | `Pe4JdBdxQJmz2HWqI` | `bodies/tiktok-ads-monitor.json` |

Values can come from earlier nodes instead of being fixed. The node accepts an expression, so a **Set** node with `queries` and `maxItems` can feed the body:

```js
{{ JSON.stringify({ queries: $json.queries.split(',').map(s => s.trim()), timespan: '24h', onlyNewItems: true, maxItems: Number($json.maxItems) }) }}
```

## Two flows that work as they are

**Morning news digest.** Schedule Trigger (08:00) > Apify node with `bodies/google-news-feed.json` > Filter (items exist) > Slack or email node. A day with no new articles sends nothing.

**New jobs into a sheet.** Schedule Trigger (every hour) > Apify node with `bodies/linkedin-jobs-feed.json` > Google Sheets append. The second run inserts only the postings that were not in the first.

Prices are per returned row, so an empty day costs only the run start fee. Free tier, per row: youtube-transcripts $0.0010, pdf-to-markdown $0.0016, url-to-markdown $0.00033, linkedin-jobs-feed $0.00033, linkedin-company-monitor $0.00129, google-news-feed $0.00136, telegram-channel-feed $0.00028, youtube-channel-monitor $0.00024, note-articles-feed $0.00121, tiktok-ads-monitor $0.00033. No per-item charge when an input yields nothing.
