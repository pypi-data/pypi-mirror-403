"""Benchmark commands for AI agent benchmarking.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Initialize Rich console
console = Console()


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# Try relative imports first, fall back to absolute
try:
    from ..core import ops
    from ..benchmarks import BenchmarkRunner, BenchmarkConfig, BenchmarkReporter
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.benchmarks import BenchmarkRunner, BenchmarkConfig, BenchmarkReporter


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]✗ Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


# Benchmark sub-app
app = typer.Typer(
    help="AI agent benchmarking framework",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def _get_benchmark_paths():
    """Get paths for benchmarking."""
    root = repo_root()
    suite_path = root / ".paircoder" / "benchmarks" / "suite.yaml"
    output_dir = root / ".paircoder" / "history" / "benchmarks"
    return suite_path, output_dir


@app.command("run")
def benchmark_run(
    only: Optional[str] = typer.Option(None, "--only", help="Comma-separated benchmark IDs"),
    agents: Optional[str] = typer.Option(None, "--agents", "-a", help="Comma-separated agents to test"),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Number of iterations per benchmark"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would run without executing"),
):
    """Run benchmarks."""
    suite_path, output_dir = _get_benchmark_paths()

    if not suite_path.exists():
        console.print(f"[red]Benchmark suite not found: {suite_path}[/red]")
        console.print("[dim]Create .paircoder/benchmarks/suite.yaml to define benchmarks[/dim]")
        raise typer.Exit(1)

    config = BenchmarkConfig(
        iterations=iterations,
        agents=agents.split(",") if agents else ["claude-code"],
        dry_run=dry_run,
    )

    runner = BenchmarkRunner(suite_path, output_dir, config)

    benchmark_ids = only.split(",") if only else None

    console.print("[bold]Running benchmarks...[/bold]\n")

    results = runner.run(
        benchmark_ids=benchmark_ids,
        agents=config.agents,
        iterations=iterations,
    )

    # Show summary
    for bench_id in set(r.benchmark_id for r in results):
        bench_results = [r for r in results if r.benchmark_id == bench_id]
        console.print(f"\n{bench_id}:")
        for agent in config.agents:
            agent_results = [r for r in bench_results if r.agent == agent]
            passed = sum(1 for r in agent_results if r.success)
            total = len(agent_results)
            avg_duration = sum(r.duration_seconds for r in agent_results) / total if total else 0
            avg_cost = sum(r.cost_usd for r in agent_results) / total if total else 0

            status = "✓" * passed + "✗" * (total - passed)
            console.print(f"  {agent}: {status} ({passed}/{total}, avg {avg_duration:.1f}s, ${avg_cost:.4f})")

    # Overall summary
    total = len(results)
    passed = sum(1 for r in results if r.success)
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total: {total} runs")
    console.print(f"  Passed: {passed} ({passed/total*100:.1f}%)")


@app.command("results")
def benchmark_results(
    run_id: Optional[str] = typer.Option(None, "--id", help="Specific run ID"),
    latest: bool = typer.Option(True, "--latest", help="Show latest results"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """View benchmark results."""
    _, output_dir = _get_benchmark_paths()

    reporter = BenchmarkReporter(output_dir)
    results = reporter.load_results(run_id if not latest else None)

    if not results:
        console.print("[dim]No benchmark results found[/dim]")
        return

    if json_out:
        print_json([r.to_dict() for r in results])
    else:
        console.print(reporter.format_summary(results))


@app.command("compare")
def benchmark_compare(
    baseline: str = typer.Option(..., "--baseline", "-b", help="Baseline agent"),
    challenger: str = typer.Option(..., "--challenger", "-c", help="Challenger agent"),
    run_id: Optional[str] = typer.Option(None, "--id", help="Specific run ID"),
):
    """Compare two agents."""
    _, output_dir = _get_benchmark_paths()

    reporter = BenchmarkReporter(output_dir)
    results = reporter.load_results(run_id)

    if not results:
        console.print("[dim]No benchmark results found[/dim]")
        return

    comparison = reporter.compare_agents(results, baseline, challenger)
    console.print(reporter.format_comparison(comparison))


@app.command("list")
def benchmark_list():
    """List available benchmarks."""
    suite_path, _ = _get_benchmark_paths()

    if not suite_path.exists():
        console.print("[dim]No benchmark suite found[/dim]")
        console.print(f"[dim]Create {suite_path} to define benchmarks[/dim]")
        return

    try:
        from ..benchmarks.runner import BenchmarkSuite
    except ImportError:
        from bpsai_pair.benchmarks.runner import BenchmarkSuite

    suite = BenchmarkSuite.from_yaml(suite_path)

    table = Table(title="Available Benchmarks")
    table.add_column("ID", style="cyan")
    table.add_column("Category")
    table.add_column("Complexity")
    table.add_column("Description")

    for bench_id, bench in suite.benchmarks.items():
        table.add_row(
            bench_id,
            bench.category,
            bench.complexity,
            bench.description[:40] + "..." if len(bench.description) > 40 else bench.description,
        )

    console.print(table)
