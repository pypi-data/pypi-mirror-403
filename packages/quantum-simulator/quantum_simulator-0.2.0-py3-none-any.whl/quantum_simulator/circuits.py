"""
Quantum circuits implementation.
"""

from typing import List, Tuple
from .simulator import QuantumSimulator
from .gates import QuantumGate


class QuantumCircuit:
    """A quantum circuit representation."""
    
    def __init__(self, num_qubits: int):
        """
        Initialize a quantum circuit.
        
        Args:
            num_qubits: Number of qubits in the circuit
        """
        self.num_qubits = num_qubits
        self.gates: List[Tuple[QuantumGate, List[int]]] = []
    
    def add_gate(self, gate: QuantumGate, target_qubits: List[int]) -> None:
        """
        Add a gate to the circuit.
        
        Args:
            gate: The quantum gate to add
            target_qubits: List of qubit indices the gate acts on
        """
        self.gates.append((gate, target_qubits))
    
    def execute(self, simulator: QuantumSimulator) -> None:
        """
        Execute the circuit on a quantum simulator.
        
        Args:
            simulator: The quantum simulator to run the circuit on
        """
        for gate, target_qubits in self.gates:
            simulator.state_vector = gate.apply(simulator.state_vector, target_qubits)
    
    def __str__(self) -> str:
        """String representation of the circuit."""
        circuit_str = f"QuantumCircuit({self.num_qubits} qubits)\n"
        for i, (gate, targets) in enumerate(self.gates):
            circuit_str += f"  {i}: {gate.name} on qubits {targets}\n"
        return circuit_str