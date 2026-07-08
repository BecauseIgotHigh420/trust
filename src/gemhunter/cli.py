"""Command-line interface for GemHunter.

Examples:
    export TRUSTMRR_API_KEY=tmrr_xxx
    gemhunter run                              # top gems from last 6 months -> HTML/JSON/CSV
    gemhunter run --months 3 --max-pages 10    # tighter window, scan deeper
    gemhunter run --sort growth-desc           # seed the scan from fastest growers
    gemhunter run --category ai --min-mrr 500
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .client import TrustMRRClient, TrustMRRError, VALID_SORTS
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
