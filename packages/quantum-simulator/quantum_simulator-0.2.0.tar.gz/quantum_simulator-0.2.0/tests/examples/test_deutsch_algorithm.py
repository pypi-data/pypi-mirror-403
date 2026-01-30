"""
Test for Deutsch Algorithm example.
"""

import sys
import os
import pytest

# Add the src directory to the path so we can import the examples
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from examples.deutsch_algorithm import (
    create_constant_zero_oracle,
    create_constant_one_oracle, 
    create_balanced_identity_oracle,
    create_balanced_negation_oracle,
    deutsch_algorithm
)


def test_constant_zero_oracle():
    """Test that constant zero oracle works correctly."""
    oracle = create_constant_zero_oracle()
    result = deutsch_algorithm(oracle, "Test Constant 0")
    assert result == True  # Should be identified as constant


def test_constant_one_oracle():
    """Test that constant one oracle works correctly."""
    oracle = create_constant_one_oracle()
    result = deutsch_algorithm(oracle, "Test Constant 1") 
    assert result == True  # Should be identified as constant


def test_balanced_identity_oracle():
    """Test that balanced identity oracle works correctly."""
    oracle = create_balanced_identity_oracle()
    result = deutsch_algorithm(oracle, "Test Balanced Identity")
    assert result == False  # Should be identified as balanced


def test_balanced_negation_oracle():
    """Test that balanced negation oracle works correctly."""
    oracle = create_balanced_negation_oracle()
    result = deutsch_algorithm(oracle, "Test Balanced Negation")
    assert result == False  # Should be identified as balanced


if __name__ == "__main__":
    test_constant_zero_oracle()
    test_constant_one_oracle()
    test_balanced_identity_oracle()
    test_balanced_negation_oracle()
    print("All Deutsch Algorithm tests passed!")