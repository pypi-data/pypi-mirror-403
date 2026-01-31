import random

import pytest

from sortedcollections import SortedDict, SortedSet


def test_sorted_dict_basic_ops():
    sd = SortedDict()
    sd[2] = "b"
    sd[1] = "a"
    sd[3] = "c"
    assert list(sd) == [1, 2, 3]
    assert len(sd) == 3
    assert sd[1] == "a"
    assert 2 in sd

    del sd[2]
    assert list(sd) == [1, 3]
    sd.clear()
    assert len(sd) == 0


def test_sorted_dict_init_update_and_views():
    sd = SortedDict([(2, "b"), (1, "a")])
    assert list(sd.items()) == [(1, "a"), (2, "b")]
    sd.update({3: "c", 4: "d"})
    assert list(sd.keys()) == [1, 2, 3, 4]
    assert list(sd.values()) == ["a", "b", "c", "d"]

    keys_view = sd.keys()
    values_view = sd.values()
    items_view = sd.items()
    assert len(keys_view) == 4
    assert keys_view[0] == 1
    assert values_view[0] == "a"
    assert items_view[0] == (1, "a")
    assert 2 in keys_view
    assert "c" in values_view
    assert (3, "c") in items_view
    assert list(reversed(keys_view)) == [4, 3, 2, 1]


def test_sorted_dict_helpers():
    sd = SortedDict([(1, "a"), (3, "c"), (5, "e")])
    assert sd.get(3) == "c"
    assert sd.get(2, "missing") == "missing"
    assert sd.setdefault(3, "x") == "c"
    assert sd.setdefault(2, "b") == "b"
    assert list(sd.items()) == [(1, "a"), (2, "b"), (3, "c"), (5, "e")]
    assert sd.pop(2) == "b"

    key, value = sd.popitem()
    assert (key, value) == (5, "e")
    assert sd.peekitem() == (1, "a")
    assert sd.peekitem(-1) == (3, "c")


def test_sorted_dict_increment():
    sd = SortedDict()
    assert sd.increment("a") == 1
    assert sd["a"] == 1
    assert sd.increment("a", 2) == 3
    assert sd["a"] == 3
    assert sd.increment("b", 5, 10) == 15
    assert sd["b"] == 15


def test_sorted_dict_bisect_and_ranges():
    sd = SortedDict([(1, "a"), (3, "c"), (5, "e"), (7, "g")])
    assert sd.bisect_left(3) == 1
    assert sd.bisect_right(3) == 2
    assert sd.bisect(3) == 2
    assert sd.index(5) == 2

    assert list(sd.irange(3, 6)) == [3, 5]
    assert list(sd.irange(3, 6, inclusive=(False, True))) == [5]
    assert list(sd.irange(3, 6, reverse=True)) == [5, 3]
    assert list(sd.islice(1, 3)) == [3, 5]
    assert list(sd.islice(0, 2, reverse=True)) == [7, 5]


def test_sorted_dict_copy_and_fromkeys():
    sd = SortedDict([(1, "a"), (2, "b")])
    copy_sd = sd.copy()
    assert list(copy_sd.items()) == [(1, "a"), (2, "b")]
    fk = SortedDict.fromkeys([3, 1], "z")
    assert list(fk.items()) == [(1, "z"), (3, "z")]


def test_sorted_dict_update_from_sorteddict_and_items():
    sd = SortedDict({1: "a", 3: "c"})
    other = SortedDict({2: "b"})
    sd.update(other)
    assert list(sd.items()) == [(1, "a"), (2, "b"), (3, "c")]

    empty = SortedDict()
    empty.update(sd)
    assert list(empty.items()) == [(1, "a"), (2, "b"), (3, "c")]

    data = {5: "e", 4: "d"}
    sd_items = SortedDict()
    sd_items.update(data.items())
    assert list(sd_items.items()) == [(4, "d"), (5, "e")]

def test_sorted_set_basic_ops():
    ss = SortedSet([3, 1, 2, 1])
    assert list(ss) == [1, 2, 3]
    ss.add(0)
    ss.add(3)
    assert list(ss) == [0, 1, 2, 3]
    ss.discard(1)
    assert list(ss) == [0, 2, 3]
    ss.remove(2)
    assert list(ss) == [0, 3]
    assert ss.pop() in {0, 3}


def test_sorted_set_setops_and_queries():
    ss = SortedSet([1, 2, 3, 4, 5])
    assert ss.bisect_left(3) == 2
    assert ss.bisect_right(3) == 3
    assert ss.index(4) == 3
    assert list(ss.irange(2, 4)) == [2, 3, 4]
    assert list(ss.islice(1, 3)) == [2, 3]
    assert ss[0] == 1
    assert ss[-1] == 5
    assert ss[1:4] == [2, 3, 4]

    other = SortedSet([4, 5, 6])
    assert list(ss.union(other)) == [1, 2, 3, 4, 5, 6]
    assert list(ss.difference(other)) == [1, 2, 3]
    assert list(ss.intersection(other)) == [4, 5]
    assert list(ss.symmetric_difference(other)) == [1, 2, 3, 6]
    assert list(ss | other) == [1, 2, 3, 4, 5, 6]
    assert list(ss & other) == [4, 5]
    assert list(ss - other) == [1, 2, 3]
    assert list(ss ^ other) == [1, 2, 3, 6]


def test_sorted_set_union_update_and_symdiff_iterables():
    ss = SortedSet([1, 2, 3])
    res = ss.union([2, 4], {5})
    assert list(res) == [1, 2, 3, 4, 5]

    ss.update(SortedSet([3, 4]))
    assert list(ss) == [1, 2, 3, 4]

    res = ss.symmetric_difference([2, 4, 6])
    assert list(res) == [1, 3, 6]

def test_sortedcontainers_compat_smoke():
    sortedcontainers = pytest.importorskip("sortedcontainers")
    sc = sortedcontainers.SortedDict()
    sd = SortedDict()

    rng = random.Random(1337)
    for _ in range(200):
        op = rng.choice(["set", "del", "pop", "setdefault"])
        key = rng.randint(0, 50)
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
