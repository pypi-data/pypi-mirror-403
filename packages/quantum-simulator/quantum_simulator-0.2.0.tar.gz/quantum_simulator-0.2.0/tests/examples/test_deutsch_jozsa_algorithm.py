"""
Test for Deutsch-Jozsa Algorithm example.
"""

import sys
import os
import pytest

# Add the src directory to the path so we can import the examples
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from examples.deutsch_jozsa_algorithm import (
    create_constant_zero_oracle,
    create_constant_one_oracle,
    create_balanced_parity_oracle,
    create_balanced_first_bit_oracle,
    deutsch_jozsa_algorithm
)


def test_constant_zero_oracle():
    """Test that constant zero oracle works correctly."""
    n_qubits = 4  # 3 input + 1 ancilla
    n_input_qubits = 3
    oracle = create_constant_zero_oracle(n_qubits)
    result = deutsch_jozsa_algorithm(oracle, "Test Constant 0", n_input_qubits)
    assert result == True  # Should be identified as constant


def test_constant_one_oracle():
    """Test that constant one oracle works correctly."""
    n_qubits = 4  # 3 input + 1 ancilla
    n_input_qubits = 3
    oracle = create_constant_one_oracle(n_qubits)
    result = deutsch_jozsa_algorithm(oracle, "Test Constant 1", n_input_qubits)
    assert result == True  # Should be identified as constant


def test_balanced_parity_oracle():
    """Test that balanced parity oracle works correctly."""
    n_qubits = 4  # 3 input + 1 ancilla
    n_input_qubits = 3
    oracle = create_balanced_parity_oracle(n_qubits)
    result = deutsch_jozsa_algorithm(oracle, "Test Balanced Parity", n_input_qubits)
    assert result == False  # Should be identified as balanced


def test_balanced_first_bit_oracle():
    """Test that balanced first bit oracle works correctly."""
    n_qubits = 4  # 3 input + 1 ancilla
    n_input_qubits = 3
    oracle = create_balanced_first_bit_oracle(n_qubits)
    result = deutsch_jozsa_algorithm(oracle, "Test Balanced First Bit", n_input_qubits)
    assert result == False  # Should be identified as balanced


if __name__ == "__main__":
    test_constant_zero_oracle()
    test_constant_one_oracle()
    test_balanced_parity_oracle()
    test_balanced_first_bit_oracle()
    print("All Deutsch-Jozsa Algorithm tests passed!")