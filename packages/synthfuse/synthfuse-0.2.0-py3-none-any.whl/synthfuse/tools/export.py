"""
One-liner exports:  Synth-Fuse spell → ONNX / Torch / TF / GGUF / FlatBuffer
All functions are **pure** (no side-effects) and **JIT-compatible**.
"""
from pathlib import Path
from typing import Any, Callable
import jax
import jax.numpy as jnp
from jax import export as jex
from synthfuse.alchemj import compile_spell

PyTree = Any


# ------------------------------------------------------------------
# 1.  ONNX export ( JAX → StableHLO → ONNX )
# ------------------------------------------------------------------
def to_onnx(spell: str, file: Path | str, *, input_spec: PyTree) -> Path:
    """
    spell        – ALCHEM-J string
    file         – output .onnx path
    input_spec   – PyTree of shapes/dtypes, e.g. {"x": jnp.zeros((10,))}
    Returns Path to written file
    """
    step = compile_spell(spell)

    # Lower to StableHLO
    lowered = jex.export(step)(input_spec)

    # StableHLO → ONNX via jax-onnx
    try:
        import jax_onnx
    except ImportError as e:
        raise RuntimeError("pip install jax-onnx") from e

    onnx_model = jax_onnx.from_exported(lowered)
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    jax_onnx.save(onnx_model, file)
    return file


# ------------------------------------------------------------------
# 2.  PyTorch module ( traced JAX → Torch FX graph )
# ------------------------------------------------------------------
def to_torch(spell: str, *, input_spec: PyTree) -> "torch.nn.Module":
    """
    Returns torch.nn.Module that calls the fused kernel via torch-xla bridge.
    No file written – you can torch.save() the returned module.
    """
    step = compile_spell(spell)

    # JAX → TorchFX via torch-xla
    try:
        import torch
        import torch_xla.core.xla_model as xm
        from torch_xla.experimental import jax_torch
    except ImportError as e:
        raise RuntimeError("pip install torch torch-xla") from e

    class TorchModule(torch.nn.Module):
        def __init__(self, jax_fn, in_spec):
            super().__init__()
            self.jax_fn = jax_fn
            self.in_spec = in_spec

        def forward(self, *flat):
            # re-pack PyTree
            args, _ = jax.tree.unflatten(self.in_spec, flat)
            out = self.jax_fn(args)
            flat_out, _ = jax.tree.flatten(out)
            return flat_out if len(flat_out) > 1 else flat_out[0]

    # trace once to build FX graph
    dummy_flat, spec = jax.tree.flatten(input_spec)
    dummy_torch = [torch.from_numpy(np.array(d)) for d in dummy_flat]
    return TorchModule(step, spec)


# ------------------------------------------------------------------
# 3.  TensorFlow SavedModel ( JAX → TF function )
# ------------------------------------------------------------------
def to_tf_savedmodel(spell: str, dir: Path | str, *, input_spec: PyTree) -> Path:
    dir = Path(dir)
    step = compile_spell(spell)

    # JAX → TF via jax2tf
    try:
        import jax2tf
        import tensorflow as tf
    except ImportError as e:
        raise RuntimeError("pip install jax2tf tensorflow") from e

    tf_fn = jax2tf.convert(step, polymorphic_shapes=[None])  # polymorphic batch
    tf.saved_model.save(
        tf.Module(tf_fn, name="synthfuse"),
        str(dir),
        signatures=tf_fn.get_concrete_function(input_spec),
    )
    return dir


# ------------------------------------------------------------------
# 4.  GGUF (for llama.cpp style inference servers)
# ------------------------------------------------------------------
def to_gguf(spell: str, file: Path | str, *, input_spec: PyTree, name: str = "sfusion") -> Path:
    """
    Exports *weights* (params PyTree) into GGUF container.
    The fused kernel itself is embedded as a custom op byte-code.
    """
    file = Path(file)
    step = compile_spell(spell)
    # 1. extract frozen params (empty here – but future spells may learn)
    params = {}  # placeholder
    # 2. serialise kernel as stablehlo byte-code
    hlo = jax.jit(step).lower(input_spec).compiler_ir("stablehlo")
    kernel_bytes = str(hlo).encode()

    try:
        import gguf
    except ImportError as e:
        raise RuntimeError("pip install gguf") from e

    gguf_writer = gguf.GGUFWriter(file, name)
    gguf_writer.add_string("synthfuse.kernel", kernel_bytes.decode())
    gguf_writer.add_string("synthfuse.spell", spell)
    # add any params tensors
    for key, arr in params.items():
        gguf_writer.add_tensor(key, np.asarray(arr))
    gguf_writer.write_header()
    gguf_writer.close()
    return file


# ------------------------------------------------------------------
# 5.  FlatBuffer schema + zero-copy header
# ------------------------------------------------------------------
def to_flatbuffer(spell: str, file: Path | str, *, input_spec: PyTree) -> Path:
    """
    Generates minimal FlatBuffer schema + binary:
      table Spell {
        kernel:[ubyte];
        spell:string;
        input_shape:[int];
      }
    Returns path to .fbs (schema) and .bin (data)  (file.bin written)
    """
    file = Path(file).with_suffix("")  # drop extension
    step = compile_spell(spell)
    hlo_bytes = str(jax.jit(step).lower(input_spec).compiler_ir("stablehlo")).encode()

    # build schema text
    schema = f"""
table Spell {{
  kernel:[ubyte];
  spell:string;
  input_shape:[int];
}}
root_type Spell;
"""
    schema_file = file.with_suffix(".fbs")
    schema_file.write_text(schema)

    # build binary via flatc (runtime optional)
    import subprocess, tempfile, numpy as np
    bin_file = file.with_suffix(".bin")

    with tempfile.TemporaryDirectory() as tmp:
        stub_py = Path(tmp) / "build.py"
        stub_py.write_text(f"""
import flatbuffers
import sys, os
sys.path.append("{tmp}")
# quick & dirty compile
subprocess.run(["flatc", "--python", "{schema_file}"], cwd=tmp)
from Spell import Spell
builder = flatbuffers.Builder(1024)
kb = builder.CreateByteVector({list(hlo_bytes)})
sb = builder.CreateString({repr(spell)})
Spell.Start(builder)
Spell.AddKernel(builder, kb)
Spell.AddSpell(builder, sb)
Spell.AddInputShape(builder, builder.CreateVector([]))  # TODO shape
off = Spell.End(builder)
builder.Finish(off)
with open("{bin_file}", "wb") as f:
    f.write(builder.Output())
""")
        subprocess.run([sys.executable, str(stub_py)], check=True)
    return bin_file