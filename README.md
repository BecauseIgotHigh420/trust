# GemHunter 💎

**Discover new startups that are already doing extremely well — ideas worth replicating.**

GemHunter pulls verified startup revenue from the
[TrustMRR API](https://trustmrr.com/docs/api) (revenue verified hourly via
Stripe / RevenueCat / etc.), keeps only **recently-founded** companies (default:
the last 6 months), ranks them by a transparent *gem score*, and generates a
standalone, filterable HTML website plus JSON/CSV exports.

![gem score = traction + velocity + growth + efficiency](https://img.shields.io/badge/gem_score-traction%20%2B%20velocity%20%2B%20growth%20%2B%20efficiency-6b46c1)

## Why

New startups that hit strong, verified revenue *fast* are the clearest signal of
a validated idea. GemHunter finds them so you can study — and replicate — what's
working right now, instead of guessing.

## How the gem score works

Each candidate is scored **0–100** from four log-scaled, min-max-normalised
signals, so no single mega-outlier dominates:

| Signal | Weight | Meaning |
|--------|-------:|---------|
| **Traction** | 35% | Current monthly revenue (MRR / last 30 days) |
| **Velocity** | 30% | Total revenue ÷ months since founding — how *fast* they got here |
| **Growth** | 20% | 30-day revenue growth |
| **Efficiency** | 15% | Revenue per visitor — do they monetise traffic well? |

Only startups founded within the window (default 6 months) and above a minimum
monthly revenue (default \$100) qualify. The per-startup breakdown is written to
`gems.json`, so every ranking is fully explainable.

## Setup

```bash
pip install -e ".[dev]"          # or: pip install -r requirements.txt

# Your TrustMRR key (starts with tmrr_). Never commit it — .env is gitignored.
export TRUSTMRR_API_KEY=tmrr_your_key_here
```

Get a key from your TrustMRR dashboard (`/dashboard-dev`).

## Usage

```bash
# Top gems from the last 6 months -> data/output/gems.{html,json,csv}
gemhunter run

# Tighter window, scan deeper, seed the scan from the fastest growers
gemhunter run --months 3 --max-pages 12 --sort growth-desc

# Focus on one category, require real revenue
gemhunter run --category ai --min-mrr 500 --top 40
```

Open `data/output/gems.html` in any browser — it's fully self-contained
(search, category filter, sort, dark/light mode; no server required).

### `gemhunter run` options

| Option | Default | Description |
|--------|---------|-------------|
| `--api-key` | `$TRUSTMRR_API_KEY` | TrustMRR API key (`tmrr_…`) |
| `--months` | `6` | Max startup age in months (lookback window) |
| `--max-pages` | `8` | Pages to scan (50/page, self-throttled to ~18 req/min) |
| `--sort` | `revenue-desc` | Server-side sort seeding the scan (`growth-desc`, `best-deal`, …) |
| `--category` | — | TrustMRR category slug (`ai`, `saas`, `fintech`, …) |
| `--min-mrr` | `100` | Minimum monthly revenue to qualify |
| `--top` | `60` | Keep the top N gems |
| `--output-dir` | `data/output` | Where to write `gems.{html,json,csv}` |

## Project layout

```
gemhunter/
├── src/gemhunter/
│   ├── client.py     # TrustMRR API client (auth, pagination, rate-limit, retries)
│   ├── models.py     # Pydantic models + derived helpers (age, MRR fallback)
│   ├── scoring.py    # 6-month filter + transparent gem score
│   ├── report.py     # CSV / JSON / standalone HTML website
│   └── cli.py        # `gemhunter run` (Click + Rich)
├── tests/            # 14 unit tests, no network required
└── data/output/      # generated gems.{html,json,csv} (sample included)
```

## Tests

```bash
pytest -q          # 14 passing, fully offline
```

## Notes

- **Rate limits:** TrustMRR allows 20 requests/min per key; GemHunter
  self-throttles (~3.2s between calls) to stay safely under.
- **Your API key is never hard-coded or logged** — it's read from
  `TRUSTMRR_API_KEY` (or `--api-key`) at runtime, and `.env` is gitignored.
- Gem scores are **heuristic discovery signals, not investment advice.**
  Verify every number at the source before acting on it.

Data: [TrustMRR](https://trustmrr.com) · Built with GemHunter.
