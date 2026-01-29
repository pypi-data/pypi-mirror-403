# file name: ensemble.py
import numpy as np
import json
import random
from typing import Dict, List, Tuple
from .cache import EvaluationCache
from .estimators import ZeroShotEstimator, SurrogateEstimator

class EnsembleEstimator:
    def __init__(self, strategies: List[str] = None, use_cache: bool = False):
        self.strategies = strategies or ['zero_shot', 'surrogate']
        self.cache = EvaluationCache(use_cache=use_cache)
        self.estimators = {}
        
        # Initialize estimators
        for strategy in self.strategies:
            if strategy == 'zero_shot':
                self.estimators[strategy] = ZeroShotEstimator()
            elif strategy == 'surrogate':
                self.estimators[strategy] = SurrogateEstimator()
        
        self._common_keys = ['latency_ms', 'memory_mb', 'flops_m']
        
        # Track iteration for warmup clamping
        self.current_iteration = 0
        self.search_noise_sigma = 0.015  # Initial noise level

    def estimate(self, arch_dict: Dict, use_cache: bool = True, 
                 search_mode: bool = True, iteration: int = 0, 
                 max_iterations: int = 200, stagnation_detected: bool = False) -> Tuple[float, Dict]:
        arch_hash = json.dumps(arch_dict, sort_keys=True)
        
        # Store current iteration for estimators
        self.current_iteration = iteration
        for estimator in self.estimators.values():
            if hasattr(estimator, 'current_iteration'):
                estimator.current_iteration = iteration
        
        if search_mode:
            # During search: use single random estimator with controlled noise
            estimator_name = random.choice(list(self.estimators.keys()))
            estimator = self.estimators[estimator_name]
            
            # Try cache first WITHOUT noise (cache stores true values)
            if use_cache:
                cached = self.cache.get(arch_hash, add_noise=False, iteration=iteration)
                # A. Cache ≠ truth - occasionally re-sample to avoid false plateaus
                if cached and random.random() < 0.05:
                    cached = None
                if cached:
                    loss, metrics = cached
                    # Apply controlled stochastic noise to loss/accuracy
                    true_loss = loss
                    true_accuracy = metrics.get('accuracy', 1.0 - min(true_loss, 1.0))
                    
                    # FIX #1: Add controlled noise to observed accuracy
                    noise_sigma = self._get_noise_sigma(iteration, max_iterations, stagnation_detected)
                    accuracy_noise = np.random.randn() * noise_sigma
                    observed_accuracy = true_accuracy + accuracy_noise
                    
                    # Ensure observed accuracy stays in [0, 1]
                    observed_accuracy = np.clip(observed_accuracy, 0.0, 1.0)
                    observed_loss = 1.0 - observed_accuracy
                    
                    # Return noisy observation
                    noisy_metrics = metrics.copy()
                    noisy_metrics['accuracy'] = observed_accuracy  # Store noisy accuracy
                    return observed_loss, noisy_metrics
            
            # Not cached, compute fresh
            loss, metrics = estimator.estimate(arch_dict, search_mode=True, iteration=iteration)
            
            # B. Estimator disagreement bonus - favor architectures where estimators disagree
            if search_mode and random.random() < 0.1:  # Occasionally check disagreement
                other_estimators = [e for name, e in self.estimators.items() if name != estimator_name]
                if other_estimators:
                    other_loss, _ = other_estimators[0].estimate(arch_dict, search_mode=True, iteration=iteration)
                    if abs(loss - other_loss) > 0.05:  # Significant disagreement
                        loss -= 0.02  # Bonus: lower loss favored
            
            # Get true accuracy
            true_loss = loss
            true_accuracy = metrics.get('accuracy', 1.0 - min(true_loss, 1.0))
            
            # Apply controlled noise
            noise_sigma = self._get_noise_sigma(iteration, max_iterations, stagnation_detected)
            accuracy_noise = np.random.randn() * noise_sigma
            observed_accuracy = true_accuracy + accuracy_noise
            observed_accuracy = np.clip(observed_accuracy, 0.0, 1.0)
            observed_loss = 1.0 - observed_accuracy
            
            # Store true values for logging (not in metrics to avoid cache contamination)
            metrics['_true_accuracy'] = true_accuracy
            metrics['accuracy'] = observed_accuracy  # Store observed accuracy
            
            return observed_loss, metrics
        else:
            # Final evaluation: NO noise, use exact values
            cached = self.cache.get(arch_hash, add_noise=False, iteration=iteration) if use_cache else None
            if cached:
                loss, metrics = cached
                # Ensure no noise in final evaluation
                if '_true_accuracy' in metrics:
                    metrics['accuracy'] = metrics['_true_accuracy']
                    del metrics['_true_accuracy']
                return loss, metrics
                
            # Compute ensemble average without noise
            losses = 0.0
            metrics_acc = {k: 0.0 for k in self._common_keys}
            count = len(self.estimators)
            
            for estimator in self.estimators.values():
                loss, metrics = estimator.estimate(arch_dict, search_mode=False, iteration=iteration)
                losses += loss
                for k in self._common_keys:
                    if k in metrics:
                        metrics_acc[k] += metrics[k]

            avg_loss = losses / count
            avg_metrics = {k: v / count for k, v in metrics_acc.items()}
            
            # Store true accuracy
            avg_metrics['accuracy'] = 1.0 - min(avg_loss, 1.0)
            
            if use_cache:
                self.cache.put(arch_hash, (avg_loss, avg_metrics), iteration=iteration)
            
            return avg_loss, avg_metrics
    
    def _get_noise_sigma(self, iteration: int, max_iterations: int, stagnation_detected: bool = False) -> float:
        """Get noise sigma that decays linearly with iteration, but increases on stagnation."""
        sigma_start = 0.02  # Start with 2% noise
        sigma_end = 0.01   # End with 1% noise (never zero)
        
        if max_iterations <= 0:
            return sigma_start
        
        progress = min(1.0, iteration / max_iterations)
        current_sigma = sigma_start + (sigma_end - sigma_start) * progress
        
        # Make noise non-monotonic: increase on stagnation
        if stagnation_detected:
            current_sigma *= 1.2
        
        return current_sigma
    
    def set_noise_level(self, sigma: float):
        """Set the current noise sigma."""
        self.search_noise_sigma = sigma
        """Switch between search and evaluation modes - only affects caching"""
        # During search, we'll add noise to cached results
        # During evaluation, we'll use exact cached results
        self.cache.set_mode(True)  # Always enable cache
        
    def set_iteration(self, iteration: int):
        """Update iteration for warmup clamping"""
        self.current_iteration = iteration