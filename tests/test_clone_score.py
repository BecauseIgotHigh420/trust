"""Tests for Clone Score v2 (no network required)."""

from datetime import datetime, timedelta, timezone

from gemhunter.clone_score import (
    enrich_and_rescore,
    passes_gates,
    rank_clones,
    score_clone,
)
from gemhunter.models import Startup

NOW = datetime(2026, 7, 8, tzinfo=timezone.utc)


def _startup(name, months_old, mrr=2000.0, last30=None, subs=50, **kw):
    """A gate-passing baseline startup; override fields to test each gate/signal."""
    founded = NOW - timedelta(days=months_old * 30.4375)
    return Startup(
        name=name,
        slug=name.lower().replace(" ", "-"),
        foundedDate=founded,
        revenue={"last30Days": mrr if last30 is None else last30, "mrr": mrr, "total": mrr * 3},
        activeSubscriptions=subs,
        **kw,
    )


class TestGates:
    def test_age_window(self):
        assert not passes_gates(_startup("too-young", 1.5), now=NOW)   # launch noise
        assert not passes_gates(_startup("too-old", 24), now=NOW)      # crowded market
        assert passes_gates(_startup("goldilocks", 8), now=NOW)

    def test_mrr_floor(self):
        assert not passes_gates(_startup("tipjar", 6, mrr=100), now=NOW)
        assert passes_gates(_startup("real", 6, mrr=800), now=NOW)

    def test_purity_kills_lifetime_deal_pops(self):
        # $40k one-off launch revenue but only $500 recurring -> not SaaS.
        ltd = _startup("ltd-pop", 6, mrr=500, last30=40000)
        assert not passes_gates(ltd, now=NOW)
        # Roofclaw-shaped: service revenue dwarfing MRR.
        service = _startup("service", 5, mrr=7500, last30=400000)
        assert not passes_gates(service, now=NOW)

    def test_min_subs_only_when_reported(self):
        assert not passes_gates(_startup("two-subs", 6, subs=2), now=NOW)
        # Unreported (0/None) is a data gap, not a failure — don't reject.
        assert passes_gates(_startup("unreported", 6, subs=0), now=NOW)

    def test_mrr_can_exceed_last30(self):
        # Annual-plan accounting: purity clamps at 1.0, must still pass.
        assert passes_gates(_startup("annual", 6, mrr=5000, last30=1200), now=NOW)


class TestScoring:
    def test_audience_driven_penalised(self):
        indie = _startup("indie", 8, xFollowerCount=400)
        influencer = _startup("influencer", 8, xFollowerCount=80000)
        s_indie, s_infl = score_clone(indie, now=NOW), score_clone(influencer, now=NOW)
        assert s_indie.distribution > s_infl.distribution
        assert s_indie.clone_score > s_infl.clone_score
        assert any("Audience-driven" in f for f in s_infl.flags)
        assert any("Product-driven" in f for f in s_indie.flags)

    def test_seo_signal_rewarded(self):
        seo = _startup("seo", 8, googleSearchImpressionsLast30Days=80000)
        dark = _startup("dark", 8, googleSearchImpressionsLast30Days=None)
        assert score_clone(seo, now=NOW).distribution > score_clone(dark, now=NOW).distribution

    def test_arpu_sweet_spot(self):
        sweet = _startup("sweet", 8, mrr=2000, subs=50)      # $40 ARPU
        cheap = _startup("cheap", 8, mrr=2000, subs=1000)    # $2 ARPU volume game
        r_sweet, r_cheap = score_clone(sweet, now=NOW), score_clone(cheap, now=NOW)
        assert r_sweet.arpu == 40.0
        assert r_sweet.simplicity > r_cheap.simplicity

    def test_scope_sprawl_penalised(self):
        focused = _startup("focused", 8, description="Turn screenshots into clean mockups.")
        sprawl = _startup(
            "sprawl", 8,
            description="The all-in-one platform: HR, CRM, projects, finance and payroll in one place.",
        )
        assert score_clone(focused, now=NOW).simplicity > score_clone(sprawl, now=NOW).simplicity

    def test_complex_stack_penalised(self):
        simple = _startup("simple", 8, techStack=[{"slug": "nextjs"}, {"slug": "supabase"}, {"slug": "stripe"}])
        heavy = _startup("heavy", 8, techStack=[{"slug": "kubernetes"}, {"slug": "kafka"}, {"slug": "pytorch"}])
        r_simple, r_heavy = score_clone(simple, now=NOW), score_clone(heavy, now=NOW)
        assert r_simple.simplicity > r_heavy.simplicity
        assert r_simple.enriched and r_heavy.enriched

    def test_geometric_one_bad_axis_sinks(self):
        # Monster demand but hopeless distribution must not rank above a
        # balanced candidate — the geometric mean enforces that.
        balanced = _startup("balanced", 8, mrr=4000, xFollowerCount=500,
                            googleSearchImpressionsLast30Days=30000)
        lopsided = _startup("lopsided", 8, mrr=45000, subs=400, xFollowerCount=500000)
        r_bal, r_lop = score_clone(balanced, now=NOW), score_clone(lopsided, now=NOW)
        assert r_bal.clone_score > r_lop.clone_score

    def test_rank_clones_sorted_and_gated(self):
        pool = [
            _startup("good", 8, mrr=5000, xFollowerCount=300),
            _startup("too-young", 1, mrr=50000),
            _startup("weak", 8, mrr=600, subs=12),
        ]
        ranked = rank_clones(pool, now=NOW)
        assert [r.startup.name for r in ranked] == ["good", "weak"]
        assert ranked[0].clone_score > ranked[1].clone_score


class TestEnrichment:
    def test_enrich_rescores_and_survives_failures(self):
        pool = [_startup("a", 8, mrr=5000), _startup("b", 8, mrr=3000)]
        prelim = rank_clones(pool, now=NOW)

        class FakeClient:
            def get_startup(self, slug):
                if slug == "b":
                    raise RuntimeError("boom")  # keep preliminary result
                # Detail reveals 'a' is audience-driven -> score drops.
                return _startup("a", 8, mrr=5000, xFollowerCount=200000)

        out = enrich_and_rescore(prelim, FakeClient(), top_n=2, now=NOW)
        by_name = {r.startup.name: r for r in out}
        assert by_name["a"].enriched is True
        assert by_name["b"].enriched is False
        assert by_name["a"].clone_score < prelim[0].clone_score
