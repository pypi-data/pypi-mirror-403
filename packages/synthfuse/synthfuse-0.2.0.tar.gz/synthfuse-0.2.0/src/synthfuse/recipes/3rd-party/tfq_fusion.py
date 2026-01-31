"""
TFQ-Fusion – TensorFlow Quantum via TFQ + JAX
TFQ operators exposed as Synth-Fuse primitives:
ℚ𝕌𝔸ℕ𝕋𝕌𝙼 (circuit), ℚℂ𝙸ℝ𝙲 (expectation), ℚ𝙼𝙴𝙰𝚂 (measurement)
Original: https://github.com/tensorflow/quantum
Converted to single Synth-Fuse spell:
(ℚ𝕌𝔸ℕ𝕋𝕌𝙼 ⊗ ℚℂ𝙸ℝ𝙲 ⊗ ℚ𝙼𝙴𝙰𝚂)(n_qubits=4, depth=3, shots=1024)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  TFQ ↔ JAX bridge (zero-copy via dlpack)
# ----------------------------------------------------------
# pip install tensorflow-quantum jax[dlpack]
import tensorflow as tf
import tensorflow_quantum as tfq
from jax import dlpack


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("ℚ𝕌𝔸ℕ𝕋𝕌𝙼")
def tfq_circuit_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    TFQ quantum circuit forward (any gate set).
    Params: n_qubits (int), depth (int), shots (int)
    Returns: circuit state vector (JAX array)
    """
    n_qubits = params["n_qubits"]
    depth = params["depth"]
    shots = params["shots"]

    # build circuit in TFQ
    qubits = cirq.GridQubit.rect(1, n_qubits)
    circuit = cirq.Circuit()
    for d in range(depth):
        for q in qubits:
            circuit.append(cirq.ry(np.pi * jax.random.uniform(key, (1,))).on(q))
        circuit.append(cirq.cz(qubits[i], qubits[i + 1]) for i in range(n_qubits - 1))

    # JAX → TF
    circuit_batch = tfq.convert_to_tensor([circuit] * 1)  # batch size 1
    output = tfq.layers.State()(circuit_batch)  # [1, 2^n]
    vec = tf.squeeze(output)  # [2^n]

    # TF → JAX (zero-copy)
    vec_jax = jax.dlpack.from_dlpack(vec.experimental_dlpack())

    return dict(circuit_vec=vec_jax, circuit_str=str(circuit))


@register("ℚℂ𝙸ℝ𝙲")
def tfq_expectation_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    TFQ expectation value (any Hamiltonian).
    Params: hamiltonian (str), shots (int)
    Returns: expectation (scalar JAX)
    """
    hamiltonian = params["hamiltonian"]  # e.g. "0.5 * Z(0) * Z(1)"
    shots = params["shots"]
    circuit_vec = state["circuit_vec"]  # from ℚ𝕌𝔸ℕ𝕋𝕌𝙼 step

    # build Hamiltonian in TFQ
    ham = tfq.convert_to_tensor([cirq.PauliString({cirq.GridQubit(0, i): cirq.Z}) for i in range(2)])
    expect = tfq.layers.Expectation()(circuit_batch, operators=ham, repetitions=shots)
    expect_jax = jax.dlpack.from_dlpack(expect.experimental_dlpack())

    return dict(expectation=expect_jax)


@register("ℚ𝙼𝙴𝙰𝚂")
def tfq_measure_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    TFQ measurement (any basis).
    Params: basis (str), shots (int)
    Returns: measurement counts (JAX array)
    """
    basis = params["basis"]  # e.g. "Z"
    shots = params["shots"]
    circuit_vec = state["circuit_vec"]

    # measurement in chosen basis
    if basis == "Z":
        ops = [cirq.Z(cirq.GridQubit(0, i)) for i in range(2)]
    else:
        ops = [cirq.X(cirq.GridQubit(0, i)) for i in range(2)]

    measured = tfq.layers.Expectation()(circuit_batch, operators=ops, repetitions=shots)
    counts_jax = jax.dlpack.from_dlpack(measured.experimental_dlpack())

    return dict(counts=counts_jax, basis=basis)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(ℚ𝕌𝔸ℕ𝕋𝕌𝙼 ⊗ ℚℂ𝙸ℝ𝕔 ⊗ ℚ𝙼𝙴𝙰𝚂)(n_qubits=4, depth=3, shots=1024, hamiltonian=0.5*Z(0)*Z(1), basis=Z)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_tfq(
    n_qubits: int = 4,
    depth: int = 3,
    shots: int = 1024,
    hamiltonian: str = "0.5 * Z(0) * Z(1)",
    basis: str = "Z",
):
    spell = "(ℚ𝕌𝔸ℕ𝕋𝕌𝙼 ⊗ ℚℂ𝙸ℝ𝕔 ⊗ ℚ𝙼𝙴𝙰𝚂)(n_qubits={}, depth={}, shots={}, hamiltonian={}, basis={})".format(
        n_qubits, depth, shots, hamiltonian, basis
    )
    step_fn = compile_spell(spell)

    # build static quantum circuit ( injected as param )
    import cirq
    qubits = cirq.GridQubit.rect(1, n_qubits)
    circuit = cirq.Circuit()
    for d in range(depth):
        for q in qubits:
            circuit.append(cirq.ry(np.pi * 0.5).on(q))
        circuit.append([cirq.cz(qubits[i], qubits[i + 1]) for i in range(n_qubits - 1)])

    # bind static circuit into params
    def bound_step(key, state):
        return step_fn(key, state, {
            "n_qubits": n_qubits,
            "depth": depth,
            "shots": shots,
            "hamiltonian": hamiltonian,
            "basis": basis,
            "circuit_batch": tfq.convert_to_tensor([circuit] * 1),  # static
        })

    # initial state – empty (TFQ fills it)
    state = dict(
        dummy=jnp.zeros(1),  # placeholder
    )

    return jax.jit(bound_step), state
