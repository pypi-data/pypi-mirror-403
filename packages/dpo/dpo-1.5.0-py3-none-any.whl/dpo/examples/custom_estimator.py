from typing import Dict, Tuple
from dpo import DPO_NAS
from dpo.core.config import DPO_Config
from dpo.evaluation.ensemble import EnsembleEstimator

class MyCustomEstimator:
    def estimate(self, arch_dict: Dict) -> Tuple[float, Dict]:
        loss = 0.3
        metrics = {
            'latency_ms': 30.0,
            'memory_mb': 20.0,
            'flops_m': 100.0,
        }
        return loss, metrics

if __name__ == "__main__":
    config = DPO_Config.fast()
    ensemble = EnsembleEstimator([])
    ensemble.estimators['custom'] = MyCustomEstimator()
    def estimate(arch_dict):
        return ensemble.estimators['custom'].estimate(arch_dict)
    # Monkey patch simple single-estimator behavior
    ensemble.estimate = estimate  # type: ignore
    optimizer = DPO_NAS(config, estimator=ensemble)
    results = optimizer.optimize()
    print("Best Fitness:", results['best_fitness'])
