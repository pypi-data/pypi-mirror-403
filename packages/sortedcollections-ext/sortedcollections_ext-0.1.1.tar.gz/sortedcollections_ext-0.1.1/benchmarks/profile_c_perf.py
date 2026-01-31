#!/usr/bin/env python3
"""
Run sampling profiler (perf) for C hot spots and optionally emit FlameGraphs.

Supports the core benchmark entry points and writes per-run perf.data,
perf report, and (if available) flamegraph SVG.
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR_DEFAULT = ROOT / "benchmarks" / "perf"

BENCH_COMMANDS = {
    "intervals": [sys.executable, "benchmarks/profile_c_perf.py", "--workload", "intervals"],
    "counters": [sys.executable, "benchmarks/profile_c_perf.py", "--workload", "counters"],
}

from sortedcollections import SortedDict as BTreeDict


def generate_random_intervals(n: int, t_max: int, max_len: int, seed: int) -> List[Tuple[int, int]]:
    rng = random.Random(seed)
    intervals: List[Tuple[int, int]] = []
    for _ in range(n):
        start = rng.randrange(0, t_max)
        length = rng.randrange(1, max_len + 1)
        end = min(start + length, t_max + 1)
        if end == start:
            end = start + 1
        intervals.append((start, end))
    return intervals


def sweep_line_max_overlap(intervals: List[Tuple[int, int]]) -> int:
    events = BTreeDict()
    for start, end in intervals:
        events.increment(start, 1)
        events.increment(end, -1)

    cur = 0
    max_overlap = 0
    times = list(events.keys())
    for i, t in enumerate(times):
        cur += events[t]
        if cur > max_overlap:
            max_overlap = cur
        if i + 1 < len(times):
            next_t = times[i + 1]
            if t < next_t and cur == max_overlap:
                pass
    return max_overlap


class ExpiringCounter:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self.data = BTreeDict()
        self.total = 0

    def insert(self, t: int, value: int) -> None:
        self.data[t] = self.data.get(t, 0) + value
        self.total += value
        self._expire(t)

    def _expire(self, current_time: int) -> None:
        cutoff = current_time - self.ttl
        while self.data:
            oldest_t, _ = self.data.peekitem(0)
            if oldest_t > cutoff:
                break
            _, v = self.data.popitem(0)
            self.total -= v

    def query(self) -> int:
        return self.total


def run_intervals_workload() -> None:
    n = 2**23
    tmax = 2**23
    tmax_scale = [1, 2, 4, 8, 16]
    max_len = 500
    seed = 42
    for scale in tmax_scale:
        t_max = max(1, int(tmax * scale))
        intervals = generate_random_intervals(n, t_max, max_len, seed=seed)
        _ = sweep_line_max_overlap(intervals)


def run_counters_workload() -> None:
    ttl = 5000
    n_inserts = 2_000_000
    query_every = 50_000
    seed = 123
    max_step = 5
    value_max = 20

    rng = random.Random(seed)
    counter = ExpiringCounter(ttl)
    t = 0
    for i in range(1, n_inserts + 1):
        t += rng.randint(0, max_step)
        value = rng.randint(1, value_max)
        counter.insert(t, value)
        if query_every and i % query_every == 0:
            _ = counter.query()


def find_flamegraph_tools() -> tuple[str | None, str | None]:
    stackcollapse = shutil.which("stackcollapse-perf.pl")
    flamegraph = shutil.which("flamegraph.pl")

    if stackcollapse and flamegraph:
        return stackcollapse, flamegraph

    fg_dir = os.environ.get("FLAMEGRAPH_DIR")
    if fg_dir:
        sc = Path(fg_dir) / "stackcollapse-perf.pl"
        fg = Path(fg_dir) / "flamegraph.pl"
        if sc.exists() and fg.exists():
            return str(sc), str(fg)

    return None, None


def run(cmd: List[str], env: dict | None = None) -> None:
    subprocess.run(cmd, cwd=str(ROOT), env=env, check=True)


def perf_record(out_path: Path, cmd: List[str], freq: int) -> None:
    run([
        "perf",
        "record",
        "-F",
        str(freq),
        "-g",
        "--call-graph",
        "dwarf",
        "-o",
        str(out_path),
        "--",
        *cmd,
    ])


def perf_report(perf_data: Path, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        subprocess.run(
            ["perf", "report", "--stdio", "-i", str(perf_data)],
            cwd=str(ROOT),
            check=True,
            stdout=f,
        )


def summarize_report(report_path: Path, out_path: Path, top_n: int = 20) -> None:
    lines = report_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    entries: List[tuple[float, str]] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # perf report stdio lines start like: "  7.12%  python  ...  [.] symbol"
        if "%" not in line:
            continue
        parts = line.split()
        try:
            pct = float(parts[0].strip("%"))
        except Exception:
            continue
        symbol = parts[-1]
        if symbol.startswith("btree_") or symbol.startswith("BTree_") or symbol.startswith("Sorted"):
            entries.append((pct, symbol))

    entries.sort(key=lambda x: x[0], reverse=True)
    entries = entries[:top_n]

    out_lines = ["top_percent,symbol"]
    out_lines.extend([f"{pct:.2f},{sym}" for pct, sym in entries])
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def perf_flamegraph(perf_data: Path, out_svg: Path, stackcollapse: str, flamegraph: str) -> None:
    p1 = subprocess.Popen(
        ["perf", "script", "-i", str(perf_data)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        text=True,
    )
    p2 = subprocess.Popen(
        [stackcollapse],
        cwd=str(ROOT),
        stdin=p1.stdout,
        stdout=subprocess.PIPE,
        text=True,
    )
    p3 = subprocess.Popen(
        [flamegraph, "--countname", "samples"],
        cwd=str(ROOT),
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert p3.stdout is not None
    svg = p3.communicate()[0]
    if p1.poll() not in (0, None):
        raise SystemExit("perf script failed")
    if p2.poll() not in (0, None):
        raise SystemExit("stackcollapse-perf.pl failed")
    if p3.returncode not in (0, None):
        raise SystemExit("flamegraph.pl failed")
    out_svg.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run perf sampling profiler on benchmarks.")
    parser.add_argument(
        "--workload",
        choices=["intervals", "counters"],
        help="Run a single workload directly (used by perf).",
    )
    parser.add_argument(
        "--bench",
        action="append",
        choices=sorted(BENCH_COMMANDS.keys()),
        help="Benchmark to run (can repeat). Default: intervals,counters",
    )
    parser.add_argument(
        "--out-dir",
        default=str(OUT_DIR_DEFAULT),
        help="Output directory for perf data/reports.",
    )
    parser.add_argument(
        "--freq",
        type=int,
        default=99,
        help="Perf sampling frequency (Hz).",
    )
    args = parser.parse_args()

    if args.workload == "intervals":
        run_intervals_workload()
        return
    if args.workload == "counters":
        run_counters_workload()
        return

    benches = args.bench or ["intervals", "counters"]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stackcollapse, flamegraph = find_flamegraph_tools()

    for bench in benches:
        cmd = BENCH_COMMANDS[bench]
        tag = bench
        perf_data = out_dir / f"perf_{tag}.data"
        report_path = out_dir / f"perf_{tag}_report.txt"
        summary_path = out_dir / f"perf_{tag}_summary.csv"
        svg_path = out_dir / f"perf_{tag}.svg"

        # Clear previous outputs for this bench
        for path in (perf_data, report_path, summary_path, svg_path):
            if path.exists():
                path.unlink()

        print(f"\n== perf: {bench} ==")
        perf_record(perf_data, cmd, args.freq)
        perf_report(perf_data, report_path)
        summarize_report(report_path, summary_path)
        print(f"  report: {report_path}")
        print(f"  summary: {summary_path}")

        if stackcollapse and flamegraph:
            perf_flamegraph(perf_data, svg_path, stackcollapse, flamegraph)
            print(f"  flamegraph: {svg_path}")
        else:
            print("  flamegraph: skipped (stackcollapse-perf.pl/flamegraph.pl not found)")


if __name__ == "__main__":
    main()
