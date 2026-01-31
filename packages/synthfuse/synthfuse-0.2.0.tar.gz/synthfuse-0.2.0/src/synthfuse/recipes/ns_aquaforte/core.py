"""Core NS-AquaForte solver implementation."""

import jax
import jax.numpy as jnp
from typing import Tuple, Dict, Any
from pysat.solvers import Minisat22, Glucose4
from .phase_detection import detect_phase_llm
from .solvers import resolution_solver, spectral_solver, hybrid_solver

def load_cnf(filepath: str):
    """Load CNF file into internal representation."""
    from pysat.formula import CNF
    return CNF(from_file=filepath)

def make(
    llm_model: str = "claude-sonnet-4",
    timeout: int = 300,
    verbose: bool = True
):
    """Create NS-AquaForte solver instance."""
    
    class NSAquaForteSolver:
        def __init__(self):
            self.llm_model = llm_model
            self.timeout = timeout
            self.verbose = verbose
        
        def run(self, problem):
            """Solve SAT instance with LLM-guided phase detection."""
            
            # Phase 1: LLM predicts clause density phase
            phase, confidence = detect_phase_llm(
                problem, 
                model=self.llm_model
            )
            
            if self.verbose:
                print(f"Phase detected: {phase} (confidence: {confidence:.2f})")
            
            # Phase 2: Select algorithm based on phase
            if phase == "low":
                solver_fn = resolution_solver
            elif phase == "high":
                solver_fn = spectral_solver
            else:  # critical
                solver_fn = hybrid_solver
            
            # Phase 3: Solve (this should be JIT-compiled)
            solution = solver_fn(problem, timeout=self.timeout)
            
            # Return results
            stats = {
                'detected_phase': phase,
                'selected_algorithm': solver_fn.__name__,
                'confidence': confidence,
                'time': solution.get('time', 0.0),
            }
            
            return solution, stats
    
    return NSAquaForteSolver()