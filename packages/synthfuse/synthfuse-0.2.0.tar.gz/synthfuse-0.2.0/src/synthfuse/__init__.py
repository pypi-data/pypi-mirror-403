"""
Synth-Fuse v0.2.0 - Unified Field Engineering
A Deterministic Hybrid Organism Architecture
"""

__version__ = "0.2.0"
__author__ = "J. Roberto Jiménez"
__email__ = "tijuanapaint@gmail.com"
__license__ = "OpenGate Integrity License"

# Core exports
from .cabinet.cabinet_orchestrator import CabinetOrchestrator
from .sigils.compiler import SigilCompiler
from .ingest.manager import IngestionManager

# Convenience imports
from .alchemj import (
    parse_spell,
    compile_spell,
    execute_spell,
)

# Version info
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "CabinetOrchestrator",
    "SigilCompiler", 
    "IngestionManager",
    "parse_spell",
    "compile_spell",
    "execute_spell",
]
def start_engine():
    """Starts the Cabinet, Librarian, and Physician in sync."""
    print("Synth-Fuse v0.2.0: Cabinet of Alchemists is ONLINE.")
    # Auto-watch the /ingest/ folder
    return cabinet.start_autonomous_loop()
