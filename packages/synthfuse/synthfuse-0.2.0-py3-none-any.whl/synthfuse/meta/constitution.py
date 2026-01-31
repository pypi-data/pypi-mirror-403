# synthfuse/meta/constitution.py
from dataclasses import dataclass

@dataclass
class Constitution:
    alpha: float = 1.0   # compression weight
    beta: float = 0.8    # composition weight
    gamma: float = 0.5   # withholding weight
    epsilon: float = 0.042  # from calibration
    delta: float = 0.15
    tau: int = 10
    theta: float = 1e-3  # non-commutativity tolerance
