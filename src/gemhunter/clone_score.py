"""Clone Score v2 — rank startups by how attractive they are to *replicate*.

The gem score answers "who is winning?". The Clone Score answers "what should
*you* build?" — a very different filter. It is a weighted geometric mean of
three 0..1 components, so a startup that badly fails one axis cannot be carried
by the others:

  clone_score = 100 x demand^0.40 x distribution^0.35 x simplicity^0.25

* demand       — validated *recurring* demand: MRR level, subscriber count,
                 subscription purity (recurring share of revenue), MRR growth.
* distribution — can a cloner reach the same customers? Organic/search-driven
                 demand is replicable; a founder's X audience is not.
* simplicity   — can a small team rebuild it quickly? Tech stack complexity,
                 ARPU in the micro-SaaS sweet spot, single-job scope vs
                 "all-in-one platform" sprawl.

Hard gates run first (age window, MRR floor, subscription purity, minimum
subscribers) so launch-week spikes, lifetime-deal pops, services, and
not-yet-validated products never reach scoring at all.

Signals use fixed saturation constants (log-scaled) rather than pool-relative
min-max, so scores are stable and comparable across runs. Unknown values fall
back to explicit neutral priors — never silently to "best" or "worst".
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable, Optional

from .models import CloneResult, Startup

WEIGHTS = {"demand": 0.40, "distribution": 0.35, "simplicity": 0.25}

# ---- Gates (defaults) ------------------------------------------------------
MIN_AGE_MONTHS = 3.0     # younger = launch noise, can't tell hype from demand
MAX_AGE_MONTHS = 18.0    # older = market may already be crowded/locked
MIN_MRR = 500.0          # real recurring revenue, not a tip jar
MIN_PURITY = 0.35        # recurring share of last-30d revenue (kills lifetime-deal pops)
MIN_SUBSCRIBERS = 10     # only enforced when the field is actually reported (>0)

# ---- Saturation constants: value at which a signal earns full marks --------
SAT_MRR = 50_000.0            # $50k MRR = fully validated for a micro-SaaS
SAT_SUBS = 500.0              # 500 paying subscribers = unambiguous market
SAT_IMPRESSIONS = 100_000.0   # 100k Google impressions/mo = strong organic pull
SAT_RPV = 50.0                # $50 revenue per visitor = excellent monetisation

# Neutral priors for unknown (un-enriched / unreported) signals.
NEUTRAL_SUBS = 0.35
NEUTRAL_AUDIENCE = 0.60
NEUTRAL_SEO = 0.30
NEUTRAL_ARPU = 0.60
NEUTRAL_STACK = 0.60

# ARPU sweet spot for cloneable micro-SaaS ($/month per paying customer).
ARPU_SWEET = (10.0, 120.0)    # low-touch, self-serve, still meaningful revenue
ARPU_OKAY = (5.0, 250.0)      # workable but harder (volume game / sales-touch)

# Tech-stack markers. Simple = commodity web stack a small team ships in weeks.
COMPLEX_TECH = {
    "kubernetes", "kafka", "pytorch", "tensorflow", "cuda", "solidity",
    "blockchain", "unity", "unreal-engine", "embedded", "rust", "c++",
    "elasticsearch", "spark", "hadoop",
}

# Scope-sprawl markers: products trying to be everything are years of build.
SCOPE_KEYWORDS = (
    "all-in-one", "all in one", "platform", "suite", "marketplace",
    "operating system", "erp", "everything you need", "one place",
)


def _sat(value: Optional[float], full_at: float) -> float:
    """Log-scaled saturation: 0 at 0, 1.0 at ``full_at`` and beyond."""
    v = max(float(value or 0.0), 0.0)
    return min(math.log1p(v) / math.log1p(full_at), 1.0)


# ---------------------------------------------------------------------------
# Stage 1: hard gates
# ---------------------------------------------------------------------------

def passes_gates(
    s: Startup,
    *,
    min_age: float = MIN_AGE_MONTHS,
    max_age: float = MAX_AGE_MONTHS,
    min_mrr: float = MIN_MRR,
    min_purity: float = MIN_PURITY,
    min_subs: int = MIN_SUBSCRIBERS,
    now: Optional[datetime] = None,
) -> bool:
    """True if the startup is even a candidate for cloning."""
    age = s.months_since_founded(now)
    if age is None or not (min_age <= age <= max_age):
        return False
    mrr = s.revenue.mrr or 0.0
    if mrr < min_mrr:
        return False
    if _purity(s) < min_purity:
        return False
    subs = s.activeSubscriptions or 0
    # Only enforce when reported: many listings simply omit subscriber counts.
    if 0 < subs < min_subs:
        return False
    return True


def _purity(s: Startup) -> float:
    """Recurring share of revenue: MRR / last-30-days revenue, clamped 0..1.

    Kills lifetime-deal launch pops (high last30Days, near-zero MRR) and
    service businesses invoicing one-offs. MRR can legitimately exceed
    last30Days (annual-plan accounting), hence the max() denominator.
    """
    mrr = s.revenue.mrr or 0.0
    last30 = s.revenue.last30Days or 0.0
    denom = max(last30, mrr)
    return (mrr / denom) if denom > 0 else 0.0


# ---------------------------------------------------------------------------
# Stage 2: component scores
# ---------------------------------------------------------------------------

def _demand(s: Startup) -> tuple[float, dict]:
    mrr_score = _sat(s.revenue.mrr, SAT_MRR)
    subs = s.activeSubscriptions or 0
    subs_score = _sat(subs, SAT_SUBS) if subs > 0 else NEUTRAL_SUBS
    purity = _purity(s)
    # MRR growth: map [-50%, +100%] linearly onto [0, 1]; clamp outside.
    g = s.growthMRR30d
    growth_score = 0.5 if g is None else max(0.0, min((g + 50.0) / 150.0, 1.0))
    score = 0.45 * mrr_score + 0.20 * subs_score + 0.20 * purity + 0.15 * growth_score
    return score, {
        "mrr": round(mrr_score, 3), "subscribers": round(subs_score, 3),
        "purity": round(purity, 3), "mrr_growth": round(growth_score, 3),
    }


def _distribution(s: Startup) -> tuple[float, dict]:
    # Audience independence: followers per MRR dollar. A founder with 50k
    # followers and $1k MRR sells to their audience — you can't clone that.
    followers = s.xFollowerCount
    if followers is None:
        audience = NEUTRAL_AUDIENCE  # un-enriched: unknown, stay neutral
    else:
        fpd = followers / max(s.revenue.mrr or 1.0, 1.0)
        audience = 1.0 / (1.0 + fpd / 2.0)  # 2 followers/$ -> 0.5; 0.1 -> ~0.95

    impressions = s.googleSearchImpressionsLast30Days
    seo = _sat(impressions, SAT_IMPRESSIONS) if impressions else NEUTRAL_SEO
    rpv = _sat(s.revenuePerVisitor, SAT_RPV)
    score = 0.45 * audience + 0.35 * seo + 0.20 * rpv
    return score, {
        "audience_independence": round(audience, 3),
        "seo": round(seo, 3), "rev_per_visitor": round(rpv, 3),
    }


def _arpu(s: Startup) -> Optional[float]:
    payers = s.activeSubscriptions or s.customers or 0
    if payers and payers > 0 and (s.revenue.mrr or 0) > 0:
        return s.revenue.mrr / payers
    return None


def _simplicity(s: Startup) -> tuple[float, dict]:
    # Stack: commodity web stack is a green light; heavy infra is a red one.
    if s.techStack:
        slugs = {t.slug.lower() for t in s.techStack}
        stack = 0.95
        stack -= 0.15 * len(slugs & COMPLEX_TECH)
        if len(slugs) > 12:            # sprawling stack = sprawling product
            stack -= 0.10
        stack = max(stack, 0.20)
    else:
        stack = NEUTRAL_STACK

    arpu = _arpu(s)
    if arpu is None:
        arpu_score = NEUTRAL_ARPU
    elif ARPU_SWEET[0] <= arpu <= ARPU_SWEET[1]:
        arpu_score = 1.0
    elif ARPU_OKAY[0] <= arpu <= ARPU_OKAY[1]:
        arpu_score = 0.70
    else:
        arpu_score = 0.40  # $3/mo B2C volume game, or $500/mo sales-touch

    text = f"{s.name} {s.description or ''}".lower()
    hits = sum(1 for kw in SCOPE_KEYWORDS if kw in text)
    scope = max(1.0 - 0.15 * hits, 0.40)

    audience_fit = {"B2B": 1.0, "B2C": 0.85}.get(s.targetAudience or "", 0.90)

    score = 0.35 * stack + 0.30 * arpu_score + 0.25 * scope + 0.10 * audience_fit
    return score, {
        "stack": round(stack, 3), "arpu_band": round(arpu_score, 3),
        "scope": round(scope, 3), "audience_fit": round(audience_fit, 3),
    }


# ---------------------------------------------------------------------------
# Flags: the human-readable clone brief bullets
# ---------------------------------------------------------------------------

def _flags(s: Startup, arpu: Optional[float], purity: float) -> list[str]:
    out: list[str] = []
    mrr = s.revenue.mrr or 0.0
    subs = int(s.activeSubscriptions or 0)

    if subs:
        arpu_txt = f" (~${arpu:,.0f}/mo each)" if arpu else ""
        out.append(f"✓ {subs:,} paying subscribers{arpu_txt}")
    else:
        out.append("⚠ Subscriber count not reported — demand depth unverified")

    if purity >= 0.8:
        out.append(f"✓ {purity:.0%} of revenue is recurring — true SaaS")
    elif purity < 0.6:
        out.append(f"⚠ Only {purity:.0%} of revenue recurs — one-off-heavy")

    if s.xFollowerCount is not None:
        fpd = s.xFollowerCount / max(mrr, 1.0)
        if fpd >= 2.0:
            out.append(
                f"⚠ Audience-driven: {int(s.xFollowerCount):,} X followers vs "
                f"${mrr:,.0f} MRR — their distribution won't transfer to you"
            )
        elif fpd <= 0.3:
            out.append(f"✓ Product-driven: only {int(s.xFollowerCount):,} X followers — revenue isn't audience-dependent")

    impressions = s.googleSearchImpressionsLast30Days
    if impressions and impressions >= 10_000:
        out.append(f"✓ Organic pull: {int(impressions):,} Google impressions/mo — search demand you can also capture")

    if s.techStack:
        slugs = [t.slug for t in s.techStack]
        complex_hits = sorted({sl for sl in (x.lower() for x in slugs)} & COMPLEX_TECH)
        if complex_hits:
            out.append(f"⚠ Heavy stack: {', '.join(complex_hits)}")
        else:
            out.append(f"✓ Commodity stack: {', '.join(slugs[:6])}{'…' if len(slugs) > 6 else ''}")

    text = f"{s.name} {s.description or ''}".lower()
    kw_hits = [kw for kw in SCOPE_KEYWORDS if kw in text]
    if kw_hits:
        out.append(f"⚠ Scope sprawl ({', '.join(kw_hits[:3])}) — big build surface")

    if s.isMerchantOfRecord:
        out.append("• Merchant-of-record setup (handles global sales tax)")
    if s.onSale:
        price = f" for ${s.askingPrice:,.0f}" if s.askingPrice else ""
        out.append(f"• Listed for sale{price} — founder may be exiting")
    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_clone(s: Startup, *, now: Optional[datetime] = None) -> CloneResult:
    """Score one gated candidate (call ``passes_gates`` first)."""
    now = now or datetime.now(timezone.utc)
    demand, d_sub = _demand(s)
    distribution, dist_sub = _distribution(s)
    simplicity, s_sub = _simplicity(s)

    eps = 1e-6  # geometric mean: protect against a hard zero wiping the score
    score = 100.0 * (
        max(demand, eps) ** WEIGHTS["demand"]
        * max(distribution, eps) ** WEIGHTS["distribution"]
        * max(simplicity, eps) ** WEIGHTS["simplicity"]
    )
    arpu = _arpu(s)
    purity = _purity(s)
    age = s.months_since_founded(now)
    return CloneResult(
        startup=s,
        clone_score=round(score, 2),
        demand=round(demand, 4),
        distribution=round(distribution, 4),
        simplicity=round(simplicity, 4),
        age_months=round(age, 1) if age is not None else None,
        arpu=round(arpu, 2) if arpu is not None else None,
        purity=round(purity, 4),
        enriched=s.techStack is not None or s.xFollowerCount is not None,
        flags=_flags(s, arpu, purity),
        breakdown={"demand": d_sub, "distribution": dist_sub, "simplicity": s_sub},
    )


def rank_clones(
    startups: Iterable[Startup],
    *,
    min_age: float = MIN_AGE_MONTHS,
    max_age: float = MAX_AGE_MONTHS,
    min_mrr: float = MIN_MRR,
    min_purity: float = MIN_PURITY,
    min_subs: int = MIN_SUBSCRIBERS,
    now: Optional[datetime] = None,
) -> list[CloneResult]:
    """Gate + score + rank. Returns CloneResults sorted by clone_score desc."""
    now = now or datetime.now(timezone.utc)
    gated = [
        s for s in startups
        if passes_gates(
            s, min_age=min_age, max_age=max_age, min_mrr=min_mrr,
            min_purity=min_purity, min_subs=min_subs, now=now,
        )
    ]
    results = [score_clone(s, now=now) for s in gated]
    results.sort(key=lambda r: r.clone_score, reverse=True)
    return results


def enrich_and_rescore(
    results: list[CloneResult],
    client,
    *,
    top_n: int = 40,
    now: Optional[datetime] = None,
) -> list[CloneResult]:
    """Fetch detail data (tech stack, followers, …) for the top ``top_n``
    candidates and re-score them with the full signal set.

    Detail fetches are the expensive part (rate-limited), so we only enrich
    the startups whose preliminary score earned a closer look. Failures leave
    the un-enriched result in place.
    """
    now = now or datetime.now(timezone.utc)
    out: list[CloneResult] = []
    for i, r in enumerate(results):
        if i < top_n:
            try:
                detail = client.get_startup(r.startup.slug)
                out.append(score_clone(detail, now=now))
                continue
            except Exception:
                pass  # keep the preliminary score; enriched stays False
        out.append(r)
    out.sort(key=lambda r: r.clone_score, reverse=True)
    return out
