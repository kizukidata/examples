// Turn two YouTube talks, a PDF and a web page into Markdown and RAG chunks.
//
// Price at the Free tier, per returned row: youtube-transcripts $0.0020,
// pdf-to-markdown $0.0022, url-to-markdown $0.0014. No per-item charge when an
// input yields nothing; Apify's run start fee still applies.
//
// Run: npm install && node rag_ingest.mjs   (with APIFY_TOKEN set)
// Writes out/*.md and out/chunks.jsonl next to this file.

import { mkdir, writeFile } from 'node:fs/promises';
import { ApifyClient } from 'apify-client';

if (!process.env.APIFY_TOKEN) {
  console.error('APIFY_TOKEN is not set');
  process.exit(1);
}

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
const OUT = new URL('./out/', import.meta.url);

const PRICE = {
  'kizukidata/youtube-transcripts': 0.002,
  'kizukidata/pdf-to-markdown': 0.0022,
  'kizukidata/url-to-markdown': 0.0014,
};

const TRANSCRIPTS_INPUT = {
  videos: [
    'https://www.youtube.com/watch?v=aircAruvnKk',
    'https://www.youtube.com/watch?v=kCc8FmEb1nY',
  ],
  languages: ['en'],
  output: 'both',
  chunkSize: 1200,
  maxItems: 2,
};

const PDF_INPUT = {
  pdfUrls: ['https://arxiv.org/pdf/1706.03762'],
  maxItems: 1,
};

const PAGE_INPUT = {
  urls: ['https://apify.com/kizukidata'],
  maxItems: 1,
  maxCharsPerPage: 20000,
};

async function runActor(actor, input) {
  const run = await client.actor(actor).call(input);
  if (!run) {
    throw new Error(`${actor}: the run did not start`);
  }
  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  // A row that only records a failure is in the dataset but is not charged.
  const charged = items.filter((row) => !row.error && (row.status === undefined || row.status === 'ok'));
  console.log(`${actor}: ${items.length} rows, ${charged.length} charged, about $${(charged.length * PRICE[actor]).toFixed(4)}`);
  return items;
}

await mkdir(OUT, { recursive: true });
const chunks = [];

for (const row of await runActor('kizukidata/youtube-transcripts', TRANSCRIPTS_INPUT)) {
  if (row.error || !row.markdown) {
    console.log(`  ${row.videoId}: skipped, ${row.error?.type ?? 'no markdown'}`);
    continue;
  }
  await writeFile(new URL(`transcript-${row.videoId}.md`, OUT), row.markdown, 'utf8');
  for (const chunk of row.chunks ?? []) {
    chunks.push({ source: row.url, title: row.title, start: chunk.start, text: chunk.text });
  }
}

for (const row of await runActor('kizukidata/pdf-to-markdown', PDF_INPUT)) {
  if (row.status !== 'ok' || !row.markdown) {
    // scan or failed: no row content, not charged
    console.log(`  ${row.url}: ${row.status}, not charged`);
    continue;
  }
  const name = row.url.replace(/\/$/, '').split('/').pop().replace(/\.pdf$/, '') || 'document';
  await writeFile(new URL(`${name}.md`, OUT), row.markdown, 'utf8');
}

for (const row of await runActor('kizukidata/url-to-markdown', PAGE_INPUT)) {
  if (!row.markdown) continue;
  await writeFile(new URL('page.md', OUT), row.markdown, 'utf8');
}

const jsonl = chunks.map((chunk) => JSON.stringify(chunk)).join('\n');
await writeFile(new URL('chunks.jsonl', OUT), jsonl ? `${jsonl}\n` : '', 'utf8');
console.log(`${chunks.length} chunks written to ${OUT.pathname}`);
