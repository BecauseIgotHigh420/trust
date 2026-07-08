# BrandRank — Claude design prompt

Paste the block below into Claude (claude.ai for a rendered artifact, or Claude
Code to generate files in this repo). It produces a high-fidelity, self-contained
design for BrandRank's core surfaces. Run it once per surface if you want deeper
iterations (landing → report → dashboard → email), or as-is for the full set.

---

```
You are designing BrandRank, a B2B SaaS that monitors how brands appear in AI
search engines (ChatGPT, Perplexity, Gemini, Google AI Overviews) and helps
them improve it. Build a complete, high-fidelity, self-contained design as a
single HTML file (inline CSS + minimal vanilla JS, no external assets, no
frameworks, no CDN). It must be responsive and support light AND dark mode via
prefers-color-scheme with a manual toggle.

## Product context (design must serve this)

- One-liner: "Know what AI says about your brand — and fix it. One flat price."
- Buyers are losing Google traffic to AI answers and have no idea whether
  ChatGPT recommends them, a competitor, or nothing. BrandRank runs their real
  buyer-intent prompts across AI engines weekly, scores their visibility 0–100,
  shows exactly which sources the engines cite, and generates a concrete Fix
  List — then proves whether completed fixes moved the score.
- ICP: marketing leads at SMB SaaS and e-commerce brands; agencies managing
  many client brands. Skeptical, dashboard-fatigued, allergic to AI hype.
- Positioning against competitors: flat per-brand pricing (rivals use confusing
  credit systems), report-first (the weekly "Monday Report" email is the hero
  artifact, not another dashboard), and receipts ("we never promise rankings —
  we measure experiments").

## Surfaces to design (all in one file, as scrollable sections or tabbed views)

1. LANDING PAGE
   - Hero: headline + subhead + the free-scan input (a single domain field +
     "Run my free scan" button). The scan input IS the primary CTA — no
     "book a demo".
   - A live-feeling product proof module directly under the hero: a mock
     report card for an example brand showing score 38, per-engine chips
     (ChatGPT ✗ absent, Perplexity ✓ #2, Gemini ✗, AI Overviews ✓ cited),
     and one fix-list item. Show, don't claim.
   - How it works (3 steps: Scan → Fix → Prove), pricing (3 flat tiers:
     Solo $29 / Growth $79 / Agency $199 — annotate what's in each, one line
     calling out "no credits, no meters"), honest FAQ, minimal footer.
2. FREE SCAN FLOW (three states)
   - Input state, running state (engine-by-engine progress with the prompts
     being tested visible — this wait is a marketing moment, make it
     fascinating not a spinner), and the RESULT: the report page.
3. REPORT PAGE (the most important surface)
   - Score hero: big 0–100 gauge with tabular numerals, per-engine breakdown
     row, share-of-voice vs 2 competitors.
   - Prompt table: each tested prompt with pass/fail per engine, expandable to
     show the ACTUAL AI answer excerpt with the brand (or competitor)
     highlighted.
   - Citations panel: "Sources AI engines cite for your prompts" — URL list
     with you-are/are-not-listed badges.
   - Fix List: checklist items with ✓/⚠ semantics, each tied to a specific
     gap ("Answer this Reddit thread", "Request listing on [URL]", "Add FAQ
     schema"), with a check-off affordance.
   - Proof module: before/after strip — "3 fixes completed → score 34 → 61,
     present in 4/5 answers" with a small trend sparkline.
   - Conversion CTA: "Track this weekly" (email + start trial), styled as the
     natural next step, not a paywall slam.
4. MONDAY REPORT EMAIL (600px email-safe table layout, in the same file as a
   framed preview): score delta, one win, one loss, top fix of the week,
   view-full-report button. This email is the retention product — design it
   like a weekly ritual, scannable in 20 seconds.

## Visual direction

- Modern B2B SaaS: generous whitespace, strong typographic hierarchy, system
  font stack or a single self-hosted-feeling sans. Data-forward: tabular
  numerals for all scores/metrics.
- One restrained accent color (deep indigo or teal family) + semantic green/
  amber for pass/warn. Neutral grays do the work. Both themes must pass WCAG
  AA contrast.
- Score gauge and sparklines drawn with inline SVG.
- Subtle motion only (150–250ms ease transitions, a gentle count-up on the
  score). No parallax, no floating blobs.
- AVOID: purple-to-pink AI gradients, glassmorphism, fake testimonials, logo
  walls of companies that don't exist, robot/brain imagery, fear-mongering
  ("your brand is INVISIBLE!"). The brand is a calm, precise instrument.

## Copy rules (write real copy, no lorem ipsum)

- Specific and falsifiable beats grand: "ChatGPT recommends your competitor
  for 6 of your 10 buyer prompts" beats "unlock AI-powered insights".
- Never promise rankings; the honest claim is measurement: "We don't promise
  #1. We prove whether what you did worked."
- Sentence-case headings, no exclamation marks, zero uses of "revolutionize",
  "supercharge", "unleash", or "game-changing".

## Output requirements

Single HTML file, semantic markup, keyboard-navigable interactive bits,
`prefers-color-scheme` + toggle, no external requests of any kind. Make every
number, prompt, and brand in the mock data plausible and internally consistent
(same example brand throughout: a fictional project-management SaaS called
"Plannery" competing with "TaskLoop" and "Boardly").
```
