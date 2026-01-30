import random
import time

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


def main():
    start = time.perf_counter()
    train_sorted_dict()
    train_sorted_set()
    elapsed = time.perf_counter() - start
    print(f"pgo training completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
