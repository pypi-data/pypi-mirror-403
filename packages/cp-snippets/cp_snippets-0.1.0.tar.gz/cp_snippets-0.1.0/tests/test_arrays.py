import unittest
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pycp.arrays import (
    get_prefix_sum, query_range_sum, DifferenceArray,
    sliding_window_sum, sliding_window_max, max_subarray_sum, two_sum_sorted
)

class TestArrayUtils(unittest.TestCase):
    def test_prefix_sum(self):
        arr = [1, 2, 3, 4, 5]
        ps = get_prefix_sum(arr)
        self.assertEqual(ps, [0, 1, 3, 6, 10, 15])
        self.assertEqual(query_range_sum(ps, 0, 2), 6) # 1+2+3
        self.assertEqual(query_range_sum(ps, 1, 3), 9) # 2+3+4
        self.assertEqual(query_range_sum(ps, 2, 2), 3) # 3

    def test_difference_array(self):
        arr = [1, 2, 3, 4, 5]
        da = DifferenceArray(arr)
        da.update(0, 2, 2) # [3, 4, 5, 4, 5]
        da.update(1, 4, 1) # [3, 5, 6, 5, 6]
        self.assertEqual(da.get_array(), [3, 5, 6, 5, 6])

    def test_sliding_window_sum(self):
        arr = [1, 3, 2, 6, -1, 4, 1, 8, 2]
        self.assertEqual(sliding_window_sum(arr, 5), [11, 14, 12, 18, 14])
        self.assertEqual(sliding_window_sum([1, 2], 3), [])
        
    def test_sliding_window_max(self):
        arr = [1, 3, -1, -3, 5, 3, 6, 7]
        self.assertEqual(sliding_window_max(arr, 3), [3, 3, 5, 5, 6, 7])
        self.assertEqual(sliding_window_max([1], 1), [1])
        
    def test_kadane(self):
        self.assertEqual(max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]), 6)
        self.assertEqual(max_subarray_sum([-1, -2, -3]), -1)
        self.assertEqual(max_subarray_sum([1, 2, 3]), 6)
        self.assertEqual(max_subarray_sum([]), 0)

    def test_two_sum_sorted(self):
        arr = [2, 7, 11, 15]
        self.assertEqual(two_sum_sorted(arr, 9), (0, 1))
        self.assertEqual(two_sum_sorted(arr, 20), None)
        self.assertEqual(two_sum_sorted([2, 3, 4], 6), (0, 2))

if __name__ == '__main__':
    unittest.main()
