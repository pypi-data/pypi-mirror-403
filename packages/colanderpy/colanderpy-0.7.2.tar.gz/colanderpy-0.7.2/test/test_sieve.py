import pytest
import numpy as np
from colanderpy.sieve import sieve


def test_sieve_empty_for_n_less_than_2():
    """Test that sieve returns empty list for n < 2"""
    assert list(sieve(0)) == []
    assert list(sieve(1)) == []
    assert list(sieve(-5)) == []


def test_sieve_small_numbers():
    """Test sieve for small values of n"""
    assert list(sieve(2)) == [2]
    assert list(sieve(3)) == [2, 3]
    assert list(sieve(10)) == [2, 3, 5, 7]


def test_sieve_returns_correct_primes():
    """Test that sieve returns known correct prime sequences"""
    # First 10 primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
    result = sieve(30)
    expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert list(result) == expected


def test_sieve_42():
    """Test sieve(42) returns primes up to 42"""
    result = sieve(42)
    expected = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
    assert list(result) == expected


def test_sieve_100():
    """Test sieve(100) returns correct count of primes"""
    result = sieve(100)
    # There are 25 primes up to 100
    assert len(result) == 25
    # Check first and last
    assert result[0] == 2
    assert result[-1] == 97


def test_sieve_returns_numpy_array():
    """Test that sieve returns a numpy array"""
    result = sieve(10)
    assert isinstance(result, np.ndarray)


def test_sieve_all_results_are_prime():
    """Test that all numbers returned by sieve are actually prime"""
    result = sieve(50)
    for p in result:
        # Check p is prime by testing divisibility
        if p < 2:
            pytest.fail(f"{p} is not prime")
        for i in range(2, int(p**0.5) + 1):
            if p % i == 0:
                pytest.fail(f"{p} is not prime (divisible by {i})")
