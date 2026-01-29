from dpo import DPO_NAS
from dpo.core.config import DPO_Config

def test_optimizer_runs_quickly():
    config = DPO_Config(population_size=10, max_iterations=5, island_model=False)
    optimizer = DPO_NAS(config)
    results = optimizer.optimize()
    assert 'best_fitness' in results and 'best_architecture' in results
