#!/usr/bin/env python3
"""
Compare SortedCollections vs SortedContainers using SortedContainers' benchmark tests.

Runs benchmark_sorteddict and benchmark_sortedset with both implementations,
then produces CSV and Markdown comparison tables based on median times.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIZES = "100,1000,10000,100000,1000000,10000000"


def run_benchmark_module(sc_path: Path, module: str, kind_label: str, sizes: List[str]) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(sc_path) + os.pathsep + str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    argv = [
        "bench",
        "--bare",
        "--kind", kind_label,
        "--kind", "SortedCollections",
    ]
    for size in sizes:
        argv.extend(["--size", size])

    code = f"""
import sys
sys.argv = {argv!r}
from tests import benchmark_sorteddict as mod if '{module}' == 'tests.benchmark_sorteddict' else None
"""
    # Inline code above isn't great; we will build explicit code per module below.

    if module == "tests.benchmark_sorteddict":
        code = f"""
import sys
sys.argv = {argv!r}
from tests import benchmark_sorteddict as mod
from sortedcollections import SortedDict as SC
# Add our implementation using SortedDict's test config as template.
for test in mod.tests:
    if 'SortedDict' in mod.impls.get(test, {{}}):
        base = mod.impls[test]['SortedDict']
        mod.impls[test]['SortedCollections'] = {{
            'setup': base['setup'],
            'ctor': SC,
            'func': base['func'],
            'limit': base['limit'],
        }}
mod.main('SortedDict')
"""
    elif module == "tests.benchmark_sortedset":
        code = f"""
import sys
sys.argv = {argv!r}
from tests import benchmark_sortedset as mod
from sortedcollections import SortedSet as SC
# Add our implementation using SortedSet's test config as template.
for test in mod.tests:
    if 'SortedSet' in mod.impls.get(test, {{}}):
        base = mod.impls[test]['SortedSet']
        mod.impls[test]['SortedCollections'] = {{
            'setup': base['setup'],
            'ctor': SC,
            'func': base['func'],
            'limit': base['limit'],
        }}
mod.main('SortedSet')
"""
    else:
        raise SystemExit(f"Unsupported module: {module}")

    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT),
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.stdout


def parse_output(output: str) -> Dict[Tuple[str, str, str], float]:
    results: Dict[Tuple[str, str, str], float] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 7:
            continue
        test, kind, size, _min, _max, median, _mean = parts
        results[(test, kind, size)] = float(median)
    return results


def write_comparison_table(
    out_path: Path,
    results: Dict[Tuple[str, str, str], float],
    base_kind: str,
    label: str,
) -> None:
    rows: List[str] = []
    rows.append("test,size,sortedcontainers_median_s,sortedcollections_median_s,ratio_sc_over_scext")

    tests = sorted({t for (t, k, s) in results.keys()})
    sizes = sorted({s for (t, k, s) in results.keys()}, key=lambda x: int(x))

    for test in tests:
        for size in sizes:
            sc_key = (test, base_kind, size)
            our_key = (test, "SortedCollections", size)
            if sc_key not in results or our_key not in results:
                continue
            sc = results[sc_key]
            our = results[our_key]
            ratio = (sc / our) if our else float("inf")
            rows.append(f"{test},{size},{sc:.6f},{our:.6f},{ratio:.3f}")

    out_path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_markdown_table(
    out_path: Path,
    results: Dict[Tuple[str, str, str], float],
    base_kind: str,
    label: str,
) -> None:
    header = "| test | size | sortedcontainers (median s) | sortedcollections (median s) | ratio sc/sc-ext |\n"
    sep = "| --- | --- | --- | --- | --- |\n"
    lines = [header, sep]

    tests = sorted({t for (t, k, s) in results.keys()})
    sizes = sorted({s for (t, k, s) in results.keys()}, key=lambda x: int(x))

    for test in tests:
        for size in sizes:
            sc_key = (test, base_kind, size)
            our_key = (test, "SortedCollections", size)
            if sc_key not in results or our_key not in results:
                continue
            sc = results[sc_key]
            our = results[our_key]
            ratio = (sc / our) if our else float("inf")
            lines.append(f"| {test} | {size} | {sc:.6f} | {our:.6f} | {ratio:.3f} |\n")

    out_path.write_text("".join(lines), encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(description="Compare SortedCollections vs SortedContainers benchmarks.")
    parser.add_argument(
        "--sc-path",
        default=str(ROOT / ".deps/python-sortedcontainers"),
        help="Path to local python-sortedcontainers clone (repo root).",
    )
    parser.add_argument(
        "--sizes",
        default=DEFAULT_SIZES,
        help="Comma-separated sizes passed to SortedContainers benchmarks.",
    )
    parser.add_argument(
        "--out-dir",
        default="benchmarks/sortedcontainers_compare",
        help="Output directory for results.",
    )
    parser.add_argument(
        "--only",
        choices=["sorteddict", "sortedset"],
        default=None,
        help="Limit to a single benchmark suite.",
    )
    args = parser.parse_args()

    sc_path = Path(args.sc_path).resolve()
    tests_dir = sc_path / "tests"
    if not tests_dir.is_dir():
        raise SystemExit(f"Invalid sortedcontainers path: {sc_path}")

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sizes = [s.strip() for s in args.sizes.split(",") if s.strip()]

    suites = [
        ("tests.benchmark_sorteddict", "SortedDict", "SortedDict", "sorteddict"),
        ("tests.benchmark_sortedset", "SortedSet", "SortedSet", "sortedset"),
    ]
    for module, label, base_kind, key in suites:
        if args.only and args.only != key:
            continue
        print(f"Running {label} benchmarks...")
        output = run_benchmark_module(sc_path, module, base_kind, sizes)
        raw_path = out_dir / f"raw_{label.lower()}.txt"
        raw_path.write_text(output, encoding="utf-8")

        results = parse_output(output)
        csv_path = out_dir / f"compare_{label.lower()}.csv"
        write_comparison_table(csv_path, results, base_kind, label)
        md_path = out_dir / f"compare_{label.lower()}.md"
        write_markdown_table(md_path, results, base_kind, label)

        print(f"  wrote {raw_path}")
        print(f"  wrote {csv_path}")
        print(f"  wrote {md_path}")


if __name__ == "__main__":
    main()
