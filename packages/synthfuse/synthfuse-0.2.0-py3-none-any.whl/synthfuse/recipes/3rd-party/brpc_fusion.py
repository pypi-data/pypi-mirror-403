"""
BRPC-Fusion – High-Performance RPC via brpc + JAX
brpc operators exposed as Synth-Fuse primitives:
𝙱𝚁𝙿𝙲 (RPC call), 𝚁𝙿𝙲 (streaming), 𝚂𝚃𝚁𝙴𝙰𝙼 (zero-copy transport)
Original: https://github.com/apache/brpc
Converted to single Synth-Fuse spell:
(𝙱𝚁𝙿𝙲 ⊗ 𝚁𝙿𝙲 ⊗ 𝚂𝚃𝚁𝙴𝙰𝙼)(host=127.0.0.1, port=8080, streaming=True, zero_copy=True)
"""
import jax
import jax.numpy as jnp
import chex
from synthfuse.alchemj import compile_spell
from synthfuse.alchemj.registry import register

# ----------------------------------------------------------
# 1.  brpc via PythonCall (zero-copy)
# ----------------------------------------------------------
# pip install brpc juliacall python-call
try:
    from juliacall import Main as jl
except ImportError as e:
    raise RuntimeError("pip install brpc juliacall python-call") from e


# ----------------------------------------------------------
# 2.  Registered primitives (JAX-safe wrappers)
# ----------------------------------------------------------
@register("𝙱𝚁𝙿𝙲")
def brpc_call_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    brpc RPC call (any method).
    Params: host (str), port (int), method (str)
    Returns: response (JAX array)
    """
    host = params["host"]
    port = params["port"]
    method = params["method"]
    payload = state["payload"]  # JAX array [n]

    # call brpc via Julia (zero-copy – arrays stay in memory)
    jl.seval("using BRPC")
    jl.host = host
    jl.port = port
    jl.method = method
    jl.payload = payload
    jl.seval("""
        using BRPC: rpc_call
        resp = rpc_call(host, port, method, payload)
    """)
    resp = jl.resp  # PyTree (JAX array)

    return dict(response=resp, host=host, port=port, method=method)


@register("𝚁𝙿𝙲")
def rpc_stream_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    brpc streaming RPC (bidirectional).
    Params: streaming (bool), chunk_size (int)
    Returns: stream of responses (JAX array)
    """
    streaming = params["streaming"]
    chunk_size = params["chunk_size"]
    stream = state["stream"]  # JAX array [n, chunk]

    # call brpc streaming via Julia (zero-copy)
    jl.seval("using BRPC: rpc_stream")
    jl.streaming = streaming
    jl.chunk_size = chunk_size
    jl.stream = stream
    jl.seval("""
        using BRPC: rpc_stream
        resp_stream = rpc_stream(stream, chunk_size=chunk_size, streaming=streaming)
    """)
    resp_stream = jl.resp_stream  # PyTree (JAX array)

    return dict(resp_stream=resp_stream, streaming=streaming, chunk_size=chunk_size)


@register("𝚂𝚃𝚁𝙴𝙰𝙼")
def brpc_zero_copy_step(key: jax.Array, state: PyTree, params: dict) -> PyTree:
    """
    brpc zero-copy transport (shared memory).
    Params: zero_copy (bool), buffer_size (int)
    Returns: zero-copy buffer (JAX array)
    """
    zero_copy = params["zero_copy"]
    buffer_size = params["buffer_size"]
    buffer = state["buffer"]  # JAX array [n]

    # call brpc zero-copy via Julia (zero-copy)
    jl.seval("using BRPC: zero_copy_transport")
    jl.zero_copy = zero_copy
    jl.buffer_size = buffer_size
    jl.buffer = buffer
    jl.seval("""
        using BRPC: zero_copy_transport
        zc_buffer = zero_copy_transport(buffer, buffer_size=buffer_size, zero_copy=zero_copy)
    """)
    zc_buffer = jl.zc_buffer  # PyTree (JAX array)

    return dict(zc_buffer=zc_buffer, zero_copy=zero_copy, buffer_size=buffer_size)


# ----------------------------------------------------------
# 4.  Fused spell
# ----------------------------------------------------------
_SPELL = "(𝙱𝚁𝙿𝙲 ⊗ 𝚁𝙿𝙲 ⊗ 𝚂𝚃𝚁𝙴𝙰𝙼)(host=127.0.0.1, port=8080, streaming=True, zero_copy=True, chunk_size=1024, buffer_size=4096)"


# ----------------------------------------------------------
# 5.  Factory – identical API to fql_rime
# ----------------------------------------------------------
def make_brpc(
    host: str = "127.0.0.1",
    port: int = 8080,
    streaming: bool = True,
    zero_copy: bool = True,
    chunk_size: int = 1024,
    buffer_size: int = 4096,
):
    spell = "(𝙱𝚁𝙿𝙲 ⊗ 𝚁𝙿𝙲 ⊗ 𝚂𝚃𝚁𝙴𝙰𝙼)(host={}, port={}, streaming={}, zero_copy={}, chunk_size={}, buffer_size={})".format(
        host, port, streaming, zero_copy, chunk_size, buffer_size
    )
    step_fn = compile_spell(spell)

    # bind static params
    def bound_step(key, state):
        return step_fn(key, state, {
            "host": host,
            "port": port,
            "streaming": streaming,
            "zero_copy": zero_copy,
            "chunk_size": chunk_size,
            "buffer_size": buffer_size,
        })

    # initial state – empty (brpc fills it)
    state = dict(
        payload=jnp.zeros(1024),  # dummy payload
        stream=jnp.zeros((10, 1024)),  # dummy stream
        buffer=jnp.zeros(4096),  # dummy buffer
    )

    return jax.jit(bound_step), state
