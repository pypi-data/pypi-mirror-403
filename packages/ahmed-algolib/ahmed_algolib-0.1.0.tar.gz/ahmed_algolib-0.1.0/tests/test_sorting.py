import algolib
from algolib import quick_sort, merge_sort

def test_quick_sort():
    assert quick_sort([3,1,2]) == [1,2,3]
    assert quick_sort([]) == []

def test_merge_sort():
    assert merge_sort([3,1,2]) == [1,2,3]
    assert merge_sort([5]) == [5]
