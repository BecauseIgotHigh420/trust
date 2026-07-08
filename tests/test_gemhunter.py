"""Tests for the gemhunter package (no network required)."""

from datetime import datetime, timedelta, timezone

import pytest

from gemhunter.client import TrustMRRClient, TrustMRRError
from gemhunter.models import Startup
from gemhunter.report import _money, _rows, generate_html
from gemhunter.scoring import filter_recent, score_gems

NOW = datetime(2026, 7, 8, tzinfo=timezone.utc)


def _startup(name, months_old, last30=0.0, mrr=0.0, total=0.0, growth=0.0, rpv=0.0, **kw):
    founded = NOW - timedelta(days=months_old * 30.4375)
    return Startup(
        name=name,
        slug=name.lower(),
        foundedDate=founded,
        revenue={"last30Days": last30, "mrr": mrr, "total": total},
        growth30d=growth,
        revenuePerVisitor=rpv,
        **kw,
    )


class TestModels:
    def test_age_and_mrr_fallback(self):
        s = _startup("A", 3, last30=500)
        assert 2.9 < s.months_since_founded(NOW) < 3.1
        assert s.mrr == 500  # falls back to last30Days when mrr is 0

    def test_naive_founded_date_treated_as_utc(self):
        s = Startup(name="B", slug="b", foundedDate="2026-01-01T00:00:00.000Z")
        assert s.months_since_founded(NOW) is not None

    def test_x_url(self):
        assert _startup("C", 1, xHandle="foo").x_url == "https://x.com/foo"
        assert _startup("D", 1).x_url is None


class TestScoring:
    def test_filter_recent_excludes_old_and_undated(self):
        pool = [
            _startup("young", 2, last30=500),
            _startup("old", 12, last30=500),
            Startup(name="undated", slug="u"),  # no foundedDate
        ]
        recent = filter_recent(pool, max_age_months=6, now=NOW)
        assert [s.name for s in recent] == ["young"]

    def test_min_revenue_filter(self):
        pool = [_startup("tiny", 1, last30=10), _startup("real", 1, last30=5000)]
        gems = score_gems(pool, min_monthly_revenue=100, now=NOW)
        assert [g.startup.name for g in gems] == ["real"]

    def test_ranking_orders_by_score(self):
        pool = [
            _startup("weak", 5, last30=150, total=200, growth=5, rpv=0.1),
            _startup("strong", 2, last30=40000, total=120000, growth=900, rpv=8.0),
        ]
        gems = score_gems(pool, min_monthly_revenue=100, now=NOW)
        assert gems[0].startup.name == "strong"
        assert gems[0].gem_score > gems[1].gem_score

    def test_velocity_computed(self):
        s = _startup("v", 2, last30=1000, total=6000)
        gem = score_gems([s], now=NOW)[0]
        assert gem.revenue_velocity == pytest.approx(6000 / 2, rel=0.05)

    def test_empty_pool_returns_empty(self):
        assert score_gems([], now=NOW) == []


class TestReport:
    def test_money_formatting(self):
        assert _money(0) == "$0"
        assert _money(950) == "$950"
        assert _money(2500) == "$2.5k"
        assert _money(3_400_000) == "$3.40M"

    def test_rows_are_ranked(self):
        gems = score_gems([_startup("a", 1, last30=9000, total=9000),
                           _startup("b", 1, last30=200, total=200)], now=NOW)
        rows = _rows(gems)
        assert rows[0]["rank_gem"] == 1
        assert rows[0]["gem_score"] >= rows[1]["gem_score"]

    def test_generate_html_is_self_contained(self):
        gems = score_gems([_startup("Acme", 2, last30=5000, total=15000, growth=300)], now=NOW)
        page = generate_html(gems, max_age_months=6)
        assert page.strip().startswith("<!DOCTYPE html>")
        assert page.strip().endswith("</html>")
        assert "const DATA" in page
        assert "Acme" in page
        assert "http" not in page.split("<script>")[0].replace("https://trustmrr.com", "")  # no external asset refs in <head>


class TestClient:
    def test_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("TRUSTMRR_API_KEY", raising=False)
        with pytest.raises(TrustMRRError):
            TrustMRRClient()

    def test_rejects_malformed_key(self):
        with pytest.raises(TrustMRRError):
            TrustMRRClient(api_key="not-a-real-key")

    def test_invalid_sort_rejected(self):
        client = TrustMRRClient(api_key="tmrr_fake")
        with pytest.raises(TrustMRRError):
            client.list_startups(sort="bogus-sort")
