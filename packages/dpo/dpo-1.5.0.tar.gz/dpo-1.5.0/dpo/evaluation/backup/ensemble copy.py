# import numpy as np
# import json
# from typing import Dict, List, Tuple
# from .cache import EvaluationCache
# from .estimators import ZeroShotEstimator, SurrogateEstimator

# class EnsembleEstimator:
#     def __init__(self, strategies: List[str] = None):
#         self.strategies = strategies or ['zero_shot', 'surrogate']
#         self.cache = EvaluationCache()
#         self.estimators = {}
#         for strategy in self.strategies:
#             if strategy == 'zero_shot':
#                 self.estimators[strategy] = ZeroShotEstimator()
#             elif strategy == 'surrogate':
#                 self.estimators[strategy] = SurrogateEstimator()

#     def estimate(self, arch_dict: Dict) -> Tuple[float, Dict]:
#         arch_hash = json.dumps(arch_dict, sort_keys=True)
#         cached = self.cache.get(arch_hash)
#         if cached:
#             return cached
#         losses = []
#         metrics_list = []
#         for _, estimator in self.estimators.items():
#             loss, metrics = estimator.estimate(arch_dict)
#             losses.append(loss)
#             metrics_list.append(metrics)
#         avg_loss = float(np.mean(losses))
#         common_keys = {'latency_ms', 'memory_mb', 'flops_m'}
#         avg_metrics = {}
#         for k in common_keys:
#             values = [m[k] for m in metrics_list if k in m]
#             if values:
#                 avg_metrics[k] = float(np.mean(values))
#         result = (avg_loss, avg_metrics)
#         self.cache.put(arch_hash, result)
#         return result

import numpy as np
import json
from typing import Dict, List, Tuple
from .cache import EvaluationCache
from .estimators import ZeroShotEstimator, SurrogateEstimator

class EnsembleEstimator:
    def __init__(self, strategies: List[str] = None):
        self.strategies = strategies or ['zero_shot', 'surrogate']
        self.cache = EvaluationCache()
        self.estimators = {}
        for strategy in self.strategies:
            if strategy == 'zero_shot':
                self.estimators[strategy] = ZeroShotEstimator()
            elif strategy == 'surrogate':
                self.estimators[strategy] = SurrogateEstimator()
        self._common_keys = ['latency_ms', 'memory_mb', 'flops_m']

    def estimate(self, arch_dict: Dict) -> Tuple[float, Dict]:
        # Optimization: json.dumps(sort_keys=True) is consistent but slow.
        # Ideally we use the gene hash, but arch_dict is passed here.
        # We assume consistent input order or pay the sort penalty.
        arch_hash = json.dumps(arch_dict, sort_keys=True)
        
        cached = self.cache.get(arch_hash)
        if cached:
            return cached

        # Vectorized accumulation
        losses = 0.0
        metrics_acc = {k: 0.0 for k in self._common_keys}
        count = len(self.estimators)
        
        for estimator in self.estimators.values():
            loss, metrics = estimator.estimate(arch_dict)
            losses += loss
            for k in self._common_keys:
                if k in metrics:
                    metrics_acc[k] += metrics[k]

        avg_loss = losses / count
        avg_metrics = {k: v / count for k, v in metrics_acc.items()}
        
        result = (avg_loss, avg_metrics)
        self.cache.put(arch_hash, result)
        return result