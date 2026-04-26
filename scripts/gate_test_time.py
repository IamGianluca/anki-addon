#!/usr/bin/env python3
"""Gate test suite wall time against a baseline.

Called by the makefile after pytest completes. Compares elapsed nanoseconds
against the stored baseline and exits with code 1 if the threshold is exceeded.

Usage:
    python3 scripts/gate_test_time.py --elapsed <ns> --suite <name> [--update-baseline] [--threshold N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASELINE_DIR = Path(__file__).parents[1] / ".test-baselines"


def _get_baseline_path(suite: str) -> Path:
    return BASELINE_DIR / f"{suite}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Gate test suite wall time")
    parser.add_argument(
        "--elapsed",
        type=int,
        required=True,
        help="Elapsed time in nanoseconds",
    )
    parser.add_argument(
        "--suite",
        type=str,
        default="test",
        help="Suite name for baseline file (default: test)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Max allowed increase over baseline in percent (default: 10)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Record current timing as new baseline",
    )
    args = parser.parse_args()

    elapsed_s = args.elapsed / 1_000_000_000
    baseline_path = _get_baseline_path(args.suite)

    if args.update_baseline:
        _save_baseline(baseline_path, {"total": round(elapsed_s, 3)})
        print(f"\nBaseline saved to {baseline_path}: {elapsed_s:.3f}s")
        sys.exit(0)

    baseline_s = _load_baseline(baseline_path)

    if baseline_s is None:
        _save_baseline(baseline_path, {"total": round(elapsed_s, 3)})
        print(
            f"\nNo baseline found. Created {baseline_path}: {elapsed_s:.3f}s\n"
            f"Run 'make {args.suite}_update_baseline' to update it intentionally."
        )
        sys.exit(0)

    allowed = baseline_s * (1 + args.threshold / 100)
    pct = (
        ((elapsed_s - baseline_s) / baseline_s * 100) if baseline_s > 0 else 0
    )
    sign = "+" if pct > 0 else ""

    if elapsed_s > allowed:
        print(
            f"\ntest time gate FAILED: {elapsed_s:.2f}s > {allowed:.2f}s "
            f"(baseline {baseline_s:.2f}s + {args.threshold}%)"
        )
        print(
            f"Run 'make {args.suite}_update_baseline' if intentional, "
            f"or investigate slow tests."
        )
        sys.exit(1)
    else:
        print(
            f"\ntest time gate PASSED: {elapsed_s:.2f}s "
            f"(baseline {baseline_s:.2f}s, {sign}{pct:.1f}%)"
        )


def _load_baseline(path: Path) -> float | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())["total"]


def _save_baseline(path: Path, data: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
