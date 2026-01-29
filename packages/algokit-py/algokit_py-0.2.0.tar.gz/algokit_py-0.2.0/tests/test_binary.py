from algokit_py.search import binary_search


def test_binary_search_found():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3


def test_binary_search_not_found():
    assert binary_search([1, 2, 3, 4, 5], 10) == -1


def test_binary_search_single_element():
    assert binary_search([7], 7) == 0


def test_binary_search_empty():
    assert binary_search([], 1) == -1
