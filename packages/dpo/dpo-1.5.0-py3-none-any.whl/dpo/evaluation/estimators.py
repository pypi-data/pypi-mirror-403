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
        else:
            noise = 0.0  # No noise during reporting
            
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
        """Enhanced estimation with architecture-aware scoring."""
        arch_hash = json.dumps(arch_dict, sort_keys=True)
        
        # During search, don't use cache or add fresh noise if cached
        if not search_mode and arch_hash in self.cache:
            return self.cache[arch_hash]

        ops = arch_dict['operations']
        kernels = arch_dict['kernels']
        skips = arch_dict['skip_connections']
        num_layers = len(ops)
        
        # Enhanced architecture scoring
        op_counts = {}
        for op in ops:
            op_counts[op] = op_counts.get(op, 0) + 1
        
        # Diversity score (Shannon entropy)
        if ops:
            total = len(ops)
            entropy = 0.0
            for count in op_counts.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log(p)
            max_entropy = math.log(len(op_counts)) if op_counts else 1.0
            diversity_score = entropy / max_entropy if max_entropy > 0 else 0.0
        else:
            diversity_score = 0.0
        
        # Balance score (mix of operation types)
        conv_ops = sum(1 for op in ops if 'conv' in op)
        pool_ops = sum(1 for op in ops if 'pool' in op)
        other_ops = num_layers - conv_ops - pool_ops
        
        balance_score = 1.0 - abs(conv_ops/num_layers - 0.5) - abs(pool_ops/num_layers - 0.2)
        
        # Skip connection efficiency
        skip_efficiency = sum(skips) / len(skips) if skips else 0.0
        optimal_skips = min(0.3, skip_efficiency) / 0.3  # 30% skips is optimal
        
        # Enhanced loss calculation with architecture intelligence
        base_loss = 0.4
        
        # Architecture quality bonuses
        arch_bonus = (
            0.1 * diversity_score +      # Diversity is good
            0.08 * balance_score +       # Balanced ops is good
            0.05 * optimal_skips -       # Optimal skips is good
            0.03 * (num_layers > 20) -   # Too many layers is bad
            0.02 * (num_layers < 8)      # Too few layers is bad
        )
        
        loss = base_loss - arch_bonus
        
        # Add noise based on mode
        if search_mode:
            noise = np.random.randn() * 0.025  # Controlled noise
            loss += noise
            
            # Warmup bias
            if iteration < 25:  # Extended warmup
                # Make complex architectures look worse early
                complexity_penalty = (num_layers * 0.0015 + 
                                    len(set(ops)) * 0.0008 +
                                    np.mean(kernels) * 0.0005)
                loss += complexity_penalty
                
                # Floor to prevent premature convergence
                loss = max(loss, 0.35)
        else:
            noise = 0.0  # No noise during reporting
        
        # Bounds checking
        loss = np.clip(loss, 0.1, 0.9)
        
        # Enhanced cost estimation
        base_latency = 20.0 + num_layers * 2.2
        base_memory = 15.0 + num_layers * 1.0
        base_flops = 70.0 + num_layers * 10.0
        
        # Operation-specific costs
        op_cost_multiplier = 1.0
        for op in ops:
            if '5x5' in op:
                op_cost_multiplier *= 1.3
            elif 'dw_conv' in op:
                op_cost_multiplier *= 0.8
            elif 'sep_conv' in op:
                op_cost_multiplier *= 0.9
        
        latency = base_latency * op_cost_multiplier * (1.0 + (arch_dict['channel_multiplier'] - 1.0) * 0.4)
        memory = base_memory * op_cost_multiplier * (1.0 + (arch_dict['channel_multiplier'] - 1.0) * 0.6)
        flops = base_flops * op_cost_multiplier * (arch_dict['depth_multiplier'] * arch_dict['channel_multiplier'])
        
        # Add correlated noise (real systems have correlated metrics)
        system_noise = np.random.randn() * 0.1
        metrics = {
            'latency_ms': max(1.0, latency + system_noise * 2 + np.random.uniform(-3, 3)),
            'memory_mb': max(5.0, memory + system_noise * 1.5 + np.random.uniform(-2, 2)),
            'flops_m': max(50.0, flops + system_noise * 10 + np.random.uniform(-10, 10)),
            'accuracy': 1.0 - loss,  # Explicit accuracy estimate
        }
        
        result = (loss, metrics)
        if not search_mode:
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