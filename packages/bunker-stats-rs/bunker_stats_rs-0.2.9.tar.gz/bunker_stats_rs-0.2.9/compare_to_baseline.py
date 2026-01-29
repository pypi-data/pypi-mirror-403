#!/usr/bin/env python3
"""
Baseline Comparison Script - Detect Regressions

Compares current state against saved baseline to detect:
- Test regressions (passing -> failing)
- Performance regressions
- New failures
- Missing tests

Usage:
    python compare_to_baseline.py                        # Compare to latest baseline
    python compare_to_baseline.py --baseline FILE        # Compare to specific baseline
    python compare_to_baseline.py --fail-on-regression   # Exit 1 if regressions found
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False


class BaselineComparator:
    """Compares current state against baseline."""
    
    def __init__(self, baseline_file: Path):
        self.baseline_file = baseline_file
        with open(baseline_file) as f:
            self.baseline = json.load(f)
    
    def run_current_tests(self) -> Dict:
        """Run tests and get current results."""
        cmd = [
            sys.executable, "-m", "pytest",
            "/mnt/user-data/uploads",
            "-v", "--tb=short", "-q",
        ]
        
        try:
            cmd.extend(["--json-report", "--json-report-file=/tmp/current_report.json"])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            with open("/tmp/current_report.json") as f:
                return json.load(f)
        except Exception:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return self._parse_pytest_output(result.stdout)
    
    def _parse_pytest_output(self, output: str) -> Dict:
        """Parse pytest text output."""
        lines = output.split('\n')
        results = {"summary": {}, "tests": []}
        
        for line in lines:
            if " passed" in line or " failed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        results["summary"]["passed"] = int(parts[i - 1])
                    elif part == "failed":
                        results["summary"]["failed"] = int(parts[i - 1])
                    elif part == "skipped":
                        results["summary"]["skipped"] = int(parts[i - 1])
            
            if "::" in line and any(x in line for x in ["PASSED", "FAILED", "SKIPPED"]):
                test_name = line.split("::")[1].split()[0] if "::" in line else "unknown"
                outcome = "passed" if "PASSED" in line else "failed" if "FAILED" in line else "skipped"
                results["tests"].append({"nodeid": test_name, "outcome": outcome})
        
        return results
    
    def compare_tests(self, current: Dict) -> Dict:
        """Compare current test results against baseline."""
        baseline_tests = {t["nodeid"]: t["outcome"] 
                         for t in self.baseline.get("test_results", {}).get("tests", [])}
        current_tests = {t["nodeid"]: t["outcome"] 
                        for t in current.get("tests", [])}
        
        comparison = {
            "regressions": [],      # passing -> failing
            "fixes": [],            # failing -> passing
            "new_failures": [],     # not in baseline, now failing
            "new_tests": [],        # not in baseline, now passing
            "missing_tests": [],    # in baseline, not in current
            "unchanged": [],        # same status
        }
        
        # Check all baseline tests
        for test_name, baseline_outcome in baseline_tests.items():
            if test_name not in current_tests:
                comparison["missing_tests"].append(test_name)
            elif current_tests[test_name] != baseline_outcome:
                if baseline_outcome == "passed" and current_tests[test_name] == "failed":
                    comparison["regressions"].append(test_name)
                elif baseline_outcome == "failed" and current_tests[test_name] == "passed":
                    comparison["fixes"].append(test_name)
            else:
                comparison["unchanged"].append(test_name)
        
        # Check for new tests
        for test_name, current_outcome in current_tests.items():
            if test_name not in baseline_tests:
                if current_outcome == "passed":
                    comparison["new_tests"].append(test_name)
                else:
                    comparison["new_failures"].append(test_name)
        
        return comparison
    
    def print_comparison_report(self, comparison: Dict, current_summary: Dict):
        """Print detailed comparison report."""
        if RICH_AVAILABLE:
            self._print_rich_report(comparison, current_summary)
        else:
            self._print_plain_report(comparison, current_summary)
    
    def _print_rich_report(self, comparison: Dict, current_summary: Dict):
        """Print with rich formatting."""
        baseline_summary = self.baseline.get("test_results", {}).get("summary", {})
        
        # Summary table
        table = Table(title="Baseline Comparison Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Baseline", style="yellow", justify="right")
        table.add_column("Current", style="green", justify="right")
        table.add_column("Change", style="magenta", justify="right")
        
        baseline_passed = baseline_summary.get("passed", 0)
        current_passed = current_summary.get("passed", 0)
        passed_change = current_passed - baseline_passed
        
        baseline_failed = baseline_summary.get("failed", 0)
        current_failed = current_summary.get("failed", 0)
        failed_change = current_failed - baseline_failed
        
        table.add_row(
            "Passed",
            str(baseline_passed),
            str(current_passed),
            f"{passed_change:+d}" if passed_change != 0 else "0",
            style="green" if passed_change >= 0 else "red"
        )
        
        table.add_row(
            "Failed",
            str(baseline_failed),
            str(current_failed),
            f"{failed_change:+d}" if failed_change != 0 else "0",
            style="red" if failed_change > 0 else "green"
        )
        
        console.print("\n")
        console.print(table)
        
        # Regressions (critical!)
        if comparison["regressions"]:
            console.print("\n[bold red]🚨 REGRESSIONS (passing → failing):[/bold red]")
            for test in comparison["regressions"]:
                console.print(f"  [red]✗[/red] {test}")
        
        # Fixes (good!)
        if comparison["fixes"]:
            console.print("\n[bold green]✅ FIXES (failing → passing):[/bold green]")
            for test in comparison["fixes"]:
                console.print(f"  [green]✓[/green] {test}")
        
        # New failures (investigate)
        if comparison["new_failures"]:
            console.print("\n[bold yellow]⚠️  NEW FAILURES:[/bold yellow]")
            for test in comparison["new_failures"]:
                console.print(f"  [yellow]?[/yellow] {test}")
        
        # New tests (good!)
        if comparison["new_tests"]:
            console.print("\n[bold green]➕ NEW TESTS (passing):[/bold green]")
            for test in comparison["new_tests"][:5]:
                console.print(f"  [green]+[/green] {test}")
            if len(comparison["new_tests"]) > 5:
                console.print(f"  ... and {len(comparison['new_tests']) - 5} more")
        
        # Missing tests (removed?)
        if comparison["missing_tests"]:
            console.print("\n[bold yellow]➖ MISSING TESTS (removed?):[/bold yellow]")
            for test in comparison["missing_tests"]:
                console.print(f"  [yellow]-[/yellow] {test}")
        
        # Overall status
        console.print("\n" + "=" * 60)
        if comparison["regressions"]:
            console.print("[bold red]❌ REGRESSIONS DETECTED![/bold red]")
            console.print(f"   {len(comparison['regressions'])} test(s) that were passing are now failing")
        elif comparison["new_failures"]:
            console.print("[bold yellow]⚠️  NEW FAILURES DETECTED[/bold yellow]")
            console.print(f"   {len(comparison['new_failures'])} new test(s) are failing")
        else:
            console.print("[bold green]✅ NO REGRESSIONS[/bold green]")
            if comparison["fixes"]:
                console.print(f"   {len(comparison['fixes'])} test(s) fixed!")
        console.print("=" * 60 + "\n")
    
    def _print_plain_report(self, comparison: Dict, current_summary: Dict):
        """Print plain text report."""
        baseline_summary = self.baseline.get("test_results", {}).get("summary", {})
        
        print("\n" + "=" * 60)
        print("BASELINE COMPARISON SUMMARY")
        print("=" * 60)
        print(f"Baseline: {self.baseline.get('metadata', {}).get('timestamp', 'unknown')}")
        print()
        
        baseline_passed = baseline_summary.get("passed", 0)
        current_passed = current_summary.get("passed", 0)
        baseline_failed = baseline_summary.get("failed", 0)
        current_failed = current_summary.get("failed", 0)
        
        print(f"Passed:  {baseline_passed} → {current_passed} ({current_passed - baseline_passed:+d})")
        print(f"Failed:  {baseline_failed} → {current_failed} ({current_failed - baseline_failed:+d})")
        print()
        
        if comparison["regressions"]:
            print("REGRESSIONS (passing → failing):")
            for test in comparison["regressions"]:
                print(f"  ✗ {test}")
            print()
        
        if comparison["fixes"]:
            print("FIXES (failing → passing):")
            for test in comparison["fixes"]:
                print(f"  ✓ {test}")
            print()
        
        if comparison["new_failures"]:
            print("NEW FAILURES:")
            for test in comparison["new_failures"]:
                print(f"  ? {test}")
            print()
        
        print("=" * 60)
        if comparison["regressions"]:
            print("❌ REGRESSIONS DETECTED!")
        elif comparison["new_failures"]:
            print("⚠️  NEW FAILURES DETECTED")
        else:
            print("✅ NO REGRESSIONS")
        print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compare current state against baseline"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Baseline file to compare against (default: latest)"
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with status 1 if regressions detected"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save comparison report to file"
    )
    
    args = parser.parse_args()
    
    # Find baseline file
    if args.baseline:
        baseline_file = args.baseline
    else:
        baseline_file = Path("baselines/baseline_latest.json")
    
    if not baseline_file.exists():
        print(f"❌ Baseline file not found: {baseline_file}")
        print("Run: python capture_baseline.py")
        sys.exit(1)
    
    print("🔍 Comparing current state to baseline...")
    print(f"   Baseline: {baseline_file}")
    print()
    
    # Run comparison
    comparator = BaselineComparator(baseline_file)
    current_results = comparator.run_current_tests()
    comparison = comparator.compare_tests(current_results)
    
    # Print report
    comparator.print_comparison_report(comparison, current_results.get("summary", {}))
    
    # Save report if requested
    if args.output:
        report_data = {
            "baseline_file": str(baseline_file),
            "comparison": comparison,
            "current_summary": current_results.get("summary", {}),
            "baseline_summary": comparator.baseline.get("test_results", {}).get("summary", {}),
        }
        with open(args.output, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Report saved to: {args.output}")
    
    # Exit with error if regressions found and flag set
    if args.fail_on_regression and comparison["regressions"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
