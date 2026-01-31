"""Tests for module imports in colanderpy package"""

def test_import_colanderpy():
    """Test that colanderpy can be imported"""
    import colanderpy
    assert colanderpy is not None


def test_import_sieve():
    """Test that sieve module can be imported"""
    from colanderpy import sieve
    assert hasattr(sieve, 'sieve')
    assert hasattr(sieve, 'main')


def test_import_pi_function():
    """Test that pi_function module can be imported"""
    from colanderpy import pi_function
    assert hasattr(pi_function, 'pi_function')
    assert hasattr(pi_function, 'main')


def test_import_functions_directly():
    """Test that functions can be imported directly"""
    from colanderpy.sieve import sieve
    from colanderpy.pi_function import pi_function
    
    assert callable(sieve)
    assert callable(pi_function)
