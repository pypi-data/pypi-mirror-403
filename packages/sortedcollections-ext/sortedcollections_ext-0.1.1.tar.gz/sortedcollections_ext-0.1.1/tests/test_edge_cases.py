import random

import pytest

from sortedcollections import SortedDict, SortedSet


def test_sorted_dict_missing_and_empty_errors():
    sd = SortedDict()
    with pytest.raises(KeyError):
        _ = sd[1]
    with pytest.raises(KeyError):
        sd.popitem()
    with pytest.raises(KeyError):
        sd.peekitem()

    sd[1] = "a"
    with pytest.raises(KeyError):
        sd.pop(2)


def test_sorted_dict_get_signature_errors():
    sd = SortedDict({1: "a"})
    with pytest.raises(TypeError):
        sd.get()
    with pytest.raises(TypeError):
        sd.get(1, "x", "y")
    with pytest.raises(TypeError):
        sd.get(key=1, default="x", extra="y")


def test_sorted_dict_update_sequence_errors():
    sd = SortedDict()
    with pytest.raises(ValueError):
        sd.update([(1, 2, 3)])
    with pytest.raises(ValueError):
        sd.update([("only_key",)])

def test_sorted_dict_view_updates():
    sd = SortedDict([(2, "b"), (1, "a")])
    keys = sd.keys()
    values = sd.values()
    items = sd.items()
    sd[3] = "c"
    assert list(keys) == [1, 2, 3]
    assert list(values) == ["a", "b", "c"]
    assert list(items) == [(1, "a"), (2, "b"), (3, "c")]



def test_sorted_set_errors_and_slices():
    ss = SortedSet()
    with pytest.raises(IndexError):
        ss.pop()
    with pytest.raises(KeyError):
        ss.remove(1)

    ss = SortedSet([5, 1, 3, 2, 4])
    del ss[::2]
    assert list(ss) == [2, 4]
    del ss[::-1]
    assert list(ss) == []


def test_sorted_set_setitem_not_supported():
    ss = SortedSet([1, 2, 3])
    with pytest.raises(NotImplementedError):
        ss[0] = 10


def test_sorted_set_getitem_out_of_range():
    ss = SortedSet([1, 2, 3])
    with pytest.raises(IndexError):
        _ = ss[3]
    with pytest.raises(IndexError):
        _ = ss[-4]

def test_sorted_set_add_duplicates():
    ss = SortedSet([1, 2, 3])
    ss.add(2)
    ss.add(2)
    assert list(ss) == [1, 2, 3]


def test_sorted_dict_irange_edge_cases():
    sd = SortedDict([(1, "a"), (3, "c"), (5, "e")])
    assert list(sd.irange()) == [1, 3, 5]
    assert list(sd.irange(None, 3)) == [1, 3]
    assert list(sd.irange(3, None)) == [3, 5]
    assert list(sd.irange(3, 3, inclusive=(False, False))) == []


def test_sorted_dict_bisect_empty():
    sd = SortedDict()
    assert sd.bisect_left(1) == 0
    assert sd.bisect_right(1) == 0
    assert list(sd.irange()) == []



def test_sorted_set_irange_edge_cases():
    ss = SortedSet([1, 2, 3, 4, 5])
    assert list(ss.irange()) == [1, 2, 3, 4, 5]
    assert list(ss.irange(None, 3)) == [1, 2, 3]
    assert list(ss.irange(3, None)) == [3, 4, 5]
    assert list(ss.irange(3, 3, inclusive=(False, False))) == []


def test_sorted_set_bisect_empty():
    ss = SortedSet()
    assert ss.bisect_left(1) == 0
    assert ss.bisect_right(1) == 0
    assert list(ss.islice(0, 10)) == []


def test_sorted_set_islice_bounds():
    ss = SortedSet([1, 2, 3, 4, 5])
    assert list(ss.islice(-5, 100)) == [1, 2, 3, 4, 5]
    assert list(ss.islice(2, 2)) == []
    assert list(ss.islice(0, 5, reverse=True)) == [5, 4, 3, 2, 1]


def test_sorted_dict_views_contains():
    sd = SortedDict([(1, "a"), (2, "b")])
    assert 1 in sd.keys()
    assert "b" in sd.values()
    assert (1, "a") in sd.items()
    assert 3 not in sd.keys()
    assert "c" not in sd.values()
    assert (3, "c") not in sd.items()
    assert list(reversed(sd.values())) == ["b", "a"]
    assert list(reversed(sd.items())) == [(2, "b"), (1, "a")]


def test_sorted_set_update_variants():
    ss = SortedSet([1, 2, 3])
    ss.update([3, 4, 5], [5, 6])
    assert list(ss) == [1, 2, 3, 4, 5, 6]

    ss2 = SortedSet([1, 2, 3, 4])
    ss2.difference_update([2, 3])
    assert list(ss2) == [1, 4]

    ss3 = SortedSet([1, 2, 3, 4])
    ss3.intersection_update([2, 4, 6])
    assert list(ss3) == [2, 4]

    ss4 = SortedSet([1, 2, 3, 4])
    ss4.symmetric_difference_update([3, 4, 5])
    assert list(ss4) == [1, 2, 5]


def test_iter_mutation_raises_sortedcollections():
    sd = SortedDict({1: "a", 2: "b"})
    it = iter(sd.keys())
    assert next(it) == 1
    sd[3] = "c"
    with pytest.raises(RuntimeError):
        next(it)

    ss = SortedSet([1, 2, 3])
    it2 = iter(ss)
    assert next(it2) == 1
    ss.add(4)
    with pytest.raises(RuntimeError):
        next(it2)


def test_nan_rejected_sortedcollections():
    nan = float("nan")
    sd = SortedDict()
    with pytest.raises(ValueError):
        sd[nan] = 1
    with pytest.raises(ValueError):
        sd.irange(nan, None)

    ss = SortedSet()
    with pytest.raises(ValueError):
        ss.add(nan)


def test_gc_cycle_sorted_dict():
    import gc
    import weakref

    sd = SortedDict()
    sd["self"] = sd
    ref = weakref.ref(sd)
    sd = None
    gc.collect()
    assert ref() is None


def test_sorted_set_comparisons():
    ss = SortedSet([1, 2, 3])
    other = SortedSet([1, 2, 3, 4])
    assert ss < other
    assert other > ss
    assert ss != other
    assert ss <= other
    assert other >= ss
    assert ss == SortedSet([1, 2, 3])
    assert ss == {1, 2, 3}
    assert ss < {1, 2, 3, 4}
    assert not (ss > {1, 2, 3, 4})



def test_sorted_set_repr_and_setops_inplace():
    ss = SortedSet([1, 2, 3])
    assert "SortedSet" in repr(ss)
    ss |= {3, 4}
    assert list(ss) == [1, 2, 3, 4]
    ss &= {2, 3, 5}
    assert list(ss) == [2, 3]
    ss ^= {3, 4}
    assert list(ss) == [2, 4]
    ss -= {2}
    assert list(ss) == [4]


def test_large_split_merge_stability():
    ss = SortedSet(range(2100))
    del ss[:1500]
    assert list(ss) == list(range(1500, 2100))


def test_sorted_dict_bulk_update_and_repr():
    items = [(i, i * 2) for i in range(2001)]
    sd = SortedDict(items)
    assert sd[0] == 0
    assert sd[2000] == 4000
    assert "SortedDict" in repr(sd)

    sd2 = SortedDict()
    sd2.update(items)
    assert list(sd2.items()) == items


def test_sorted_dict_popitem_index():
    sd = SortedDict([(1, "a"), (2, "b"), (3, "c")])
    assert sd.popitem(0) == (1, "a")
    assert sd.popitem(-1) == (3, "c")


def test_randomized_ops_consistency_sorted_dict():
    sortedcontainers = pytest.importorskip("sortedcontainers")
    sc = sortedcontainers.SortedDict()
    sd = SortedDict()
    rng = random.Random(2024)

    for _ in range(500):
        op = rng.choice(["set", "del", "pop", "setdefault"])
        key = rng.randint(-20, 20)
        if op == "set":
            value = rng.randint(0, 1000)
            sc[key] = value
            sd[key] = value
        elif op == "del":
            if key in sc:
                del sc[key]
                del sd[key]
        elif op == "pop":
            if key in sc:
                assert sd.pop(key) == sc.pop(key)
            else:
                assert sd.pop(key, None) == sc.pop(key, None)
        else:
            value = rng.randint(0, 1000)
            assert sd.setdefault(key, value) == sc.setdefault(key, value)

        assert list(sd.items()) == list(sc.items())



def test_randomized_ops_consistency_sorted_set():
    sortedcontainers = pytest.importorskip("sortedcontainers")
    sc = sortedcontainers.SortedSet()
    ss = SortedSet()
    rng = random.Random(2026)

    for _ in range(500):
        op = rng.choice(["add", "discard", "remove", "pop"])
        if op == "add":
            value = rng.randint(-50, 50)
            sc.add(value)
            ss.add(value)
        elif op == "discard":
            value = rng.randint(-50, 50)
            sc.discard(value)
            ss.discard(value)
        elif op == "remove":
            value = rng.randint(-50, 50)
            if value in sc:
                sc.remove(value)
                ss.remove(value)
            else:
                with pytest.raises(KeyError):
                    ss.remove(value)
        else:
            if sc:
                idx = rng.randint(-len(sc), len(sc) - 1)
                assert ss.pop(idx) == sc.pop(idx)
            else:
                with pytest.raises(IndexError):
                    ss.pop()

        assert list(ss) == list(sc)
