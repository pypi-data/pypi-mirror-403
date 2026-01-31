import jax
import jax.numpy as jnp
from synthfuse.meta import rollback, gradient_clip
from synthfuse.systems import stcl

class DiagnosticAlchemist:
    """
    The Native Health Physician. 
    Monitors Manifold Vital Signs and performs 'Surgical' interventions.
    """
    def __init__(self, entropy_limit=0.85, divergence_threshold=1e3):
        self.entropy_limit = entropy_limit
        self.threshold = divergence_threshold

    def check_vitals(self, state, loop_metrics):
        """
        Monitors the Semantic-Thermodynamic Loop (STCL) for 'fevers'.
        """
        # 1. Check Entropy (The System's Temperature)
        current_entropy = loop_metrics.get('entropy', 0.0)
        
        if current_entropy > self.entropy_limit:
            return self.prescribe_treatment("ENTROPY_FEVER", state)

        # 2. Check for Gradient Divergence (Cardiac Arrhythmia)
        if jnp.any(jnp.isnan(state)) or jnp.max(jnp.abs(state)) > self.threshold:
            return self.prescribe_treatment("DIVERGENCE_CRISIS", state)
            
        return "HEALTHY"

    def prescribe_treatment(self, condition, state):
        """
        Executes native medical protocols based on the diagnosis.
        """
        if condition == "ENTROPY_FEVER":
            # Apply 'Cooling': Surgical Gradient Clipping
            return gradient_clip.apply_lyapunov_buffer(state)
            
        if condition == "DIVERGENCE_CRISIS":
            # Immediate 'Emergency Resuscitation': Rollback to stable hash
            print("CRITICAL: Manifold Divergence detected. Initiating Rollback...")
            return rollback.to_last_stable_checkpoint()
