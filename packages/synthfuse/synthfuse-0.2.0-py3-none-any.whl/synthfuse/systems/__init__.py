from .erudite import SystemErudite
from .achiever import Achiever
from .gatekeeper import Gatekeeper
from .thermo_mesh import ThermoMesh
from .stcl import SemanticThermodynamicLoop

# Registering the 'Body' components
librarian = SystemErudite()
executive = Achiever()
shield = Gatekeeper()
thermal_controller = ThermoMesh()
