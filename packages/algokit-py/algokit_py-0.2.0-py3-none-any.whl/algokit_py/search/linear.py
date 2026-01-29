from typing import TypeVar, Iterable

T = TypeVar('T')
def linear_search(iterable: Iterable[T] , target: T)-> int:
    """
    This function do linear search.

    :param iterable:
    :param target:
    :return:  return index of first occurrence, -1 if target is not found

    Time complexity: O(n)
    Space complexity: O(1)
    """
    for i,v in enumerate(iterable):
        if v == target:
            return i

    return -1
