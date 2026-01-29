# file name: cache.py
from typing import Dict, Optional, Tuple
import numpy as np

class EvaluationCache:
    def __init__(self, max_size: int = 10000, use_cache: bool = True, warmup_iters: int = 10):
        self.cache: Dict[str, Tuple[float, Dict]] = {}
        self.access_count: Dict[str, int] = {}
        self.max_size = max_size
        self.use_cache = use_cache
        self.noise_sigma = 0.01  # Noise added to cached results during search
        self.warmup_iters = warmup_iters

    def get(self, arch_hash: str, add_noise: bool = False, noise_sigma: float = None, iteration: int = 0) -> Optional[Tuple[float, Dict]]:
        if not self.use_cache or arch_hash not in self.cache or iteration < self.warmup_iters:
            return None
        
        self.access_count[arch_hash] += 1
        loss, metrics, stored_iteration = self.cache[arch_hash]
        
        # Track evaluation age - old evaluations are less trusted
        age = iteration - stored_iteration
        current_noise_sigma = noise_sigma if noise_sigma is not None else self.noise_sigma
        if age > 50:  # Old evaluations get more noise
            current_noise_sigma *= 1.2
        
        # Add fresh noise if requested (for search mode)
        if add_noise:
            # Add noise to loss
            loss = loss + np.random.randn() * current_noise_sigma
            # Add smaller noise to metrics
            for k in metrics:
                if isinstance(metrics[k], (int, float)):
                    metrics[k] = metrics[k] + np.random.randn() * (current_noise_sigma * 5)
        
        return (loss, metrics)

    def put(self, arch_hash: str, result: Tuple[float, Dict], iteration: int = 0) -> None:
        if not self.use_cache or iteration < self.warmup_iters:
            return
        if len(self.cache) >= self.max_size:
            lru_key = min(self.access_count, key=self.access_count.get)
            del self.cache[lru_key]
            del self.access_count[lru_key]
        self.cache[arch_hash] = (result[0], result[1], iteration)
        self.access_count[arch_hash] = 1

    def clear(self) -> None:
        self.cache.clear()
        self.access_count.clear()
        
    def set_mode(self, use_cache: bool) -> None:
        """Enable/disable caching during different phases"""
        self.use_cache = use_cache
        
    def set_noise_level(self, sigma: float) -> None:
        """Set noise level for cached results during search"""
        self.noise_sigma = sigma