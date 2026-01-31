#!/usr/bin/env python3
"""
Run SortedContainers' official benchmark scripts and optionally generate plots.

Requires a local clone of python-sortedcontainers and uses its tests/* scripts.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]

BENCHES = [
    ("sortedlist", "SortedList"),
    ("sorteddict", "SortedDict"),
    ("sortedset", "SortedSet"),
]


def run(cmd: List[str], env: dict) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.stdout


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run SortedContainers benchmark scripts and save outputs.",
    )
    parser.add_argument(
        "--sc-path",
        required=True,
        help="Path to local python-sortedcontainers clone (repo root).",
    )
    parser.add_argument(
        "--out-dir",
        default="benchmarks/sortedcontainers_results",
        help="Output directory for result files and plots.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Do not generate plots (only save raw results).",
    )
    args = parser.parse_args()

    sc_path = Path(args.sc_path).resolve()
    tests_dir = sc_path / "tests"
    if not tests_dir.is_dir():
        raise SystemExit(f"Invalid sortedcontainers path: {sc_path}")

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    # Ensure sortedcontainers repo is on PYTHONPATH so tests.* modules import.
    env["PYTHONPATH"] = str(sc_path) + os.pathsep + env.get("PYTHONPATH", "")

    for bench_name, label in BENCHES:
        print(f"Running {bench_name}...")
        result_path = out_dir / f"results_{bench_name}.txt"
        output = run([sys.executable, "-m", f"tests.benchmark_{bench_name}", "--bare"], env)
        result_path.write_text(output, encoding="utf-8")
        print(f"  wrote {result_path}")

        if not args.no_plot:
            print(f"  plotting {label}...")
            run(
                [
                    sys.executable,
                    "-m",
                    "tests.benchmark_plot",
                    str(result_path),
                    label,
                    "--save",
                ],
                env,
            )

    print("Done.")


if __name__ == "__main__":
    main()
