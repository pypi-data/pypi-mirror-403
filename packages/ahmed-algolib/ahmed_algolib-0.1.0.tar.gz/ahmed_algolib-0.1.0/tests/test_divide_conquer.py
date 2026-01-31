import algolib
from algolib import max_subarray_sum

def test_max_subarray_sum():
    assert max_subarray_sum([1, -2, 3, 4, -1]) == 7
    assert max_subarray_sum([5]) == 5
