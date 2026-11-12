# Kizuki Actor examples

Copy-paste examples for the Kizuki Actors on [Apify Store](https://apify.com/kizukidata). MIT licensed, so you can change and reuse them.

The examples are grouped by job, because most jobs need two or three Actors: a transcript plus a PDF for a RAG index, a jobs feed plus a company monitor for hiring signals.

| Job | Actors used | Python | JavaScript |
|---|---|---|---|
| RAG ingest: talks, PDFs and pages as Markdown and chunks | `youtube-transcripts`, `pdf-to-markdown`, `url-to-markdown` | [rag_ingest.py](python/rag_ingest.py) | [rag_ingest.mjs](javascript/rag_ingest.mjs) |
| Hiring signals: new jobs and changed company pages | `linkedin-jobs-feed`, `linkedin-company-monitor` | [hiring_signals.py](python/hiring_signals.py) | [hiring_signals.mjs](javascript/hiring_signals.mjs) |
| Morning news digest: news, channels, video | `google-news-feed`, `telegram-channel-feed`, `youtube-channel-monitor` | [news_digest.py](python/news_digest.py) | [news_digest.mjs](javascript/news_digest.mjs) |
| Ad lifecycle: what started, scaled or stopped | `tiktok-ads-monitor` | [ads_lifecycle.py](python/ads_lifecycle.py) | use the same pattern as `news_digest.mjs` |
| Japanese creator posts | `note-articles-feed` | use the same pattern as `news_digest.py` | use the same pattern as `news_digest.mjs` |

## Set a token

The examples read `APIFY_TOKEN` from the environment. They never contain a token. Create one at [Apify Console > Settings > API & Integrations](https://console.apify.com/settings/integrations).

```powershell
$env:APIFY_TOKEN = "<your Apify API token>"   # PowerShell
```

```bash
export APIFY_TOKEN="<your Apify API token>"   # bash, zsh
```

Install and run:

```bash
python -m pip install -r python/requirements.txt
python python/rag_ingest.py

cd javascript && npm install && node rag_ingest.mjs
```

## Prices

Apify Free tier prices per returned row, November 2026. A higher Apify plan lowers the row price; it does not change the run start fee.

| Actor | One row | Per row | Rows for the USD 5 monthly free credit (start fees aside) |
|---|---|---|---|
| `youtube-transcripts` | one video's captions: Markdown, segments, chunks | $0.0010 | 5,000 videos |
| `pdf-to-markdown` | one PDF as page-numbered Markdown | $0.0016 | 3,125 PDFs |
| `url-to-markdown` | one page's main content as Markdown | $0.00033 | 15,151 pages |
| `linkedin-jobs-feed` | one job posting, with the job page read | $0.00033 | 15,151 jobs |
| `linkedin-company-monitor` | one company page | $0.00129 | 3,875 companies |
| `google-news-feed` | one article | $0.00136 | 3,676 articles |
| `telegram-channel-feed` | one post | $0.00028 | 17,857 posts |
| `youtube-channel-monitor` | one channel, video or comment row | $0.00024 | 20,833 rows |
| `note-articles-feed` | one note.com article | $0.00121 | 4,132 articles |
| `tiktok-ads-monitor` | one ad | $0.00033 | 15,151 ads |
| `wechat-article-reader` | one WeChat Official Account article: text, Markdown, account data | $0.0016 | 3,125 articles |
| `mcp-server-directory` | one public MCP server merged from three directories | $0.00036 | 13,888 servers |

A run that finds nothing has no per-row charge. `pdf-to-markdown` returns a PDF without a text layer as an uncharged row with `status: "scan"` and the pages that need OCR; a PDF it cannot download comes back as an uncharged `status: "failed"` row. A page that is not a PDF or a file it cannot read is listed in the run's `OUTPUT` record, and neither is charged. A blocked LinkedIn job page and an unknown Telegram channel are rows in the dataset with the reason. `url-to-markdown` writes no row for a page it cannot read and reports it in the run's `OUTPUT` record under `skippedInputs`. Apify's run start fee applies to every run: USD 0.00005 per GB of memory (one event per GB, minimum one event; USD 0.0001 at 2 GB, for example). Each Actor's page shows its default memory.

## Cost control in the examples

- `maxItems` bounds the rows in one run. Every example sets it.
- `onlyNewItems: true` (jobs, news, Telegram, YouTube, note) returns only rows that an earlier run with the same input did not return, and charges only those. State is kept for 90 days in a key-value store in your own Apify account.
- `onlyChanges: true` (company pages, TikTok ads) returns only rows whose tracked fields moved.
- The first run with `onlyNewItems` returns everything inside the window, so start with a small `maxItems`.

The examples do not use Apify's `maxTotalChargeUsd` run option; set it in the n8n node, the Console or the API if you want a hard cap on a run.

## From code (curl)

```bash
curl -s -X POST "https://api.apify.com/v2/acts/kizukidata~url-to-markdown/run-sync-get-dataset-items?format=json" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://apify.com/kizukidata"], "maxItems": 1}'
```

`run-sync-get-dataset-items` waits for the run and returns the rows. For long runs, start with `POST /v2/acts/{actorId}/runs` and read the dataset afterwards.

## From an AI agent (MCP)

Three bundles are in the official MCP Registry: `io.github.kizukidata/hiring-signals`, `io.github.kizukidata/news-monitoring`, `io.github.kizukidata/rag-ingest`. The MCP server at `https://mcp.apify.com` takes a `tools` parameter, so an agent can load just one bundle:

```bash
claude mcp add --transport http kizuki-rag "https://mcp.apify.com?tools=kizukidata/youtube-transcripts,kizukidata/pdf-to-markdown,kizukidata/url-to-markdown"
```

Config files for Claude Desktop and Cursor, the Bearer token form and a stdio fallback are in [mcp/](mcp/).

## From n8n

Node settings, one body per Actor and two ready flows are in [n8n/](n8n/).

## What a failure row looks like

A row that records a failure is still returned, so a scheduled flow can tell "nothing happened" from "the source refused us":

```json
{
  "id": "3a26182bd67c0580",
  "type": "company",
  "status": "failed",
  "slug": "apify",
  "url": "https://www.linkedin.com/company/apify/",
  "changes": null,
  "errorCode": "authwall"
}
```

(Fields abridged. `status: ok` rows carry the company values; `failed` rows carry `errorCode` and `errorMessage` instead.)

Check `error` (most Actors), `status` (PDF and company pages) or `detailsStatus` (LinkedIn jobs) before you use a row. A row with `error` set, `status: "failed"` or `"scan"`, or `detailsStatus: "blocked"` is not charged; an `unavailable` job row is charged.

`url-to-markdown` writes no row for a page it cannot read; the reason is in the run's `OUTPUT` record under `skippedInputs`.

## Not official data

Kizuki is an independent developer on Apify Store. The Actors are unofficial and not affiliated with or endorsed by Apify, LinkedIn, Google, YouTube, Telegram, TikTok, note or Tencent, or by the MCP project, Smithery or the maintainers of the awesome-mcp-servers list. You are responsible for how you use the data, including any licence or privacy rule that applies to it.

## 日本語の要点

- このリポジトリは Kizuki の Actor を、用途ごと（RAG 取り込み・採用の変化・ニュースの朝のまとめ・広告の変化）に API・Python・JavaScript・MCP・n8n から使う例です。MIT で、書き換えて使えます。
- トークンは環境変数 `APIFY_TOKEN` から読みます。値はどのファイルにも入っていません。
- 値段は 1 行あたり（Free の段、2026-11 の時点）。例ごとに、その Actor の値段を書いてあります。Free の月 USD 5 で何件ほど試せるかも表にしています。
- 入力を処理して 0 件だったときは、1 件あたりの課金はありません。テキストの無い PDF は `status: "scan"` の行で返り、課金されません。ダウンロードできなかった PDF は `status: "failed"` の行で返り、これも課金されません。PDF でないページや読めないファイルは run の `OUTPUT` に載り、どちらも課金されません。読めない URL は行を作らず、run の `OUTPUT` の `skippedInputs` に残ります。走らせるたびに Apify の起動料（1 GB ごとに USD 0.00005、1 GB 未満でも 1 回分。2 GB なら USD 0.0001。既定のメモリは各 Actor の頁）がかかります。
- `onlyNewItems` / `onlyChanges` を付けると、前回と同じ入力で返した行は返さず、課金もしません（状態は自分のアカウントの key-value store に 90 日残ります）。最初の 1 回は窓の中の全部が返るので、`maxItems` を小さくして始めてください。
- MCP は 3 つのまとめ（hiring-signals・news-monitoring・rag-ingest）を公式の MCP Registry に置いています。`https://mcp.apify.com?tools=...` の形で、使う Actor だけを読み込めます。
