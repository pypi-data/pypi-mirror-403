"""
Cabinet of Alchemists - Main Orchestrator
Coordinates all specialist agents for Unified Field Engineering
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .roles.architect import Architect
from .roles.engineer import Engineer
from .roles.librarian import Librarian
from .roles.physician import Physician
from .roles.shield import Shield
from .roles.body import Body
from .roles.jury import Jury


class CabinetStatus(Enum):
    """Cabinet operational status."""
    OFFLINE = "offline"
    BOOTING = "booting"
    ONLINE = "online"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"


@dataclass
class CabinetState:
    """Current state of the Cabinet."""
    status: CabinetStatus
    architect_ready: bool
    engineer_ready: bool
    librarian_ready: bool
    physician_ready: bool
    shield_ready: bool
    body_ready: bool
    jury_ready: bool
    last_consensus: Optional[float]
    entropy_level: float
    thermal_load: float


class CabinetOrchestrator:
    """
    Main orchestrator for the Cabinet of Alchemists.
    Manages initialization, consensus, and emergency procedures.
    """
    
    def __init__(self):
        self.architect = Architect()
        self.engineer = Engineer()
        self.librarian = Librarian()
        self.physician = Physician()
        self.shield = Shield()
        self.body = Body()
        self.jury = Jury()
        
        self.status = CabinetStatus.OFFLINE
        self.state = CabinetState(
            status=CabinetStatus.OFFLINE,
            architect_ready=False,
            engineer_ready=False,
            librarian_ready=False,
            physician_ready=False,
            shield_ready=False,
            body_ready=False,
            jury_ready=False,
            last_consensus=None,
            entropy_level=0.0,
            thermal_load=0.0,
        )
        
    async def initialize(self) -> bool:
        """
        Initialize all Cabinet members in proper sequence.
        
        Sequence:
        1. Shield (safety first)
        2. Physician (health monitoring)
        3. Librarian (data ingestion)
        4. Architect (strategy)
        5. Engineer (implementation)
        6. Body (thermal management)
        7. Jury (consensus)
        """
        print("🛡️  Initializing Shield...")
        self.state.shield_ready = await self.shield.initialize()
        
        print("🩺 Initializing Physician...")
        self.state.physician_ready = await self.physician.initialize()
        
        print("📚 Initializing Librarian...")
        self.state.librarian_ready = await self.librarian.initialize()
        
        print("🏛️  Initializing Architect...")
        self.state.architect_ready = await self.architect.initialize()
        
        print("🔧 Initializing Engineer...")
        self.state.engineer_ready = await self.engineer.initialize()
        
        print("🌡️  Initializing Body...")
        self.state.body_ready = await self.body.initialize()
        
        print("⚖️  Initializing Jury...")
        self.state.jury_ready = await self.jury.initialize()
        
        # Check if all ready
        all_ready = all([
            self.state.shield_ready,
            self.state.physician_ready,
            self.state.librarian_ready,
            self.state.architect_ready,
            self.state.engineer_ready,
            self.state.body_ready,
            self.state.jury_ready,
        ])
        
        if all_ready:
            self.status = CabinetStatus.ONLINE
            self.state.status = CabinetStatus.ONLINE
            print("✅ Cabinet of Alchemists fully operational!")
            return True
        else:
            self.status = CabinetStatus.DEGRADED
            self.state.status = CabinetStatus.DEGRADED
            print("⚠️  Cabinet running in degraded mode")
            return False
    
    async def process_sigil(self, sigil_str: str, input_data: Any = None) -> Dict[str, Any]:
        """
        Process a Sigil through the full Cabinet workflow.
        
        Flow:
        1. Architect validates Sigil topology
        2. Engineer compiles to executable kernel
        3. Shield enforces safety bounds
        4. Physician monitors execution
        5. Body manages thermal load
        6. Jury reaches consensus on result
        """
        if self.status != CabinetStatus.ONLINE:
            raise RuntimeError("Cabinet not fully operational")
        
        print(f"🔮 Processing Sigil: {sigil_str}")
        
        # Step 1: Architect designs execution plan
        blueprint = await self.architect.design_blueprint(sigil_str, input_data)
        
        # Step 2: Engineer compiles blueprint
        executable = await self.engineer.compile_blueprint(blueprint)
        
        # Step 3: Shield safety validation
        safety_ok = await self.shield.validate_execution(executable)
        if not safety_ok:
            raise SecurityError("Sigil rejected by Shield - safety violation")
        
        # Step 4: Physician starts monitoring
        monitor_task = asyncio.create_task(
            self.physician.monitor_execution(executable)
        )
        
        # Step 5: Body manages thermal load
        thermal_ok = await self.body.allocate_resources(executable)
        if not thermal_ok:
            await monitor_task  # Clean up
            raise ResourceError("Insufficient thermal budget")
        
        # Step 6: Execute with consensus
        result = await self.jury.execute_with_consensus(
            executable, 
            cabinet_members=[
                self.architect,
                self.engineer,
                self.shield,
                self.physician,
                self.body,
            ]
        )
        
        # Update state
        self.state.last_consensus = asyncio.get_event_loop().time()
        self.state.entropy_level = await self.physician.get_entropy()
        self.state.thermal_load = await self.body.get_thermal_load()
        
        return {
            "result": result,
            "consensus_reached": True,
            "entropy": self.state.entropy_level,
            "thermal_load": self.state.thermal_load,
            "safety_validated": safety_ok,
        }
    
    async def emergency_shutdown(self) -> None:
        """Perform controlled emergency shutdown."""
        print("🛑 Emergency shutdown initiated!")
        
        self.status = CabinetStatus.EMERGENCY
        
        # Shutdown in reverse order
        await self.jury.shutdown()
        await self.body.shutdown()
        await self.engineer.shutdown()
        await self.architect.shutdown()
        await self.librarian.shutdown()
        await self.physician.shutdown()
        await self.shield.shutdown()
        
        print("🛑 Cabinet shutdown complete.")
