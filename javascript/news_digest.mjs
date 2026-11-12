// A morning digest from Google News, Telegram channels and YouTube channels.
//
// Price at the Free tier, per returned row: google-news-feed $0.00136,
// telegram-channel-feed $0.00028, youtube-channel-monitor $0.00024. No per-item
// charge when an input yields nothing; Apify's run start fee still applies.
//
// Run: npm install && node news_digest.mjs   (with APIFY_TOKEN set)
// The second run with the same input returns only what is new (state is kept
// per input for 90 days in your own key-value store).

import { ApifyClient } from 'apify-client';

if (!process.env.APIFY_TOKEN) {
  console.error('APIFY_TOKEN is not set');
  process.exit(1);
}

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

const NEWS_INPUT = {
  queries: ['electric vehicles', '"grid storage"'],
  edition: 'US:en',
  timespan: '24h',
  onlyNewItems: true,
  resolveArticleUrls: true,
  maxItems: 25,
};

const TELEGRAM_INPUT = {
  channels: ['durov'],
  maxPostsPerChannel: 20,
  onlyNewItems: true,
  maxItems: 20,
};

const YOUTUBE_INPUT = {
  channels: ['@AndrejKarpathy'],
  mode: 'videos',
  maxVideosPerChannel: 3,
  onlyNewItems: true,
  maxItems: 20,
};

const PRICE = {
  'kizukidata/google-news-feed': 0.0017,
  'kizukidata/telegram-channel-feed': 0.002,
  'kizukidata/youtube-channel-monitor': 0.0011,
};

async function runActor(actor, input) {
  const run = await client.actor(actor).call(input);
  if (!run) {
    throw new Error(`${actor}: the run did not start`);
  }
  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  const charged = items.filter((row) => !row.error);
  console.log(`${actor}: ${items.length} rows, about $${(charged.length * PRICE[actor]).toFixed(4)}`);
  return items;
}

console.log('\nGoogle News');
for (const row of await runActor('kizukidata/google-news-feed', NEWS_INPUT)) {
  console.log(`  ${(row.publishedAt ?? '').slice(0, 16)}  ${row.outlet}: ${row.title}\n    ${row.articleUrl ?? row.googleNewsUrl}`);
}

console.log('\nTelegram');
for (const row of await runActor('kizukidata/telegram-channel-feed', TELEGRAM_INPUT)) {
  if (row.error) {
    console.log(`  ${row.channel}: ${row.error?.type ?? 'error'} (not charged)`);
    continue;
  }
  const firstLine = (row.text ?? '').trim().split('\n')[0];
  console.log(`  ${(row.publishedAt ?? '').slice(0, 16)}  ${row.channel}: ${firstLine.slice(0, 120)}\n    ${row.url}`);
}

console.log('\nYouTube');
for (const row of await runActor('kizukidata/youtube-channel-monitor', YOUTUBE_INPUT)) {
  if (row.error) {
    console.log(`  ${row.channelId}: ${row.error?.type ?? 'error'} (not charged)`);
    continue;
  }
  if (row.type !== 'video') continue; // channel and comment rows share the dataset
  console.log(`  ${row.publishedAt}  ${row.title} (${row.views} views)\n    ${row.url}`);
}
