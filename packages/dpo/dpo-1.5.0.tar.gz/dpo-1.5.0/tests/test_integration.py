from dpo import DPO_NAS
from dpo.core.config import DPO_Config
from dpo.evaluation import EnsembleEstimator
from dpo.constraints import AdvancedConstraintHandler

def test_integration_pipeline():
    config = DPO_Config(population_size=8, max_iterations=3)
    ensemble = EnsembleEstimator(['zero_shot', 'surrogate'])
    handler = AdvancedConstraintHandler(config)
    optimizer = DPO_NAS(config, estimator=ensemble, constraint_handler=handler)
    results = optimizer.optimize()
    assert isinstance(results['best_fitness'], float)
