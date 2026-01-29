"""Benchmark reporting and comparison utilities."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

from .runner import BenchmarkResult


@dataclass
class AgentStats:
    """Statistics for an agent across benchmarks."""
    agent: str
    total_runs: int = 0
    successful_runs: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float = 0.0
    avg_cost_usd: float = 0.0
    total_tokens: int = 0


@dataclass
class BenchmarkComparison:
    """Comparison between agents."""
    baseline: str
    challenger: str
    baseline_stats: AgentStats
    challenger_stats: AgentStats
    winner_success: str
    winner_speed: str
    winner_cost: str
    recommendations: List[str] = field(default_factory=list)


class BenchmarkReporter:
    """Generates reports from benchmark results."""

    def __init__(self, results_dir: Path):
        self.results_dir = results_dir

    def load_results(self, run_id: Optional[str] = None) -> List[BenchmarkResult]:
        """Load results from a benchmark run."""
        if run_id:
            run_dir = self.results_dir / run_id
        else:
            # Get latest run
            runs = sorted(self.results_dir.glob("bench-*"))
            if not runs:
                return []
            run_dir = runs[-1]

        results_file = run_dir / "results.jsonl"
        if not results_file.exists():
            return []

        results = []
        with open(results_file, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    results.append(BenchmarkResult.from_dict(json.loads(line)))

        return results

    def get_agent_stats(self, results: List[BenchmarkResult], agent: str) -> AgentStats:
        """Calculate statistics for an agent."""
        agent_results = [r for r in results if r.agent == agent]

        if not agent_results:
            return AgentStats(agent=agent)

        total = len(agent_results)
        successful = sum(1 for r in agent_results if r.success)
        total_duration = sum(r.duration_seconds for r in agent_results)
        total_cost = sum(r.cost_usd for r in agent_results)
        total_tokens = sum(r.tokens_input + r.tokens_output for r in agent_results)

        return AgentStats(
            agent=agent,
            total_runs=total,
            successful_runs=successful,
            success_rate=successful / total if total > 0 else 0,
            avg_duration_seconds=total_duration / total if total > 0 else 0,
            avg_cost_usd=total_cost / total if total > 0 else 0,
            total_tokens=total_tokens,
        )

    def compare_agents(self, results: List[BenchmarkResult],
                       baseline: str, challenger: str) -> BenchmarkComparison:
        """Compare two agents."""
        baseline_stats = self.get_agent_stats(results, baseline)
        challenger_stats = self.get_agent_stats(results, challenger)

        # Determine winners
        winner_success = baseline if baseline_stats.success_rate >= challenger_stats.success_rate else challenger
        winner_speed = baseline if baseline_stats.avg_duration_seconds <= challenger_stats.avg_duration_seconds else challenger
        winner_cost = baseline if baseline_stats.avg_cost_usd <= challenger_stats.avg_cost_usd else challenger

        # Generate recommendations
        recommendations = []

        if baseline_stats.success_rate > challenger_stats.success_rate:
            diff = (baseline_stats.success_rate - challenger_stats.success_rate) * 100
            recommendations.append(f"Use {baseline} for higher success rate ({diff:.1f}% better)")
        elif challenger_stats.success_rate > baseline_stats.success_rate:
            diff = (challenger_stats.success_rate - baseline_stats.success_rate) * 100
            recommendations.append(f"Use {challenger} for higher success rate ({diff:.1f}% better)")

        if baseline_stats.avg_duration_seconds < challenger_stats.avg_duration_seconds:
            diff = challenger_stats.avg_duration_seconds - baseline_stats.avg_duration_seconds
            recommendations.append(f"Use {baseline} for faster execution ({diff:.1f}s faster)")
        elif challenger_stats.avg_duration_seconds < baseline_stats.avg_duration_seconds:
            diff = baseline_stats.avg_duration_seconds - challenger_stats.avg_duration_seconds
            recommendations.append(f"Use {challenger} for faster execution ({diff:.1f}s faster)")

        if baseline_stats.avg_cost_usd < challenger_stats.avg_cost_usd:
            diff = challenger_stats.avg_cost_usd - baseline_stats.avg_cost_usd
            recommendations.append(f"Use {baseline} for lower cost (${diff:.4f} cheaper)")
        elif challenger_stats.avg_cost_usd < baseline_stats.avg_cost_usd:
            diff = baseline_stats.avg_cost_usd - challenger_stats.avg_cost_usd
            recommendations.append(f"Use {challenger} for lower cost (${diff:.4f} cheaper)")

        return BenchmarkComparison(
            baseline=baseline,
            challenger=challenger,
            baseline_stats=baseline_stats,
            challenger_stats=challenger_stats,
            winner_success=winner_success,
            winner_speed=winner_speed,
            winner_cost=winner_cost,
            recommendations=recommendations,
        )

    def get_by_category(self, results: List[BenchmarkResult]) -> Dict[str, Dict[str, AgentStats]]:
        """Get stats grouped by benchmark category."""
        # First group results by benchmark
        by_benchmark: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        for r in results:
            by_benchmark[r.benchmark_id].append(r)

        # Would need benchmark metadata for categories
        # For now, infer from benchmark_id naming
        categories: Dict[str, Dict[str, List[BenchmarkResult]]] = defaultdict(lambda: defaultdict(list))

        for bench_id, bench_results in by_benchmark.items():
            # Infer category from benchmark name
            if "fix" in bench_id.lower() or "bug" in bench_id.lower():
                category = "fix"
            elif "implement" in bench_id.lower() or "feature" in bench_id.lower():
                category = "implement"
            elif "design" in bench_id.lower() or "architect" in bench_id.lower():
                category = "design"
            elif "refactor" in bench_id.lower():
                category = "refactor"
            else:
                category = "other"

            for r in bench_results:
                categories[category][r.agent].append(r)

        # Calculate stats per category per agent
        result: Dict[str, Dict[str, AgentStats]] = {}
        for category, agents in categories.items():
            result[category] = {}
            for agent, agent_results in agents.items():
                result[category][agent] = self.get_agent_stats(agent_results, agent)

        return result

    def format_summary(self, results: List[BenchmarkResult]) -> str:
        """Format results as human-readable summary."""
        if not results:
            return "No results found."

        lines = [
            "Benchmark Results Summary",
            "=" * 50,
            "",
        ]

        # Overall stats
        total = len(results)
        passed = sum(1 for r in results if r.success)
        total_duration = sum(r.duration_seconds for r in results)
        total_cost = sum(r.cost_usd for r in results)

        lines.extend([
            f"Total Runs:    {total}",
            f"Passed:        {passed} ({passed/total*100:.1f}%)",
            f"Failed:        {total - passed}",
            f"Total Time:    {total_duration:.1f}s",
            f"Total Cost:    ${total_cost:.4f}",
            "",
        ])

        # By agent
        agents = set(r.agent for r in results)
        if len(agents) > 1:
            lines.append("By Agent:")
            for agent in sorted(agents):
                stats = self.get_agent_stats(results, agent)
                lines.append(
                    f"  {agent}: {stats.success_rate*100:.1f}% success, "
                    f"avg {stats.avg_duration_seconds:.1f}s, "
                    f"avg ${stats.avg_cost_usd:.4f}"
                )
            lines.append("")

        # By benchmark
        benchmarks = set(r.benchmark_id for r in results)
        lines.append("By Benchmark:")
        for bench in sorted(benchmarks):
            bench_results = [r for r in results if r.benchmark_id == bench]
            passed = sum(1 for r in bench_results if r.success)
            total = len(bench_results)
            lines.append(f"  {bench}: {passed}/{total} passed")

        return "\n".join(lines)

    def format_comparison(self, comparison: BenchmarkComparison) -> str:
        """Format comparison as human-readable report."""
        lines = [
            f"Agent Comparison: {comparison.baseline} vs {comparison.challenger}",
            "=" * 60,
            "",
            f"{'Metric':<20} {comparison.baseline:<15} {comparison.challenger:<15} {'Winner'}",
            "-" * 60,
        ]

        # Success rate
        lines.append(
            f"{'Success Rate':<20} "
            f"{comparison.baseline_stats.success_rate*100:.1f}%{' '*10} "
            f"{comparison.challenger_stats.success_rate*100:.1f}%{' '*10} "
            f"{comparison.winner_success}"
        )

        # Duration
        lines.append(
            f"{'Avg Duration':<20} "
            f"{comparison.baseline_stats.avg_duration_seconds:.1f}s{' '*11} "
            f"{comparison.challenger_stats.avg_duration_seconds:.1f}s{' '*11} "
            f"{comparison.winner_speed}"
        )

        # Cost
        lines.append(
            f"{'Avg Cost':<20} "
            f"${comparison.baseline_stats.avg_cost_usd:.4f}{' '*8} "
            f"${comparison.challenger_stats.avg_cost_usd:.4f}{' '*8} "
            f"{comparison.winner_cost}"
        )

        lines.extend(["", "Recommendations:"])
        for rec in comparison.recommendations:
            lines.append(f"  - {rec}")

        return "\n".join(lines)
