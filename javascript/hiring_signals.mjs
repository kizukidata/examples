// New LinkedIn jobs and changed company pages in one pass, written to jobs.csv.
//
// Price at the Free tier, per returned row: linkedin-jobs-feed $0.0012,
// linkedin-company-monitor $0.0020. No per-item charge when an input yields
// nothing; Apify's run start fee still applies.
//
// Run: npm install && node hiring_signals.mjs   (with APIFY_TOKEN set)

import { mkdir, writeFile } from 'node:fs/promises';
import { ApifyClient } from 'apify-client';

if (!process.env.APIFY_TOKEN) {
  console.error('APIFY_TOKEN is not set');
  process.exit(1);
}

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

const JOBS_INPUT = {
  keywords: 'data engineer',
  location: 'Berlin, Germany',
  daysSincePosted: 7,
  onlyNewItems: true, // only what an earlier run with the same search did not return
  includeDetails: true,
  maxItems: 20,
};

const COMPANY_INPUT = {
  companies: ['apify', 'google'],
  onlyChanges: true, // only companies whose fields differ from the previous run
  maxItems: 5,
};

const PRICE = {
  'kizukidata/linkedin-jobs-feed': 0.0012,
  'kizukidata/linkedin-company-monitor': 0.002,
};

async function runActor(actor, input, charged) {
  const run = await client.actor(actor).call(input);
  if (!run) {
    throw new Error(`${actor}: the run did not start`);
  }
  const { items } = await client.dataset(run.defaultDatasetId).listItems();
  const billable = items.filter(charged);
  console.log(`${actor}: ${items.length} rows, ${billable.length} charged, about $${(billable.length * PRICE[actor]).toFixed(4)}`);
  return items;
}

function pay(row) {
  if (row.compensationSummary) return row.compensationSummary;
  if (row.salaryMin == null && row.salaryMax == null) return '';
  const span = row.salaryMin != null && row.salaryMax != null ? `${row.salaryMin}-${row.salaryMax}` : String(row.salaryMin ?? row.salaryMax);
  return [row.salaryCurrency, span, row.salaryPeriod].filter(Boolean).join(' ');
}

function csvCell(value) {
  const text = String(value ?? '');
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const jobs = await runActor('kizukidata/linkedin-jobs-feed', JOBS_INPUT, (row) => row.detailsStatus !== 'blocked');
const columns = ['postedAt', 'title', 'companyName', 'location', 'employmentType', 'seniority', 'pay', 'url'];
const lines = [columns.join(',')];
for (const row of jobs) {
  lines.push(
    [
      row.postedAt,
      row.title,
      row.companyName,
      row.location,
      row.employmentType,
      row.seniority,
      pay(row),
      row.url,
    ]
      .map(csvCell)
      .join(','),
  );
}
const out = new URL('./out/', import.meta.url);
await mkdir(out, { recursive: true });
await writeFile(new URL('jobs.csv', out), `${lines.join('\n')}\n`, 'utf8');
console.log(`${jobs.length} jobs written to out/jobs.csv`);

const companies = await runActor('kizukidata/linkedin-company-monitor', COMPANY_INPUT, (row) => row.status === 'ok');
for (const row of companies) {
  if (row.status !== 'ok') {
    console.log(`  ${row.slug}: ${row.errorCode} (not charged)`);
    continue;
  }
  const changes = row.changes ?? {};
  if (changes.baseline) {
    console.log(`  ${row.name}: first run, the current values are the baseline`);
    continue;
  }
  const diffs = changes.diffs ?? [];
  console.log(`  ${row.name}: ${diffs.length} fields changed`);
  for (const diff of diffs) {
    console.log(`    ${diff.field}: ${diff.from} -> ${diff.to}`);
  }
}
