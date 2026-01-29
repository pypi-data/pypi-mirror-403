from dpo import DPO_NAS
from dpo.core.config import DPO_Config

if __name__ == "__main__":
    config = DPO_Config(
        population_size=60,
        max_iterations=120,
        latency_constraint=50.0,
        w_loss=0.6,
        island_model=True,
        num_islands=3,
    )
    optimizer = DPO_NAS(config)
    results = optimizer.optimize()
    print("Best Fitness:", results['best_fitness'])
