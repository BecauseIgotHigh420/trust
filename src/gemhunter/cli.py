"""Command-line interface for GemHunter.

Examples:
    export TRUSTMRR_API_KEY=tmrr_xxx
    gemhunter run                              # top gems from last 6 months -> HTML/JSON/CSV
    gemhunter run --months 3 --max-pages 10    # tighter window, scan deeper
    gemhunter run --sort growth-desc           # seed the scan from fastest growers
    gemhunter run --category ai --min-mrr 500

    gemhunter clones                           # Clone Score v2: what should YOU build?
    gemhunter clones --enrich 40 --top 30      # deep-analyse the top 40 candidates
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from . import clone_report
from .client import TrustMRRClient, TrustMRRError, VALID_SORTS
from .clone_score import enrich_and_rescore, rank_clones
from .report import save_csv, save_html, save_json, _money
from .scoring import filter_recent, score_gems

console = Console()


@click.group()
@click.version_option()
def cli():
    """GemHunter — find recently-founded startups that are already doing extremely well."""


@cli.command()
@click.option("--api-key", envvar="TRUSTMRR_API_KEY", help="TrustMRR API key (or set TRUSTMRR_API_KEY).")
@click.option("--months", default=6.0, show_default=True, help="Max age in months (the lookback window).")
@click.option("--max-pages", default=8, show_default=True, help="Pages to scan (50 startups/page, ~3s each).")
@click.option("--sort", default="revenue-desc", show_default=True,
              type=click.Choice(sorted(VALID_SORTS)), help="Server-side sort used to seed the scan.")
@click.option("--category", default=None, help="Restrict to a TrustMRR category slug (e.g. ai, saas).")
@click.option("--min-mrr", default=100.0, show_default=True, help="Minimum monthly revenue to count as a gem.")
@click.option("--top", default=60, show_default=True, help="Keep the top N gems in the output.")
@click.option("--output-dir", default="data/output", show_default=True, type=click.Path(), help="Where to write files.")
@click.option("--open-html/--no-open-html", default=False, help="Print the HTML path when done.")
def run(api_key, months, max_pages, sort, category, min_mrr, top, output_dir, open_html):
    """Fetch, score, and export startup gems."""
    try:
        client = TrustMRRClient(api_key=api_key)
    except TrustMRRError as exc:
        console.print(f"[red]✗ {exc}[/red]")
        sys.exit(1)

    console.print(
        f"[bold]Scanning TrustMRR[/bold] — sort=[cyan]{sort}[/cyan], "
        f"up to [cyan]{max_pages}[/cyan] pages, window [cyan]{months:g}mo[/cyan]…"
    )

    fetched: list = []

    def _progress(page, meta):
        console.print(f"  page {page} · {len(fetched)} fetched · total available {meta.get('total','?')}", style="dim")

    try:
        for s in client.iter_startups(sort=sort, category=category, max_pages=max_pages, progress=None):
            fetched.append(s)
            if len(fetched) % 50 == 0:
                _progress(len(fetched) // 50, {"total": "?"})
    except TrustMRRError as exc:
        console.print(f"[red]✗ API error: {exc}[/red]")
        sys.exit(1)

    console.print(f"Fetched [bold]{len(fetched)}[/bold] startups. Filtering to last {months:g} months…")
    recent = filter_recent(fetched, max_age_months=months)
    console.print(f"[bold]{len(recent)}[/bold] founded within the window.")

    gems = score_gems(recent, min_monthly_revenue=min_mrr)[:top]
    if not gems:
        console.print("[yellow]No gems matched. Try --max-pages higher, --min-mrr lower, or --sort growth-desc.[/yellow]")
        sys.exit(0)

    out = Path(output_dir)
    save_html(gems, out / "gems.html", max_age_months=months)
    save_json(gems, out / "gems.json")
    save_csv(gems, out / "gems.csv")

    _print_table(gems[:15])
    console.print(
        f"\n[green]✓ Wrote {len(gems)} gems[/green] → "
        f"[bold]{out / 'gems.html'}[/bold], gems.json, gems.csv"
    )
    if open_html:
        console.print(f"Open: file://{(out / 'gems.html').resolve()}")


@cli.command()
@click.option("--api-key", envvar="TRUSTMRR_API_KEY", help="TrustMRR API key (or set TRUSTMRR_API_KEY).")
@click.option("--min-age", default=3.0, show_default=True, help="Min age in months (younger = launch noise).")
@click.option("--max-age", default=18.0, show_default=True, help="Max age in months (older = crowded market).")
@click.option("--min-mrr", default=500.0, show_default=True, help="Minimum MRR gate (real recurring revenue).")
@click.option("--min-purity", default=0.35, show_default=True, help="Min recurring share of revenue (0-1).")
@click.option("--min-subs", default=10, show_default=True, help="Min subscribers, when the field is reported.")
@click.option("--max-pages", default=8, show_default=True, help="List pages to scan (50 startups/page).")
@click.option("--enrich", default=40, show_default=True,
              help="Deep-fetch detail data (stack, followers) for the top N candidates. ~3s each.")
@click.option("--category", default=None, help="Restrict to a TrustMRR category slug (e.g. ai, saas).")
@click.option("--top", default=40, show_default=True, help="Keep the top N clone targets in the output.")
@click.option("--output-dir", default="data/output", show_default=True, type=click.Path())
def clones(api_key, min_age, max_age, min_mrr, min_purity, min_subs, max_pages,
           enrich, category, top, output_dir):
    """Clone Score v2 — rank micro-SaaS by how attractive they are to REPLICATE.

    Two-stage: a wide scan gated on age window / MRR floor / subscription
    purity / subscriber count, then detail enrichment (tech stack, founder
    followers, search impressions) for the top candidates before final
    scoring: demand^0.40 x distribution^0.35 x simplicity^0.25.
    """
    try:
        client = TrustMRRClient(api_key=api_key)
    except TrustMRRError as exc:
        console.print(f"[red]✗ {exc}[/red]")
        sys.exit(1)

    console.print(
        f"[bold]Stage 1[/bold] — scanning up to {max_pages} pages, gates: "
        f"age [cyan]{min_age:g}–{max_age:g}mo[/cyan], MRR ≥ [cyan]${min_mrr:,.0f}[/cyan], "
        f"recurring ≥ [cyan]{min_purity:.0%}[/cyan], subs ≥ [cyan]{min_subs}[/cyan]…"
    )
    try:
        fetched = list(client.iter_startups(sort="revenue-desc", category=category, max_pages=max_pages))
    except TrustMRRError as exc:
        console.print(f"[red]✗ API error: {exc}[/red]")
        sys.exit(1)

    prelim = rank_clones(
        fetched, min_age=min_age, max_age=max_age, min_mrr=min_mrr,
        min_purity=min_purity, min_subs=min_subs,
    )
    console.print(f"  {len(fetched)} scanned → [bold]{len(prelim)}[/bold] pass the gates.")
    if not prelim:
        console.print("[yellow]Nothing passed. Loosen gates (--min-mrr, --min-purity) or scan more pages.[/yellow]")
        sys.exit(0)

    n_enrich = min(enrich, len(prelim))
    if n_enrich:
        eta = int(n_enrich * client.min_interval)
        console.print(f"[bold]Stage 2[/bold] — enriching top {n_enrich} with detail data (~{eta}s, rate-limited)…")
        try:
            results = enrich_and_rescore(prelim, client, top_n=n_enrich)
        except TrustMRRError as exc:
            console.print(f"[yellow]Enrichment aborted ({exc}); using preliminary scores.[/yellow]")
            results = prelim
    else:
        results = prelim
    results = results[:top]

    out = Path(output_dir)
    clone_report.save_html(results, out / "clones.html", min_age_months=min_age, max_age_months=max_age,
                           gems_href="gems.html")
    clone_report.save_json(results, out / "clones.json")
    clone_report.save_csv(results, out / "clones.csv")

    _print_clone_table(results[:15])
    console.print(
        f"\n[green]✓ Wrote {len(results)} clone targets[/green] → "
        f"[bold]{out / 'clones.html'}[/bold], clones.json, clones.csv"
    )


def _print_clone_table(results):
    table = Table(title="Top clone targets", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Score", justify="right", style="cyan")
    table.add_column("Startup", style="bold")
    table.add_column("Age", justify="right")
    table.add_column("MRR", justify="right", style="green")
    table.add_column("ARPU", justify="right")
    table.add_column("Dem", justify="right")
    table.add_column("Dist", justify="right")
    table.add_column("Simp", justify="right")
    table.add_column("Top flag")
    for i, r in enumerate(results, 1):
        s = r.startup
        arpu = f"${r.arpu:,.0f}" if r.arpu else "—"
        flag = r.flags[0] if r.flags else ""
        table.add_row(
            str(i), f"{r.clone_score:.0f}", s.name[:22], f"{r.age_months:g}mo",
            _money(s.revenue.mrr), arpu,
            f"{r.demand:.2f}", f"{r.distribution:.2f}", f"{r.simplicity:.2f}",
            flag[:46],
        )
    console.print(table)


def _print_table(gems):
    table = Table(title="Top gems", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Score", justify="right", style="magenta")
    table.add_column("Startup", style="bold")
    table.add_column("Cat")
    table.add_column("Age", justify="right")
    table.add_column("MRR", justify="right", style="green")
    table.add_column("Rev/mo", justify="right")
    table.add_column("30d gr.", justify="right")
    for i, g in enumerate(gems, 1):
        s = g.startup
        growth = "—" if s.growth30d is None else f"{s.growth30d:,.0f}%"
        table.add_row(
            str(i), f"{g.gem_score:.0f}", s.name, (s.category or "")[:14],
            f"{g.age_months:g}mo", _money(s.mrr), _money(g.revenue_velocity), growth,
        )
    console.print(table)


def main():
    cli()


if __name__ == "__main__":
    main()
