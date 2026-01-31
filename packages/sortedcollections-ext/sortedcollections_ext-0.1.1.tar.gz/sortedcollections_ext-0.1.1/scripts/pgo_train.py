import random
import time
import os

from sortedcollections import SortedDict, SortedSet


def train_sorted_dict(size=200_000, ops=300_000, seed=1234):
    rng = random.Random(seed)
    keys = list(range(size))
    rng.shuffle(keys)
    d = SortedDict()
    for k in keys[: size // 2]:
        d[k] = k
    for _ in range(ops):
        r = rng.random()
        k = rng.randrange(size)
        if r < 0.45:
            d[k] = k
        elif r < 0.75:
            try:
                _ = d[k]
            except KeyError:
                pass
        elif r < 0.9:
            try:
                del d[k]
            except KeyError:
                pass
        else:
            _ = d.bisect_left(k)
            _ = d.bisect_right(k)
    return d


def train_sorted_set(size=200_000, ops=300_000, seed=4321):
    rng = random.Random(seed)
    keys = list(range(size))
    rng.shuffle(keys)
    s = SortedSet()
    for k in keys[: size // 2]:
        s.add(k)
    for _ in range(ops):
        r = rng.random()
        k = rng.randrange(size)
        if r < 0.5:
            s.add(k)
        elif r < 0.8:
            _ = k in s
        else:
            try:
                s.remove(k)
            except KeyError:
                pass
    return s


def train_intervals(n=1_000_000, t_max=1_000_000, max_len=200, seed=42):
    rng = random.Random(seed)
    intervals = []
    for _ in range(n):
        start = rng.randrange(0, t_max)
        length = rng.randrange(1, max_len + 1)
        end = min(start + length, t_max + 1)
        if end == start:
            end = start + 1
        intervals.append((start, end))

    events = SortedDict()  # time -> delta
    for start, end in intervals:
        events[start] = events.get(start, 0) + 1
        events[end] = events.get(end, 0) - 1

    cur = 0
    max_overlap = 0
    times = list(events.keys())
    for i, t in enumerate(times):
        cur += events[t]
        if cur > max_overlap:
            max_overlap = cur
    return max_overlap


def main():
    start = time.perf_counter()
    train_sorted_dict()
    train_sorted_set()
    train_intervals(
        n=int(os.environ.get("SC_PGO_INTERVALS_N", "1000000")),
        t_max=int(os.environ.get("SC_PGO_INTERVALS_TMAX", "1000000")),
        max_len=int(os.environ.get("SC_PGO_INTERVALS_MAX_LEN", "200")),
        seed=int(os.environ.get("SC_PGO_INTERVALS_SEED", "42")),
    )
    elapsed = time.perf_counter() - start
    print(f"pgo training completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
