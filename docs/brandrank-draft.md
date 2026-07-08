# BrandRank — clone draft (A → Z)

*Working blueprint for cloning Rank Prompt (rankprompt.com) as **BrandRank**.*
*Drafted 2026-07-08. All Rank Prompt revenue figures are TrustMRR-verified (Stripe).*

---

## 1. Why this target (the verified numbers)

Rank Prompt is the strongest clone target in our Clone Score run (74.9: demand 0.86 / distribution 0.63 / simplicity 0.76) because every axis checks out:

| Signal | Value | Read |
|---|---|---|
| MRR | **$33,964** | Real business, not a side project |
| Paying subscribers | **225** | Deep demand, not 3 whales |
| ARPU | **$151/mo** | B2B money without enterprise sales |
| Recurring share | **96%** | True SaaS |
| MRR growth | **+13.2%/mo** | Still compounding at 14 months old |
| Age | 13.8 months (founded May 2025) | Market young enough for a #2 |
| Founder X followers | **28** | Zero audience-dependence — customers come from the product's channels, not the founder's fame |
| Traffic | 10,363 visitors/mo, **$3.44 revenue/visitor** | Small, high-intent traffic |
| Marketing channels | blog, content marketing, newsletter — **100% organic** | The distribution playbook is replicable |
| Team | No cofounders listed | A solo founder built this: so can you |

**The meta-lesson**: ~$34k MRR from ~10k visitors/mo means this market converts on *intent*, not volume. Whoever ranks for the right queries gets paid.

## 2. What the product actually is

**Category**: AI search visibility / AEO / GEO ("SEO for ChatGPT"). Brands are losing Google traffic to AI answers and have no idea whether ChatGPT recommends them, their competitor, or hallucinated nonsense. These tools answer: *"When people ask AI about my category, do I show up — and how do I fix it if not?"*

**Rank Prompt's feature map** (what 14 months of iteration converged on):
1. **Visibility monitoring** — run a set of buyer-intent prompts against ChatGPT, Perplexity, Google AI Mode/Overviews, Gemini, Claude, Grok; detect brand mentions; compute a visibility score; trend it over time.
2. **Competitor tracking** — same prompts, competitor mentions, share-of-voice.
3. **Citation tracking** — which URLs/sources the engines cite; those are the pages to influence.
4. **Content studio** — generate articles engineered to get cited by AI.
5. **Technical audits** — schema, Core Web Vitals, llms.txt-era checks.
6. **Extras**: citation outreach campaigns, "agent mode" chat, scheduled reports, white-label for agencies, WordPress/GA4/GSC integrations, developer API.

**Pricing** (annual): Starter $39/mo (150 credits), Pro $71 (500), Agency $119 (1,000), Agency Plus $239 (2,000), Enterprise custom, plus credit top-ups. 7-day trial.

The $151 ARPU vs a $39 entry tier tells you the money is in **Pro/Agency** — agencies managing many brands are the profitable segment.

## 3. Honest market check (read before building)

This is a **hot, crowding** category — that cuts both ways:

- **Enterprise is taken**: Profound raised **$155M at a $1B valuation** (Feb 2026), charges $499+/mo. Don't fight them.
- **The low end is contested**: Otterly ($29/mo), Frase ($39), Geoptie ($49), MaxAEO, SE Ranking's AI tracker, Omnia, and a dozen others.
- **Yet Rank Prompt grew +13%/mo *inside* that field** — with 28 followers and no funding. The demand wave (every marketing team suddenly needs an "AI visibility" line item) is still bigger than the supply of good tools. There is room for well-distributed clones for roughly another 12–24 months, after which this consolidates.
- **Naming risk — important**: **BrandRank.AI already exists** (Pete Blackshaw's AI trust/answer-engine audit firm) and operates in an adjacent space. Shipping "BrandRank" in the same category invites confusion and a possible trademark fight. Options: (a) pick a variant early — BrandRank**ed**, RankBrand, BrandRadar, AnswerRank; (b) get real trademark advice before buying domains. Budget a rename now, not after launch. *(Everything below still says BrandRank for readability.)*

**Verdict**: still worth cloning IF you win on a sharper wedge + distribution, not feature parity.

## 4. The BrandRank wedge (how we differ, not just copy)

Three deliberate choices against Rank Prompt's weaknesses:

1. **Flat, simple pricing — no credits.** Rank Prompt's credit system (prompts + articles + audits + "agent budget" all metered) is confusing. BrandRank: **per-brand flat plans with a fixed prompt allowance, unlimited viewing, no expiring anything.** "One price. Track your brand everywhere AI answers." Pricing simplicity is a marketable feature in a category full of credit math.
2. **The Monday Report is the product.** Most customers don't want a dashboard; they want to *know when something changes* and prove value to a boss/client. Obsess over one artifact: a beautiful weekly email/PDF — visibility score, deltas, "you lost the #1 spot for X to Competitor Y", "ChatGPT is citing this Reddit thread — go answer it". Retention lives here.
3. **Do monitoring excellently; skip the kitchen sink at launch.** No content studio, no outreach campaigns, no agent mode in v1. Those exist to inflate credits. Ship the monitor + report + fix-list, integrate deeply later. (Agency white-label comes in v1.5 — it's where ARPU is — but not day one.)

**Positioning line**: *"Know what AI says about your brand — and fix it. One flat price."*

## 5. How the core tech works (the part that looks scary but isn't)

The engine is a scheduled pipeline, ~4 steps:

```
prompts × engines → collect answers → extract mentions → score & store → report/alerts
```

1. **Prompt sets.** Onboarding wizard: user enters domain → we crawl homepage → LLM proposes 25–100 buyer-intent prompts ("best expense tool for freelancers", "X vs Y", "is <brand> legit"). User edits/approves. *This onboarding magic is half the perceived value.*
2. **Answer collection** per engine:
   - **ChatGPT**: OpenAI Responses API with `web_search` tool.
   - **Perplexity**: official Sonar API (cheap, returns citations natively — best-in-class for this).
   - **Gemini**: Gemini API with Google Search grounding.
   - **Claude**: Messages API with web search tool.
   - **Google AI Overviews**: no official API — use a SERP provider (SerpAPI/DataForSEO, ~$1–3/1k queries).
   - **Grok**: xAI API. *(v1: ship ChatGPT + Perplexity + Gemini + AI Overviews. Add Claude/Grok later — 4 engines cover ~90% of what buyers ask for.)*
3. **Mention extraction.** Feed each answer to a cheap model (Haiku-class) with a strict JSON schema: `{brand_mentioned, position (1st/2nd/listed/absent), sentiment, competitors_mentioned[], cited_urls[]}`. Brand-alias table (e.g. "HubSpot" / "hubspot.com") to avoid misses. This classifier is the only "hard" NLP and it's a solved problem.
4. **Scoring.** Visibility score per engine = weighted mention rate (presence 60% + position 25% + sentiment 15%) across the prompt set; overall = engine average. Store every run → trends, share-of-voice vs competitors, citation frequency table. Keep the formula *explainable* — customers will screenshot it into client decks.

**COGS reality check** (why tier design matters): a prompt-engine check costs roughly $0.005 (Perplexity/SERP) to $0.03 (OpenAI/Claude with search). 
- Starter: 25 prompts × 4 engines × weekly ≈ 430 checks/mo ≈ **$4–8 COGS** on $29–39 → fine.
- Naive daily on 100 prompts × 6 engines = 18k checks ≈ **$200–500/mo** → margin death.
- Rule: **weekly runs on Starter, daily only on the top tier, and daily = your 2 cheapest engines + weekly for the rest.** Sampling cadence IS the unit-economics lever in this business.

## 6. Stack & architecture (boring on purpose)

Rank Prompt's own listed profile proves commodity infra suffices. BrandRank:

- **App**: Next.js + TypeScript on Vercel; Tailwind + shadcn/ui.
- **DB/Auth**: Supabase (Postgres + RLS + auth). 
- **Jobs**: the collection pipeline needs real workers with retries/rate-limits — Inngest or Trigger.dev (both fit Vercel-land); queue per engine, exponential backoff, idempotent runs.
- **Billing**: Stripe (or Paddle if you want merchant-of-record for EU VAT — Rank Prompt is *not* MoR; mildly easier for you to sell globally if you are).
- **Email**: Resend + React Email for The Monday Report.
- **LLM calls**: one thin provider-agnostic client; log every raw answer (they're your audit trail *and* future training/marketing data — "we analyzed 1M AI answers" posts).

**Data model (core tables)**: `orgs, brands (domain, aliases[]), competitors, prompts (brand_id, text, intent_tag), runs (prompt_id, engine, raw_answer, collected_at), extractions (run_id, mentioned, position, sentiment, citations[]), scores (brand_id, engine, period, value), reports, alerts`.

**Total infra bill before LLM COGS: <$100/mo.** One person can operate this.

## 7. Pricing (v1)

| Tier | Price (mo/annual) | Brands | Prompts | Cadence | Engines |
|---|---|---|---|---|---|
| Free scan | $0 | 1 (one-shot) | 10 | once | 2 | 
| Solo | $29 / $24 | 1 | 50 | weekly | 4 |
| Growth | $79 / $66 | 3 | 150/brand | 2×/week | 4 + AI Overviews |
| Agency | $199 / $166 | 15 | 150/brand | daily (top engines) | all + white-label reports |

- Undercuts Rank Prompt at entry, matches at agency, zero credit math anywhere.
- **The free scan is the growth engine, not a plan** (see §8).
- Trial: no card, 7 days of Solo. Annual = 2 months free.
- Target blended ARPU ~$85–120 with agencies pulling it up; COGS ≤15%.

## 8. Distribution plan (the axis that decides everything)

Rank Prompt's own channels — blog, content, newsletter, all organic — are the proven playbook. Copy it and add the wedge they underuse:

1. **Free scan as programmatic front door.** `brandrank.com/scan` → enter domain, get a real 10-prompt visibility snapshot + emailed report. It's the irresistible demo AND the lead capture. Then programmatic pages: "AI visibility for **Shopify stores**", "…for **law firms**", "Is your brand in **ChatGPT**?" etc. Every one of these queries is exploding and weakly contested.
2. **Comparison/alternative pages** week one: "Rank Prompt alternative", "Otterly vs BrandRank", "Profound pricing (and what to use under $500/mo)". Bottom-funnel, high intent, exactly how challengers eat incumbents' traffic.
3. **The public data flywheel.** Monthly "**AI Visibility Index**": which brands dominate AI answers in CRM/fintech/DTC. Screenshot-bait for LinkedIn/X, links from journalists, and — recursively — gets BrandRank itself cited by AI engines. (Being the cited source in your own category is the ultimate proof.)
4. **Newsletter** ("What AI said this week") fed by the same pipeline — zero marginal content cost.
5. **Marketplace listings**: Shopify/WordPress plugin ("AI visibility widget"), agency directories, AppSumo *only if* desperate for velocity (it poisons MRR purity — we literally gate on that).
6. Launch checklist: Product Hunt, HN Show, r/SEO + r/bigseo, indie communities, 20 hand-picked agencies offered 3 months free for feedback + testimonials.

**KPI targets**: free scans → trial 15%, trial → paid 25%, month-3 logo churn <5% (the Monday Report is the churn weapon). 100 paying × $85 ≈ $8.5k MRR by month 6 = realistic good outcome; Rank Prompt's curve says the ceiling is much higher.

## 9. Build plan — 12 weeks, A → Z

**Weeks 1–2 — skeleton.** Auth, orgs/brands/prompts models, Stripe plans, onboarding wizard (domain → generated prompt set). One engine (Perplexity — cheapest, citation-native) end-to-end: collect → extract → score → chart. *Milestone: your own brand tracked, real score on screen.*

**Weeks 3–4 — the monitor.** Add ChatGPT + Gemini + AI Overviews. Scheduler + retries. Score trends, per-prompt drill-down (show the actual AI answers — customers love reading them), competitor share-of-voice. *Milestone: 5 design-partner brands tracked free.*

**Weeks 5–6 — the report + free scan.** Monday Report email/PDF (delta-focused), alerts ("you disappeared from Perplexity for prompt X"), public free-scan page. Soft launch to communities. *Milestone: first stranger pays.*

**Weeks 7–8 — money features.** Citation tracking table ("who does ChatGPT cite in your niche — get on those pages"), fix-list recommendations (rule-based + LLM: schema gaps, missing comparison page, unanswered Reddit threads), annual billing, onboarding polish. 

**Weeks 9–10 — distribution sprint.** 10 programmatic landing pages, 3 comparison pages, first AI Visibility Index post, Product Hunt launch. Instrument funnel.

**Weeks 11–12 — agency tier.** Multi-brand workspace, white-label PDF, client-facing scheduled reports. Raise prices for new signups if conversion >30%. *Milestone: first $199 agency customer — the segment that decides whether this becomes $30k MRR.*

**Explicitly NOT in v1**: content studio, outreach automation, agent chat, developer API, WordPress plugin, Grok/Claude engines, SOC2. Every one is a v2 candidate *pulled by customer demand*, not pushed.

## 10. Risks (ranked)

1. **Category compression** — dozens of clones + Semrush/Ahrefs bolting this on. *Mitigation: speed + wedge + own a niche vertical if traction stalls; 12–24mo window.*
2. **Naming/trademark collision with BrandRank.AI** — real. Decide the name in week 0 (see §3).
3. **Engine access shifts** — no official AI Overviews API; providers change search-tool pricing/ToS. *Mitigation: 4+ engines so no single dependency; SERP vendors abstract the scraping risk; never scrape consumer UIs yourself.*
4. **COGS creep** — one misconfigured daily cadence nukes margin. *Mitigation: per-tier budget caps enforced in the worker, cost dashboards from day one.*
5. **Churn after the "aha"** — customer fixes visibility, wonders why keep paying. *Mitigation: competitor tracking + alerts make it a monitoring habit, not an audit; agencies churn least — chase them.*
6. **Clone ethics/legal** — features and market positioning are fair game; **do not** copy their code, UI design, copy, or name. Build from this spec, not from screenshots.

## 11. Budget to first revenue

- Infra + tools: <$100/mo. LLM/SERP COGS at 20 design partners: ~$100–200/mo.
- Domain + trademark screen: ~$500 one-off (don't skip the screen — see risk #2).
- Paid ads: $0. This category is won organically (Rank Prompt proved it: 28 followers, $34k MRR).
- **Total: under $1k/mo burn until revenue.** Time is the real cost: ~12 focused weeks.

## 12. Definition of done for "the clone worked"

- Month 3: 25 paying, $1.5k MRR, churn <7%, one agency logo.
- Month 6: $8–10k MRR, free-scan → paid funnel converting ≥3%, AI Visibility Index cited by ≥1 external publication.
- Month 12: $25k+ MRR → you've replicated 75% of Rank Prompt's outcome in half the time, or you've learned exactly which assumption broke — with <$12k total spent.

---

*Sources: TrustMRR verified data (rank-prompt), rankprompt.com product & pricing pages, category landscape via Otterly, Frase, Geoptie, Profound public pricing (Feb–Jul 2026 reporting). Scores from GemHunter Clone Score v2.*
