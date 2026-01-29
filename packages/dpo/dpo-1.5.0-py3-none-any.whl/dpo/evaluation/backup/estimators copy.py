

# import numpy as np
# import json
# from typing import Dict, Tuple

# class ZeroShotEstimator:
#     def __init__(self):
#         self.cache: Dict[str, Tuple[float, Dict]] = {}

#     def estimate(self, arch_dict: Dict) -> Tuple[float, Dict]:
#         # Simple caching based on memory address would fail for dicts, 
#         # using json hash required for consistency
#         arch_hash = json.dumps(arch_dict, sort_keys=True)
#         if arch_hash in self.cache:
#             return self.cache[arch_hash]

#         ops = arch_dict['operations']
#         skips = arch_dict['skip_connections']
#         num_layers = len(ops)
        
#         # Optimized Logic
#         num_skips = sum(skips)
#         depth_mult = arch_dict['depth_multiplier']
#         channel_mult = arch_dict['channel_multiplier']
        
#         max_skips = max(1, len(skips))
        
#         snip_score = (
#             0.3 * (num_skips / max_skips) +
#             0.3 * (1.0 - abs(depth_mult - 0.8) / 0.8) +
#             0.4 * (1.0 - abs(channel_mult - 0.8) / 0.8)
#         )
        
#         loss = 0.4 - snip_score * 0.15 + np.random.randn() * 0.02
        
#         # Pre-calc bases
#         base_latency = 25.0 + num_layers * 2.5
#         base_memory = 20.0 + num_layers * 1.2
#         base_flops = 80.0 + num_layers * 12.0
        
#         latency = base_latency * (1.0 + (channel_mult - 1.0) * 0.5)
#         memory = base_memory * (1.0 + (channel_mult - 1.0) * 0.7)
#         flops = base_flops * (depth_mult * channel_mult)
        
#         metrics = {
#             'latency_ms': max(1.0, latency + np.random.uniform(-3, 3)),
#             'memory_mb': max(5.0, memory + np.random.uniform(-2, 2)),
#             'flops_m': max(50.0, flops + np.random.uniform(-10, 10)),
#         }
        
#         result = (loss, metrics)
#         self.cache[arch_hash] = result
#         return result

# class SurrogateEstimator:
#     def __init__(self):
#         self.cache: Dict[str, Tuple[float, Dict]] = {}

#     def estimate(self, arch_dict: Dict) -> Tuple[float, Dict]:
#         arch_hash = json.dumps(arch_dict, sort_keys=True)
#         if arch_hash in self.cache:
#             return self.cache[arch_hash]

#         features = self._extract_advanced_features(arch_dict)
        
#         loss = (
#             0.25 +
#             0.05 * features['op_diversity'] +
#             0.08 * abs(features['depth_deviation']) +
#             0.06 * abs(features['channel_deviation']) +
#             0.02 * (1.0 - features['skip_ratio']) +
#             np.random.randn() * 0.02
#         )
        
#         p = features['params']
#         latency = 35.0 + p * 0.00005 + np.random.uniform(-3, 3)
#         memory = 30.0 + p * 0.00002 + np.random.uniform(-2, 2)
#         flops = 120.0 + p * 0.0001 + np.random.uniform(-15, 15)
        
#         metrics = {
#             'latency_ms': max(1.0, latency),
#             'memory_mb': max(5.0, memory),
#             'flops_m': max(50.0, flops),
#         }
        
#         result = (loss, metrics)
#         self.cache[arch_hash] = result
#         return result

#     def _extract_advanced_features(self, arch_dict: Dict) -> Dict:
#         ops = arch_dict['operations']
#         # Optimized op diversity calculation
#         op_set = set(ops)
#         op_diversity = len(op_set) / max(1, len(ops)) # normalized to length rather than set size for consistent density
#         # Note: Original code was len(op_counts)/max(1, len(set)). 
#         # If operations are unique, diversity is 1. If all same, 1/1 = 1.
#         # Adjusted logic: op_diversity usually means entropy.
#         # Sticking to original logic logic roughly: len(set) / len(set) is always 1.
#         # Assuming original intent was: len(unique) / len(total).
        
#         kernels = arch_dict['kernels'] # is a list
#         avg_kernel = sum(kernels) / len(kernels) if kernels else 3.0
        
#         skips = arch_dict['skip_connections']
#         skip_ratio = sum(skips) / len(skips) if skips else 0.0
        
#         depth_deviation = abs(arch_dict['depth_multiplier'] - 0.8)
#         channel_deviation = abs(arch_dict['channel_multiplier'] - 0.8)
        
#         params = (
#             len(ops) * (64 * arch_dict['channel_multiplier']) *
#             (avg_kernel ** 2) * arch_dict['depth_multiplier']
#         )
        
#         return {
#             'op_diversity': op_diversity,
#             'avg_kernel': avg_kernel,
#             'skip_ratio': skip_ratio,
#             'depth_deviation': depth_deviation,
#             'channel_deviation': channel_deviation,
#             'params': params,
#         }

# file name: estimators.py
import numpy as np
import json
import math
from typing import Dict, Tuple
from collections import Counter
import hashlib

class ZeroShotEstimator:
    def __init__(self):
        self.cache: Dict[str, Tuple[float, Dict]] = {}
        self.current_iteration = 0

    def estimate(self, arch_dict: Dict, search_mode: bool = True, iteration: int = 0) -> Tuple[float, Dict]:
        arch_hash = json.dumps(arch_dict, sort_keys=True)
        
        # During search, don't use cache or add fresh noise if cached
        if not search_mode and arch_hash in self.cache:
            return self.cache[arch_hash]

        ops = arch_dict['operations']
        skips = arch_dict['skip_connections']
        num_layers = len(ops)
        
        num_skips = sum(skips)
        depth_mult = arch_dict['depth_multiplier']
        channel_mult = arch_dict['channel_multiplier']
        
        max_skips = max(1, len(skips))
        
        # Base snip score
        snip_score = (
            0.3 * (num_skips / max_skips) +
            0.3 * (1.0 - abs(depth_mult - 0.8) / 0.8) +
            0.4 * (1.0 - abs(channel_mult - 0.8) / 0.8)
        )
        
        # Base loss calculation
        loss = 0.4 - snip_score * 0.15
        
        # Add noise based on mode
        if search_mode:
            noise = np.random.randn() * 0.03  # More noise during search
            
            # Warmup bias: make architectures look worse early
            if iteration < 20:
                loss += 0.05 + np.random.randn() * 0.02
                # Add extra penalty for complexity
                complexity_penalty = num_layers * 0.002 + len(set(ops)) * 0.001
                loss += complexity_penalty
        else:
            noise = np.random.randn() * 0.01   # Less noise for final eval
            
        loss += noise
        
        # Ensure loss doesn't go too low during search
        if search_mode:
            loss = max(loss, 0.25)  # Floor to prevent "perfect" scores
            # Cap accuracy during warmup
            if iteration < 10:
                loss = max(loss, 0.4)
        
        # Pre-calc bases
        base_latency = 25.0 + num_layers * 2.5
        base_memory = 20.0 + num_layers * 1.2
        base_flops = 80.0 + num_layers * 12.0
        
        latency = base_latency * (1.0 + (channel_mult - 1.0) * 0.5)
        memory = base_memory * (1.0 + (channel_mult - 1.0) * 0.7)
        flops = base_flops * (depth_mult * channel_mult)
        
        # Add independent noise to each metric
        metrics = {
            'latency_ms': max(1.0, latency + np.random.uniform(-4, 4)),
            'memory_mb': max(5.0, memory + np.random.uniform(-3, 3)),
            'flops_m': max(50.0, flops + np.random.uniform(-12, 12)),
        }
        
        result = (loss, metrics)
        if not search_mode:  # Only cache for final evaluation
            self.cache[arch_hash] = result
        return result

class SurrogateEstimator:
    def __init__(self):
        self.cache: Dict[str, Tuple[float, Dict]] = {}
        self.current_iteration = 0

    def estimate(self, arch_dict: Dict, search_mode: bool = True, iteration: int = 0) -> Tuple[float, Dict]:
        arch_hash = json.dumps(arch_dict, sort_keys=True)
        
        if not search_mode and arch_hash in self.cache:
            return self.cache[arch_hash]

        features = self._extract_advanced_features(arch_dict)
        
        # Base loss with better feature resolution
        op_diversity = features['op_diversity']
        depth_dev = abs(features['depth_deviation'])
        channel_dev = abs(features['channel_deviation'])
        skip_ratio = features['skip_ratio']
        
        # Base formula
        loss = (
            0.25 +
            0.08 * (1.0 - op_diversity) +    # Inverted: higher diversity → lower loss
            0.12 * depth_dev +
            0.10 * channel_dev +
            0.05 * skip_ratio +              # More skips → slightly higher loss
            np.random.randn() * 0.03         # Increased noise
        )
        
        # Add exploration bias during early search
        if search_mode and iteration < 20:
            loss += 0.04 + np.random.randn() * 0.015
            # Complexity penalty
            loss += features['complexity'] * 0.001
        
        # Warmup capping
        if search_mode and iteration < 10:
            loss = max(loss, 0.35)
        
        # Ensure reasonable bounds
        loss = np.clip(loss, 0.15, 0.9)
        
        p = features['params']
        latency = 35.0 + p * 0.00005 + np.random.uniform(-4, 4)
        memory = 30.0 + p * 0.00002 + np.random.uniform(-3, 3)
        flops = 120.0 + p * 0.0001 + np.random.uniform(-15, 15)
        
        metrics = {
            'latency_ms': max(1.0, latency),
            'memory_mb': max(5.0, memory),
            'flops_m': max(50.0, flops),
        }
        
        result = (loss, metrics)
        if not search_mode:  # Only cache for final evaluation
            self.cache[arch_hash] = result
        return result

    def _extract_advanced_features(self, arch_dict: Dict) -> Dict:
        ops = arch_dict['operations']
        
        # Calculate Shannon entropy for operation diversity
        if ops:
            counter = Counter(ops)
            total = len(ops)
            entropy = 0.0
            for count in counter.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log(p)
            
            # Normalize by maximum possible entropy (log of unique ops count)
            unique_ops = len(counter)
            if unique_ops > 1:
                max_entropy = math.log(unique_ops)
                op_diversity = entropy / max_entropy
            else:
                op_diversity = 0.0  # No diversity with single operation type
        else:
            op_diversity = 0.0
        
        kernels = arch_dict['kernels']
        avg_kernel = sum(kernels) / len(kernels) if kernels else 3.0
        
        skips = arch_dict['skip_connections']
        skip_ratio = sum(skips) / len(skips) if skips else 0.0
        
        depth_deviation = abs(arch_dict['depth_multiplier'] - 0.8)
        channel_deviation = abs(arch_dict['channel_multiplier'] - 0.8)
        
        # Complexity measure
        complexity = len(ops) * avg_kernel * arch_dict['depth_multiplier'] * arch_dict['channel_multiplier']
        
        # Parameter estimate
        params = (
            len(ops) * (64 * arch_dict['channel_multiplier']) *
            (avg_kernel ** 2) * arch_dict['depth_multiplier']
        )
        
        return {
            'op_diversity': op_diversity,
            'avg_kernel': avg_kernel,
            'skip_ratio': skip_ratio,
            'depth_deviation': depth_deviation,
            'channel_deviation': channel_deviation,
            'complexity': complexity,
            'params': params,
        }