# sortedcollections

High‑performance sorted containers for CPython backed by a ranked B+ tree.

This project provides **SortedDict** and **SortedSet** as C extensions. The backend is a ranked B+ tree optimized for cache locality, predictable O(log M) operations, and fast iteration/range queries.

## Highlights

- Ranked B+ tree (values stored only in leaves)
- O(log M) lookup/insert/delete and rank‑based indexing
- Leaf‑linked iterators for O(1) step traversal
- Bulk‑loading for union/intersection/difference (O(M))
- Cache‑line aligned node allocations + freelists
- LTO enabled by default, optional PGO

## Install

```bash
python -m pip install sortedcollections-ext
```

Editable (dev) install:

```bash
python -m pip install -e .
```

### Build flags

- Disable LTO:

```bash
SORTEDCOLLECTIONS_LTO=0 python -m pip install -e .
```

- PGO (two‑phase):

```bash
SORTEDCOLLECTIONS_PGO=1 SORTEDCOLLECTIONS_PGO_MODE=gen python -m pip install -e .
python scripts/pgo_train.py
SORTEDCOLLECTIONS_PGO=1 SORTEDCOLLECTIONS_PGO_MODE=use python -m pip install -e .
```

## Quick usage

```python
from sortedcollections import SortedDict, SortedSet

sd = SortedDict()
sd["a"] = 1
sd["b"] = 2

ss = SortedSet([3, 1, 2])
print(list(ss))
```

## API overview

SortedDict
- `__getitem__`, `__setitem__`, `__delitem__`
- `bisect_left`, `bisect_right`
- `irange(min, max, inclusive)`
- `islice(start, stop, reverse)`
- `keys()`, `values()`, `items()` (lazy iterators)

SortedSet
- `add`, `discard`, `remove`
- `bisect_left`, `bisect_right`
- `irange(min, max, inclusive)`
- `islice(start, stop, reverse)`
- `union`, `intersection`, `difference` (bulk‑loaded fast path for SortedSet)

See `docs/` for detailed notes.

## Benchmarks

```bash
python benchmarks/bench_main_api.py --sizes 1000 10000 100000 --only both
```

## Development

```bash
pytest -q
```

## License

MIT
