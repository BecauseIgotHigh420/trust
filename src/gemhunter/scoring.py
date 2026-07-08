"""Turn raw startups into ranked "gems".

A gem = a *young* startup (founded within the lookback window) that is already
doing extremely well. We score on four transparent, log-scaled components so no
single mega-outlier dominates:

  * traction   — monthly revenue right now (last 30 days)
  * velocity   — total revenue earned per month since founding (how fast they got here)
  * growth     — 30-day revenue growth
  * efficiency — revenue per visitor (do they monetise traffic well?)

Each component is scaled to 0..1 across the candidate set, then combined with
weights into a 0..100 gem_score. Everything is explainable via score_breakdown.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Iterable

from .models import GemResult, Startup

DEFAULT_WEIGHTS = {
    "traction": 0.35,
    "velocity": 0.30,
    "growth": 0.20,
    "efficiency": 0.15,
}


def _log1p_clamped(value: float | None, cap: float) -> float:
    """log1p with a non-negative, capped input — tames outliers and negatives."""
    v = max(float(value or 0.0), 0.0)
    v = min(v, cap)
    return math.log1p(v)


def _normalise(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def filter_recent(
    startups: Iterable[Startup],
    *,
    max_age_months: float = 6.0,
    now: datetime | None = None,
) -> list[Startup]:
    """Keep only startups founded within ``max_age_months`` (and with a known date)."""
    now = now or datetime.now(timezone.utc)
    out = []
    for s in startups:
        age = s.months_since_founded(now)
        if age is not None and age <= max_age_months:
            out.append(s)
    return out


def score_gems(
    startups: Iterable[Startup],
    *,
    weights: dict | None = None,
    min_monthly_revenue: float = 100.0,
    now: datetime | None = None,
) -> list[GemResult]:
    """Score and rank startups. Returns GemResults sorted by gem_score desc.

    ``min_monthly_revenue`` filters out noise — a "gem doing extremely well"
    should have at least some verified monthly revenue.
    """
    weights = weights or DEFAULT_WEIGHTS
    now = now or datetime.now(timezone.utc)

    pool = [
        s for s in startups
        if (s.revenue.last30Days or 0.0) >= min_monthly_revenue
        or (s.revenue.mrr or 0.0) >= min_monthly_revenue
    ]
    if not pool:
        return []

    raw = {"traction": [], "velocity": [], "growth": [], "efficiency": []}
    velocities: list[float] = []
    for s in pool:
        age = s.months_since_founded(now) or 0.0
        velocity = (s.revenue.total or 0.0) / max(age, 0.5)  # $/month since founding
        velocities.append(velocity)
        raw["traction"].append(_log1p_clamped(s.mrr, cap=5_000_000))
        raw["velocity"].append(_log1p_clamped(velocity, cap=5_000_000))
        # growth30d is a percent (e.g. 120 == 120%); clamp the crazy tails.
        raw["growth"].append(_log1p_clamped(s.growth30d, cap=2_000))
        raw["efficiency"].append(_log1p_clamped(s.revenuePerVisitor, cap=1_000))

    norm = {k: _normalise(v) for k, v in raw.items()}

    results: list[GemResult] = []
    for i, s in enumerate(pool):
        breakdown = {k: round(norm[k][i], 4) for k in norm}
        score = sum(weights[k] * norm[k][i] for k in weights) * 100.0
        results.append(
            GemResult(
                startup=s,
                gem_score=round(score, 2),
                age_months=round(s.months_since_founded(now) or 0.0, 1),
                revenue_velocity=round(velocities[i], 2),
                score_breakdown=breakdown,
            )
        )

    results.sort(key=lambda r: r.gem_score, reverse=True)
    return results
