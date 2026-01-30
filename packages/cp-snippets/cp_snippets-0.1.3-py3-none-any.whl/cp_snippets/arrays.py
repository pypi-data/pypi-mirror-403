from typing import List, Tuple, Optional
from collections import deque

def get_prefix_sum(arr: List[int]) -> List[int]:
    """
    Computes the prefix sum array P where P[i] is the sum of arr[0...i-1].
    P[0] = 0.
    """
    n = len(arr)
    prefix_sum = [0] * (n + 1)
    for i in range(n):
        prefix_sum[i + 1] = prefix_sum[i] + arr[i]
    return prefix_sum


def query_range_sum(prefix_sum: List[int], l: int, r: int) -> int:
    """
    Returns the sum of arr[l...r] (inclusive) using the prefix sum array.
    """
    return prefix_sum[r + 1] - prefix_sum[l]


class DifferenceArray:
    """
    Helper class for range updates using difference array technique.
    """
    def __init__(self, arr: List[int]):
        self.n = len(arr)
        # diff array size is n+1 to handle updates ending at n-1 effortlessly
        self.diff = [0] * (self.n + 1)
        self.diff[0] = arr[0]
        for i in range(1, self.n):
            self.diff[i] = arr[i] - arr[i - 1]

    def update(self, l: int, r: int, val: int):
        """
        Adds val to arr[l...r] (inclusive).
        """
        self.diff[l] += val
        self.diff[r + 1] -= val

    def get_array(self) -> List[int]:
        """
        Reconstructs and returns the modified array.
        """
        arr = [0] * self.n
        arr[0] = self.diff[0]
        for i in range(1, self.n):
            arr[i] = arr[i - 1] + self.diff[i]
        return arr


def sliding_window_sum(arr: List[int], k: int) -> List[int]:
    """
    Calculates the sum of every window of size k.
    """
    if not arr or k <= 0 or k > len(arr):
        return []
    
    window_sum = sum(arr[:k])
    result = [window_sum]
    for i in range(len(arr) - k):
        window_sum = window_sum - arr[i] + arr[i + k]
        result.append(window_sum)
    return result


def sliding_window_max(arr: List[int], k: int) -> List[int]:
    """
    Calculates the maximum of every window of size k using a deque.
    """
    if not arr or k <= 0 or k > len(arr):
        return []

    result = []
    dq = deque()

    for i in range(len(arr)):
        # Remove elements out of the current window
        while dq and dq[0] < i - k + 1:
            dq.popleft()

        # Remove elements smaller than the current element from the right
        while dq and arr[dq[-1]] < arr[i]:
            dq.pop()

        dq.append(i)

        # The first window is completed at index k-1
        if i >= k - 1:
            result.append(arr[dq[0]])

    return result


def max_subarray_sum(arr: List[int]) -> int:
    """
    Finds the maximum subarray sum using Kadane's Algorithm.
    Returns 0 if the array is empty. For arrays with all negative numbers, returns the max single element.
    """
    if not arr:
        return 0
    
    max_so_far = arr[0]
    current_max = arr[0]
    
    for i in range(1, len(arr)):
        current_max = max(arr[i], current_max + arr[i])
        max_so_far = max(max_so_far, current_max)
        
    return max_so_far


def two_sum_sorted(arr: List[int], target: int) -> Optional[Tuple[int, int]]:
    """
    Finds two indices (i, j) in a sorted array such that arr[i] + arr[j] == target.
    Returns (i, j) 0-indexed if found, otherwise None.
    """
    l, r = 0, len(arr) - 1
    while l < r:
        curr_sum = arr[l] + arr[r]
        if curr_sum == target:
            return (l, r)
        elif curr_sum < target:
            l += 1
        else:
            r -= 1
    return None
