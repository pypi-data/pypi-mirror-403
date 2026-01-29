"""
The True Minimum Requirements for Binary Search
Now we can state them precisely:
- The data must be sorted
- The data must support random access (you must be able to get the middle element)
- The elements must be comparable to the target

Every step of binary search answers one question only:
 - "Which half can I safely throw away without losing the target?"

For binary search, always remember this sentence:
At every step, the algorithm maintains a range that is guaranteed to contain the target if it exists.

"""

from typing import Sequence, TypeVar

T = TypeVar('T')
# here we use Sequence because binary search does not support for not indexed iterables.
# Binary search requires a sorted sequence.
def binary_search(sequence: Sequence[T], target: T)-> int:
    """
    This function will perform the binary search. Sequence must be a sorted sequence

    :param sequence: sorted and indexed sequence
    :param target: value that you want to find
    :return: return index of a occurrence, -1 if target is not found


    Time Complexity: O(log(n))
    Space Complexity: O(1)
    """

    left,right = 0, len(sequence)-1

    while left <= right:
        mid = (left + right) // 2

        if sequence[mid] == target:
            return mid

        if target < sequence[mid]:
            right = mid - 1
        else:
            left = mid +1

    return -1
