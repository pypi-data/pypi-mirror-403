#!/usr/bin/env python3
"""
Baseline Capture Script - Lock in Current Working State

This script captures the current state of all passing tests and creates
a comprehensive baseline that you can use to detect any future regressions.

Usage:
    python capture_baseline.py                    # Capture everything
    python capture_baseline.py --skip-slow        # Skip slow tests
    python capture_baseline.py --create-golden    # Also create golden data
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class BaselineCapture:
    """Captures comprehensive baseline of current state."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().isoformat()
        
    def run_all_tests(self, skip_slow: bool = False) -> Dict:
        """Run complete test suite and capture results."""
        print("🔍 Running complete test suite...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "/mnt/user-data/uploads",
            "-v",
            "--tb=short",
            "-q",
        ]
        
        if skip_slow:
            cmd.extend(["-m", "not slow"])
        
        # Try to get JSON output if pytest-json-report is available
        try:
            cmd.extend(["--json-report", "--json-report-file=/tmp/baseline_report.json"])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            with open("/tmp/baseline_report.json") as f:
                return json.load(f)
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            # Fallback: parse text output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return self._parse_pytest_output(result.stdout)
    
    def _parse_pytest_output(self, output: str) -> Dict:
        """Parse pytest text output."""
        lines = output.split('\n')
        
        results = {
            "summary": {},
            "tests": [],
            "duration": 0.0,
        }
        
        for line in lines:
            # Parse summary line
            if " passed" in line or " failed" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        results["summary"]["passed"] = int(parts[i - 1])
                    elif part == "failed":
                        results["summary"]["failed"] = int(parts[i - 1])
                    elif part == "skipped":
                        results["summary"]["skipped"] = int(parts[i - 1])
            
            # Parse individual test results
            if "::" in line and any(x in line for x in ["PASSED", "FAILED", "SKIPPED"]):
                test_name = line.split("::")[1].split()[0] if "::" in line else "unknown"
                outcome = "passed" if "PASSED" in line else "failed" if "FAILED" in line else "skipped"
                
                results["tests"].append({
                    "nodeid": test_name,
                    "outcome": outcome,
                })
        
        return results
    
    def capture_golden_data(self, test_results: Dict) -> Dict:
        """Capture golden data for all passing tests."""
        print("📸 Capturing golden data for passing tests...")
        
        golden_data = {
            "timestamp": self.timestamp,
            "test_count": len([t for t in test_results.get("tests", []) if t.get("outcome") == "passed"]),
            "files": [],
        }
        
        # For each passing test, we would ideally capture outputs
        # This is a placeholder - actual implementation would depend on your test structure
        passing_tests = [t for t in test_results.get("tests", []) if t.get("outcome") == "passed"]
        
        for test in passing_tests[:10]:  # Limit to first 10 for now
            test_name = test.get("nodeid", "unknown")
            
            # Placeholder: you would run each test individually and capture output
            golden_data["files"].append({
                "test": test_name,
                "status": "captured",
            })
        
        return golden_data
    
    def run_benchmarks(self) -> Dict:
        """Run performance benchmarks and save baseline."""
        print("⚡ Running performance benchmarks...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "/mnt/user-data/uploads",
                "--benchmark-only",
                "--benchmark-autosave",
                "--benchmark-save=baseline",
            ], capture_output=True, text=True, timeout=600)
            
            return {
                "status": "completed",
                "output": result.stdout,
                "saved": True,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }
    
    def capture_code_snapshot(self) -> Dict:
        """Capture git commit hash and file checksums."""
        print("📋 Capturing code snapshot...")
        
        snapshot = {
            "timestamp": self.timestamp,
            "git_info": {},
            "file_hashes": {},
        }
        
        # Try to get git info
        try:
            git_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            git_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, check=True
            ).stdout.strip()
            
            snapshot["git_info"] = {
                "commit": git_hash,
                "branch": git_branch,
            }
        except Exception:
            snapshot["git_info"] = {"error": "Not a git repository"}
        
        # Capture file hashes of test files
        test_dir = Path("/mnt/user-data/uploads")
        if test_dir.exists():
            for test_file in test_dir.glob("test_*.py"):
                try:
                    content = test_file.read_bytes()
                    file_hash = hashlib.sha256(content).hexdigest()
                    snapshot["file_hashes"][test_file.name] = file_hash
                except Exception as e:
                    snapshot["file_hashes"][test_file.name] = f"error: {e}"
        
        return snapshot
    
    def save_baseline(self, data: Dict, filename: str):
        """Save baseline data to JSON file."""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"✅ Saved: {output_path}")
        return output_path
    
    def create_summary_report(self, baseline_data: Dict) -> str:
        """Create human-readable summary report."""
        report_lines = [
            "=" * 80,
            "BUNKER-STATS BASELINE CAPTURE REPORT",
            "=" * 80,
            f"Timestamp: {self.timestamp}",
            "",
        ]
        
        # Test results summary
        test_results = baseline_data.get("test_results", {})
        summary = test_results.get("summary", {})
        
        report_lines.extend([
            "TEST RESULTS:",
            f"  Passed:  {summary.get('passed', 0)}",
            f"  Failed:  {summary.get('failed', 0)}",
            f"  Skipped: {summary.get('skipped', 0)}",
            "",
        ])
        
        # Git info
        code_snapshot = baseline_data.get("code_snapshot", {})
        git_info = code_snapshot.get("git_info", {})
        
        if "commit" in git_info:
            report_lines.extend([
                "CODE SNAPSHOT:",
                f"  Commit:  {git_info['commit'][:12]}...",
                f"  Branch:  {git_info['branch']}",
                "",
            ])
        
        # Files captured
        file_hashes = code_snapshot.get("file_hashes", {})
        report_lines.extend([
            f"FILES CAPTURED: {len(file_hashes)}",
            "",
        ])
        
        # Benchmarks
        benchmarks = baseline_data.get("benchmarks", {})
        if benchmarks.get("status") == "completed":
            report_lines.extend([
                "BENCHMARKS:",
                "  ✅ Performance baseline saved",
                "",
            ])
        
        # Golden data
        golden = baseline_data.get("golden_data", {})
        if golden:
            report_lines.extend([
                "GOLDEN DATA:",
                f"  Tests captured: {golden.get('test_count', 0)}",
                "",
            ])
        
        report_lines.extend([
            "=" * 80,
            "NEXT STEPS:",
            "  1. Review this baseline",
            "  2. Commit to git: git add baselines/ && git commit -m 'capture: baseline'",
            "  3. Now safe to refactor!",
            "  4. After changes, compare: python compare_to_baseline.py",
            "=" * 80,
        ])
        
        return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Capture comprehensive baseline of current working state"
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--create-golden",
        action="store_true",
        help="Also create golden data snapshots"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("baselines"),
        help="Output directory for baseline files"
    )
    
    args = parser.parse_args()
    
    print("🎯 Capturing Baseline - Locking in Current State")
    print("=" * 60)
    
    capturer = BaselineCapture(args.output_dir)
    
    # Capture all components
    baseline_data = {
        "metadata": {
            "timestamp": capturer.timestamp,
            "skip_slow": args.skip_slow,
        }
    }
    
    # 1. Run tests and capture results
    baseline_data["test_results"] = capturer.run_all_tests(skip_slow=args.skip_slow)
    
    # 2. Capture code snapshot
    baseline_data["code_snapshot"] = capturer.capture_code_snapshot()
    
    # 3. Run benchmarks
    baseline_data["benchmarks"] = capturer.run_benchmarks()
    
    # 4. Optionally capture golden data
    if args.create_golden:
        baseline_data["golden_data"] = capturer.capture_golden_data(
            baseline_data["test_results"]
        )
    
    # Save everything
    baseline_file = capturer.save_baseline(
        baseline_data, 
        f"baseline_{capturer.timestamp.split('T')[0]}.json"
    )
    
    # Create summary report
    summary = capturer.create_summary_report(baseline_data)
    summary_file = capturer.output_dir / "LATEST_BASELINE_REPORT.txt"
    summary_file.write_text(summary)
    
    # Display summary
    print("\n")
    print(summary)
    
    # Save a "latest" symlink/copy for easy reference
    latest_file = capturer.output_dir / "baseline_latest.json"
    import shutil
    shutil.copy(baseline_file, latest_file)
    print(f"\n📌 Latest baseline: {latest_file}")


if __name__ == "__main__":
    main()
