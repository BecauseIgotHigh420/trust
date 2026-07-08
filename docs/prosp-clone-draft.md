# PROSP clone — draft (A → Z)

*Working blueprint for cloning Prosp (prosp.ai). Working name: **OutReach** placeholder — naming TBD.*
*Drafted 2026-07-08. All Prosp revenue figures are TrustMRR-verified (Stripe).*
*Companion to `brandrank-draft.md` — read the differences section (§3) first: this target has a fundamentally different risk profile.*

---

## 1. Why this target (the verified numbers)

Prosp ranked #5 in our Clone Score run (75.7: demand **0.93** / distribution 0.55 / simplicity 0.86):

| Signal | Value | Read |
|---|---|---|
| MRR | **$128,005** | The biggest verified business in our whole scan |
| Paying subscribers | **1,108** | Massive validated demand |
| ARPU | **$115/mo** | Agencies stacking multiple LinkedIn accounts |
| Recurring share | **100%** | Pure subscription |
| Age | 10.5 months | $0 → $128k MRR in under a year |
| Founder X followers | 3,245 | Product-driven, not audience-driven |
| Country | France (founder: @yanndine) | Solo-ish EU builder |
| **On sale** | **asking $1,000,000** | ⚠ See below — this is the tell |

**The $1M asking price is the most informative data point.** $128k MRR ≈ $1.54M ARR, so the ask is **~0.65× ARR** — healthy SaaS trades at 3–5× ARR. When a founder prices a $128k/mo machine at 8 months of revenue, he is telling you what he thinks of its durability. The discount is the market pricing in the risks in §3. Read that section before falling in love with the demand numbers.

## 2. What the product actually is

**Category**: LinkedIn outreach automation for agencies and sales teams. Prosp automates connection requests, AI-personalized DMs, follow-up sequences, and — its signature feature — **AI voice notes cloned in the sender's own voice**, sent per-prospect. Voice notes get dramatically higher reply rates because nobody believes a voice note is automated (that's exactly the point, and exactly the ethical tension).

**Feature map**:
1. **Cloud automation** — campaigns run server-side 24/7; user connects their LinkedIn via login or Chrome extension; each account gets a **dedicated residential proxy**; activity is paced to mimic human behavior and stay under LinkedIn's limits.
2. **AI personalization** — messages generated from the prospect's profile + recent activity.
3. **AI voice notes** — cloned voice, generated per prospect. The moat-ish feature.
4. **Multi-account + unified inbox** — agencies run 10+ client accounts from one dashboard, with account rotation to spread volume.
5. **Lead finder / enrichment** + Chrome extension for sourcing.

**Pricing**: Basic $29 (1 account), Professional $59, Enterprise $79 (multi-account; ~$59 per additional account), 33% annual discount, free trial, 30-day guarantee. The $115 ARPU vs $29 entry confirms: **revenue is agencies with many seats/accounts**, exactly like Rank Prompt's pattern.

**Competitive field** (crowded, mature): HeyReach ($79–199, flat multi-account — $179/5 accounts, the agency favorite), Expandi ($99/account, dedicated-IP safety leader), Dripify ($59–99), La Growth Machine ($80–240, LinkedIn+email), Waalaxy ($33–80, browser-extension tier), Linked Helper, Dux-Soup. Prosp grew to $128k MRR *inside* this crowd in 10 months — mostly on the voice-note wedge.

## 3. ⚠ How this differs from the BrandRank target — read this first

Cloning Rank Prompt is a clean business. Cloning Prosp is not, and I'd be doing you a disservice to write this draft as if they were the same:

1. **The core product violates LinkedIn's Terms of Service.** LinkedIn explicitly prohibits automation of member accounts. The entire category operates by logging into customer accounts server-side, masking that automation behind residential proxies and human-like pacing. This is not a side effect — **evading LinkedIn's detection IS the product**.
2. **Platform crackdown is active.** LinkedIn tightened enforcement in January 2026: ~100 connection requests/week caps and materially better detection. Every tool in the category took churn. Your customers' LinkedIn accounts — often their livelihood — can get restricted or banned using your product. Some Waalaxy users report suspensions even on default settings.
3. **Legal exposure is real, not theoretical**: ToS breach at scale, CFAA-adjacent questions (hiQ v. LinkedIn didn't bless account automation), and GDPR on scraped/enriched prospect data — especially operating from/selling into the EU.
4. **This is why a $1.5M-ARR business is asking $1M.** The founder is selling you the platform risk.
5. **Technical bar is much higher than the Clone Score suggested.** Our simplicity score (0.86) leaned on a neutral prior — Prosp publishes no tech stack. In reality: browser-automation fleets, anti-detect fingerprinting, proxy management, session security (you hold customers' LinkedIn credentials — a breach is existential), inbox sync, voice cloning. This is 6–12 months of hard infrastructure, not a Next.js weekend.

**I'll draft all three strategic options, but I recommend Option B.**

## 4. The strategic fork

### Option A — Full clone (fight in the gray zone)
Build what Prosp is: cloud automation + proxies + voice notes. It's a proven $128k/mo formula and the market keeps paying despite the risks.
- Requires: anti-detect browser infra (incumbents build on stacks like Multilogin-class tooling), residential proxy contracts ($3–8/account/mo), security posture for holding customer sessions, and an appetite for the platform/legal risk above.
- Realistic only if you accept that LinkedIn can vaporize the business (or your payment processing — Stripe has terminated accounts in this category) at any moment, and price/structure accordingly (LLC separation, aggressive profit-taking, no long-term contracts).
- **I can't in good conscience make this the recommendation**, and I won't spec the detection-evasion internals — but the market reality is that dozens of funded companies do exactly this.

### Option B — The "assist, don't automate" wedge ✅ recommended
Keep Prosp's two genuinely valuable innovations — **AI personalization + cloned voice notes** — but flip the architecture from *automation* to *human-in-the-loop assistance*:
- A Chrome extension / desktop companion where **the human stays in the driver's seat**: it drafts the personalized message and generates the voice note; the *user* clicks send inside LinkedIn's own UI. No server-side account access, no proxies, no credential custody, radically lower ToS surface (comparable to Grammarly-in-LinkedIn, not bot farms).
- Add the parts of the workflow that are unambiguously legal and sticky: unified pipeline/CRM for conversations, reply detection, follow-up reminders, team analytics, message A/B stats, lead enrichment via licensed data APIs.
- Positioning: **"Reply rates of automation, without risking your LinkedIn account."** Every January-2026-crackdown horror story is your marketing. Expandi/HeyReach refugees are the ICP.
- Trade-off, stated plainly: you lose "wake up to 50 sent messages" magic — throughput becomes the user's time. The bet is that post-crackdown, *safety + quality* beats *volume*. The voice-note quality wedge matters more when you send 20 great messages instead of 200 spammy ones.

### Option C — Buy Prosp instead of cloning it
At $1M asking (likely negotiable) you'd acquire 1,108 customers, working infra, and the brand — at 0.65× ARR.
- Only sane with hard due diligence: monthly churn cohorts (the number that explains the price), ban-rate metrics, proxy/infra costs, Stripe account health, what Jan 2026 did to net revenue retention.
- You inherit Option A's risk profile wholesale, plus key-man risk on undocumented infra. If churn is >8%/mo, the real price isn't cheap at all.
- Worth a conversation if you have $1M and gray-zone appetite; otherwise skip. (TrustMRR listing is the contact path.)

## 5. Blueprint for Option B (the recommended clone)

### Product v1 (12 weeks)
1. **Chrome extension** (Plasmo framework) overlaying LinkedIn: on any profile/DM thread, one click → AI-drafted personalized message (profile + recent posts as context) → user edits → user sends. 
2. **Voice notes**: user records 60s once; ElevenLabs-class API clones the voice; per-prospect voice note generated from the approved text; user attaches via LinkedIn's own voice-message UI (extension guides, human clicks).
3. **Command center web app**: pipeline board of conversations (synced from what the extension sees as the user browses — no background scraping), follow-up queue ("6 people to nudge today"), templates, team stats.
4. **Enrichment**: licensed B2B data APIs for firmographics (the same vendors sales tools license — you already have Lusha wired into this workspace, which is exactly this kind of source) — not scraped data.

**Explicitly NOT built**: server-side sending, session/credential storage, proxies, account rotation, auto-connect campaigns. That's not this product — that's the liability we're arbitraging away.

### Tech & COGS
- Stack: Next.js + Supabase + Stripe (same boring core as BrandRank), Plasmo for the extension, ElevenLabs API for voice (~$0.10–0.30/min generated; a heavy user sending 300 voice notes/mo ≈ $10–15 COGS), Haiku-class LLM for drafting (~$1–3/user/mo). 
- **COGS ~10–15% at $49/user** — better margins than Prosp, who pays for a residential proxy per account.
- No fleet infra, no anti-detect arms race → one person can actually run this.

### Pricing
| Tier | Price | For |
|---|---|---|
| Solo | $39/mo | 1 user, 100 AI drafts + 50 voice notes/mo |
| Pro | $79/mo | Unlimited drafts, 300 voice notes, pipeline + analytics |
| Team | $59/user/mo (min 3) | Shared templates, manager analytics, agency workspaces |

Undercuts Expandi ($99/account) while being the only one that can honestly say "your account is never at risk from us."

### Distribution (the 0.55 axis — Prosp's weakest, and the category's)
1. **Safety-fear content**: "Is Expandi safe in 2026?", "LinkedIn banned my account — what now?", "HeyReach alternatives that won't get you restricted". Post-crackdown search volume on these is the entry wound. (Same comparison-page playbook as BrandRank.)
2. **The voice-note demo is inherently viral** — "this AI voice note got a 43% reply rate" posts with audio embeds; free tool: *clone your voice, get 3 free voice notes* → the BrandRank free-scan pattern.
3. **Agency channel**: 20 design-partner agencies (they feel ban-risk most — client accounts), white-label reports later.
4. LinkedIn itself is the distribution platform: founders posting *manually* about selling *manually-but-assisted* is on-brand and free.

### 12-week plan
- **Wk 1–3**: extension MVP — profile context → drafted DM, manual send. Web app skeleton + Stripe.
- **Wk 4–5**: voice cloning + voice-note flow end-to-end. *Milestone: first "holy shit" demo video.*
- **Wk 6–7**: pipeline board, follow-up queue, reply detection. 10 design partners.
- **Wk 8–9**: team features, template library, analytics. First paid conversions.
- **Wk 10–12**: comparison/safety content sprint (10 pages), free voice-note tool, Product Hunt. *Milestone: 25 paying.*

### Success gates
- Month 3: 25 paying, $1.5k MRR, extension DAU/paying >60% (it must live in their daily workflow or it churns).
- Month 6: $8k MRR, reply-rate case studies published, 2 agency teams.
- Month 12: $25k+ MRR — or the market has told you post-crackdown buyers still want gray-zone volume, in which case revisit the fork with real data.

## 6. Risks (ranked)

1. **LinkedIn breaks even assist-mode** — extensions that touch their DOM are also ToS-gray (lower risk than automation, not zero; Grammarly-class tools survive, scrapers don't). *Mitigation: no background actions ever; user-initiated only; be ready to ship a desktop-app variant.*
2. **The market wants volume, not quality** — post-crackdown, maybe buyers just migrate to the next bot. *Mitigation: the design-partner phase answers this before you've spent 12 weeks.*
3. **Voice-note deception backlash** — an AI voice note pretending to be personally recorded is borderline. *Mitigation: it IS the user's real cloned voice reading their approved text; add optional disclosure setting; never fake scarcity/human typos.*
4. **Incumbent response** — HeyReach/Expandi can bolt on voice notes. *Mitigation: they can't easily abandon their automation architecture (their revenue is the risk you don't have); your positioning is the moat, not the feature.*
5. **ElevenLabs dependency/pricing** — single-vendor voice. *Mitigation: abstraction layer; 2–3 voice API vendors exist.*

## 7. Bottom line vs BrandRank

| | BrandRank (Rank Prompt) | This (Prosp) |
|---|---|---|
| Verified MRR of target | $34k | $128k |
| Market risk | Category crowding | **Platform can kill the category** |
| Legal/ToS | Clean | Gray (full clone) / manageable (assist wedge) |
| Tech difficulty | Low (pipeline + dashboards) | Medium (extension + voice) / High (full clone) |
| Recommendation | **Clone as spec'd** | **Clone the wedge (Option B), not the automation** |

If you only build one: **BrandRank first**. Cleaner risk, faster to revenue, same distribution muscles. Build the Prosp wedge second — or use Option C's due-diligence questions to lowball the $1M listing if you want the shortcut and accept its risks.

---

*Sources: TrustMRR verified data (prosp), prosp.ai product/pricing, category landscape & Jan-2026 crackdown reporting via HeyReach, Expandi, Waalaxy, La Growth Machine comparison coverage (SyncGTM, LinkedRent, Modern Inbound, 2026). Scores from GemHunter Clone Score v2.*
