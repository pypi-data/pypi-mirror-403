# synthfuse/notebook/checkpoint.py
import pickle
from pathlib import Path

def save_cell(cell: SpellCell, path: str):
    Path(path).parent.mkdir(exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump({
            "spell": cell.spell_str,
            "state": cell.state,
            "history": cell.history
        }, f)

def load_cell(path: str) -> SpellCell:
    # reconstruct + recompile
