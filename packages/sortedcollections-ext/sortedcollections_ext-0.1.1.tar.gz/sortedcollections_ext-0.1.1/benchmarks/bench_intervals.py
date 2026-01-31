#!/usr/bin/env python3
"""
Random interval overlap demo using btreedict.BTreeDict (sorted map).

Problem:
- Given N half-open intervals [start, end), compute:
  1) maximum number of overlapping intervals
  2) the time segments where the overlap equals that maximum

Approach:
- Sweep line with a sorted dict of time -> delta (+1 at start, -1 at end)
- Prefix sum over times in sorted order

Also includes a naive verification.
"""

from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from typing import List, Tuple

from sortedcollections import SortedDict as BTreeDict
from sortedcontainers import SortedDict


@dataclass(frozen=True)
class Interval:
    start: int
    end: int  # half-open: [start, end)

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError(f"Invalid interval [{self.start}, {self.end})")


def generate_random_intervals(
    n: int,
    t_max: int,
    max_len: int,
    seed: int | None = 0,
) -> List[Interval]:
    rng = random.Random(seed)
    intervals: List[Interval] = []
    for _ in range(n):
        start = rng.randrange(0, t_max)
        length = rng.randrange(1, max_len + 1)
        end = min(start + length, t_max + 1)  # keep within range
        if end == start:
            end = start + 1
        intervals.append(Interval(start, end))
    return intervals


def sweep_line_max_overlap(intervals: List[Interval]) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Returns:
      max_overlap: int
      max_segments: list of (a, b) segments (half-open) where overlap == max_overlap
    """
    events = BTreeDict()  # time -> delta

    # Build the event map
    for iv in intervals:
        events.increment(iv.start, 1)
        events.increment(iv.end, -1)

    # Sweep in sorted order
    cur = 0
    max_overlap = 0
    max_segments: List[Tuple[int, int]] = []

    times = list(events.keys())
    for i, t in enumerate(times):
        cur += events[t]
        max_overlap = max(max_overlap, cur)

        # Segment is [t, next_t) with constant 'cur'
        if i + 1 < len(times):
            next_t = times[i + 1]
            if t < next_t and cur == max_overlap:
                max_segments.append((t, next_t))

    # Merge adjacent max segments (optional tidy-up)
    merged: List[Tuple[int, int]] = []
    for a, b in max_segments:
        if not merged or merged[-1][1] != a:
            merged.append((a, b))
        else:
            merged[-1] = (merged[-1][0], b)

    return max_overlap, merged


def sweep_line_max_overlap_sorteddict(intervals: List[Interval]) -> Tuple[int, List[Tuple[int, int]]]:
    """
    Same algorithm but using sortedcontainers.SortedDict.
    
    Returns:
      max_overlap: int
      max_segments: list of (a, b) segments (half-open) where overlap == max_overlap
    """
    events = SortedDict()  # time -> delta

    # Build the event map
    for iv in intervals:
        events[iv.start] = events.get(iv.start, 0) + 1
        events[iv.end] = events.get(iv.end, 0) - 1

    # Sweep in sorted order
    cur = 0
    max_overlap = 0
    max_segments: List[Tuple[int, int]] = []

    times = list(events.keys())
    for i, t in enumerate(times):
        cur += events[t]
        max_overlap = max(max_overlap, cur)

        # Segment is [t, next_t) with constant 'cur'
        if i + 1 < len(times):
            next_t = times[i + 1]
            if t < next_t and cur == max_overlap:
                max_segments.append((t, next_t))

    # Merge adjacent max segments (optional tidy-up)
    merged: List[Tuple[int, int]] = []
    for a, b in max_segments:
        if not merged or merged[-1][1] != a:
            merged.append((a, b))
        else:
            merged[-1] = (merged[-1][0], b)

    return max_overlap, merged


def naive_max_overlap(intervals: List[Interval]) -> int:
    """
    Naive verification by scanning all integer time points.
    Assumes integer endpoints and half-open intervals [start, end).
    """
    if not intervals:
        return 0
    t_min = min(iv.start for iv in intervals)
    t_max = max(iv.end for iv in intervals)

    best = 0
    for t in range(t_min, t_max):
        cur = 0
        for iv in intervals:
            if iv.start <= t < iv.end:
                cur += 1
        best = max(best, cur)
    return best


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interval overlap benchmark with scalable T_MAX"
    )
    parser.add_argument("--n", type=int, default=2**22, help="number of intervals")
    parser.add_argument("--tmax", type=int, default=2**22, help="base max time value")
    parser.add_argument(
        "--tmax-scale",
        type=float,
        nargs="*",
        default=[1, 2, 4, 8],
        help="multipliers for T_MAX",
    )
    parser.add_argument("--max-len", type=int, default=200, help="max interval length")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = parser.parse_args()

    for scale in args.tmax_scale:
        t_max = max(1, int(args.tmax * scale))
        intervals = generate_random_intervals(args.n, t_max, args.max_len, seed=args.seed)

        print(f"N={args.n} T_MAX={t_max} (scale {scale}) MAX_LEN={args.max_len}")

        # BTreeDict timing
        start = time.time()
        max_overlap_btree, max_segments_btree = sweep_line_max_overlap(intervals)
        btree_time = time.time() - start
        print(f"BTreeDict sweep: {btree_time:.4f}s")
        print(f"  Max overlap: {max_overlap_btree}")

        # SortedDict timing
        start = time.time()
        max_overlap_sorted, _ = sweep_line_max_overlap_sorteddict(intervals)
        sorted_time = time.time() - start
        print(f"SortedDict sweep: {sorted_time:.4f}s")
        print(f"  Max overlap: {max_overlap_sorted}")

        print(
            f"Results match: {max_overlap_btree == max_overlap_sorted}"
            if max_overlap_btree == max_overlap_sorted
            else "Results match: False"
        )
        print(
            "Performance summary: "
            f"BTreeDict={btree_time:.4f}s "
            f"SortedDict={sorted_time:.4f}s "
            f"SortedDict/BTreeDict={sorted_time/btree_time:.2f}x"
        )


if __name__ == "__main__":
    main()
