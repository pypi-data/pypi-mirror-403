# import numpy as np
# from collections import deque
# from typing import Dict
# from ..core.config import DPO_Config

# class AdvancedConstraintHandler:
#     def __init__(self, config: DPO_Config):
#         self.config = config
#         self.violation_history = deque(maxlen=100)
#         self.penalty_scale = 1.0

#     def compute_adaptive_penalty(self, metrics: Dict, iteration: int, max_iter: int) -> float:
#         penalty = 0.0
#         if metrics['latency_ms'] > self.config.latency_constraint:
#             excess = metrics['latency_ms'] - self.config.latency_constraint
#             penalty += excess * 0.01 * self.penalty_scale
#         if metrics['memory_mb'] > self.config.memory_constraint:
#             excess = metrics['memory_mb'] - self.config.memory_constraint
#             penalty += excess * 0.015 * self.penalty_scale
#         if metrics['flops_m'] > self.config.flops_constraint:
#             excess = metrics['flops_m'] - self.config.flops_constraint
#             penalty += excess * 0.002 * self.penalty_scale
#         self.violation_history.append(penalty > 0)
#         phase = iteration / max(1, max_iter)
#         if phase < 0.3:
#             self.penalty_scale = 1.0
#         else:
#             recent = list(self.violation_history)[-20:]
#             violation_rate = np.mean(recent) if len(recent) > 0 else 0
#             self.penalty_scale = 1.0 + 2.0 * violation_rate
#         return penalty

#     def is_valid(self, metrics: Dict) -> bool:
#         return (
#             metrics['latency_ms'] <= self.config.latency_constraint and
#             metrics['memory_mb'] <= self.config.memory_constraint and
#             metrics['flops_m'] <= self.config.flops_constraint
#         )


import numpy as np
from collections import deque
from typing import Dict
from ..core.config import DPO_Config

class AdvancedConstraintHandler:
    def __init__(self, config: DPO_Config):
        self.config = config
        self.violation_history = deque(maxlen=100)
        self.penalty_scale = 1.0

    def compute_adaptive_penalty(self, metrics: Dict, iteration: int, max_iter: int) -> float:
        penalty = 0.0
        
        # Direct access to config values to avoid repeated attribute lookups
        c_lat = self.config.latency_constraint
        c_mem = self.config.memory_constraint
        c_flop = self.config.flops_constraint
        
        # Check constraints
        if metrics['latency_ms'] > c_lat:
            penalty += (metrics['latency_ms'] - c_lat) * 0.01
        
        if metrics['memory_mb'] > c_mem:
            penalty += (metrics['memory_mb'] - c_mem) * 0.015
            
        if metrics['flops_m'] > c_flop:
            penalty += (metrics['flops_m'] - c_flop) * 0.002
            
        if penalty > 0:
            penalty *= self.penalty_scale
            self.violation_history.append(True)
        else:
            self.violation_history.append(False)

        # Adaptive scaling
        if iteration > 0 and (iteration / max(1, max_iter)) >= 0.3:
            # Optimization: Use sum/len instead of np.mean for small deques
            vh = self.violation_history
            if len(vh) > 0:
                # Calculate rate over last 20 efficiently
                recent_count = 0
                limit = min(len(vh), 20)
                for i in range(1, limit + 1):
                    if vh[-i]:
                        recent_count += 1
                violation_rate = recent_count / limit
                self.penalty_scale = 1.0 + 2.0 * violation_rate
        else:
            self.penalty_scale = 1.0
            
        return penalty

    def is_valid(self, metrics: Dict) -> bool:
        return (
            metrics['latency_ms'] <= self.config.latency_constraint and
            metrics['memory_mb'] <= self.config.memory_constraint and
            metrics['flops_m'] <= self.config.flops_constraint
        )