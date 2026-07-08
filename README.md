# GemHunter 💎

**Find the best micro-SaaS to clone — backed by verified revenue data.**

GemHunter pulls verified startup revenue from the
[TrustMRR API](https://trustmrr.com/docs/api) (revenue verified hourly via
Stripe / RevenueCat / etc.) and ranks startups through two lenses:

1. **Clone Score v2** (`gemhunter clones`, the default web view) — *"what
   should **you** build?"* Gates out launch-week spikes, lifetime-deal pops,
   services, and audience-driven products, then scores what's left on
   **demand × distribution × simplicity**.
2. **Gem score** (`gemhunter run`, `?view=gems` on the web) — *"who's winning
   right now?"* Raw traction leaderboard for recently-founded startups.

Both produce a standalone, filterable HTML website plus JSON/CSV exports.

## Clone Score v2 — how it works

**Success ≠ clonability.** A payroll platform, a regulated fintech wallet, or a
product whose revenue is really its founder's X audience can top a revenue
leaderboard while being terrible clone targets. Clone Score separates the two
questions.

**Stage 1 — hard gates** (a candidate must pass all):

| Gate | Default | Kills |
|------|---------|-------|
| Age window | 3–18 months | launch-week noise (younger) & locked-up markets (older) |
| MRR floor | ≥ $500 | tip jars |
| Subscription purity: MRR / last-30d revenue | ≥ 35% | lifetime-deal pops, one-off services |
| Subscribers (when reported) | ≥ 10 | "two friends subscribed" |

**Stage 2 — enrichment + scoring.** The top candidates get a detail fetch
(tech stack, founder follower count, search impressions), then:

```
clone_score = 100 × demand^0.40 × distribution^0.35 × simplicity^0.25
```

Geometric, not additive — **one bad axis sinks the score**; monster MRR can't
carry unreachable distribution.

| Component | Signals |
|-----------|---------|
| **Demand** (0.40) | MRR level, paying-subscriber count, recurring share, MRR growth |
| **Distribution** (0.35) | audience independence (X followers per MRR dollar — *penalty*), Google search impressions (*replicable demand — bonus*), revenue per visitor |
| **Simplicity** (0.25) | commodity vs heavy tech stack, ARPU in the $10–120/mo sweet spot, single-job scope vs "all-in-one platform" sprawl, B2B fit |

Every card shows the three component bars plus ✓/⚠ clone-brief flags
(e.g. *"⚠ Audience-driven: 80k followers vs $2k MRR — their distribution won't
transfer to you"*). Unknown signals fall back to explicit neutral priors, and
un-enriched candidates are marked *preliminary*.

```bash
gemhunter clones                        # scan, gate, enrich top 40, export
gemhunter clones --enrich 40 --top 30   # deep analysis (~3s per enriched startup)
gemhunter clones --min-age 3 --max-age 12 --min-mrr 1000 --category saas
```

## How the gem score works (v1 leaderboard)

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
