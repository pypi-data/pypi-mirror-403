
from algokit_py.sort import insertion_sort


def test_insertion_sort_basic():
    data = [3, 1, 2]
    insertion_sort(data)
    assert data == [1, 2, 3]


def test_insertion_sort_already_sorted():
    data = [1, 2, 3, 4]
    insertion_sort(data)
    assert data == [1, 2, 3, 4]


def test_insertion_sort_reverse():
    data = [4, 3, 2, 1]
    insertion_sort(data)
    assert data == [1, 2, 3, 4]


def test_insertion_sort_single_element():
    data = [5]
    insertion_sort(data)
    assert data == [5]


def test_insertion_sort_empty():
    data = []
    insertion_sort(data)
    assert data == []
