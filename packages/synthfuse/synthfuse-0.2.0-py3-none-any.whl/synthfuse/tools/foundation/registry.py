from synthfuse.tools import Registry

# Register a custom optimizer
@Registry.register("optimizer", "custom_pso")
class CustomPSO:
    def __init__(self, config):
        self.config = config
    
    def update(self, state, fitness):
        # Implementation
        pass

# Later, instantiate by name
optimizer_class = Registry.get("optimizer", "custom_pso")
optimizer = optimizer_class(config)
