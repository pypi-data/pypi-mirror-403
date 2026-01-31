import pytest
from colanderpy.pi_function import pi_function


def test_pi_function_zero_and_one():
    """Test pi_function for n=0 and n=1"""
    assert pi_function(0) == 0
    assert pi_function(1) == 0


def test_pi_function_small_values():
    """Test pi_function for small values"""
    assert pi_function(2) == 1  # Only 2
    assert pi_function(3) == 2  # 2, 3
    assert pi_function(5) == 3  # 2, 3, 5
    assert pi_function(10) == 4  # 2, 3, 5, 7


def test_pi_function_42():
    """Test pi_function(42) - there are 13 primes up to 42"""
    assert pi_function(42) == 13


def test_pi_function_100():
    """Test pi_function(100) - there are 25 primes up to 100"""
    assert pi_function(100) == 25


def test_pi_function_1000():
    """Test pi_function(1000) - there are 168 primes up to 1000"""
    assert pi_function(1000) == 168


def test_pi_function_negative():
    """Test pi_function for negative numbers"""
    assert pi_function(-5) == 0


def test_pi_function_is_non_decreasing():
    """Test that pi_function is non-decreasing"""
    values = [pi_function(n) for n in range(0, 50)]
    for i in range(1, len(values)):
        assert values[i] >= values[i-1], f"pi({i}) < pi({i-1})"
