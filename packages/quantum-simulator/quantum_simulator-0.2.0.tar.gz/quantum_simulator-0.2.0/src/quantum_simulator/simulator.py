"""
Quantum simulator implementation.
"""

import numpy as np
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .circuits import QuantumCircuit


class QuantumSimulator:
    """A quantum computer simulator."""
    
    def __init__(self, num_qubits: int):
        """
        Initialize the quantum simulator.
        
        Args:
            num_qubits: Number of qubits in the quantum system
        """
        self.num_qubits = num_qubits
        self.num_states = 2 ** num_qubits
        # Initialize all qubits in |0> state
        self.state_vector = np.zeros(self.num_states, dtype=complex)
        self.state_vector[0] = 1.0
    
    def reset(self) -> None:
        """Reset all qubits to |0> state."""
        self.state_vector = np.zeros(self.num_states, dtype=complex)
        self.state_vector[0] = 1.0
    
    def get_state_vector(self) -> np.ndarray:
        """Get the current state vector."""
        return self.state_vector.copy()
    
    def measure(self, qubit: int) -> int:
        """
        Measure a specific qubit.
        
        Args:
            qubit: Index of the qubit to measure (0-indexed)
            
        Returns:
            Measurement result (0 or 1)
        """
        # This is a simplified measurement implementation
        probabilities = np.abs(self.state_vector) ** 2
        # Calculate probability of measuring |0> for the specified qubit
        prob_0 = sum(probabilities[i] for i in range(self.num_states) 
                    if not (i >> qubit) & 1)
        
        # Simulate measurement outcome
        result = 0 if np.random.random() < prob_0 else 1
        
        # Collapse the state vector (simplified)
        new_state = np.zeros_like(self.state_vector)
        norm = 0
        for i in range(self.num_states):
            if ((i >> qubit) & 1) == result:
                new_state[i] = self.state_vector[i]
                norm += abs(self.state_vector[i]) ** 2
        
        if norm > 0:
            self.state_vector = new_state / np.sqrt(norm)
        
        return result
    
    def execute_circuit(self, circuit: 'QuantumCircuit') -> None:
        """
        Execute a quantum circuit on this simulator.
        
        Args:
            circuit: QuantumCircuit to execute
        """
        circuit.execute(self)