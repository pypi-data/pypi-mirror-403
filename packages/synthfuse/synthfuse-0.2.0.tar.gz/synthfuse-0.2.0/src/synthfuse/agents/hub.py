# src/synthfuse/agents/hub.py
"""
Unified agent registry and loader for Synth-Fuse.

Supports:
- Cloud API agents (Qwen, Kimi, etc.)
- On-device fused pipelines (e.g., Tensor-Graph Fusion)
- Auto-discovery via @register_agent decorator
"""

from typing import Dict, Any, Optional, Type
from .base import Agent

# Global registry populated by @register_agent
_AGENT_REGISTRY: Dict[str, Type[Agent]] = {}

def list_agents() -> list[str]:
    """Return all registered agent names."""
    return list(_AGENT_REGISTRY.keys())

def load_agent(
    name: str,
    **config: Any
) -> Agent:
    """
    Load an agent by name with configuration.
    
    Examples:
        >>> agent = load_agent("qwen", api_key="sk-...")
        >>> agent = load_agent("tensor_fusion", steps=30, noise_scale=0.1)
    """
    if name not in _AGENT_REGISTRY:
        raise ValueError(
            f"Agent '{name}' not found. Available: {list_agents()}. "
            "Did you forget to install a plugin or define @register_agent?"
        )
    
    cls = _AGENT_REGISTRY[name]
    return cls(**config)

def register_agent(name: str):
    """
    Decorator to register an agent class under a name.
    Used in external/*/client.py or local implementations.
    """
    def decorator(cls: Type[Agent]) -> Type[Agent]:
        if not issubclass(cls, Agent):
            raise TypeError(f"Class {cls.__name__} must inherit from synthfuse.agents.base.Agent")
        _AGENT_REGISTRY[name] = cls
        return cls
    return decorator
