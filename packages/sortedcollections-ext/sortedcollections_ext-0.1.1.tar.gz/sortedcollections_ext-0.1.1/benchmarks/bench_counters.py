#!/usr/bin/env python3
"""
Write-intensive benchmark:
Dynamic multiset with expiration (sliding TTL window).
Operations:
- insert(timestamp, value)
- expire old entries
- query current sum (rare)
"""

from __future__ import annotations

import argparse
import random
import time

from sortedcollections import SortedDict as BTreeDict
from sortedcontainers import SortedDict


class ExpiringCounter:
    def __init__(self, ttl: int, use_btree: bool = False) -> None:
        self.ttl = ttl
        self.data = BTreeDict() if use_btree else SortedDict()
        self.total = 0
        self.use_btree = use_btree

    def insert(self, t: int, value: int) -> None:
        self.data[t] = self.data.get(t, 0) + value
        self.total += value
        self._expire(t)

    def _expire(self, current_time: int) -> None:
        cutoff = current_time - self.ttl
        if self.use_btree:
            while self.data:
                oldest_t = next(iter(self.data))
                if oldest_t > cutoff:
                    break
                v = self.data.pop(oldest_t)
                self.total -= v
        else:
            while self.data:
                oldest_t = self.data.peekitem(0)[0]
                if oldest_t > cutoff:
                    break
                v = self.data.popitem(0)[1]
                self.total -= v

    def query(self) -> int:
        return self.total


def run_benchmark(
    *,
    ttl: int,
    n_inserts: int,
    query_every: int,
    seed: int,
    max_step: int,
    value_max: int,
    use_btree: bool,
) -> tuple[float, int, int]:
    rng = random.Random(seed)
    counter = ExpiringCounter(ttl, use_btree=use_btree)
    t = 0

    start = time.perf_counter()
    for i in range(1, n_inserts + 1):
        t += rng.randint(0, max_step)
        value = rng.randint(1, value_max)
        counter.insert(t, value)
        if query_every and i % query_every == 0:
            _ = counter.query()
    elapsed = time.perf_counter() - start
    return elapsed, len(counter.data), counter.total


def main() -> None:
    parser = argparse.ArgumentParser(description="Sliding TTL counter benchmark.")
    parser.add_argument("--ttl", type=int, default=1000, help="time-to-live window size")
    parser.add_argument("--n", type=int, default=200_000, help="number of inserts")
    parser.add_argument("--query-every", type=int, default=10_000, help="query every N inserts")
    parser.add_argument("--seed", type=int, default=123, help="RNG seed")
    parser.add_argument("--max-step", type=int, default=3, help="max timestamp step per insert")
    parser.add_argument("--value-max", type=int, default=5, help="max value per insert")
    args = parser.parse_args()

    print(
        f"N={args.n} TTL={args.ttl} QUERY_EVERY={args.query_every} "
        f"MAX_STEP={args.max_step} VALUE_MAX={args.value_max}"
    )

    btree_time, btree_size, btree_total = run_benchmark(
        ttl=args.ttl,
        n_inserts=args.n,
        query_every=args.query_every,
        seed=args.seed,
        max_step=args.max_step,
        value_max=args.value_max,
        use_btree=True,
    )
    print(f"BTreeDict sweep: {btree_time:.4f}s")

    sorted_time, sorted_size, sorted_total = run_benchmark(
        ttl=args.ttl,
        n_inserts=args.n,
        query_every=args.query_every,
        seed=args.seed,
        max_step=args.max_step,
        value_max=args.value_max,
        use_btree=False,
    )
    print(f"SortedDict sweep: {sorted_time:.4f}s")
    print(
        f"Results match: {btree_size == sorted_size and btree_total == sorted_total} ✓"
        if btree_size == sorted_size and btree_total == sorted_total
        else "Results match: False ❌"
    )
    print(
        "Performance summary: "
        f"BTreeDict={btree_time:.4f}s "
        f"SortedDict={sorted_time:.4f}s "
        f"SortedDict/BTreeDict={sorted_time/btree_time:.2f}x"
    )


if __name__ == "__main__":
    main()
