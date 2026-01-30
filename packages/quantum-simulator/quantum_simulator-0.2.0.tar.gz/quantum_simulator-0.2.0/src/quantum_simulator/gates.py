"""
Quantum gates implementation.
"""

import numpy as np
from typing import List


class QuantumGate:
    """Base class for quantum gates."""
    
    def __init__(self, name: str, matrix: np.ndarray):
        """
        Initialize a quantum gate.
        
        Args:
            name: Name of the gate
            matrix: Unitary matrix representing the gate
        """
        self.name = name
        self.matrix = matrix
        self.num_qubits = int(np.log2(matrix.shape[0]))
    
    def apply(self, state_vector: np.ndarray, target_qubits: List[int]) -> np.ndarray:
        """
        Apply the gate to specific qubits.
        
        Args:
            state_vector: Current quantum state vector
            target_qubits: List of qubit indices to apply the gate to
            
        Returns:
            New state vector after applying the gate
        """
        n_qubits = int(np.log2(len(state_vector)))
        
        if self.num_qubits == 1 and len(target_qubits) == 1:
            # Single-qubit gate
            return self._apply_single_qubit_gate(state_vector, target_qubits[0], n_qubits)
        elif self.num_qubits == 2 and len(target_qubits) == 2:
            # Two-qubit gate (like CNOT, CZ)
            return self._apply_two_qubit_gate(state_vector, target_qubits[0], target_qubits[1], n_qubits)
        elif self.num_qubits == 3 and len(target_qubits) == 3:
            # Three-qubit gate (like Toffoli, CCZ)
            return self._apply_three_qubit_gate(state_vector, target_qubits[0], target_qubits[1], target_qubits[2], n_qubits)
        else:
            raise ValueError(f"Gate requires {self.num_qubits} qubits, got {len(target_qubits)}")
    
    def _apply_single_qubit_gate(self, state_vector: np.ndarray, target_qubit: int, n_qubits: int) -> np.ndarray:
        """Apply a single-qubit gate to the state vector."""
        new_state = np.zeros_like(state_vector)
        
        for i in range(len(state_vector)):
            # Extract the bit value of the target qubit from state index i
            bit_val = (i >> target_qubit) & 1
            
            # Apply gate matrix
            for new_bit_val in range(2):
                # Flip the target qubit bit to new_bit_val
                new_i = i ^ (bit_val << target_qubit) | (new_bit_val << target_qubit)
                new_state[new_i] += self.matrix[new_bit_val, bit_val] * state_vector[i]
        
        return new_state
    
    def _apply_two_qubit_gate(self, state_vector: np.ndarray, control_qubit: int, target_qubit: int, n_qubits: int) -> np.ndarray:
        """Apply a two-qubit gate to the state vector."""
        new_state = np.zeros_like(state_vector)
        
        # Special handling for CNOT and CZ (for backward compatibility and efficiency)
        if self.name == "CNOT":
            for i in range(len(state_vector)):
                # Extract control and target qubit values
                control_bit = (i >> control_qubit) & 1
                target_bit = (i >> target_qubit) & 1
                
                # For CNOT: flip target if control is 1, otherwise leave unchanged
                if control_bit == 1:
                    # Flip the target qubit
                    flipped_i = i ^ (1 << target_qubit)
                    new_state[flipped_i] += state_vector[i]
                else:
                    # Control is 0, no change
                    new_state[i] += state_vector[i]
        elif self.name == "CZ":
            for i in range(len(state_vector)):
                # Extract control and target qubit values
                control_bit = (i >> control_qubit) & 1
                target_bit = (i >> target_qubit) & 1
                
                # For CZ: flip phase if both control and target are 1
                if control_bit == 1 and target_bit == 1:
                    new_state[i] -= state_vector[i]  # Phase flip
                else:
                    new_state[i] += state_vector[i]  # No change
        else:
            # General two-qubit gate implementation
            for i in range(len(state_vector)):
                # Extract control and target qubit values
                control_bit = (i >> control_qubit) & 1
                target_bit = (i >> target_qubit) & 1
                
                # Map to 2x2 basis: |control_bit, target_bit⟩
                input_basis_state = (control_bit << 1) | target_bit
                
                # Apply the 4x4 matrix to all relevant basis combinations
                for output_control in range(2):
                    for output_target in range(2):
                        output_basis_state = (output_control << 1) | output_target
                        
                        # Calculate the new state index
                        new_i = i ^ (control_bit << control_qubit) ^ (target_bit << target_qubit) | (output_control << control_qubit) | (output_target << target_qubit)
                        
                        # Add contribution from the matrix element
                        new_state[new_i] += self.matrix[output_basis_state, input_basis_state] * state_vector[i]
        
        return new_state

    def _apply_three_qubit_gate(self, state_vector: np.ndarray, qubit0: int, qubit1: int, qubit2: int, n_qubits: int) -> np.ndarray:
        """
        Apply a three-qubit gate to the state vector.
        
        Args:
            state_vector: Current state vector
            qubit0: First qubit (corresponds to bit 0 in matrix indexing)
            qubit1: Second qubit (corresponds to bit 1 in matrix indexing) 
            qubit2: Third qubit (corresponds to bit 2 in matrix indexing)
            n_qubits: Total number of qubits
            
        Note: For Toffoli gate with qubits [0, 1, 2]:
        - qubit0 and qubit1 are controls
        - qubit2 is target
        """
        new_state = np.zeros_like(state_vector)
        
        # Special handling for common three-qubit gates
        if self.name == "Toffoli" or self.name == "CCX":
            for i in range(len(state_vector)):
                # Extract qubit values
                bit0 = (i >> qubit0) & 1
                bit1 = (i >> qubit1) & 1
                bit2 = (i >> qubit2) & 1
                
                # For Toffoli: flip qubit2 if both qubit0 and qubit1 are 1
                if bit0 == 1 and bit1 == 1:
                    # Flip qubit2
                    flipped_i = i ^ (1 << qubit2)
                    new_state[flipped_i] += state_vector[i]
                else:
                    # At least one control is 0, no change
                    new_state[i] += state_vector[i]
        elif self.name == "CCZ":
            for i in range(len(state_vector)):
                # Extract qubit values
                bit0 = (i >> qubit0) & 1
                bit1 = (i >> qubit1) & 1
                bit2 = (i >> qubit2) & 1
                
                # For CCZ: flip phase if all three qubits are 1
                if bit0 == 1 and bit1 == 1 and bit2 == 1:
                    new_state[i] -= state_vector[i]  # Phase flip
                else:
                    new_state[i] += state_vector[i]  # No change
        else:
            # General three-qubit gate implementation (8x8 matrix)
            for i in range(len(state_vector)):
                # Extract qubit values
                bit0 = (i >> qubit0) & 1
                bit1 = (i >> qubit1) & 1
                bit2 = (i >> qubit2) & 1
                
                # Map to 3-qubit basis state (qubit2 is MSB, qubit0 is LSB for standard ordering)
                input_basis_state = (bit2 << 2) | (bit1 << 1) | bit0
                
                # Apply the 8x8 matrix
                for output_bit2 in range(2):
                    for output_bit1 in range(2):
                        for output_bit0 in range(2):
                            output_basis_state = (output_bit2 << 2) | (output_bit1 << 1) | output_bit0
                            
                            # Calculate the new state index
                            new_i = (i ^ (bit0 << qubit0) ^ (bit1 << qubit1) ^ (bit2 << qubit2) |
                                   (output_bit0 << qubit0) | (output_bit1 << qubit1) | (output_bit2 << qubit2))
                            
                            # Add contribution from the matrix element
                            new_state[new_i] += self.matrix[output_basis_state, input_basis_state] * state_vector[i]
        
        return new_state


# Common single-qubit gates
X_GATE = QuantumGate("X", np.array([[0, 1], [1, 0]], dtype=complex))
Y_GATE = QuantumGate("Y", np.array([[0, -1j], [1j, 0]], dtype=complex))
Z_GATE = QuantumGate("Z", np.array([[1, 0], [0, -1]], dtype=complex))
H_GATE = QuantumGate("H", np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2))

# Rotation gates
def RX(theta: float) -> QuantumGate:
    """
    Create a rotation gate around X-axis by angle theta.
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: RX rotation gate
    """
    cos_half = np.cos(theta / 2)
    sin_half = np.sin(theta / 2)
    matrix = np.array([
        [cos_half, -1j * sin_half],
        [-1j * sin_half, cos_half]
    ], dtype=complex)
    return QuantumGate(f"RX({theta:.3f})", matrix)

def RY(theta: float) -> QuantumGate:
    """
    Create a rotation gate around Y-axis by angle theta.
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: RY rotation gate
    """
    cos_half = np.cos(theta / 2)
    sin_half = np.sin(theta / 2)
    matrix = np.array([
        [cos_half, -sin_half],
        [sin_half, cos_half]
    ], dtype=complex)
    return QuantumGate(f"RY({theta:.3f})", matrix)

def RZ(theta: float) -> QuantumGate:
    """
    Create a rotation gate around Z-axis by angle theta.
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: RZ rotation gate
    """
    exp_neg = np.exp(-1j * theta / 2)
    exp_pos = np.exp(1j * theta / 2)
    matrix = np.array([
        [exp_neg, 0],
        [0, exp_pos]
    ], dtype=complex)
    return QuantumGate(f"RZ({theta:.3f})", matrix)

# Specific angles for W state construction
# RY gate with theta = arccos(sqrt(2/3)) ≈ 0.9553 radians
W_STATE_ANGLE_1 = np.arccos(np.sqrt(2/3))  # ~0.9553 radians
RY_W1 = RY(W_STATE_ANGLE_1)

# RY gate with theta = arccos(sqrt(1/2)) = π/4
W_STATE_ANGLE_2 = np.arccos(np.sqrt(1/2))  # π/4 radians
RY_W2 = RY(W_STATE_ANGLE_2)

# Two-qubit gates
CNOT_GATE = QuantumGate("CNOT", np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
], dtype=complex))

CZ_GATE = QuantumGate("CZ", np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, -1]
], dtype=complex))

# Controlled rotation gates for W state
def controlled_RX(theta: float) -> QuantumGate:
    """
    Create a controlled rotation gate around X-axis.
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: Controlled RX gate (2-qubit gate)
    """
    cos_half = np.cos(theta / 2)
    sin_half = np.sin(theta / 2)
    
    # 4x4 matrix for controlled gate: I ⊗ |0⟩⟨0| + RX(θ) ⊗ |1⟩⟨1|
    matrix = np.array([
        [1, 0, 0, 0],                    # |00⟩ → |00⟩
        [0, 1, 0, 0],                    # |01⟩ → |01⟩
        [0, 0, cos_half, -1j * sin_half], # |10⟩ → cos(θ/2)|10⟩ - i·sin(θ/2)|11⟩
        [0, 0, -1j * sin_half, cos_half]  # |11⟩ → -i·sin(θ/2)|10⟩ + cos(θ/2)|11⟩
    ], dtype=complex)
    
    return QuantumGate(f"CRX({theta:.3f})", matrix)

def controlled_RY(theta: float) -> QuantumGate:
    """
    Create a controlled rotation gate around Y-axis.
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: Controlled RY gate (2-qubit gate)
    """
    cos_half = np.cos(theta / 2)
    sin_half = np.sin(theta / 2)
    
    # 4x4 matrix for controlled gate: I ⊗ |0⟩⟨0| + RY(θ) ⊗ |1⟩⟨1|
    matrix = np.array([
        [1, 0, 0, 0],           # |00⟩ → |00⟩
        [0, 1, 0, 0],           # |01⟩ → |01⟩
        [0, 0, cos_half, -sin_half],  # |10⟩ → cos(θ/2)|10⟩ - sin(θ/2)|11⟩
        [0, 0, sin_half, cos_half]    # |11⟩ → sin(θ/2)|10⟩ + cos(θ/2)|11⟩
    ], dtype=complex)
    
    return QuantumGate(f"CRY({theta:.3f})", matrix)

def controlled_RZ(theta: float) -> QuantumGate:
    """
    Create a controlled rotation gate around Z-axis.
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: Controlled RZ gate (2-qubit gate)
    """
    exp_neg = np.exp(-1j * theta / 2)
    exp_pos = np.exp(1j * theta / 2)
    
    # 4x4 matrix for controlled gate: I ⊗ |0⟩⟨0| + RZ(θ) ⊗ |1⟩⟨1|
    matrix = np.array([
        [1, 0, 0, 0],       # |00⟩ → |00⟩
        [0, 1, 0, 0],       # |01⟩ → |01⟩
        [0, 0, exp_neg, 0], # |10⟩ → e^(-iθ/2)|10⟩
        [0, 0, 0, exp_pos]  # |11⟩ → e^(iθ/2)|11⟩
    ], dtype=complex)
    
    return QuantumGate(f"CRZ({theta:.3f})", matrix)

# Specific controlled rotation for W state
CRY_W = controlled_RY(W_STATE_ANGLE_2)

# Three-qubit gates
TOFFOLI_GATE = QuantumGate("Toffoli", np.array([
    [1, 0, 0, 0, 0, 0, 0, 0],  # |000⟩ → |000⟩
    [0, 1, 0, 0, 0, 0, 0, 0],  # |001⟩ → |001⟩
    [0, 0, 1, 0, 0, 0, 0, 0],  # |010⟩ → |010⟩
    [0, 0, 0, 1, 0, 0, 0, 0],  # |011⟩ → |011⟩
    [0, 0, 0, 0, 1, 0, 0, 0],  # |100⟩ → |100⟩
    [0, 0, 0, 0, 0, 1, 0, 0],  # |101⟩ → |101⟩
    [0, 0, 0, 0, 0, 0, 0, 1],  # |110⟩ → |111⟩
    [0, 0, 0, 0, 0, 0, 1, 0]   # |111⟩ → |110⟩
], dtype=complex))

# Alias for Toffoli
CCX_GATE = TOFFOLI_GATE

CCZ_GATE = QuantumGate("CCZ", np.array([
    [1, 0, 0, 0, 0, 0, 0, 0],   # |000⟩ → |000⟩
    [0, 1, 0, 0, 0, 0, 0, 0],   # |001⟩ → |001⟩
    [0, 0, 1, 0, 0, 0, 0, 0],   # |010⟩ → |010⟩
    [0, 0, 0, 1, 0, 0, 0, 0],   # |011⟩ → |011⟩
    [0, 0, 0, 0, 1, 0, 0, 0],   # |100⟩ → |100⟩
    [0, 0, 0, 0, 0, 1, 0, 0],   # |101⟩ → |101⟩
    [0, 0, 0, 0, 0, 0, 1, 0],   # |110⟩ → |110⟩
    [0, 0, 0, 0, 0, 0, 0, -1]   # |111⟩ → -|111⟩
], dtype=complex))


# Additional gates for QAOA (Quantum Approximate Optimization Algorithm)

def RZZ(theta: float) -> QuantumGate:
    """
    Create a two-qubit RZZ rotation gate for angle theta.
    This gate is commonly used in QAOA cost Hamiltonians.
    RZZ(θ) = exp(-iθ/2 * Z⊗Z)
    
    Args:
        theta: Rotation angle in radians
        
    Returns:
        QuantumGate: Two-qubit RZZ gate
    """
    exp_neg = np.exp(-1j * theta / 2)
    exp_pos = np.exp(1j * theta / 2)
    
    matrix = np.array([
        [exp_neg, 0, 0, 0],         # |00⟩ → e^(-iθ/2)|00⟩
        [0, exp_pos, 0, 0],         # |01⟩ → e^(iθ/2)|01⟩  
        [0, 0, exp_pos, 0],         # |10⟩ → e^(iθ/2)|10⟩
        [0, 0, 0, exp_neg]          # |11⟩ → e^(-iθ/2)|11⟩
    ], dtype=complex)
    
    return QuantumGate(f"RZZ({theta:.3f})", matrix)


def phase_gate(phi: float) -> QuantumGate:
    """
    Create a single-qubit phase gate with phase phi.
    This applies a phase e^(i*phi) to the |1⟩ state.
    
    Args:
        phi: Phase angle in radians
        
    Returns:
        QuantumGate: Single-qubit phase gate
    """
    matrix = np.array([
        [1, 0],
        [0, np.exp(1j * phi)]
    ], dtype=complex)
    
    return QuantumGate(f"Phase({phi:.3f})", matrix)