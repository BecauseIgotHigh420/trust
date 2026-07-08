"""Render Clone Score results to CSV, JSON, and a standalone HTML website."""

from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import CloneResult
from .report import _money


def _rows(results: Iterable[CloneResult]) -> list[dict]:
    rows = []
    for i, r in enumerate(results, start=1):
        s = r.startup
        rows.append(
            {
                "rank": i,
                "clone_score": r.clone_score,
                "demand": r.demand,
                "distribution": r.distribution,
                "simplicity": r.simplicity,
                "name": s.name,
                "slug": s.slug,
                "category": s.category or "",
                "country": s.country or "",
                "age_months": r.age_months,
                "mrr": round(s.revenue.mrr or 0.0, 2),
                "arpu": r.arpu,
                "purity": r.purity,
                "subscribers": int(s.activeSubscriptions or 0),
                "mrr_growth30d_pct": round(s.growthMRR30d, 2) if s.growthMRR30d is not None else None,
                "x_followers": int(s.xFollowerCount) if s.xFollowerCount is not None else None,
                "google_impressions_30d": s.googleSearchImpressionsLast30Days,
                "tech_stack": ", ".join(t.slug for t in (s.techStack or [])),
                "target_audience": s.targetAudience or "",
                "enriched": r.enriched,
                "on_sale": s.onSale,
                "asking_price": s.askingPrice,
                "flags": r.flags,
                "website": s.website or "",
                "trustmrr_url": s.url or f"https://trustmrr.com/startup/{s.slug}",
                "x_url": s.x_url or "",
                "description": (s.description or "").strip(),
                "breakdown": r.breakdown,
            }
        )
    return rows


def save_csv(results: list[CloneResult], path: Path) -> None:
    rows = _rows(results)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    flat = [{**r, "flags": " | ".join(r["flags"]), "breakdown": json.dumps(r["breakdown"])} for r in rows]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(flat[0].keys()))
        writer.writeheader()
        writer.writerows(flat)


def save_json(results: list[CloneResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(results),
        "source": "TrustMRR API (https://trustmrr.com/docs/api)",
        "scoring": "clone_score = 100 * demand^0.40 * distribution^0.35 * simplicity^0.25",
        "clones": _rows(results),
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def save_html(results: list[CloneResult], path: Path, **kw) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_clones_html(results, **kw), encoding="utf-8")


def generate_clones_html(
    results: list[CloneResult],
    *,
    min_age_months: float = 3.0,
    max_age_months: float = 18.0,
    gems_href: str = "?view=gems",
) -> str:
    rows = _rows(results)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    categories = sorted({r["category"] for r in rows if r["category"]})
    cat_options = "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in categories)

    total = len(rows)
    enriched = sum(1 for r in rows if r["enriched"])
    top_mrr = _money(max((r["mrr"] for r in rows), default=0))
    data_json = json.dumps(rows, default=str)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GemHunter — micro-SaaS clone targets</title>
<style>
  :root {{
    --bg:#f7f8fa; --card:#ffffff; --text:#1a202c; --muted:#718096;
    --border:#e2e8f0; --accent:#0987a0; --accent2:#38a169; --warn:#b7791f; --chip:#edf2f7;
  }}
  [data-theme="dark"] {{
    --bg:#0f1117; --card:#1a1d27; --text:#e2e8f0; --muted:#9aa5b1;
    --border:#2d3140; --accent:#63cadf; --accent2:#68d391; --warn:#f6ad55; --chip:#252a37;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--text); line-height:1.5; }}
  header {{ padding:28px 20px 12px; max-width:1200px; margin:0 auto; }}
  h1 {{ margin:0 0 4px; font-size:1.7rem; }}
  h1 .gem {{ color:var(--accent); }}
  .sub {{ color:var(--muted); font-size:.9rem; }}
  .sub a {{ color:var(--accent); }}
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
             border-radius:8px; padding:9px 12px; color:var(--text); }}
  main {{ max-width:1200px; margin:16px auto 60px; padding:0 20px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:14px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px;
           display:flex; flex-direction:column; gap:10px; }}
  .card .head {{ display:flex; gap:12px; align-items:flex-start; }}
  .card .name {{ font-weight:700; font-size:1.05rem; margin:0; }}
  .card .name a {{ color:inherit; text-decoration:none; }}
  .card .name a:hover {{ color:var(--accent); }}
  .badge {{ font-size:1.1rem; font-weight:800; color:#fff; background:var(--accent);
            border-radius:8px; padding:2px 10px; margin-left:auto; flex:none; }}
  .meta {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .chip {{ background:var(--chip); color:var(--muted); border-radius:20px; padding:2px 10px; font-size:.72rem; }}
  .chip.sale {{ background:var(--accent2); color:#04220f; font-weight:700; }}
  .chip.prelim {{ border:1px dashed var(--muted); background:transparent; }}
  .desc {{ color:var(--muted); font-size:.85rem; margin:0; display:-webkit-box; -webkit-line-clamp:2;
           -webkit-box-orient:vertical; overflow:hidden; }}
  .bars {{ display:flex; flex-direction:column; gap:5px; }}
  .bar {{ display:grid; grid-template-columns:82px 1fr 38px; gap:8px; align-items:center; font-size:.72rem; }}
  .bar .lbl {{ color:var(--muted); text-transform:uppercase; letter-spacing:.03em; }}
  .bar .track {{ background:var(--chip); border-radius:6px; height:8px; overflow:hidden; }}
  .bar .fill {{ height:100%; border-radius:6px; background:var(--accent); }}
  .bar .val {{ text-align:right; color:var(--muted); }}
  .metrics {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }}
  .m {{ background:var(--chip); border-radius:8px; padding:8px; text-align:center; }}
  .m .v {{ font-weight:700; font-size:.95rem; }}
  .m .l {{ font-size:.65rem; color:var(--muted); text-transform:uppercase; letter-spacing:.03em; }}
  .flags {{ margin:0; padding:0; list-style:none; font-size:.78rem; display:flex; flex-direction:column; gap:3px; }}
  .flags li {{ color:var(--muted); }}
  .flags li.ok {{ color:var(--accent2); }}
  .flags li.warn {{ color:var(--warn); }}
  .links {{ display:flex; gap:14px; font-size:.82rem; margin-top:auto; }}
  .links a {{ color:var(--accent); text-decoration:none; }}
  .empty {{ text-align:center; color:var(--muted); padding:60px 20px; }}
  footer {{ text-align:center; color:var(--muted); font-size:.78rem; padding:0 20px 40px; }}
</style>
</head>
<body>
<header>
  <h1><span class="gem">⧉</span> GemHunter <span style="font-weight:400;color:var(--muted)">/ clone targets</span></h1>
  <div class="sub">Micro-SaaS worth <b>replicating</b>: {min_age_months:g}–{max_age_months:g} months old, real recurring revenue,
  reachable customers, buildable by a small team. Clone score = demand × distribution × simplicity (geometric — one bad axis sinks it).
  Data: <a href="https://trustmrr.com">TrustMRR</a> · <a href="{html.escape(gems_href)}">switch to gem leaderboard →</a> · Generated {generated}.</div>
  <div class="stats">
    <div class="stat"><div class="num">{total}</div><div class="lbl">Clone targets</div></div>
    <div class="stat"><div class="num">{enriched}</div><div class="lbl">Fully analysed</div></div>
    <div class="stat"><div class="num">{top_mrr}</div><div class="lbl">Top MRR</div></div>
    <div class="stat"><div class="num">{min_age_months:g}–{max_age_months:g}mo</div><div class="lbl">Age window</div></div>
  </div>
</header>
<div class="controls">
  <input id="q" type="search" placeholder="Search name, description, stack…">
  <select id="cat"><option value="">All categories</option>{cat_options}</select>
  <select id="sort">
    <option value="clone_score">Sort: Clone score</option>
    <option value="demand">Sort: Demand</option>
    <option value="distribution">Sort: Distribution</option>
    <option value="simplicity">Sort: Simplicity</option>
    <option value="mrr">Sort: MRR</option>
    <option value="age_months">Sort: Youngest</option>
  </select>
  <button class="toggle" id="themeBtn">🌓 Theme</button>
</div>
<main>
  <div id="grid" class="grid"></div>
  <div id="empty" class="empty" style="display:none">No clone targets match your filters.</div>
</main>
<footer>
  Clone scores are heuristic signals for idea research — not diligence, not investment advice.
  Verify demand, competition, and every number at the source before building anything.
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
  let rows = DATA.filter(r => {{
    if (cat && r.category !== cat) return false;
    if (q) {{
      const hay = (r.name+' '+r.description+' '+r.tech_stack+' '+r.category).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
  rows.sort((a,b) => (sort==='age_months' ? (a[sort]-b[sort]) : (b[sort]||0)-(a[sort]||0)));
  $('#grid').innerHTML = rows.map(cardHTML).join('');
  $('#empty').style.display = rows.length ? 'none' : 'block';
}}

function barHTML(lbl, v) {{
  const pct = Math.round((+v||0)*100);
  return `<div class="bar"><span class="lbl">${{lbl}}</span><span class="track"><span class="fill" style="width:${{pct}}%"></span></span><span class="val">${{pct}}</span></div>`;
}}

function cardHTML(r) {{
  const arpu = r.arpu ? '$'+Math.round(r.arpu) : '—';
  const purity = r.purity!=null ? Math.round(r.purity*100)+'%' : '—';
  const sale = r.on_sale ? `<span class="chip sale">On sale ${{r.asking_price?money(r.asking_price):''}}</span>` : '';
  const prelim = r.enriched ? '' : '<span class="chip prelim" title="Detail data (stack, followers) not fetched">preliminary</span>';
  const flags = (r.flags||[]).map(f => {{
    const cls = f.startsWith('✓') ? 'ok' : (f.startsWith('⚠') ? 'warn' : '');
    return `<li class="${{cls}}">${{esc(f)}}</li>`;
  }}).join('');
  const x = r.x_url ? `<a href="${{esc(r.x_url)}}" target="_blank" rel="noopener">𝕏 founder</a>` : '';
  const site = r.website ? `<a href="${{esc(r.website)}}" target="_blank" rel="noopener">Website</a>` : '';
  return `<div class="card">
    <div class="head">
      <p class="name"><a href="${{esc(r.trustmrr_url)}}" target="_blank" rel="noopener">${{esc(r.name)}}</a></p>
      <span class="badge" title="Clone score">${{r.clone_score.toFixed(0)}}</span>
    </div>
    <div class="meta">
      ${{r.category?`<span class="chip">${{esc(r.category)}}</span>`:''}}
      <span class="chip">${{r.age_months}} mo old</span>
      ${{r.target_audience?`<span class="chip">${{esc(r.target_audience)}}</span>`:''}}
      ${{prelim}} ${{sale}}
    </div>
    <p class="desc">${{esc(r.description)}}</p>
    <div class="bars">
      ${{barHTML('Demand', r.demand)}}
      ${{barHTML('Distribution', r.distribution)}}
      ${{barHTML('Simplicity', r.simplicity)}}
    </div>
    <div class="metrics">
      <div class="m"><div class="v">${{money(r.mrr)}}</div><div class="l">MRR</div></div>
      <div class="m"><div class="v">${{arpu}}</div><div class="l">ARPU</div></div>
      <div class="m"><div class="v">${{purity}}</div><div class="l">Recurring</div></div>
    </div>
    <ul class="flags">${{flags}}</ul>
    <div class="links">${{site}} <a href="${{esc(r.trustmrr_url)}}" target="_blank" rel="noopener">TrustMRR</a> ${{x}}</div>
  </div>`;
}}

['input','change'].forEach(ev => {{
  ['#q','#cat','#sort'].forEach(sel => $(sel).addEventListener(ev, render));
}});
function setTheme(t) {{ document.documentElement.setAttribute('data-theme', t); localStorage.setItem('gh-theme', t); }}
$('#themeBtn').addEventListener('click', () => {{
  setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}});
setTheme(localStorage.getItem('gh-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
render();
</script>
</body>
</html>"""
