from .meta_alchemist import MetaAlchemist
from .engineer_alchemist import EngineerAlchemist
from .zeta_alchemist import ZetaAlchemist
from .diagnostic import DiagnosticAlchemist
from .regulator import RegulatorState, regulator_step

# The Cabinet Initialization
# This binds the Specialists into a singular 'Council'
class Cabinet:
    def __init__(self):
        self.architect = MetaAlchemist()
        self.engineer = EngineerAlchemist()
        self.physician = DiagnosticAlchemist()
        self.zeta_shield = ZetaAlchemist()

    def resolve(self, problem_description, ingest_path="./ingest/raw/"):
        """
        The Unified Solving Sequence:
        1. Ingest -> 2. Architect -> 3. Engineer -> 4. Execute (with Physician)
        """
        return "Initiating Cabinet Resolution..."

# Global Instance for the Unified Vector Pipeline
cabinet = Cabinet()
