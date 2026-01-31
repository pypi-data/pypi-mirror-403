import argparse
import random
import time
from statistics import mean, median

from sortedcollections import SortedDict as MySortedDict
from sortedcollections import SortedSet as MySortedSet

try:
    from sortedcontainers import SortedDict as ScSortedDict
    from sortedcontainers import SortedSet as ScSortedSet
except Exception:
    ScSortedDict = None
    ScSortedSet = None


def _timeit(fn, repeats=5, warmup=1):
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        ops = fn()
        elapsed = time.perf_counter() - start
        samples.append(elapsed / ops if ops else float("inf"))
    return median(samples), mean(samples)


def _format_us(value):
    return f"{value * 1_000_000:9.2f}"


def _format_ratio(base, other):
    if other is None:
        return "   n/a  "
    if base == 0:
        return "   inf  "
    return f"{other / base:7.2f}x"


def _print_table(title, rows, have_baseline):
    print(f"\n== {title} ==")
    if have_baseline:
        print("operation      sortedcollections   sortedcontainers     ratio")
        print("------------   -------------------   ---------------   --------")
        for name, ours, theirs in rows:
            ours_s = _format_us(ours)
            theirs_s = _format_us(theirs) if theirs is not None else "   n/a  "
            ratio_s = _format_ratio(ours, theirs)
            print(f"{name:<12}   {ours_s} us/op      {theirs_s} us/op   {ratio_s}")
    else:
        print("operation      sortedcollections")
        print("------------   -------------------")
        for name, ours, _ in rows:
            ours_s = _format_us(ours)
            print(f"{name:<12}   {ours_s} us/op")


def _build_dict(keys, cls):
    d = cls()
    for k in keys:
        d[k] = k
    return d


def _build_set(keys, cls):
    s = cls()
    for k in keys:
        s.add(k)
    return s


def bench_sorted_dict(size, repeats=5, warmup=1, seed=1234, mixed_ops=50_000, hot_ops=200_000, hot_range=10_000):
    rng = random.Random(seed)
    keys = list(range(size))
    rng.shuffle(keys)
    lookup_keys = [keys[i] for i in range(min(size, 10_000))]
    range_min = keys[min(size // 4, size - 1)]
    range_max = keys[min(size // 2, size - 1)]

    def do_insert(cls):
        d = cls()
        for k in keys:
            d[k] = k
        return len(keys)

    def do_get(cls):
        d = _build_dict(keys, cls)
        for k in lookup_keys:
            _ = d[k]
        return len(lookup_keys)

    def do_contains(cls):
        d = _build_dict(keys, cls)
        for k in lookup_keys:
            _ = k in d
        return len(lookup_keys)

    def do_delete(cls):
        d = _build_dict(keys, cls)
        for k in lookup_keys:
            del d[k]
        return len(lookup_keys)

    def do_bisect(cls):
        d = _build_dict(keys, cls)
        for k in lookup_keys:
            _ = d.bisect_left(k)
            _ = d.bisect_right(k)
        return len(lookup_keys) * 2

    def do_irange(cls):
        d = _build_dict(keys, cls)
        try:
            _ = d.irange(min=range_min, max=range_max)
        except TypeError:
            _ = d.irange(minimum=range_min, maximum=range_max)
        return 1

    rows = []
    for label, fn in (
        ("insert", do_insert),
        ("get", do_get),
        ("contains", do_contains),
        ("delete", do_delete),
        ("bisect", do_bisect),
        ("irange", do_irange),
        ("mixed", lambda cls: _mixed_ops_dict(size, cls, ops=mixed_ops)),
        ("hotupd", lambda cls: _hot_updates_dict_increment(size, cls, ops=hot_ops, key_range=hot_range)),
    ):
        ours, _ = _timeit(lambda: fn(MySortedDict), repeats=repeats, warmup=warmup)
        theirs = None
        if ScSortedDict:
            if label == "hotupd":
                theirs, _ = _timeit(
                    lambda: _hot_updates_dict_getset(size, ScSortedDict, ops=hot_ops, key_range=hot_range),
                    repeats=repeats,
                    warmup=warmup,
                )
            else:
                theirs, _ = _timeit(lambda: fn(ScSortedDict), repeats=repeats, warmup=warmup)
        rows.append((label, ours, theirs))

    _print_table(
        f"SortedDict size={size}",
        rows,
        have_baseline=ScSortedDict is not None,
    )


def bench_sorted_set(size, repeats=5, warmup=1, seed=4321, mixed_ops=50_000):
    rng = random.Random(seed)
    keys = list(range(size))
    rng.shuffle(keys)
    lookup_keys = [keys[i] for i in range(min(size, 10_000))]

    def do_add(cls):
        s = cls()
        for k in keys:
            s.add(k)
        return len(keys)

    def do_contains(cls):
        s = _build_set(keys, cls)
        for k in lookup_keys:
            _ = k in s
        return len(lookup_keys)

    def do_remove(cls):
        s = _build_set(keys, cls)
        for k in lookup_keys:
            s.remove(k)
        return len(lookup_keys)

    def do_union(cls):
        s = _build_set(keys, cls)
        other = keys[: min(1000, size)]
        _ = s.union(other)
        return 1

    rows = []
    for label, fn in (
        ("add", do_add),
        ("contains", do_contains),
        ("remove", do_remove),
        ("union", do_union),
        ("mixed", lambda cls: _mixed_ops_set(size, cls, ops=mixed_ops)),
    ):
        ours, _ = _timeit(lambda: fn(MySortedSet), repeats=repeats, warmup=warmup)
        theirs = None
        if ScSortedSet:
            theirs, _ = _timeit(lambda: fn(ScSortedSet), repeats=repeats, warmup=warmup)
        rows.append((label, ours, theirs))

    _print_table(
        f"SortedSet size={size}",
        rows,
        have_baseline=ScSortedSet is not None,
    )


def _mixed_ops_dict(size, cls, seed=2020, ops=50_000):
    rng = random.Random(seed)
    keys = list(range(size))
    rng.shuffle(keys)
    d = cls()
    for k in keys[: size // 2]:
        d[k] = k
    count = 0
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
        count += 1
    return count


def _mixed_ops_set(size, cls, seed=3030, ops=50_000):
    rng = random.Random(seed)
    keys = list(range(size))
    rng.shuffle(keys)
    s = cls()
    for k in keys[: size // 2]:
        s.add(k)
    count = 0
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
        count += 1
    return count


def _hot_updates_dict_increment(size, cls, seed=4040, ops=200_000, key_range=10_000):
    rng = random.Random(seed)
    hot_range = min(size, key_range)
    d = cls()
    count = 0
    for _ in range(ops):
        k = rng.randrange(hot_range)
        d.increment(k, 1)
        count += 1
    return count


def _hot_updates_dict_getset(size, cls, seed=4040, ops=200_000, key_range=10_000):
    rng = random.Random(seed)
    hot_range = min(size, key_range)
    d = cls()
    count = 0
    for _ in range(ops):
        k = rng.randrange(hot_range)
        d[k] = d.get(k, 0) + 1
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Bench sortedcollections vs sortedcontainers")
    parser.add_argument("--sizes", nargs="+", type=int, default=[1_000, 10_000, 100_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--mixed-ops", type=int, default=200_000)
    parser.add_argument("--hot-ops", type=int, default=500_000)
    parser.add_argument("--hot-range", type=int, default=10_000)
    parser.add_argument("--only", choices=["dict", "set", "both"], default="both")
    args = parser.parse_args()

    for size in args.sizes:
        if args.only in ("dict", "both"):
            bench_sorted_dict(
                size,
                repeats=args.repeats,
                warmup=args.warmup,
                mixed_ops=args.mixed_ops,
                hot_ops=args.hot_ops,
                hot_range=args.hot_range,
            )
        if args.only in ("set", "both"):
            bench_sorted_set(
                size,
                repeats=args.repeats,
                warmup=args.warmup,
                mixed_ops=args.mixed_ops,
            )

    if not (ScSortedDict and ScSortedSet):
        print("\n(sortedcontainers not installed; skipping its benchmarks)")


if __name__ == "__main__":
    main()
