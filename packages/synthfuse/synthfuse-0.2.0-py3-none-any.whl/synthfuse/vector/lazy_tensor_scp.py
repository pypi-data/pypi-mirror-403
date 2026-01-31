# synthfuse/vector/lazy_tensor_scp.py
import jax
import jax.numpy as jnp
from jax import jit, vmap
from synthfuse.solvers.scp import truncated_svd, max_kurtosis_match

class LazyTensorSCP:
    """
    Lazy Tensor Database enhanced with Spectral Compression Parser.
    Stores SVD-compressed generation functions with MaxKurtosis querying.
    """
    
    def __init__(self, compression_rank: int = 64):
        self.rank = compression_rank
        self.compressed_db = {}  # id -> (U_k, Σ_k, V_k_T, gen_metadata)
    
    def register(self, id: str, gen_matrix: jnp.ndarray):
        """Compress and store generation function via SCP."""
        U_k, Σ_k, V_k_T = truncated_svd(gen_matrix, k=self.rank)
        self.compressed_db[id] = (U_k, Σ_k, V_k_T)
    
    @jit
    def query(self, query_vec: jnp.ndarray, id: str) -> float:
        """MaxKurtosis-optimized similarity via SCP reconstruction."""
        U_k, Σ_k, V_k_T = self.compressed_db[id]
        # Reconstruct approximation: gen_matrix ≈ U_k @ diag(Σ_k) @ V_k_T
        reconstructed = (U_k * Σ_k) @ V_k_T  # O(k * (m + n)) vs O(m*n)
        return max_kurtosis_match(query_vec, reconstructed)
