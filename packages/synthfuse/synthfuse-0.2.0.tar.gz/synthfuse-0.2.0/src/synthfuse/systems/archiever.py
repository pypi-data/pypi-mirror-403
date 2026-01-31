# src/synthfuse/systems/achiever.py
from synthfuse.systems import erudite, gatekeeper

class Achiever:
    """
    The Executive. Uses retrieved context to fulfill the Alchemist's Spells.
    """
    def __init__(self):
        self.librarian = erudite.SystemErudite()
        self.shield = gatekeeper.Gatekeeper()

    def execute_goal(self, goal_description):
        # 1. Ask Librarian for the "Shape" of the data
        context_manifold = self.librarian.search_manifold(goal_description)
        
        # 2. The Achiever 'Achieves' by reducing entropy in the manifold
        # This triggers the STCL (Semantic-Thermodynamic Loop)
        result = self.run_fusion_loop(goal_description, context_manifold)
        
        return result
