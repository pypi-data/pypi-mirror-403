from algokit_py.search import linear_search


def test_linear_search_found():
    assert linear_search([1, 2, 3, 4], 3) == 2


def test_linear_search_not_found():
    assert linear_search([1, 2, 3, 4], 5) == -1


def test_linear_search_empty():
    assert linear_search([], 1) == -1


def test_linear_search_generator():
    gen = (x for x in [10, 20, 30])
    assert linear_search(gen, 20) == 1
