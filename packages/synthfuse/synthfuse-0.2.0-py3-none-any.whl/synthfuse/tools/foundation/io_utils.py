from synthfuse.tools import save_checkpoint, load_checkpoint

# Save full training state
save_checkpoint(
    path="checkpoints/iteration_1000.pkl",
    state={
        "params": model_params,
        "optimizer": opt_state,
        "step": current_step,
        "rng": rng_key
    }
)

# Load with automatic device placement
restored = load_checkpoint("checkpoints/iteration_1000.pkl", device=jax.devices()[0])
