#!/usr/bin/env python3
"""
Sweep B-tree degree values and compare BTreeDict vs sortedcontainers.SortedDict
using the existing interval and counter benchmarks.

This rebuilds the C extensions for each degree via setup.py.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List
import statistics

RE_BTREEDICT = re.compile(r"BTreeDict sweep: ([0-9.]+)s")
RE_SORTEDDICT = re.compile(r"SortedDict sweep: ([0-9.]+)s")

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DEGREES = "16,32,64,128"
WORKLOADS = {
    "small": {
        "intervals": ["--n", "100000", "--tmax", "100000", "--tmax-scale", "1", "--max-len", "200", "--seed", "42"],
        "counters": ["--n", "100000", "--ttl", "1000", "--query-every", "10000", "--seed", "123", "--max-step", "3", "--value-max", "5"],
    },
    "medium": {
        "intervals": ["--n", "500000", "--tmax", "500000", "--tmax-scale", "1", "--max-len", "200", "--seed", "42"],
        "counters": ["--n", "500000", "--ttl", "2000", "--query-every", "20000", "--seed", "123", "--max-step", "3", "--value-max", "5"],
    },
    "heavy": {
        "intervals": ["--n", "2000000", "--tmax", "2000000", "--tmax-scale", "1", "--max-len", "200", "--seed", "42"],
        "counters": ["--n", "2000000", "--ttl", "4000", "--query-every", "40000", "--seed", "123", "--max-step", "3", "--value-max", "5"],
    },
}


def run(cmd: List[str], env: dict | None = None) -> str:
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


def parse_times(output: str) -> tuple[float, float]:
    m_btree = RE_BTREEDICT.search(output)
    m_sorted = RE_SORTEDDICT.search(output)
    if not m_btree or not m_sorted:
        raise RuntimeError("Failed to parse benchmark output:\n" + output)
    return float(m_btree.group(1)), float(m_sorted.group(1))


def run_benchmark_median(cmd: List[str], runs: int) -> tuple[float, float]:
    btree_times: List[float] = []
    sorted_times: List[float] = []
    for _ in range(runs):
        out = run(cmd)
        btree_t, sorted_t = parse_times(out)
        btree_times.append(btree_t)
        sorted_times.append(sorted_t)
    return statistics.median(btree_times), statistics.median(sorted_times)


def build_for_degree(degree: int) -> None:
    env = os.environ.copy()
    cflags = env.get("CFLAGS", "")
    flags = f"-DBTREE_LEAF_MIN_DEGREE={degree} -DBTREE_INTERNAL_MIN_DEGREE={degree}"
    env["CFLAGS"] = (cflags + " " + flags).strip()
    # env.setdefault("SORTEDCOLLECTIONS_LTO", "0")
    # Force rebuild so the new macros are picked up.
    run([sys.executable, "setup.py", "build_ext", "--inplace", "--force"], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sweep B-tree degree and benchmark.",
        epilog="Runs small, medium, and heavy workloads for each degree.",
    )
    parser.add_argument(
        "--degrees",
        default=DEFAULT_DEGREES,
        help="Comma-separated list of degrees (default: 16,32,64,128,256)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=5,
        help="Number of runs per workload (median is reported)",
    )
    parser.add_argument(
        "--csv",
        default="benchmarks/degree_sweep_results.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    workloads = ["small", "medium", "heavy"]

    degrees = [int(x.strip()) for x in args.degrees.split(",") if x.strip()]
    if not degrees:
        raise SystemExit("No degrees provided.")

    csv_path = ROOT / args.csv
    rows: List[list[str]] = []

    for degree in degrees:
        print(f"\n== Degree {degree} ==")
        build_for_degree(degree)

        for workload in workloads:
            intervals_args = WORKLOADS[workload]["intervals"]
            counters_args = WORKLOADS[workload]["counters"]

            btree_i, sorted_i = run_benchmark_median(
                [sys.executable, "benchmarks/bench_intervals.py", *intervals_args],
                args.runs,
            )
            ratio_i = sorted_i / btree_i if btree_i else float("inf")
            print(
                f"[{workload}] Intervals (median of {args.runs}): "
                f"BTree={btree_i:.4f}s Sorted={sorted_i:.4f}s Ratio={ratio_i:.2f}x"
            )

            btree_c, sorted_c = run_benchmark_median(
                [sys.executable, "benchmarks/bench_counters.py", *counters_args],
                args.runs,
            )
            ratio_c = sorted_c / btree_c if btree_c else float("inf")
            print(
                f"[{workload}] Counters  (median of {args.runs}): "
                f"BTree={btree_c:.4f}s Sorted={sorted_c:.4f}s Ratio={ratio_c:.2f}x"
            )

            rows.append([
                str(degree),
                workload,
                f"{btree_i:.6f}",
                f"{sorted_i:.6f}",
                f"{ratio_i:.3f}",
                f"{btree_c:.6f}",
                f"{sorted_c:.6f}",
                f"{ratio_c:.3f}",
            ])

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "degree",
            "workload",
            "intervals_btree_s",
            "intervals_sorted_s",
            "intervals_ratio_sorted_over_btree",
            "counters_btree_s",
            "counters_sorted_s",
            "counters_ratio_sorted_over_btree",
        ])
        writer.writerows(rows)

    print(f"\nWrote results to {csv_path}")


if __name__ == "__main__":
    main()
