"""Benchmark runner for AI agent performance testing."""

import json
import shutil
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import subprocess

import yaml

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkTask:
    """Definition of a benchmark task."""
    id: str
    description: str
    category: str  # fix, implement, design, refactor
    complexity: str  # low, medium, high
    prompt: str
    setup: List[Dict[str, str]] = field(default_factory=list)
    validation: List[Dict[str, str]] = field(default_factory=list)
    expected_files: List[str] = field(default_factory=list)
    timeout_seconds: int = 300

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "BenchmarkTask":
        return cls(
            id=id,
            description=data.get("description", ""),
            category=data.get("category", "implement"),
            complexity=data.get("complexity", "medium"),
            prompt=data.get("prompt", ""),
            setup=data.get("setup", []),
            validation=data.get("validation", []),
            expected_files=data.get("expected_files", []),
            timeout_seconds=data.get("timeout_seconds", 300),
        )


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    benchmark_id: str
    agent: str
    model: str
    iteration: int
    timestamp: str
    success: bool
    validation_passed: List[str] = field(default_factory=list)
    validation_failed: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    files_modified: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkResult":
        return cls(**data)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark tasks."""
    benchmarks: Dict[str, BenchmarkTask]
    name: str = "default"
    description: str = ""

    @classmethod
    def from_yaml(cls, path: Path) -> "BenchmarkSuite":
        """Load benchmark suite from YAML file."""
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        benchmarks = {}
        for bench_id, bench_data in data.get("benchmarks", {}).items():
            benchmarks[bench_id] = BenchmarkTask.from_dict(bench_id, bench_data)

        return cls(
            benchmarks=benchmarks,
            name=data.get("name", path.stem),
            description=data.get("description", ""),
        )


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""
    iterations: int = 3
    agents: List[str] = field(default_factory=lambda: ["claude-code"])
    timeout_seconds: int = 300
    save_logs: bool = True
    dry_run: bool = False


class BenchmarkRunner:
    """Runs benchmarks across agents."""

    def __init__(self, suite_path: Path, output_dir: Path, config: Optional[BenchmarkConfig] = None):
        self.suite = BenchmarkSuite.from_yaml(suite_path) if suite_path.exists() else BenchmarkSuite({})
        self.output_dir = output_dir
        self.config = config or BenchmarkConfig()
        self.fixtures_dir = suite_path.parent / "fixtures" if suite_path.exists() else None

    def run(self, benchmark_ids: Optional[List[str]] = None,
            agents: Optional[List[str]] = None,
            iterations: Optional[int] = None) -> List[BenchmarkResult]:
        """Run benchmarks across agents with multiple iterations."""
        benchmark_ids = benchmark_ids or list(self.suite.benchmarks.keys())
        agents = agents or self.config.agents
        iterations = iterations or self.config.iterations

        results = []
        run_id = f"bench-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
        run_dir = self.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save run config
        config_data = {
            "run_id": run_id,
            "started_at": datetime.now().isoformat(),
            "benchmarks": benchmark_ids,
            "agents": agents,
            "iterations": iterations,
        }
        (run_dir / "config.yaml").write_text(yaml.dump(config_data), encoding="utf-8")

        for bench_id in benchmark_ids:
            if bench_id not in self.suite.benchmarks:
                logger.warning(f"Benchmark not found: {bench_id}")
                continue

            benchmark = self.suite.benchmarks[bench_id]

            for agent in agents:
                for i in range(iterations):
                    logger.info(f"Running {bench_id} with {agent} (iteration {i+1}/{iterations})")

                    if self.config.dry_run:
                        result = BenchmarkResult(
                            benchmark_id=bench_id,
                            agent=agent,
                            model="dry-run",
                            iteration=i,
                            timestamp=datetime.now().isoformat(),
                            success=True,
                        )
                    else:
                        result = self._run_single(benchmark, agent, i, run_dir)

                    results.append(result)

        # Save results
        self._save_results(run_dir, results)

        return results

    def _run_single(self, benchmark: BenchmarkTask, agent: str,
                    iteration: int, run_dir: Path) -> BenchmarkResult:
        """Run a single benchmark iteration."""
        # Create isolated workspace
        workspace = Path(tempfile.mkdtemp(prefix=f"bench-{benchmark.id}-"))

        try:
            # Setup workspace
            self._setup_workspace(benchmark, workspace)

            # Execute benchmark
            start_time = time.time()
            execution = self._execute(agent, benchmark.prompt, workspace, benchmark.timeout_seconds)
            duration = time.time() - start_time

            # Validate results
            from .validation import BenchmarkValidator
            validator = BenchmarkValidator(workspace)
            validation = validator.validate(benchmark.validation)

            # Collect modified files
            files_modified = self._get_modified_files(workspace)

            # Save log if enabled
            if self.config.save_logs:
                log_path = run_dir / "logs" / f"{benchmark.id}-{agent}-{iteration}.log"
                log_path.parent.mkdir(exist_ok=True)
                log_path.write_text(execution.get("output", ""), encoding="utf-8")

            return BenchmarkResult(
                benchmark_id=benchmark.id,
                agent=agent,
                model=execution.get("model", "unknown"),
                iteration=iteration,
                timestamp=datetime.now().isoformat(),
                success=validation.passed,
                validation_passed=validation.passed_checks,
                validation_failed=validation.failed_checks,
                duration_seconds=duration,
                tokens_input=execution.get("tokens_input", 0),
                tokens_output=execution.get("tokens_output", 0),
                cost_usd=execution.get("cost_usd", 0.0),
                files_modified=files_modified,
                error=execution.get("error"),
            )

        except Exception as e:
            logger.error(f"Benchmark {benchmark.id} failed: {e}")
            return BenchmarkResult(
                benchmark_id=benchmark.id,
                agent=agent,
                model="unknown",
                iteration=iteration,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=str(e),
            )

        finally:
            # Cleanup workspace
            shutil.rmtree(workspace, ignore_errors=True)

    def _setup_workspace(self, benchmark: BenchmarkTask, workspace: Path) -> None:
        """Setup workspace for benchmark."""
        for setup_item in benchmark.setup:
            if "copy" in setup_item:
                src = self.fixtures_dir / setup_item["copy"] if self.fixtures_dir else None
                if src and src.exists():
                    if src.is_dir():
                        shutil.copytree(src, workspace, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, workspace)
            elif "create" in setup_item:
                path = workspace / setup_item["create"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(setup_item.get("content", ""), encoding="utf-8")

    def _execute(self, agent: str, prompt: str, workspace: Path,
                 timeout: int) -> Dict[str, Any]:
        """Execute the benchmark with the specified agent."""
        if agent == "claude-code":
            return self._execute_claude_code(prompt, workspace, timeout)
        elif agent == "codex-cli":
            return self._execute_codex(prompt, workspace, timeout)
        else:
            return {"error": f"Unknown agent: {agent}"}

    def _execute_claude_code(self, prompt: str, workspace: Path,
                             timeout: int) -> Dict[str, Any]:
        """Execute with Claude Code CLI."""
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "json", "--no-input"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    return {
                        "output": result.stdout,
                        "model": data.get("model", "claude-code"),
                        "tokens_input": data.get("tokens", {}).get("input", 0),
                        "tokens_output": data.get("tokens", {}).get("output", 0),
                        "cost_usd": data.get("cost_usd", 0.0),
                    }
                except json.JSONDecodeError:
                    return {"output": result.stdout, "model": "claude-code"}
            else:
                return {"error": result.stderr, "output": result.stdout}

        except subprocess.TimeoutExpired:
            return {"error": f"Timeout after {timeout}s"}
        except FileNotFoundError:
            return {"error": "claude CLI not found"}

    def _execute_codex(self, prompt: str, workspace: Path,
                       timeout: int) -> Dict[str, Any]:
        """Execute with Codex CLI."""
        try:
            result = subprocess.run(
                ["codex", "--approval-mode", "full-auto", prompt],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "output": result.stdout,
                "model": "codex-cli",
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {"error": f"Timeout after {timeout}s"}
        except FileNotFoundError:
            return {"error": "codex CLI not found"}

    def _get_modified_files(self, workspace: Path) -> List[str]:
        """Get list of files in workspace."""
        files = []
        for path in workspace.rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                files.append(str(path.relative_to(workspace)))
        return files

    def _save_results(self, run_dir: Path, results: List[BenchmarkResult]) -> None:
        """Save benchmark results."""
        # JSONL format for raw results
        results_path = run_dir / "results.jsonl"
        with open(results_path, "w", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result.to_dict()) + "\n")

        # Summary JSON
        summary = self._compute_summary(results)
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def _compute_summary(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Compute summary statistics from results."""
        if not results:
            return {"total": 0}

        total = len(results)
        passed = sum(1 for r in results if r.success)
        total_cost = sum(r.cost_usd for r in results)
        total_duration = sum(r.duration_seconds for r in results)

        by_agent: Dict[str, Dict[str, Any]] = {}
        for result in results:
            if result.agent not in by_agent:
                by_agent[result.agent] = {
                    "total": 0,
                    "passed": 0,
                    "cost_usd": 0.0,
                    "duration_seconds": 0.0,
                }
            by_agent[result.agent]["total"] += 1
            by_agent[result.agent]["passed"] += 1 if result.success else 0
            by_agent[result.agent]["cost_usd"] += result.cost_usd
            by_agent[result.agent]["duration_seconds"] += result.duration_seconds

        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": passed / total if total > 0 else 0,
            "total_cost_usd": total_cost,
            "total_duration_seconds": total_duration,
            "by_agent": by_agent,
        }
