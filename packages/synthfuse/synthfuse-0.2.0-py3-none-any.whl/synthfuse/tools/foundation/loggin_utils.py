from synthfuse.tools import get_logger, TensorBoardLogger

logger = get_logger("synthfuse.swarm")

logger.info("Starting PSO optimization", 
            swarm_size=100, 
            dimensions=50,
            device_type=jax.default_backend())

# TensorBoard integration
tb_logger = TensorBoardLogger("runs/experiment_1")
tb_logger.scalar("fitness/best", best_fitness, step=iteration)
tb_logger.histogram("positions", positions, step=iteration)
