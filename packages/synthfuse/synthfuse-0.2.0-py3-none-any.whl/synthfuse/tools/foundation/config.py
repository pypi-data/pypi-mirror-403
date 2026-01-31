from synthfuse.tools import Config, load_config

# Load from YAML/JSON
config = load_config("experiments/swarm_pso.yaml")

# Access nested parameters
learning_rate = config.optim.learning_rate
batch_size = config.data.batch_size
