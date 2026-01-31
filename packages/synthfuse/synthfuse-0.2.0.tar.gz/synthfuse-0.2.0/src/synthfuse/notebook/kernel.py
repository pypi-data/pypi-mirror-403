# synthfuse/notebook/kernel.py
import jax
from .cell import SpellCell
from .viz import render_spell_viz

def run_cell(spell: str, steps=100, seed=42, viz=True):
    key = jax.random.PRNGKey(seed)
    cell = SpellCell(spell)
    final_state = cell.run(steps, key)
    
    if viz:
        svg = render_spell_viz(spell)  # calls sfviz internally
        display(HTML(svg))  # works in Jupyter
    
    return cell, final_state
