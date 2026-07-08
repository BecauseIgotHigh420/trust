"""Render scored gems to CSV, JSON, and a standalone filterable HTML website."""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import GemResult


def _money(value: float | None) -> str:
    if not value:
        return "$0"
    value = float(value)
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}k"
    return f"${value:,.0f}"


def _rows(results: Iterable[GemResult]) -> list[dict]:
    rows = []
    for r in results:
        s = r.startup
        rows.append(
            {
                "rank_gem": None,  # filled below
                "gem_score": r.gem_score,
                "name": s.name,
                "slug": s.slug,
                "category": s.category or "",
                "country": s.country or "",
                "age_months": r.age_months,
                "founded": s.foundedDate.date().isoformat() if s.foundedDate else "",
                "mrr": round(s.mrr, 2),
                "revenue_last30d": round(s.revenue.last30Days or 0.0, 2),
                "revenue_total": round(s.revenue.total or 0.0, 2),
                "revenue_velocity_per_month": r.revenue_velocity,
                "growth30d_pct": round(s.growth30d, 2) if s.growth30d is not None else None,
                "customers": s.customers,
                "visitors_last30d": s.visitorsLast30Days,
                "revenue_per_visitor": s.revenuePerVisitor,
                "payment_provider": s.paymentProvider or "",
                "target_audience": s.targetAudience or "",
                "on_sale": s.onSale,
                "asking_price": s.askingPrice,
                "website": s.website or "",
                "trustmrr_url": s.url or f"https://trustmrr.com/startup/{s.slug}",
                "x_url": s.x_url or "",
                "description": (s.description or "").strip(),
            }
        )
    for i, row in enumerate(rows, start=1):
        row["rank_gem"] = i
    return rows


def save_csv(results: list[GemResult], path: Path) -> None:
    rows = _rows(results)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_json(results: list[GemResult], path: Path) -> None:
    rows = _rows(results)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "source": "TrustMRR API (https://trustmrr.com/docs/api)",
        "gems": rows,
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def save_html(results: list[GemResult], path: Path, *, max_age_months: float = 6.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_html(results, max_age_months=max_age_months), encoding="utf-8")


def generate_html(results: list[GemResult], *, max_age_months: float = 6.0) -> str:
    rows = _rows(results)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    categories = sorted({r["category"] for r in rows if r["category"]})
    cat_options = "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in categories)

    total = len(rows)
    avg_score = round(sum(r["gem_score"] for r in rows) / total, 1) if total else 0
    top_mrr = _money(max((r["mrr"] for r in rows), default=0))

    data_json = json.dumps(rows, default=str)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GemHunter — startup gems to replicate</title>
<style>
  :root {{
    --bg:#f7f8fa; --card:#ffffff; --text:#1a202c; --muted:#718096;
    --border:#e2e8f0; --accent:#6b46c1; --accent2:#38a169; --chip:#edf2f7;
  }}
  [data-theme="dark"] {{
    --bg:#0f1117; --card:#1a1d27; --text:#e2e8f0; --muted:#9aa5b1;
    --border:#2d3140; --accent:#b794f4; --accent2:#68d391; --chip:#252a37;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--text); line-height:1.5; }}
  header {{ padding:28px 20px 12px; max-width:1200px; margin:0 auto; }}
  h1 {{ margin:0 0 4px; font-size:1.7rem; }}
  h1 .gem {{ color:var(--accent); }}
  .sub {{ color:var(--muted); font-size:.9rem; }}
  .stats {{ display:flex; gap:12px; flex-wrap:wrap; margin:16px 0 0; }}
  .stat {{ background:var(--card); border:1px solid var(--border); border-radius:10px;
           padding:10px 16px; min-width:120px; }}
  .stat .num {{ font-size:1.4rem; font-weight:700; color:var(--accent); }}
  .stat .lbl {{ font-size:.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }}
  .controls {{ max-width:1200px; margin:20px auto 0; padding:0 20px; display:flex; gap:10px;
               flex-wrap:wrap; align-items:center; }}
  input,select {{ background:var(--card); color:var(--text); border:1px solid var(--border);
                  border-radius:8px; padding:9px 12px; font-size:.9rem; }}
  input#q {{ flex:1; min-width:220px; }}
  .toggle {{ margin-left:auto; cursor:pointer; background:var(--card); border:1px solid var(--border);
             border-radius:8px; padding:9px 12px; }}
  main {{ max-width:1200px; margin:16px auto 60px; padding:0 20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:14px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px;
           display:flex; flex-direction:column; gap:10px; }}
  .card .head {{ display:flex; gap:12px; align-items:flex-start; }}
  .card img.logo {{ width:42px; height:42px; border-radius:9px; object-fit:cover; background:var(--chip); flex:none; }}
  .card .name {{ font-weight:700; font-size:1.05rem; margin:0; }}
  .card .name a {{ color:inherit; text-decoration:none; }}
  .card .name a:hover {{ color:var(--accent); }}
  .badge {{ font-size:1.1rem; font-weight:800; color:#fff; background:var(--accent);
            border-radius:8px; padding:2px 10px; margin-left:auto; flex:none; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .chip {{ background:var(--chip); color:var(--muted); border-radius:20px; padding:2px 10px; font-size:.72rem; }}
  .chip.sale {{ background:var(--accent2); color:#04220f; font-weight:700; }}
  .desc {{ color:var(--muted); font-size:.85rem; margin:0; display:-webkit-box; -webkit-line-clamp:3;
           -webkit-box-orient:vertical; overflow:hidden; }}
  .metrics {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:auto; }}
  .m {{ background:var(--chip); border-radius:8px; padding:8px; text-align:center; }}
  .m .v {{ font-weight:700; font-size:.95rem; }}
  .m .l {{ font-size:.65rem; color:var(--muted); text-transform:uppercase; letter-spacing:.03em; }}
  .links {{ display:flex; gap:14px; font-size:.82rem; }}
  .links a {{ color:var(--accent); text-decoration:none; }}
  .empty {{ text-align:center; color:var(--muted); padding:60px 20px; }}
  footer {{ text-align:center; color:var(--muted); font-size:.78rem; padding:0 20px 40px; }}
</style>
</head>
<body>
<header>
  <h1><span class="gem">◆</span> GemHunter</h1>
  <div class="sub">Recently-founded startups (last {max_age_months:g} months) with strong verified revenue — ideas worth replicating. Data: <a href="https://trustmrr.com" style="color:var(--accent)">TrustMRR</a>. Generated {generated}.</div>
  <div class="stats">
    <div class="stat"><div class="num">{total}</div><div class="lbl">Gems found</div></div>
    <div class="stat"><div class="num">{avg_score}</div><div class="lbl">Avg gem score</div></div>
    <div class="stat"><div class="num">{top_mrr}</div><div class="lbl">Top MRR</div></div>
    <div class="stat"><div class="num">&le;{max_age_months:g}mo</div><div class="lbl">Max age</div></div>
  </div>
</header>
<div class="controls">
  <input id="q" type="search" placeholder="Search name, description, X handle…">
  <select id="cat"><option value="">All categories</option>{cat_options}</select>
  <select id="sort">
    <option value="gem_score">Sort: Gem score</option>
    <option value="mrr">Sort: MRR</option>
    <option value="revenue_velocity_per_month">Sort: Revenue velocity</option>
    <option value="growth30d_pct">Sort: 30d growth</option>
    <option value="age_months">Sort: Youngest</option>
  </select>
  <label class="chip" style="display:flex;align-items:center;gap:6px;cursor:pointer">
    <input id="saleonly" type="checkbox" style="margin:0"> On sale only
  </label>
  <button class="toggle" id="themeBtn">🌓 Theme</button>
</div>
<main>
  <div id="grid" class="grid"></div>
  <div id="empty" class="empty" style="display:none">No gems match your filters.</div>
</main>
<footer>
  Built with GemHunter · Scores are heuristic (traction + velocity + growth + efficiency), not investment advice.
  Verify every number at the source before acting.
</footer>
<script>
const DATA = {data_json};
const $ = s => document.querySelector(s);
const money = v => {{ v=+v||0; if(v>=1e6) return '$'+(v/1e6).toFixed(2)+'M'; if(v>=1e3) return '$'+(v/1e3).toFixed(1)+'k'; return '$'+Math.round(v); }};
const esc = s => (s||'').replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));

function render() {{
  const q = $('#q').value.toLowerCase().trim();
  const cat = $('#cat').value;
  const sort = $('#sort').value;
  const saleOnly = $('#saleonly').checked;
  let rows = DATA.filter(r => {{
    if (cat && r.category !== cat) return false;
    if (saleOnly && !r.on_sale) return false;
    if (q) {{
      const hay = (r.name+' '+r.description+' '+r.x_url+' '+r.category).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
  rows.sort((a,b) => (sort==='age_months' ? (a[sort]-b[sort]) : (b[sort]||0)-(a[sort]||0)));
  const grid = $('#grid');
  grid.innerHTML = rows.map(cardHTML).join('');
  $('#empty').style.display = rows.length ? 'none' : 'block';
}}

function cardHTML(r) {{
  const growth = r.growth30d_pct==null ? '—' : (r.growth30d_pct>=1000 ? Math.round(r.growth30d_pct)+'%' : r.growth30d_pct.toFixed(0)+'%');
  const sale = r.on_sale ? `<span class="chip sale">On sale ${{r.asking_price?money(r.asking_price):''}}</span>` : '';
  const x = r.x_url ? `<a href="${{esc(r.x_url)}}" target="_blank" rel="noopener">𝕏 founder</a>` : '';
  const site = r.website ? `<a href="${{esc(r.website)}}" target="_blank" rel="noopener">Website</a>` : '';
  return `<div class="card">
    <div class="head">
      <p class="name"><a href="${{esc(r.trustmrr_url)}}" target="_blank" rel="noopener">${{esc(r.name)}}</a></p>
      <span class="badge" title="Gem score">${{r.gem_score.toFixed(0)}}</span>
    </div>
    <div class="meta">
      ${{r.category?`<span class="chip">${{esc(r.category)}}</span>`:''}}
      ${{r.country?`<span class="chip">${{esc(r.country)}}</span>`:''}}
      <span class="chip">${{r.age_months}} mo old</span>
      ${{r.target_audience?`<span class="chip">${{esc(r.target_audience)}}</span>`:''}}
      ${{sale}}
    </div>
    <p class="desc">${{esc(r.description)}}</p>
    <div class="metrics">
      <div class="m"><div class="v">${{money(r.mrr)}}</div><div class="l">MRR</div></div>
      <div class="m"><div class="v">${{money(r.revenue_velocity_per_month)}}</div><div class="l">Rev / mo</div></div>
      <div class="m"><div class="v">${{growth}}</div><div class="l">30d growth</div></div>
    </div>
    <div class="links">${{site}} <a href="${{esc(r.trustmrr_url)}}" target="_blank" rel="noopener">TrustMRR</a> ${{x}}</div>
  </div>`;
}}

['input','change'].forEach(ev => {{
  ['#q','#cat','#sort','#saleonly'].forEach(sel => $(sel).addEventListener(ev, render));
}});

function setTheme(t) {{ document.documentElement.setAttribute('data-theme', t); localStorage.setItem('gh-theme', t); }}
$('#themeBtn').addEventListener('click', () => {{
  const cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  setTheme(cur);
}});
const saved = localStorage.getItem('gh-theme');
setTheme(saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
render();
</script>
</body>
</html>"""
