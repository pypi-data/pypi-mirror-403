#!/usr/bin/env python3
"""
Cache profiling script for sortedcollections.
Run with: perf stat -e cache-misses,cache-references,L1-dcache-load-misses,LLC-load-misses python scripts/profile_cache.py
"""
import random
from sortedcollections import SortedDict, SortedSet

def profile_sorteddict(n=100000, ops=500000):
    """Profile SortedDict with mixed operations."""
    print(f"Profiling SortedDict: {n} items, {ops} operations")
    
    # Pre-generate keys to avoid profiling random number generation
    keys = list(range(n))
    random.shuffle(keys)
    lookup_keys = [random.randint(0, n-1) for _ in range(ops)]
    
    sd = SortedDict()
    
    # Insert phase
    for k in keys:
        sd[k] = k
    
    # Lookup phase (this is where cache behavior matters most)
    found = 0
    for k in lookup_keys:
        if k in sd:
            found += 1
    
    # Range query phase
    for i in range(1000):
        list(sd.irange(i * 100, i * 100 + 50))
    
    print(f"  Found: {found}")
    return sd

def profile_sortedset(n=100000, ops=500000):
    """Profile SortedSet with mixed operations."""
    print(f"Profiling SortedSet: {n} items, {ops} operations")
    
    keys = list(range(n))
    random.shuffle(keys)
    lookup_keys = [random.randint(0, n-1) for _ in range(ops)]
    
    ss = SortedSet()
    
    # Insert phase
    for k in keys:
        ss.add(k)
    
    # Lookup phase
    found = 0
    for k in lookup_keys:
        if k in ss:
            found += 1
    
    print(f"  Found: {found}")
    return ss

def profile_binary_search_stress(n=100000, ops=1000000):
    """Stress test binary search - most cache-sensitive operation."""
    print(f"Binary search stress test: {n} items, {ops} lookups")
    
    sd = SortedDict((i, i) for i in range(n))
    lookup_keys = [random.randint(0, n-1) for _ in range(ops)]
    
    # Pure lookup - isolates binary search cache behavior
    found = 0
    for k in lookup_keys:
        v = sd.get(k)
        if v is not None:
            found += 1
    
    print(f"  Found: {found}")

if __name__ == "__main__":
    random.seed(42)
    
    print("=" * 60)
    print("Cache Profiling for sortedcollections")
    print("=" * 60)
    
    profile_sorteddict()
    print()
    profile_sortedset()
    print()
    profile_binary_search_stress()
    print()
    print("Done!")
