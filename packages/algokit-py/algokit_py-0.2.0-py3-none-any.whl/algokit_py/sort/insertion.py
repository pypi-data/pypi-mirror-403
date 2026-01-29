from typing import MutableSequence, TypeVar

T = TypeVar('T')
def insertion_sort(sequence: MutableSequence[T])-> None:
    """
    At the start of iteration i, the subarray sequence[0:i] is sorted.

    :param sequence
    :return None

    Worst Case Time Complexity: O(n²)
    Space Complexity: O(1)
    """
    length = len(sequence)
    for i in range(1, length):
        key = sequence[i]
        j = i-1
        while sequence[j] > key and j >= 0:
            sequence[j+1]= sequence[j]
            j -= 1
        sequence[j + 1] = key





