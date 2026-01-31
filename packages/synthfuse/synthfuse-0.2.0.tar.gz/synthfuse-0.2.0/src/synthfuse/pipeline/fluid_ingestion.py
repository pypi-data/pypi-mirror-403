import jax
import jax.numpy as jnp
from pathlib import Path
from synthfuse.meta import zeta_alchemist
from synthfuse.systems import erudite, gatekeeper

class FluidIngestor:
    """
    The 'Digestive Tract' of Synth-Fuse.
    Converts raw byte-streams into Zeta-aligned Lazy Tensors.
    """
    def __init__(self, watch_path="./ingest/raw/", buffer_size=1024):
        self.path = Path(watch_path)
        self.buffer_size = buffer_size
        self.physician_gate = gatekeeper.Gatekeeper()

    def stream_to_manifold(self, filename: str):
        """
        Inhales a file and immediately projects it into the 
        System Erudite's frequency vault.
        """
        full_path = self.path / filename
        
        # 1. Open Gate Check (Is this data signed/safe?)
        if not self.physician_gate.verify_data_integrity(full_path):
            raise ConnectionRefusedError("Fluid Ingestion: Data block rejected by Gatekeeper.")

        # 2. Async Inhalation
        # We process in 'Fluid Blocks' to prevent Thermal Mesh spikes
        raw_data = self._read_as_lazy_blocks(full_path)
        
        # 3. Zeta-Projection (Frequency Alignment)
        # This is where the 'Alchemy' happens: Bytes -> Frequencies
        zeta_manifold = zeta_alchemist.project_to_zeta(raw_data)
        
        # 4. Hand-off to Librarian
        return erudite.librarian.register_vault_entry(
            name=filename,
            tensor=zeta_manifold,
            metadata={"source": "fluid_ingestion", "dtype": "spectral"}
        )

    def _read_as_lazy_blocks(self, path):
        """Lazy generator to keep memory lean."""
        with open(path, 'rb') as f:
            while chunk := f.read(self.buffer_size):
                yield jnp.frombuffer(chunk, dtype=jnp.uint8)
