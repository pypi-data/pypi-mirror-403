"""
Test for QAOA Max-Cut Algorithm example.
"""

import sys
import os
import pytest

# Add the src directory to the path so we can import the examples
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from examples.qaoa_max_cut import QAOAMaxCut


def test_qaoa_max_cut_initialization():
    """Test that QAOA Max-Cut can be initialized correctly."""
    edges = [(0, 1), (1, 2), (0, 2)]
    n_vertices = 3
    qaoa = QAOAMaxCut(edges, n_vertices)
    
    assert qaoa.edges == edges
    assert qaoa.n_vertices == n_vertices
    assert qaoa.n_qubits == n_vertices


def test_evaluate_max_cut():
    """Test the Max-Cut evaluation function."""
    edges = [(0, 1), (1, 2), (0, 2)]
    n_vertices = 3
    qaoa = QAOAMaxCut(edges, n_vertices)
    
    # Test various partitions
    assert qaoa.evaluate_max_cut("000") == 0  # No edges cut
    assert qaoa.evaluate_max_cut("001") == 2  # Two edges cut
    assert qaoa.evaluate_max_cut("010") == 2  # Two edges cut
    assert qaoa.evaluate_max_cut("100") == 2  # Two edges cut
    assert qaoa.evaluate_max_cut("111") == 0  # No edges cut


def test_create_hamiltonians():
    """Test that Hamiltonian circuits can be created."""
    edges = [(0, 1), (1, 2), (0, 2)]
    n_vertices = 3
    qaoa = QAOAMaxCut(edges, n_vertices)
    
    # Test cost Hamiltonian
    gamma = 0.5
    cost_circuit = qaoa.create_cost_hamiltonian_circuit(gamma)
    assert cost_circuit.num_qubits == n_vertices
    assert len(cost_circuit.gates) == len(edges)  # One RZZ gate per edge
    
    # Test mixer Hamiltonian
    beta = 0.3
    mixer_circuit = qaoa.create_mixer_hamiltonian_circuit(beta)
    assert mixer_circuit.num_qubits == n_vertices
    assert len(mixer_circuit.gates) == n_vertices  # One RX gate per qubit


def test_create_qaoa_circuit():
    """Test that full QAOA circuit can be created."""
    edges = [(0, 1), (1, 2), (0, 2)]
    n_vertices = 3
    qaoa = QAOAMaxCut(edges, n_vertices)
    
    gammas = [0.5, 0.3]
    betas = [0.2, 0.7]
    
    circuit = qaoa.create_qaoa_circuit(gammas, betas)
    assert circuit.num_qubits == n_vertices
    
    # Should have: 3 Hadamards + 2*(3 RZZ + 3 RX) gates
    expected_gates = 3 + 2 * (3 + 3)  # 15 gates total
    assert len(circuit.gates) == expected_gates


def test_compute_expectation_value():
    """Test that expectation value computation doesn't crash."""
    edges = [(0, 1)]  # Simple 2-vertex graph
    n_vertices = 2
    qaoa = QAOAMaxCut(edges, n_vertices)
    
    gammas = [0.5]
    betas = [0.3]
    
    # This should run without error and return a value between 0 and 1
    expectation = qaoa.compute_expectation_value(gammas, betas, num_shots=10)
    assert 0 <= expectation <= 1


if __name__ == "__main__":
    test_qaoa_max_cut_initialization()
    test_evaluate_max_cut()
    test_create_hamiltonians()
    test_create_qaoa_circuit()
    test_compute_expectation_value()
    print("All QAOA Max-Cut tests passed!")