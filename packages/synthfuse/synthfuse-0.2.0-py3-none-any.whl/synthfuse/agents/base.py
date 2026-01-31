# src/synthfuse/agents/base.py
from __future__ import annotations
import abc
import jax.numpy as jnp
from typing import Any, Dict, List, Optional, Union, Protocol
from dataclasses import dataclass

# --- Core Types ---
@dataclass
class AgentResponse:
    """Standardized response from any agent."""
    content: Union[str, jnp.ndarray, Dict[str, Any]]
    metadata: Dict[str, Any]  # latency, tokens, model_version, etc.
    vector: Optional[jnp.ndarray] = None  # optional latent embedding


class Agent(abc.ABC):
    """
    Abstract base class for all agents in Synth-Fuse.
    
    Every agent—whether a cloud LLM, distilled on-device model,
    or fused generative pipeline—must implement this interface.
    """

    @abc.abstractmethod
    def generate(
        self,
        prompt: Union[str, jnp.ndarray],
        **kwargs
    ) -> AgentResponse:
        """
        Synchronous generation.
        For images: prompt may be jnp.ndarray; for text: str.
        """
        pass

    @abc.abstractmethod
    async def agenerate(
        self,
        prompt: Union[str, jnp.ndarray],
        **kwargs
    ) -> AgentResponse:
        """
        Asynchronous generation (for API-backed agents).
        On-device agents may just wrap `generate`.
        """
        pass

    @abc.abstractmethod
    def embed(self, input: Union[str, jnp.ndarray]) -> jnp.ndarray:
        """
        Return a latent vector representation.
        Critical for /vector integration and forum consensus.
        """
        pass

    def to_forum_ready(self) -> "ForumAgent":
        """
        Wrap this agent for participation in LLM-to-LLM debate.
        Default implementation provided; override if needed.
        """
        return ForumAgent(self)


# --- Forum Participation Protocol ---
class ForumAgent:
    """
    Lightweight wrapper enabling any Agent to join the `forum/arena`.
    """
    def __init__(self, agent: Agent):
        self._agent = agent
        self.identity = getattr(agent, "name", agent.__class__.__name__)

    def respond(self, message: str, context: Dict[str, Any]) -> AgentResponse:
        return self._agent.generate(message, context=context)

    def get_embedding(self, message: str) -> jnp.ndarray:
        return self._agent.embed(message)


# --- Utility: Agent Registry Hook ---
def register_agent(name: str):
    """
    Decorator to auto-register agents in hub.py.
    Example:
        @register_agent("qwen")
        class QwenAgent(Agent): ...
    """
    def decorator(cls):
        from .hub import _AGENT_REGISTRY
        _AGENT_REGISTRY[name] = cls
        return cls
    return decorator
