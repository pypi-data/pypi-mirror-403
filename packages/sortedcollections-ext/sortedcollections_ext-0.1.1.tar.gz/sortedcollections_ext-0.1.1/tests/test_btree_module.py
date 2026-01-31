import pytest

import btree


def test_btree_basic_ops_and_iterators():
    bt = btree.BTree()
    bt.insert(2, "b")
    bt.insert(1, "a")
    bt.insert(3, "c")

    assert len(bt) == 3
    assert bt.search(1) == "a"
    assert bt.search(2) == "b"
    assert bt.search(3) == "c"

    assert list(bt.keys()) == [1, 2, 3]
    assert list(bt.values()) == ["a", "b", "c"]
    assert list(bt.items()) == [(1, "a"), (2, "b"), (3, "c")]

    assert bt.bisect_left(2) == 1
    assert bt.bisect_right(2) == 2

    bt.insert(2, "bb")
    assert bt.search(2) == "bb"

    bt.delete(2)
    assert list(bt.keys()) == [1, 3]
    with pytest.raises(KeyError):
        bt.search(2)
    with pytest.raises(KeyError):
        bt.delete(2)

    bt.clear()
    assert len(bt) == 0
    assert list(bt.keys()) == []


def test_btree_irange_and_errors():
    bt = btree.BTree()
    for key in [1, 3, 5, 7]:
        bt.insert(key, str(key))

    assert bt.irange() == [1, 3, 5, 7]
    assert bt.irange(3, 6) == [3, 5]
    assert bt.irange(3, 6, inclusive=(False, True)) == [5]

    with pytest.raises(ValueError):
        bt.irange(inclusive=(True,))

    with pytest.raises(TypeError):
        bt.irange(inclusive=1)

    with pytest.raises(TypeError):
        bt.insert("x", "bad")


def test_btree_empty_errors_and_bisect():
    bt = btree.BTree()
    with pytest.raises(KeyError):
        bt.search(1)
    with pytest.raises(KeyError):
        bt.delete(1)

    assert bt.bisect_left(10) == 0
    assert bt.bisect_right(10) == 0
    assert bt.irange() == []


def test_btree_float_keys_and_mixed_int_subclass():
    bt = btree.BTree()
    for key in [1.5, 0.5, 2.0, 2.5]:
        bt.insert(key, str(key))
    assert list(bt.keys()) == [0.5, 1.5, 2.0, 2.5]
    assert bt.irange(1.0, 2.0) == [1.5, 2.0]

    class IntSub(int):
        pass

    bt2 = btree.BTree()
    bt2.insert(1, "a")
    bt2.insert(IntSub(2), "b")
    bt2.insert(3, "c")
    assert list(bt2.keys()) == [1, 2, 3]


def test_btree_custom_keys_and_compare_errors():
    class Key:
        __slots__ = ("v",)

        def __init__(self, v):
            self.v = v

        def __lt__(self, other):
            return self.v < other.v

        def __eq__(self, other):
            return self.v == other.v

    bt = btree.BTree()
    for key in [Key(2), Key(1), Key(3)]:
        bt.insert(key, key.v)
    assert [k.v for k in bt.keys()] == [1, 2, 3]
    assert bt.search(Key(2)) == 2

    class BadKey:
        __slots__ = ("v",)

        def __init__(self, v):
            self.v = v

        def __lt__(self, other):
            raise RuntimeError("boom")

        def __eq__(self, other):
            return False

    bt_bad = btree.BTree()
    bt_bad.insert(BadKey(1), "a")
    with pytest.raises(RuntimeError):
        bt_bad.insert(BadKey(2), "b")


def test_btree_bulk_insert_delete_rebalance():
    bt = btree.BTree()
    for i in range(20000):
        bt.insert(i, i)
    assert len(bt) == 20000

    for i in range(0, 20000, 2):
        bt.delete(i)
    for i in range(19999, -1, -2):
        bt.delete(i)

    assert len(bt) == 0


def test_btree_iter_mutation_raises():
    bt = btree.BTree()
    for i in range(5):
        bt.insert(i, i)
    it = bt.keys()
    assert next(it) == 0
    bt.insert(10, 10)
    with pytest.raises(RuntimeError):
        next(it)


def test_btree_nan_rejected():
    nan = float("nan")
    bt = btree.BTree()
    with pytest.raises(ValueError):
        bt.insert(nan, "x")
    with pytest.raises(ValueError):
        bt.search(nan)
    with pytest.raises(ValueError):
        bt.bisect_left(nan)
    with pytest.raises(ValueError):
        bt.irange(nan, None)


def test_btree_separator_key_released_after_delete():
    import gc
    import weakref

    class Key:
        __slots__ = ("v", "__weakref__")

        def __init__(self, v):
            self.v = v

        def __lt__(self, other):
            return self.v < other.v

        def __eq__(self, other):
            return self.v == other.v

    bt = btree.BTree()
    keys = [Key(i) for i in range(130)]
    for k in keys:
        bt.insert(k, k.v)

    target = keys[64]
    ref = weakref.ref(target)
    bt.delete(target)
    keys[64] = None
    del target
    gc.collect()
    assert ref() is None
