"""Pydantic models for TrustMRR startups and scored gem results.

All monetary values from the TrustMRR API are in **US dollars** (despite the
docs describing some filter params in cents). We keep them as dollars here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Revenue(BaseModel):
    last30Days: float = 0.0
    mrr: float = 0.0
    total: float = 0.0


class Startup(BaseModel):
    """A startup listing as returned by the TrustMRR API.

    Only fields we care about are modelled; extra keys are ignored so the model
    survives upstream additions.
    """

    model_config = {"extra": "ignore"}

    name: str
    slug: str
    url: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    foundedDate: Optional[datetime] = None
    category: Optional[str] = None
    paymentProvider: Optional[str] = None
    targetAudience: Optional[str] = None

    revenue: Revenue = Field(default_factory=Revenue)
    customers: Optional[float] = None
    activeSubscriptions: Optional[float] = None
    askingPrice: Optional[float] = None
    profitMarginLast30Days: Optional[float] = None

    growth30d: Optional[float] = None
    growthMRR30d: Optional[float] = None
    multiple: Optional[float] = None
    rank: Optional[int] = None

    visitorsLast30Days: Optional[float] = None
    googleSearchImpressionsLast30Days: Optional[float] = None
    revenuePerVisitor: Optional[float] = None

    onSale: bool = False
    firstListedForSaleAt: Optional[datetime] = None
    xHandle: Optional[str] = None
    xProfilePicture: Optional[str] = None

    @field_validator("foundedDate", "firstListedForSaleAt", mode="before")
    @classmethod
    def _empty_dates(cls, v):
        if v in ("", None):
            return None
        return v

    # ---- Derived helpers -------------------------------------------------

    def months_since_founded(self, now: Optional[datetime] = None) -> Optional[float]:
        if self.foundedDate is None:
            return None
        now = now or datetime.now(timezone.utc)
        founded = self.foundedDate
        if founded.tzinfo is None:
            founded = founded.replace(tzinfo=timezone.utc)
        days = (now - founded).total_seconds() / 86400.0
        return max(days / 30.4375, 0.0)

    @property
    def mrr(self) -> float:
        # Prefer explicit MRR; fall back to last-30-days revenue as a proxy.
        return self.revenue.mrr or self.revenue.last30Days or 0.0

    @property
    def x_url(self) -> Optional[str]:
        return f"https://x.com/{self.xHandle}" if self.xHandle else None


class GemResult(BaseModel):
    """A startup plus its computed gem score and the sub-scores behind it."""

    model_config = {"extra": "ignore"}

    startup: Startup
    gem_score: float
    age_months: Optional[float] = None
    revenue_velocity: float = 0.0  # total revenue / months since founded ($/month)
    score_breakdown: dict = Field(default_factory=dict)
