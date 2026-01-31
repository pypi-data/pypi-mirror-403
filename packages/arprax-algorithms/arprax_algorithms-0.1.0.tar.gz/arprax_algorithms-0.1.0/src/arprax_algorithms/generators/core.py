import random
from typing import List

def random_array(n: int, lo: int = 0, hi: int = 1000) -> List[int]:
    """Generates an array of n random integers."""
    return [random.randint(lo, hi) for _ in range(n)]

def sorted_array(n: int) -> List[int]:
    """Generates an array of n integers in ascending order."""
    return list(range(n))

def reverse_sorted_array(n: int) -> List[int]:
    """Generates an array of n integers in descending order (Worst case for many algos)."""
    return list(range(n, 0, -1))