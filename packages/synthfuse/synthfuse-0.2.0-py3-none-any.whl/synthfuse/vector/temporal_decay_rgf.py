# synthfuse/vector/temporal_decay_rgf.py
import jax
import jax.numpy as jnp
from jax import jit, grad, vmap
from jax.experimental import optimizers
import flax.linen as nn
from typing import Callable, Tuple, Dict
from dataclasses import dataclass
from synthfuse.solvers.rgf_f import MatrixGreenFunction, SpatiotemporalGraph
from synthfuse.rl.ppo_graph import PPOGraphOptimizer

@dataclass
class RGFTemporalState:
    """State container for RGF-F temporal decay."""
    vector: jnp.ndarray
    stored_time: float
    uncertainty: jnp.ndarray  # Diagonal covariance estimate
    graph_node_id: int        # Position in spatiotemporal graph

class MatrixGreenFunction(nn.Module):
    """
    Learned Matrix Green Function for information propagation.
    Replaces scalar decay with structured temporal diffusion.
    """
    hidden_dim: int = 128
    num_heads: int = 4
    
    @nn.compact
    def __call__(self, time_delta: float, edge_features: jnp.ndarray) -> jnp.ndarray:
        """
        Compute Green function matrix G(t, t_stored).
        
        Args:
            time_delta: (t - t_stored) - age of information
            edge_features: Graph edge properties [distance, type, weight]
            
        Returns:
            G: Diffusion matrix encoding how information propagates
        """
        # Time encoding with exponential decay basis
        time_embed = jnp.exp(-jnp.arange(self.hidden_dim) * time_delta / 10.0)
        
        # Edge-aware attention for structured diffusion
        edge_embed = nn.Dense(self.hidden_dim)(edge_features)
        edge_embed = nn.relu(edge_embed)
        
        # Combine time and structure
        combined = jnp.concatenate([time_embed, edge_embed])
        
        # Multi-head attention for different "modes" of information decay
        attention_logits = nn.Dense(self.num_heads)(combined)
        attention_weights = jax.nn.softmax(attention_logits)
        
        # Generate Green function components
        green_components = nn.Dense(self.num_heads * self.hidden_dim)(combined)
        green_components = green_components.reshape(self.num_heads, self.hidden_dim)
        
        # Weighted combination
        G = jnp.sum(attention_weights[:, None] * green_components, axis=0)
        G = nn.Dense(self.hidden_dim)(G)  # Final projection
        
        return G

class SpatiotemporalDecayGraph:
    """
    Graph structure where nodes are vector states at different times.
    Edges represent information flow with learnable weights.
    """
    
    def __init__(self, max_nodes: int = 10000, dim: int = 768):
        self.max_nodes = max_nodes
        self.dim = dim
        self.nodes: Dict[int, RGFTemporalState] = {}
        self.adjacency = jnp.zeros((max_nodes, max_nodes))
        self.edge_features = jnp.zeros((max_nodes, max_nodes, 3))  # [dist, type, init_weight]
        self.current_time = 0.0
        
    def add_vector(self, vector_id: str, vector: jnp.ndarray, 
                   uncertainty: jnp.ndarray = None) -> int:
        """Add new vector to graph, return node index."""
        node_idx = len(self.nodes)
        if uncertainty is None:
            uncertainty = jnp.eye(self.dim) * 0.1  # Default uncertainty
            
        state = RGFTemporalState(
            vector=vector,
            stored_time=self.current_time,
            uncertainty=uncertainty,
            graph_node_id=node_idx
        )
        self.nodes[node_idx] = state
        
        # Update temporal edges (connect to recent nodes)
        for prev_idx in range(max(0, node_idx-10), node_idx):
            time_diff = self.current_time - self.nodes[prev_idx].stored_time
            self.adjacency = self.adjacency.at[prev_idx, node_idx].set(1.0)
            self.edge_features = self.edge_features.at[prev_idx, node_idx, 0].set(time_diff)
            self.edge_features = self.edge_features.at[prev_idx, node_idx, 1].set(1.0)  # Temporal edge
            
        return node_idx
    
    def compute_green_propagation(self, node_idx: int, 
                                  green_fn: MatrixGreenFunction,
                                  params) -> jnp.ndarray:
        """
        Apply Matrix Green Function to propagate information from node_idx
        to current time through graph structure.
        """
        state = self.nodes[node_idx]
        time_delta = self.current_time - state.stored_time
        
        # Aggregate edge features from neighbors
        neighbors = jnp.where(self.adjacency[node_idx] > 0)[0]
        
        if len(neighbors) == 0:
            # Isolated node - use simple decay
            return state.vector * jnp.exp(-0.01 * time_delta)
        
        # Compute Green function for each edge
        propagated_vectors = []
        for neighbor in neighbors:
            edge_feat = self.edge_features[node_idx, neighbor]
            G = green_fn.apply(params, time_delta, edge_feat)
            
            # Apply Green function to vector (matrix multiplication)
            propagated = G @ state.vector  # G acts as diffusion operator
            propagated_vectors.append(propagated)
        
        # Combine via attention over temporal neighbors
        stacked = jnp.stack(propagated_vectors)
        attention_scores = jnp.dot(stacked, state.vector)  # Compatibility
        attention_weights = jax.nn.softmax(attention_scores)
        
        return jnp.sum(attention_weights[:, None] * stacked, axis=0)

class PPOGraphOptimizer:
    """
    PPO agent that optimizes graph structure (edge weights, connectivity)
    to maximize prediction accuracy of temporal decay.
    """
    
    def __init__(self, graph: SpatiotemporalDecayGraph, 
                 green_fn: MatrixGreenFunction,
                 learning_rate: float = 3e-4):
        self.graph = graph
        self.green_fn = green_fn
        self.lr = learning_rate
        
        # PPO hyperparameters
        self.clip_epsilon = 0.2
        self.value_coef = 0.5
        self.entropy_coef = 0.01
        self.gamma = 0.99
        self.lam = 0.95
        
        # Initialize networks
        self.policy_net = self._build_policy_network()
        self.value_net = self._build_value_network()
        self.optimizer = optimizers.adam(self.lr)
        
    def _build_policy_network(self):
        """Actor: decides which edges to strengthen/weaken."""
        return nn.Sequential([
            nn.Dense(256), nn.relu,
            nn.Dense(256), nn.relu,
            nn.Dense(self.graph.max_nodes * self.graph.max_nodes),
            lambda x: jax.nn.sigmoid(x.reshape(self.graph.max_nodes, 
                                                self.graph.max_nodes))
        ])
    
    def _build_value_network(self):
        """Critic: estimates value of graph state."""
        return nn.Sequential([
            nn.Dense(256), nn.relu,
            nn.Dense(256), nn.relu,
            nn.Dense(1)
        ])
    
    def compute_reward(self, predicted_vectors: Dict[int, jnp.ndarray],
                      actual_future_vectors: Dict[int, jnp.ndarray]) -> float:
        """
        Reward = negative prediction error + graph efficiency bonus.
        """
        total_error = 0.0
        for node_idx, pred in predicted_vectors.items():
            if node_idx in actual_future_vectors:
                actual = actual_future_vectors[node_idx]
                # Cosine similarity reward
                similarity = jnp.dot(pred, actual) / (jnp.linalg.norm(pred) * 
                                                      jnp.linalg.norm(actual))
                total_error += -jnp.log(1 + (1 - similarity))  # Negative log error
        
        # Efficiency bonus: sparsity in adjacency matrix
        sparsity_bonus = -0.01 * jnp.sum(self.graph.adjacency > 0)
        
        return total_error + sparsity_bonus
    
    def ppo_update(self, rollout_data: Dict):
        """
        Standard PPO update with clipping.
        """
        states = rollout_data['states']
        actions = rollout_data['actions']
        old_log_probs = rollout_data['log_probs']
        advantages = rollout_data['advantages']
        returns = rollout_data['returns']
        
        def loss_fn(params):
            # Policy loss with clipping
            new_logits = self.policy_net.apply(params['policy'], states)
            new_log_probs = jnp.log(new_logits * actions + (1 - new_logits) * (1 - actions))
            ratio = jnp.exp(new_log_probs - old_log_probs)
            
            clipped_ratio = jnp.clip(ratio, 1 - self.clip_epsilon, 
                                    1 + self.clip_epsilon)
            policy_loss = -jnp.mean(jnp.minimum(ratio * advantages, 
                                                clipped_ratio * advantages))
            
            # Value loss
            values = self.value_net.apply(params['value'], states)
            value_loss = jnp.mean((values - returns) ** 2)
            
            # Entropy bonus
            entropy = -jnp.mean(new_logits * jnp.log(new_logits + 1e-8))
            
            total_loss = (policy_loss + 
                         self.value_coef * value_loss - 
                         self.entropy_coef * entropy)
            
            return total_loss
        
        # Gradient update
        grads = grad(loss_fn)(self.optimizer.target)
        self.optimizer = self.optimizer.update(grads)

class RGFTemporalDecay:
    """
    Main interface: Temporal Decay Graph upgraded with RGF-F.
    Combines Matrix Green Function with PPO-optimized structure.
    """
    
    def __init__(self, vector_dim: int = 768, max_nodes: int = 10000):
        self.graph = SpatiotemporalDecayGraph(max_nodes, vector_dim)
        self.green_fn = MatrixGreenFunction()
        self.ppo = PPOGraphOptimizer(self.graph, self.green_fn)
        
        # Initialize Green function parameters
        self.green_params = self.green_fn.init(
            jax.random.PRNGKey(0),
            time_delta=1.0,
            edge_features=jnp.ones(3)
        )
        
    def store(self, vector_id: str, vector: jnp.ndarray, 
              uncertainty: jnp.ndarray = None) -> None:
        """Store vector with temporal metadata."""
        self.graph.add_vector(vector_id, vector, uncertainty)
        
    def query(self, vector_id: str, query_time: float = None) -> Tuple[jnp.ndarray, jnp.ndarray]:
        """
        Retrieve vector with RGF-F temporal decay applied.
        
        Returns:
            (decayed_vector, uncertainty_estimate)
        """
        if query_time is None:
            query_time = self.graph.current_time
            
        # Find node by ID (simplified - use hash map in production)
        node_idx = None
        for idx, state in self.graph.nodes.items():
            # Match by vector content similarity (or maintain ID mapping)
            pass
            
        if node_idx is None:
            raise ValueError(f"Vector {vector_id} not found")
        
        # Apply Matrix Green Function propagation
        decayed = self.graph.compute_green_propagation(
            node_idx, self.green_fn, self.green_params
        )
        
        # Uncertainty grows with time (structural uncertainty)
        state = self.graph.nodes[node_idx]
        time_delta = query_time - state.stored_time
        uncertainty = state.uncertainty * (1 + 0.1 * time_delta)
        
        return decayed, uncertainty
    
    def update_graph_structure(self, feedback_batch: Dict):
        """
        Use PPO to optimize graph based on prediction feedback.
        Call this periodically with (predicted, actual) pairs.
        """
        # Unpack feedback
        predicted = feedback_batch['predicted']
        actual = feedback_batch['actual']
        
        # Compute reward
        reward = self.ppo.compute_reward(predicted, actual)
        
        # Collect rollout data and update
        rollout = self._collect_rollout(reward)
        self.ppo.ppo_update(rollout)
        
        # Apply policy to update graph edges
        new_adjacency = self.ppo.policy_net.apply(
            self.ppo.optimizer.target['policy'],
            self._graph_to_state()
        )
        self.graph.adjacency = (self.graph.adjacency * 0.9 + 
                               new_adjacency * 0.1)  # Smooth update
    
    def _collect_rollout(self, reward):
        """Helper to structure data for PPO update."""
        # Simplified - full implementation would track trajectories
        return {
            'states': self._graph_to_state(),
            'actions': self.graph.adjacency,
            'log_probs': jnp.zeros_like(self.graph.adjacency),
            'advantages': jnp.array([reward]),
            'returns': jnp.array([reward])
        }
    
    def _graph_to_state(self):
        """Flatten graph to state vector for policy network."""
        # Concatenate key graph statistics
        node_stats = jnp.array([len(self.graph.nodes)])
        edge_stats = jnp.array([jnp.sum(self.graph.adjacency)])
        time_stats = jnp.array([self.graph.current_time])
        return jnp.concatenate([node_stats, edge_stats, time_stats])

# synthfuse/vector/__init__.py
from .lazy_tensor_scp import LazyTensorSCP
from .temporal_decay_rgf import RGFTemporalDecay
from .manifold_nro import ManifoldNRO

__all__ = ['LazyTensorSCP', 'RGFTemporalDecay', 'ManifoldNRO']
