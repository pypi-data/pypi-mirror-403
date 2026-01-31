import jax
import jax.numpy as jnp
from typing import List, Dict
from synthfuse.meta import zeta_alchemist

class Quorum:
    """
    The Jury of the Cabinet.
    Validates Sigil impulses using Weighted Consensus and Entropy Gates.
    """
    def __init__(self, threshold: float = 0.66, min_agents: int = 3):
        self.threshold = threshold
        self.min_agents = min_agents

    def validate_impulse(self, sigil_id: str, agent_votes: List[Dict]):
        """
        Processes a collection of agent impulses. 
        Each vote contains a vector and a confidence score.
        """
        if len(agent_votes) < self.min_agents:
            return False, "Insufficient agent quorum."

        # 1. Calculate Weighted Mean Vector
        # We use JAX to perform this at VRAM speed
        vectors = jnp.stack([v['vector'] for v in agent_votes])
        weights = jnp.array([v['confidence'] for v in agent_votes])
        
        # Normalize weights
        weights = weights / jnp.sum(weights)
        
        # Weighted Average (The 'Consensus Vector')
        consensus_vector = jnp.sum(vectors * weights[:, None], axis=0)

        # 2. Spectral Consistency Check (Zeta-Domain)
        # Does the consensus vector fit the system's frequency constraints?
        is_consistent = zeta_alchemist.verify_spectral_fit(consensus_vector)

        # 3. Decision Logic
        # Calculate the 'Agreement Score' (Cosine similarity between agents)
        avg_similarity = self._calculate_similarity(vectors, consensus_vector)
        
        if avg_similarity >= self.threshold and is_consistent:
            return True, consensus_vector
        else:
            return False, "Consensus failed: Low similarity or Spectral drift."

    def _calculate_similarity(self, vectors, consensus):
        dot_products = jnp.dot(vectors, consensus)
        norms = jnp.linalg.norm(vectors, axis=1) * jnp.linalg.norm(consensus)
        return jnp.mean(dot_products / norms)
