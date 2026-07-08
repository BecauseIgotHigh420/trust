"""Vercel serverless function: live GemHunter website.

Fetches fresh startups from the TrustMRR API on demand, filters to the last
N months, scores them, and returns the standalone HTML page. The response is
cached at Vercel's edge (s-maxage) so we stay well under TrustMRR's
20-requests/min limit no matter how many visitors hit the page.

The TrustMRR API key is read from the TRUSTMRR_API_KEY environment variable,
which you set in the Vercel dashboard (Project → Settings → Environment
Variables) — it is never stored in the repo.
"""

from __future__ import annotations

import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Make the gemhunter package importable when running as a Vercel function.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gemhunter.client import TrustMRRClient, TrustMRRError  # noqa: E402
from gemhunter.clone_report import generate_clones_html  # noqa: E402
from gemhunter.clone_score import enrich_and_rescore, rank_clones  # noqa: E402
from gemhunter.report import generate_html  # noqa: E402
from gemhunter.scoring import filter_recent, score_gems  # noqa: E402


def _int(qs: dict, key: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(qs.get(key, [default])[0])))
    except (ValueError, TypeError):
        return default


def _float(qs: dict, key: str, default: float, lo: float, hi: float) -> float:
    try:
        return max(lo, min(hi, float(qs.get(key, [default])[0])))
    except (ValueError, TypeError):
        return default


def build_page(qs: dict) -> str:
    """Build HTML from live TrustMRR data. ``?view=gems`` for the original
    leaderboard; the default view is Clone Score v2 (micro-SaaS to replicate)."""
    view = qs.get("view", ["clones"])[0]
    if view == "gems":
        return build_gems_page(qs)
    return build_clones_page(qs)


def build_gems_page(qs: dict) -> str:
    months = _float(qs, "months", 6.0, 0.5, 24.0)
    max_pages = _int(qs, "max_pages", 4, 1, 8)  # keep request fast + API-light
    min_mrr = _float(qs, "min_mrr", 100.0, 0.0, 1_000_000.0)
    top = _int(qs, "top", 60, 1, 200)
    sort = qs.get("sort", ["revenue-desc"])[0]
    category = qs.get("category", [None])[0] or None

    # Shorter throttle is fine here: max_pages<=8 stays under 20 req/min, and
    # the edge cache means we rarely hit the origin anyway.
    client = TrustMRRClient(min_interval=1.2)
    fetched = list(client.iter_startups(sort=sort, category=category, max_pages=max_pages))
    recent = filter_recent(fetched, max_age_months=months)
    gems = score_gems(recent, min_monthly_revenue=min_mrr)[:top]
    return generate_html(gems, max_age_months=months)


def build_clones_page(qs: dict) -> str:
    """Clone Score v2. Serverless budget maths: 4 list pages + up to 12 detail
    fetches at 2s spacing ≈ 16 calls / ~35s — inside the 60s function limit and
    under TrustMRR's 20 req/min. The CLI (`gemhunter clones --enrich 40`) is the
    place for deeper enrichment; results here are edge-cached for 6h anyway."""
    min_age = _float(qs, "min_age", 3.0, 0.0, 36.0)
    max_age = _float(qs, "max_age", 18.0, min_age, 48.0)
    min_mrr = _float(qs, "min_mrr", 500.0, 0.0, 1_000_000.0)
    min_purity = _float(qs, "min_purity", 0.35, 0.0, 1.0)
    max_pages = _int(qs, "max_pages", 4, 1, 6)
    enrich = _int(qs, "enrich", 10, 0, 12)
    top = _int(qs, "top", 40, 1, 100)
    category = qs.get("category", [None])[0] or None

    client = TrustMRRClient(min_interval=2.0)
    fetched = list(client.iter_startups(sort="revenue-desc", category=category, max_pages=max_pages))
    prelim = rank_clones(fetched, min_age=min_age, max_age=max_age,
                         min_mrr=min_mrr, min_purity=min_purity)
    results = enrich_and_rescore(prelim, client, top_n=min(enrich, len(prelim)))[:top]
    return generate_clones_html(results, min_age_months=min_age, max_age_months=max_age,
                                gems_href="?view=gems")


def _error_page(title: str, message: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>GemHunter — {title}</title>
<style>body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f1117;color:#e2e8f0;
display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px}}
.box{{max-width:560px;background:#1a1d27;border:1px solid #2d3140;border-radius:14px;padding:32px}}
h1{{color:#b794f4;margin:0 0 12px}}code{{background:#252a37;padding:2px 6px;border-radius:6px}}
a{{color:#b794f4}}</style></head><body><div class="box"><h1>◆ {title}</h1>
<p>{message}</p></div></body></html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (Vercel requires this signature)
        qs = parse_qs(urlparse(self.path).query)
        status = 200
        # Clone view does detail enrichment (expensive) -> cache longer.
        is_clones = qs.get("view", ["clones"])[0] != "gems"
        max_age = 21600 if is_clones else 3600
        cache = f"public, s-maxage={max_age}, stale-while-revalidate=86400"
        try:
            if not os.environ.get("TRUSTMRR_API_KEY"):
                status = 500
                cache = "no-store"
                body = _error_page(
                    "Missing API key",
                    "Set <code>TRUSTMRR_API_KEY</code> in Vercel → Project → Settings → "
                    "Environment Variables (value starts with <code>tmrr_</code>), then redeploy.",
                )
            else:
                body = build_page(qs)
        except TrustMRRError as exc:
            status, cache = 502, "no-store"
            body = _error_page("TrustMRR error", str(exc))
        except Exception:  # pragma: no cover - defensive
            status, cache = 500, "no-store"
            body = _error_page("Unexpected error", "<pre>" + traceback.format_exc()[-1200:] + "</pre>")

        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", cache)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
