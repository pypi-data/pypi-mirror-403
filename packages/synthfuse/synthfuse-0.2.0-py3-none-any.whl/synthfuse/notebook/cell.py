# synthfuse/notebook/cell.py
from typing import Any, Dict
from jax import Array
from synthfuse.recipes import parse_spell

class SpellCell:
    def __init__(self, spell_str: str, params: Dict[str, Any] = None):
        self.spell_str = spell_str
        self.params = params or {}
        self.compiled_step, self.init_state = parse_spell(spell_str)
        self.state = None
        self.history = []  # [(step, metrics), ...]

    def run(self, steps: int, key: Array):
        if self.state is None:
            self.state = self.init_state(key, **self.params)
        for _ in range(steps):
            self.state = self.compiled_step(key, self.state, self.params)
            self.history.append(self._extract_metrics(self.state))
        return self.state

    def _extract_metrics(self, state):
        # Extract x, loss, entropy, etc. based on recipe
        return {"x": state.x.mean(), "entropy": ...}
