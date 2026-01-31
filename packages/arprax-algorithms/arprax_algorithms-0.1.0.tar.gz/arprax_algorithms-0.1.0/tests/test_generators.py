from arprax_algorithms.generators import random_array, sorted_array

def test_random_array_length():
    data = random_array(100)
    assert len(data) == 100

def test_sorted_array_is_actually_sorted():
    data = sorted_array(50)
    assert data == sorted(data)