from collections import UserDict

import pytest

from sortedcollections import SortedDict, SortedSet


def test_sorted_dict_init_kwargs_and_mapping_update():
    sd = SortedDict(c=3, a=1, b=2)
    assert list(sd.items()) == [("a", 1), ("b", 2), ("c", 3)]

    sd.update(UserDict({"d": 4}))
    assert list(sd.items()) == [("a", 1), ("b", 2), ("c", 3), ("d", 4)]


def test_sorted_dict_update_sequence_and_mixed_numeric_types():
    sd = SortedDict()
    sd.update([[2, "b"], [1, "a"]])
    assert list(sd.items()) == [(1, "a"), (2, "b")]

    sd2 = SortedDict()
    sd2.update({1: "a", 2.5: "b"})
    assert list(sd2.items()) == [(1, "a"), (2.5, "b")]


def test_sorted_dict_irange_inclusive_errors():
    sd = SortedDict({1: "a", 2: "b"})
    with pytest.raises(ValueError):
        sd.irange(inclusive=(True,))
    with pytest.raises(TypeError):
        sd.irange(inclusive=1)


def test_sorted_set_slicing_and_deletion():
    ss = SortedSet([1, 2, 3, 4, 5])
    assert ss[::-2] == [5, 3, 1]

    del ss[1]
    assert list(ss) == [1, 3, 4, 5]

    with pytest.raises(TypeError):
        _ = ss["a"]


def test_sorted_set_multi_iterable_ops():
    ss = SortedSet([1, 2, 3, 4, 5])
    diff = ss.difference([2, 3], [5])
    assert list(diff) == [1, 4]

    inter = ss.intersection([2, 3, 6], [3, 4])
    assert list(inter) == [2, 3, 4]

    sym = ss.symmetric_difference([2, 3], [5, 6])
    assert list(sym) == [1, 4, 6]


def test_sorted_set_pop_contains_and_compare():
    ss = SortedSet([1, 2, 3])
    assert ss.pop(0) == 1
    assert 2 in ss
    assert 10 not in ss

    with pytest.raises(IndexError):
        ss.pop(10)

    assert (ss == [2, 3]) is False
