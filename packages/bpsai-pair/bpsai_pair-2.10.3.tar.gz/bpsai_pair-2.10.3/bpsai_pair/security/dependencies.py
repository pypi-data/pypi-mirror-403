"""Dependency vulnerability scanning for PairCoder.

This module provides:
- DependencyScanner: Scans project dependencies for known CVEs
- Vulnerability: Data class for detected vulnerabilities
- ScanReport: Aggregated scan results with severity analysis
"""

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
import hashlib


class Severity(Enum):
    """Vulnerability severity levels."""
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum."""
        value_lower = value.lower()
        for severity in cls:
            if severity.value == value_lower:
                return severity
        return cls.UNKNOWN

    def __lt__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        order = [self.UNKNOWN, self.LOW, self.MEDIUM, self.HIGH, self.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: "Severity") -> bool:
        return self == other or self < other


@dataclass
class Vulnerability:
    """A detected vulnerability in a dependency.

    Attributes:
        package: Name of the vulnerable package
        version: Installed version of the package
        cve_id: CVE identifier (e.g., CVE-2021-12345)
        severity: Severity level (low, medium, high, critical)
        description: Human-readable description of the vulnerability
        fixed_version: Version that fixes the vulnerability (if known)
        source: Source of the vulnerability report (pip-audit, npm-audit)
    """
    package: str
    version: str
    cve_id: str
    severity: Severity
    description: str
    fixed_version: Optional[str] = None
    source: str = "unknown"

    def format(self) -> str:
        """Format vulnerability for display."""
        fix_info = f" (fix: {self.fixed_version})" if self.fixed_version else ""
        return (
            f"[{self.severity.value.upper()}] {self.package}@{self.version}: "
            f"{self.cve_id}{fix_info}"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "package": self.package,
            "version": self.version,
            "cve_id": self.cve_id,
            "severity": self.severity.value,
            "description": self.description,
            "fixed_version": self.fixed_version,
            "source": self.source,
        }


@dataclass
class ScanReport:
    """Aggregated vulnerability scan results.

    Attributes:
        vulnerabilities: List of detected vulnerabilities
        scanned_at: Timestamp of the scan
        packages_scanned: Number of packages scanned
        scan_duration: Duration of scan in seconds
        errors: Any errors encountered during scanning
    """
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    scanned_at: datetime = field(default_factory=datetime.now)
    packages_scanned: int = 0
    scan_duration: float = 0.0
    errors: list[str] = field(default_factory=list)

    def has_critical(self) -> bool:
        """Check if any critical vulnerabilities were found."""
        return any(v.severity == Severity.CRITICAL for v in self.vulnerabilities)

    def has_high_or_above(self) -> bool:
        """Check if any high or critical vulnerabilities were found."""
        return any(v.severity >= Severity.HIGH for v in self.vulnerabilities)

    def has_severity(self, min_severity: Severity) -> bool:
        """Check if any vulnerabilities meet or exceed the given severity."""
        return any(v.severity >= min_severity for v in self.vulnerabilities)

    def count_by_severity(self) -> dict[str, int]:
        """Count vulnerabilities by severity level."""
        counts: dict[str, int] = {}
        for vuln in self.vulnerabilities:
            key = vuln.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "scanned_at": self.scanned_at.isoformat(),
            "packages_scanned": self.packages_scanned,
            "scan_duration": self.scan_duration,
            "errors": self.errors,
            "summary": {
                "total": len(self.vulnerabilities),
                "by_severity": self.count_by_severity(),
                "has_critical": self.has_critical(),
                "has_high": self.has_high_or_above(),
            }
        }

    def format(self, verbose: bool = False) -> str:
        """Format report for display."""
        lines = []

        if not self.vulnerabilities:
            lines.append("No vulnerabilities found.")
            lines.append(f"Scanned {self.packages_scanned} packages in {self.scan_duration:.2f}s")
            return "\n".join(lines)

        lines.append(f"Found {len(self.vulnerabilities)} vulnerabilities:")
        lines.append("")

        # Group by severity
        by_severity: dict[Severity, list[Vulnerability]] = {}
        for vuln in self.vulnerabilities:
            by_severity.setdefault(vuln.severity, []).append(vuln)

        # Display in severity order (critical first)
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            if severity not in by_severity:
                continue
            vulns = by_severity[severity]
            lines.append(f"### {severity.value.upper()} ({len(vulns)})")
            for vuln in vulns:
                if verbose:
                    lines.append(f"  {vuln.package}@{vuln.version}")
                    lines.append(f"    CVE: {vuln.cve_id}")
                    lines.append(f"    {vuln.description[:100]}...")
                    if vuln.fixed_version:
                        lines.append(f"    Fix: upgrade to {vuln.fixed_version}")
                else:
                    lines.append(f"  {vuln.format()}")
            lines.append("")

        lines.append(f"Scanned {self.packages_scanned} packages in {self.scan_duration:.2f}s")

        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  - {error}")

        return "\n".join(lines)


class DependencyScanner:
    """Scans project dependencies for known vulnerabilities.

    Supports:
    - Python: pip-audit for requirements.txt, pyproject.toml
    - Node.js: npm audit for package.json

    Attributes:
        cache_dir: Directory for caching scan results
        cache_ttl: Cache time-to-live in seconds (default 1 hour)
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 3600,
    ):
        """Initialize dependency scanner.

        Args:
            cache_dir: Directory for caching scan results
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "paircoder" / "vuln-scans"
        self.cache_ttl = cache_ttl

    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key for a dependency file."""
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]

    def _get_cached_result(self, file_path: Path) -> Optional[list[Vulnerability]]:
        """Get cached scan result if still valid."""
        if not self.cache_dir.exists():
            return None

        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # Check if cache is still valid
        cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
        if cache_age > self.cache_ttl:
            cache_file.unlink()
            return None

        try:
            with open(cache_file, encoding='utf-8') as f:
                data = json.load(f)
            return [
                Vulnerability(
                    package=v["package"],
                    version=v["version"],
                    cve_id=v["cve_id"],
                    severity=Severity.from_string(v["severity"]),
                    description=v["description"],
                    fixed_version=v.get("fixed_version"),
                    source=v.get("source", "cache"),
                )
                for v in data
            ]
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_to_cache(self, file_path: Path, vulnerabilities: list[Vulnerability]):
        """Save scan result to cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump([v.to_dict() for v in vulnerabilities], f)

    def scan_python(
        self,
        requirements: Path,
        use_cache: bool = True,
    ) -> tuple[list[Vulnerability], list[str]]:
        """Scan Python dependencies using pip-audit.

        Args:
            requirements: Path to requirements.txt or pyproject.toml
            use_cache: Whether to use cached results

        Returns:
            Tuple of (vulnerabilities, errors)
        """
        vulnerabilities = []
        errors = []

        # Check cache
        if use_cache:
            cached = self._get_cached_result(requirements)
            if cached is not None:
                return cached, []

        # Check if pip-audit is available
        try:
            subprocess.run(
                ["pip-audit", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("pip-audit not installed. Install with: pip install pip-audit")
            return vulnerabilities, errors

        # Determine file type and build command
        if requirements.suffix == ".toml":
            # For pyproject.toml, we need to scan the current environment
            cmd = ["pip-audit", "--format", "json", "--progress-spinner", "off"]
        else:
            cmd = ["pip-audit", "-r", str(requirements), "--format", "json", "--progress-spinner", "off"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # pip-audit returns non-zero if vulnerabilities found
            if result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = self._parse_pip_audit(data)

            if result.stderr and "error" in result.stderr.lower():
                errors.append(result.stderr.strip())

        except subprocess.TimeoutExpired:
            errors.append("pip-audit scan timed out")
        except json.JSONDecodeError:
            errors.append("Failed to parse pip-audit output")
        except Exception as e:
            errors.append(f"pip-audit error: {str(e)}")

        # Cache results
        if use_cache and not errors:
            self._save_to_cache(requirements, vulnerabilities)

        return vulnerabilities, errors

    def _parse_pip_audit(self, data: dict | list) -> list[Vulnerability]:
        """Parse pip-audit JSON output.

        Args:
            data: Parsed JSON from pip-audit

        Returns:
            List of Vulnerability objects
        """
        vulnerabilities = []

        # Handle different pip-audit output formats
        if isinstance(data, dict):
            # Newer format: {"dependencies": [...]}
            deps = data.get("dependencies", [])
        else:
            # Older format: direct list
            deps = data

        for dep in deps:
            package = dep.get("name", "")
            version = dep.get("version", "")
            vulns = dep.get("vulns", [])

            for vuln in vulns:
                vuln_id = vuln.get("id", "")
                # pip-audit uses "id" which can be CVE, GHSA, or PYSEC
                if not vuln_id.startswith("CVE"):
                    # Try to get aliases
                    aliases = vuln.get("aliases", [])
                    cve_id = next((a for a in aliases if a.startswith("CVE")), vuln_id)
                else:
                    cve_id = vuln_id

                # Determine severity from fix availability or description
                fix_versions = vuln.get("fix_versions", [])
                fixed_version = fix_versions[0] if fix_versions else None

                # pip-audit doesn't always provide severity, default to HIGH
                severity_str = vuln.get("severity", "high")
                severity = Severity.from_string(severity_str)

                vulnerabilities.append(Vulnerability(
                    package=package,
                    version=version,
                    cve_id=cve_id,
                    severity=severity,
                    description=vuln.get("description", "No description available"),
                    fixed_version=fixed_version,
                    source="pip-audit",
                ))

        return vulnerabilities

    def scan_npm(
        self,
        package_json: Path,
        use_cache: bool = True,
    ) -> tuple[list[Vulnerability], list[str]]:
        """Scan npm dependencies using npm audit.

        Args:
            package_json: Path to package.json
            use_cache: Whether to use cached results

        Returns:
            Tuple of (vulnerabilities, errors)
        """
        vulnerabilities = []
        errors = []

        # Check cache
        if use_cache:
            cached = self._get_cached_result(package_json)
            if cached is not None:
                return cached, []

        # Check if npm is available
        try:
            subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            errors.append("npm not installed or not in PATH")
            return vulnerabilities, errors

        # Check if node_modules exists
        node_modules = package_json.parent / "node_modules"
        if not node_modules.exists():
            errors.append("node_modules not found. Run 'npm install' first.")
            return vulnerabilities, errors

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=package_json.parent,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = self._parse_npm_audit(data)

        except subprocess.TimeoutExpired:
            errors.append("npm audit scan timed out")
        except json.JSONDecodeError:
            errors.append("Failed to parse npm audit output")
        except Exception as e:
            errors.append(f"npm audit error: {str(e)}")

        # Cache results
        if use_cache and not errors:
            self._save_to_cache(package_json, vulnerabilities)

        return vulnerabilities, errors

    def _parse_npm_audit(self, data: dict) -> list[Vulnerability]:
        """Parse npm audit JSON output.

        Args:
            data: Parsed JSON from npm audit

        Returns:
            List of Vulnerability objects
        """
        vulnerabilities = []

        # npm audit v7+ format
        vulns_dict = data.get("vulnerabilities", {})

        for package_name, vuln_info in vulns_dict.items():
            severity_str = vuln_info.get("severity", "unknown")
            severity = Severity.from_string(severity_str)

            # Get via chain (which versions are affected)
            via = vuln_info.get("via", [])

            # Via can be a list of vulnerability objects or package names
            for via_item in via:
                if isinstance(via_item, dict):
                    # Direct vulnerability
                    cve_id = via_item.get("url", "").split("/")[-1] if via_item.get("url") else "N/A"
                    if not cve_id.startswith(("CVE", "GHSA")):
                        cve_id = f"NPM:{via_item.get('source', 'unknown')}"

                    vulnerabilities.append(Vulnerability(
                        package=package_name,
                        version=vuln_info.get("range", "unknown"),
                        cve_id=cve_id,
                        severity=severity,
                        description=via_item.get("title", "No description available"),
                        fixed_version=vuln_info.get("fixAvailable", {}).get("version") if isinstance(vuln_info.get("fixAvailable"), dict) else None,
                        source="npm-audit",
                    ))

        return vulnerabilities

    def scan_all(
        self,
        root_dir: Optional[Path] = None,
        use_cache: bool = True,
    ) -> ScanReport:
        """Scan all detected dependency files.

        Args:
            root_dir: Root directory to search for dependency files
            use_cache: Whether to use cached results

        Returns:
            Aggregated scan report
        """
        import time

        start_time = time.time()
        root_dir = root_dir or Path.cwd()

        all_vulns: list[Vulnerability] = []
        all_errors: list[str] = []
        packages_scanned = 0

        # Scan Python dependencies
        for req_file in self._find_python_deps(root_dir):
            vulns, errors = self.scan_python(req_file, use_cache=use_cache)
            all_vulns.extend(vulns)
            all_errors.extend(errors)
            packages_scanned += self._count_python_packages(req_file)

        # Scan npm dependencies
        for pkg_file in self._find_npm_deps(root_dir):
            vulns, errors = self.scan_npm(pkg_file, use_cache=use_cache)
            all_vulns.extend(vulns)
            all_errors.extend(errors)
            packages_scanned += self._count_npm_packages(pkg_file)

        scan_duration = time.time() - start_time

        return ScanReport(
            vulnerabilities=all_vulns,
            scanned_at=datetime.now(),
            packages_scanned=packages_scanned,
            scan_duration=scan_duration,
            errors=all_errors,
        )

    def _find_python_deps(self, root_dir: Path) -> list[Path]:
        """Find Python dependency files."""
        files = []

        # Look for requirements.txt variants
        for pattern in ["requirements*.txt", "requirements/*.txt"]:
            files.extend(root_dir.glob(pattern))

        # Look for pyproject.toml
        pyproject = root_dir / "pyproject.toml"
        if pyproject.exists():
            files.append(pyproject)

        return files

    def _find_npm_deps(self, root_dir: Path) -> list[Path]:
        """Find npm dependency files."""
        files = []

        # Look for package.json (not in node_modules)
        for pkg_json in root_dir.glob("**/package.json"):
            if "node_modules" not in str(pkg_json):
                files.append(pkg_json)

        return files

    def _count_python_packages(self, req_file: Path) -> int:
        """Count packages in Python requirements file."""
        try:
            if req_file.suffix == ".toml":
                # Count from pyproject.toml
                content = req_file.read_text(encoding="utf-8")
                # Simple heuristic: count lines with package specs
                return len([l for l in content.split("\n") if "=" in l and not l.strip().startswith("#")])
            else:
                # Count from requirements.txt
                content = req_file.read_text(encoding="utf-8")
                return len([l for l in content.split("\n") if l.strip() and not l.strip().startswith("#")])
        except Exception:
            return 0

    def _count_npm_packages(self, pkg_file: Path) -> int:
        """Count packages in package.json."""
        try:
            data = json.loads(pkg_file.read_text(encoding="utf-8"))
            deps = len(data.get("dependencies", {}))
            dev_deps = len(data.get("devDependencies", {}))
            return deps + dev_deps
        except Exception:
            return 0


def format_scan_report(report: ScanReport, verbose: bool = False) -> str:
    """Format scan report for display.

    Args:
        report: The scan report to format
        verbose: Whether to show detailed output

    Returns:
        Formatted string for display
    """
    return report.format(verbose=verbose)
