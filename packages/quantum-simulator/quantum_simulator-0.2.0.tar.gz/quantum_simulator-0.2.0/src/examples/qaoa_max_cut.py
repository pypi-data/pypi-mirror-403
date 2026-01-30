"""
Quantum Approximate Optimization Algorithm (QAOA) Example

This example demonstrates the Quantum Approximate Optimization Algorithm (QAOA),
a variational quantum algorithm for solving combinatorial optimization problems.
QAOA is particularly useful for finding approximate solutions to NP-hard problems
like Max-Cut, Maximum Independent Set, and others.

What this example does:
1. Solves a simple Max-Cut problem on a 3-vertex graph using QAOA
2. Uses a classical optimizer to find optimal QAOA parameters
3. Demonstrates the alternating application of cost and mixer Hamiltonians
4. Shows how quantum superposition helps explore multiple solutions simultaneously

The Max-Cut problem: Given a graph, find a partition of vertices into two sets
such that the number of edges crossing between the sets is maximized.

For this example, we use a triangle graph (3 vertices, all connected):
   0 --- 1
    \\   /
     \\ /
      2
      
The optimal Max-Cut solution cuts 2 edges (any partition of 2+1 vertices).
"""

from quantum_simulator import QuantumSimulator, QuantumCircuit
from quantum_simulator.gates import H_GATE, RX, RZ, CNOT_GATE, RZZ
import numpy as np
from typing import List, Tuple, Dict
import itertools
from scipy.optimize import minimize  # type: ignore


class QAOAMaxCut:
    """QAOA implementation for the Max-Cut problem."""
    
    def __init__(self, edges: List[Tuple[int, int]], n_vertices: int):
        """
        Initialize QAOA for Max-Cut problem.
        
        Args:
            edges: List of edges in the graph as (vertex1, vertex2) tuples
            n_vertices: Number of vertices in the graph
        """
        self.edges = edges
        self.n_vertices = n_vertices
        self.n_qubits = n_vertices  # One qubit per vertex
    
    def create_cost_hamiltonian_circuit(self, gamma: float) -> QuantumCircuit:
        """
        Create the cost Hamiltonian circuit for Max-Cut.
        The cost Hamiltonian is: H_C = Σ_{(i,j) ∈ E} (1 - Z_i Z_j) / 2
        We implement this using RZZ gates: exp(-iγH_C) 
        
        Args:
            gamma: Cost Hamiltonian parameter
            
        Returns:
            QuantumCircuit: Cost Hamiltonian circuit
        """
        circuit = QuantumCircuit(self.n_qubits)
        
        # For each edge (i,j), apply RZZ(gamma) gate
        # RZZ implements exp(-iγ/2 * Z_i ⊗ Z_j)
        # For Max-Cut, we want exp(-iγ/2 * (1 - Z_i Z_j))
        # This is equivalent to a phase and RZZ(-gamma)
        for i, j in self.edges:
            # Apply RZZ gate with parameter -gamma to implement (1 - Z_i Z_j) term
            rzz_gate = RZZ(-gamma)
            circuit.add_gate(rzz_gate, [i, j])
        
        return circuit
    
    def create_mixer_hamiltonian_circuit(self, beta: float) -> QuantumCircuit:
        """
        Create the mixer Hamiltonian circuit.
        The mixer Hamiltonian is: H_M = Σ_i X_i
        We implement this using RX gates: exp(-iβH_M) = Π_i exp(-iβX_i)
        
        Args:
            beta: Mixer Hamiltonian parameter
            
        Returns:
            QuantumCircuit: Mixer Hamiltonian circuit
        """
        circuit = QuantumCircuit(self.n_qubits)
        
        # Apply RX(2*beta) to each qubit
        # RX(2β) implements exp(-iβX)
        for i in range(self.n_qubits):
            rx_gate = RX(2 * beta)
            circuit.add_gate(rx_gate, [i])
        
        return circuit
    
    def create_qaoa_circuit(self, gammas: List[float], betas: List[float]) -> QuantumCircuit:
        """
        Create the full QAOA circuit with p layers.
        
        Args:
            gammas: List of gamma parameters (cost Hamiltonian parameters)
            betas: List of beta parameters (mixer Hamiltonian parameters)
            
        Returns:
            QuantumCircuit: Complete QAOA circuit
        """
        if len(gammas) != len(betas):
            raise ValueError("Number of gamma and beta parameters must be equal")
        
        p = len(gammas)  # Number of QAOA layers
        circuit = QuantumCircuit(self.n_qubits)
        
        # Step 1: Initialize all qubits in superposition (|+⟩ state)
        for i in range(self.n_qubits):
            circuit.add_gate(H_GATE, [i])
        
        # Step 2: Apply p layers of cost and mixer Hamiltonians
        for layer in range(p):
            # Apply cost Hamiltonian
            cost_circuit = self.create_cost_hamiltonian_circuit(gammas[layer])
            for gate, qubits in cost_circuit.gates:
                circuit.add_gate(gate, qubits)
            
            # Apply mixer Hamiltonian
            mixer_circuit = self.create_mixer_hamiltonian_circuit(betas[layer])
            for gate, qubits in mixer_circuit.gates:
                circuit.add_gate(gate, qubits)
        
        return circuit
    
    def evaluate_max_cut(self, bitstring: str) -> int:
        """
        Evaluate the Max-Cut cost for a given bitstring.
        
        Args:
            bitstring: Binary string representing vertex partition
            
        Returns:
            int: Number of edges cut
        """
        cut_count = 0
        for i, j in self.edges:
            if bitstring[i] != bitstring[j]:  # Edge is cut
                cut_count += 1
        return cut_count
    
    def compute_expectation_value(self, gammas: List[float], betas: List[float], 
                                num_shots: int = 1000) -> float:
        """
        Compute the expectation value of the cost function for given parameters.
        
        Args:
            gammas: Gamma parameters
            betas: Beta parameters  
            num_shots: Number of measurement shots
            
        Returns:
            float: Expectation value of the cost function
        """
        # Create and execute QAOA circuit
        circuit = self.create_qaoa_circuit(gammas, betas)
        
        total_cost = 0
        for shot in range(num_shots):
            sim = QuantumSimulator(self.n_qubits)
            sim.execute_circuit(circuit)
            
            # Measure all qubits
            bitstring = ""
            for qubit in range(self.n_qubits):
                measurement = sim.measure(qubit)
                bitstring += str(measurement)
            
            # Compute cost for this measurement
            cost = self.evaluate_max_cut(bitstring)
            total_cost += cost
        
        return total_cost / num_shots
    
    def optimize_parameters(self, p: int = 1, num_shots: int = 100) -> Tuple[List[float], List[float], float]:
        """
        Optimize QAOA parameters using classical optimization.
        
        Args:
            p: Number of QAOA layers
            num_shots: Number of shots for expectation value estimation
            
        Returns:
            Tuple of (optimal_gammas, optimal_betas, best_expectation_value)
        """
        def objective(params: np.ndarray) -> float:
            """Objective function to minimize (negative expectation value)."""
            gammas = params[:p].tolist()
            betas = params[p:].tolist()
            return -self.compute_expectation_value(gammas, betas, num_shots)
        
        # Initialize parameters randomly
        initial_params = np.random.uniform(0, 2*np.pi, 2*p)
        
        print(f"Optimizing QAOA parameters for p={p} layers...")
        print(f"Initial parameters: {initial_params}")
        
        # Use classical optimizer
        result = minimize(objective, initial_params, method='COBYLA',
                         options={'maxiter': 50, 'disp': True})
        
        optimal_params = result.x
        optimal_gammas = optimal_params[:p].tolist()
        optimal_betas = optimal_params[p:].tolist()
        best_expectation = -result.fun
        
        return optimal_gammas, optimal_betas, best_expectation
    
    def find_best_solutions(self, gammas: List[float], betas: List[float], 
                          num_shots: int = 1000) -> Dict[str, int]:
        """
        Find the most frequently measured solutions.
        
        Args:
            gammas: Optimal gamma parameters
            betas: Optimal beta parameters
            num_shots: Number of measurement shots
            
        Returns:
            Dict mapping bitstrings to their frequency
        """
        circuit = self.create_qaoa_circuit(gammas, betas)
        solution_counts: Dict[str, int] = {}
        
        for shot in range(num_shots):
            sim = QuantumSimulator(self.n_qubits)
            sim.execute_circuit(circuit)
            
            # Measure all qubits
            bitstring = ""
            for qubit in range(self.n_qubits):
                measurement = sim.measure(qubit)
                bitstring += str(measurement)
            
            solution_counts[bitstring] = solution_counts.get(bitstring, 0) + 1
        
        return solution_counts


def main() -> None:
    """
    Demonstrate QAOA for solving Max-Cut on a triangle graph.
    
    This function sets up a 3-vertex complete graph (triangle) and uses QAOA
    to find the optimal cut. The optimal solution should cut 2 out of 3 edges.
    """
    print("Quantum Approximate Optimization Algorithm (QAOA) Demonstration")
    print("=" * 70)
    print("Solving Max-Cut problem on a triangle graph:")
    print("   0 --- 1")
    print("    \\   /")
    print("     \\ /")
    print("      2")
    print()
    
    # Define the triangle graph
    edges = [(0, 1), (1, 2), (0, 2)]  # Complete graph on 3 vertices
    n_vertices = 3
    
    print(f"Graph edges: {edges}")
    print(f"Number of vertices: {n_vertices}")
    print()
    
    # Create QAOA instance
    qaoa = QAOAMaxCut(edges, n_vertices)
    
    # Analyze all possible classical solutions
    print("Classical analysis of all possible cuts:")
    print("-" * 40)
    max_classical_cut = 0
    optimal_classical_solutions = []
    
    for i in range(2**n_vertices):
        bitstring = format(i, f'0{n_vertices}b')
        cut_value = qaoa.evaluate_max_cut(bitstring)
        print(f"Partition {bitstring}: {cut_value} edges cut")
        
        if cut_value > max_classical_cut:
            max_classical_cut = cut_value
            optimal_classical_solutions = [bitstring]
        elif cut_value == max_classical_cut:
            optimal_classical_solutions.append(bitstring)
    
    print(f"\nOptimal classical Max-Cut value: {max_classical_cut}")
    print(f"Optimal classical solutions: {optimal_classical_solutions}")
    print()
    
    # Run QAOA optimization
    print("Running QAOA optimization...")
    print("-" * 40)
    
    # Try different numbers of QAOA layers
    for p in [1, 2]:
        print(f"\nQAOA with p={p} layers:")
        try:
            optimal_gammas, optimal_betas, best_expectation = qaoa.optimize_parameters(p, num_shots=50)
            
            print(f"Optimal gammas: {[f'{g:.3f}' for g in optimal_gammas]}")
            print(f"Optimal betas: {[f'{b:.3f}' for b in optimal_betas]}")
            print(f"Best expectation value: {best_expectation:.3f}")
            
            # Find most common solutions
            solution_counts = qaoa.find_best_solutions(optimal_gammas, optimal_betas, num_shots=200)
            
            print("Most frequent solutions:")
            sorted_solutions = sorted(solution_counts.items(), key=lambda x: x[1], reverse=True)
            for bitstring, count in sorted_solutions[:5]:  # Show top 5
                cut_value = qaoa.evaluate_max_cut(bitstring)
                probability = count / sum(solution_counts.values())
                print(f"  {bitstring}: {count} times ({probability:.3f} prob), {cut_value} cuts")
                
        except Exception as e:
            print(f"Optimization failed for p={p}: {e}")
    
    print(f"\n" + "=" * 70)
    print("QAOA SUMMARY:")
    print(f"• Classical optimal: {max_classical_cut} cuts")
    print(f"• QAOA explores quantum superpositions to find good solutions")
    print(f"• As p increases, QAOA should better approximate the optimal solution")
    print(f"• This demonstrates quantum advantage in combinatorial optimization")


if __name__ == "__main__":
    main()