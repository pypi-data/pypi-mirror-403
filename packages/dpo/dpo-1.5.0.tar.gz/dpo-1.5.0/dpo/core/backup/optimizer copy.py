

# import numpy as np
# import logging
# from typing import Dict, Optional
# from collections import deque

# from .config import DPO_Config
# from .agent import SearchAgent
# from ..architecture.gene import ArchitectureGene
# from ..evaluation.ensemble import EnsembleEstimator
# from ..constraints.handler import AdvancedConstraintHandler
# from ..utils.logger import get_logger

# class DPO_NAS:
#     def __init__(self,
#                  config: DPO_Config,
#                  estimator: Optional[EnsembleEstimator] = None,
#                  constraint_handler: Optional[AdvancedConstraintHandler] = None,
#                  logger: Optional[logging.Logger] = None):
#         self.config = config
#         self.estimator = estimator or EnsembleEstimator()
#         self.constraint_handler = constraint_handler or AdvancedConstraintHandler(config)
#         self.logger = logger or get_logger('DPO-NAS', self.config.verbose)
#         self.islands = [[] for _ in range(config.num_islands if config.island_model else 1)]
#         self.best_agent: Optional[SearchAgent] = None
#         self.best_fitness: float = float('inf')
#         self.best_per_island = [None] * len(self.islands)
#         self.history = {
#             'iterations': [],
#             'best_fitness': [],
#             'avg_fitness': [],
#             'worst_fitness': [],
#             'improvement_rate': [],
#             'best_architecture': None,
#         }
#         self.improvement_tracker = deque(maxlen=30)
        
#         # Pre-calculate bounds for enforcement
#         self._ops_len = len(ArchitectureGene.OPERATIONS) - 0.01
#         self._kers_len = len(ArchitectureGene.KERNELS) - 0.01

#     def initialize_population(self) -> None:
#         agents_per_island = max(1, self.config.population_size // len(self.islands))
#         self.logger.info(f"Initializing population: {self.config.population_size} agents")
        
#         for island_idx, island in enumerate(self.islands):
#             for _ in range(agents_per_island):
#                 gene = ArchitectureGene()
#                 # Create agent
#                 agent = SearchAgent(gene=gene, island_id=island_idx)
#                 # Evaluate
#                 self._evaluate_agent(agent, iteration=0)
#                 island.append(agent)
                
#                 # Update bests
#                 if agent.fitness < self.best_fitness:
#                     self.best_fitness = agent.fitness
#                     self.best_agent = agent
                
#                 if self.best_per_island[island_idx] is None or agent.fitness < self.best_per_island[island_idx].fitness:
#                     self.best_per_island[island_idx] = agent

#     def _evaluate_agent(self, agent: SearchAgent, iteration: int) -> None:
#         arch_dict = agent.gene.to_architecture_dict()
#         loss, metrics = self.estimator.estimate(arch_dict)
#         penalty = self.constraint_handler.compute_adaptive_penalty(metrics, iteration, self.config.max_iterations)
        
#         # Fast arithmetic
#         lat_norm = metrics['latency_ms'] / self.config.latency_constraint
#         mem_norm = metrics['memory_mb'] / self.config.memory_constraint
#         flop_norm = metrics['flops_m'] / self.config.flops_constraint
        
#         agent.fitness = (
#             self.config.w_loss * loss +
#             self.config.w_latency * lat_norm +
#             self.config.w_memory * mem_norm +
#             self.config.w_flops * flop_norm +
#             penalty
#         )
#         agent.metrics = metrics

#     def _get_adaptive_parameters(self, iteration: int) -> Dict[str, float]:
#         t = iteration / max(1, self.config.max_iterations)
        
#         # Vectorized-style scalar operations
#         decay = (1 - t) ** self.config.decay_power
#         alpha = self.config.alpha_0 * decay
#         beta = self.config.beta_0 + 0.5 * t
#         gamma = self.config.gamma_0 * (1 - 0.5 * t)
#         delta = self.config.delta_0 * (1 - 0.3 * t)
        
#         if self.config.adaptive_alpha and len(self.improvement_tracker) > 10:
#             # sum / len is faster than np.mean for deque
#             it = self.improvement_tracker
#             recent_avg = sum(list(it)[-10:]) / 10.0
#             alpha *= 1.2 if recent_avg < 0.001 else 0.9
            
#         return {
#             'alpha': float(np.clip(alpha, 0.01, 0.3)),
#             'beta': float(np.clip(beta, 0.8, 1.5)),
#             'gamma': float(np.clip(gamma, 0.5, 1.5)),
#             'delta': float(np.clip(delta, 0.05, 0.4)),
#         }

#     def _clip_gene_array(self, gene_arr: np.ndarray, num_layers: int, num_cells: int) -> None:
#         """Helper to enforce bounds in-place on numpy array"""
#         # Operations
#         np.clip(gene_arr[:num_layers], 0, self._ops_len, out=gene_arr[:num_layers])
#         # Kernels
#         np.clip(gene_arr[num_layers:2*num_layers], 0, self._kers_len, out=gene_arr[num_layers:2*num_layers])
#         # Skip connections
#         np.clip(gene_arr[2*num_layers:2*num_layers+num_cells], 0, 1, out=gene_arr[2*num_layers:2*num_layers+num_cells])
#         # Multipliers
#         np.clip(gene_arr[-2:], 0.3, 2.0, out=gene_arr[-2:])

#     def _dpo_step(self, agent: SearchAgent, params: Dict, iteration: int) -> SearchAgent:
#         # OPTIMIZED: Perform vector math on arrays without creating intermediate ArchitectureGene objects
#         # This reduces object overhead significantly
        
#         current_vec = agent.gene.gene
        
#         # 1. Debt Gene Logic (Agent + Perturbation)
#         perturbation = np.random.randn(agent.gene.D) * params['alpha']
#         debt_vec = current_vec + perturbation
#         self._clip_gene_array(debt_vec, agent.gene.num_layers, agent.gene.num_cells)
        
#         # Debt Vector
#         debt_delta = debt_vec - current_vec
        
#         # 2. Repay Gene Logic (Agent - Beta * Debt)
#         repay_vec = current_vec - (params['beta'] * debt_delta)
#         self._clip_gene_array(repay_vec, agent.gene.num_layers, agent.gene.num_cells)
        
#         # 3. Double Gene Logic (Repay - Gamma * Debt)
#         double_vec = repay_vec - (params['gamma'] * debt_delta)
#         self._clip_gene_array(double_vec, agent.gene.num_layers, agent.gene.num_cells)
        
#         # 4. Smart Gene Logic (Double + Delta * (GlobalBest - Current))
#         best_global = self.best_agent or agent
#         smart_vec = double_vec + params['delta'] * (best_global.gene.gene - current_vec)
#         self._clip_gene_array(smart_vec, agent.gene.num_layers, agent.gene.num_cells)
        
#         # Create Final Object
#         smart_gene = ArchitectureGene(agent.gene.num_layers, agent.gene.num_cells)
#         smart_gene.gene = smart_vec
        
#         candidate = SearchAgent(gene=smart_gene, island_id=agent.island_id)
#         self._evaluate_agent(candidate, iteration)
        
#         if candidate.fitness < agent.fitness:
#             candidate.improvements = agent.improvements + 1
#             return candidate
            
#         agent.age += 1
#         return agent

#     def _migrate_between_islands(self) -> None:
#         if not self.config.island_model or len(self.islands) < 2:
#             return
            
#         num_migrate = max(1, self.config.population_size // 20)
        
#         for island_idx in range(len(self.islands)):
#             # Find best neighbors
#             best_neighbors = [
#                 self.best_per_island[o] 
#                 for o in range(len(self.islands)) 
#                 if o != island_idx and self.best_per_island[o]
#             ]
            
#             if best_neighbors:
#                 best_neighbor = min(best_neighbors, key=lambda a: a.fitness)
#                 # Sort current island
#                 self.islands[island_idx].sort(key=lambda a: a.fitness, reverse=True) # Worst first
                
#                 # Replace worst
#                 for i in range(num_migrate):
#                     if i < len(self.islands[island_idx]):
#                         # Deep copy gene
#                         new_gene = best_neighbor.gene.copy()
#                         new_agent = SearchAgent(gene=new_gene, island_id=island_idx)
#                         self._evaluate_agent(new_agent, iteration=0)
#                         self.islands[island_idx][i] = new_agent

#     def _inject_diversity(self) -> None:
#         for island in self.islands:
#             n = len(island)
#             elite_count = max(1, int(n * self.config.elite_ratio))
#             island.sort(key=lambda a: a.fitness)
#             elite = island[:elite_count]
            
#             # Replace non-elites
#             for i in range(elite_count, n):
#                 if elite:
#                     parent = elite[np.random.randint(0, len(elite))]
#                     mutant_gene = parent.gene.mutate()
#                     new_agent = SearchAgent(gene=mutant_gene, island_id=parent.island_id)
#                     self._evaluate_agent(new_agent, iteration=0)
#                     island[i] = new_agent

#     def optimize(self) -> Dict:
#         self.logger.info("=" * 70)
#         self.logger.info("Starting DPO-NAS Optimization")
#         self.logger.info(f"Strategy: {self.config.eval_strategy}")
#         self.logger.info(f"Population: {self.config.population_size} | Islands: {len(self.islands)}")
#         self.logger.info("=" * 70)
        
#         self.initialize_population()
        
#         for iteration in range(self.config.max_iterations):
#             params = self._get_adaptive_parameters(iteration)
            
#             for island in self.islands:
#                 for idx, agent in enumerate(island):
#                     new_agent = self._dpo_step(agent, params, iteration)
#                     island[idx] = new_agent
                    
#                     if new_agent.fitness < self.best_fitness:
#                         self.best_fitness = new_agent.fitness
#                         self.best_agent = new_agent
#                         self.logger.info(f"[Iter {iteration}] New best: {self.best_fitness:.4f}")

#             # Periodic tasks
#             if (iteration + 1) % self.config.migration_freq == 0 and self.config.island_model:
#                 self._migrate_between_islands()
                
#             if (iteration + 1) % self.config.diversity_inject_freq == 0:
#                 self._inject_diversity()

#             # Tracking
#             # Optim: generator expression for fitness sum/stats
#             all_fitness = np.array([a.fitness for island in self.islands for a in island])
            
#             improvement = (self.history['best_fitness'][-1] - self.best_fitness) if self.history['best_fitness'] else 0.0
#             self.improvement_tracker.append(improvement)
            
#             self.history['iterations'].append(iteration)
#             self.history['best_fitness'].append(self.best_fitness)
#             self.history['avg_fitness'].append(float(np.mean(all_fitness)))
#             self.history['worst_fitness'].append(float(np.max(all_fitness)))
#             self.history['improvement_rate'].append(float(improvement))
            
#             if iteration % 10 == 0:
#                 self.logger.info(f"[Iter {iteration:3d}] Best: {self.best_fitness:.4f} | Avg: {np.mean(all_fitness):.4f} | Improvement: {improvement:.6f}")

#         if self.best_agent:
#             self.history['best_architecture'] = self.best_agent.gene.to_architecture_dict()

#         self.logger.info("=" * 70)
#         self.logger.info("Optimization Complete!")
#         self.logger.info(f"Best Fitness: {self.best_fitness:.4f}")
#         self.logger.info("=" * 70)

#         return {
#             'best_fitness': self.best_fitness,
#             'best_architecture': self.history.get('best_architecture'),
#             'best_metrics': getattr(self.best_agent, 'metrics', {}),
#             'history': self.history,
#             'config': {
#                 'population_size': self.config.population_size,
#                 'islands': len(self.islands),
#                 'eval_strategy': self.config.eval_strategy,
#                 'max_iterations': len(self.history['iterations']),
#             }
#         }

# file name: optimizer.py (updated with fixes for SearchAgent initialization)
import numpy as np
import logging
import math
from typing import Dict, List, Optional, Tuple
from collections import deque

from .config import DPO_Config
from .agent import SearchAgent
from ..architecture.gene import ArchitectureGene
from ..evaluation.ensemble import EnsembleEstimator
from ..constraints.handler import AdvancedConstraintHandler
from ..utils.logger import get_logger

class DPO_NAS:
    def __init__(self,
                 config: DPO_Config,
                 estimator: Optional[EnsembleEstimator] = None,
                 constraint_handler: Optional[AdvancedConstraintHandler] = None,
                 logger: Optional[logging.Logger] = None):
        self.config = config
        
        # Validate configuration
        config.validate()
        if config.w_loss > 0:
            if logger:
                logger.warning("w_loss > 0: Using legacy loss-based fitness. For accuracy-aware mode, set w_loss = 0.0")
        
        self.estimator = estimator or EnsembleEstimator()
        self.constraint_handler = constraint_handler or AdvancedConstraintHandler(config)
        self.logger = logger or get_logger('DPO-NAS', self.config.verbose)
        self.islands = [[] for _ in range(config.num_islands if config.island_model else 1)]
        self.best_agent: Optional[SearchAgent] = None
        self.best_fitness: float = float('inf')
        self.best_accuracy: float = 0.0  # Track best accuracy separately
        self.best_per_island = [None] * len(self.islands)
        
        # Pareto archive for optional Pareto-assisted mode
        self.pareto_archive: List[SearchAgent] = []
        
        # Temperature for probabilistic acceptance
        self.temperature: float = config.temperature_start
        
        # History tracking with accuracy focus
        self.history = {
            'iterations': [],
            'best_fitness': [],
            'best_accuracy': [],  # Track accuracy progression
            'avg_fitness': [],
            'worst_fitness': [],
            'improvement_rate': [],
            'temperature': [],  # Track temperature decay
            'debt_norms': [],  # Track average debt magnitude
            'diversity_scores': [],  # Track population diversity
            'acceptance_rates': [],  # Track acceptance probabilities
            'best_architecture': None,
            'auc_10': 0.0,
            'auc_25': 0.0,
            'auc_50': 0.0,
            'time_to_95': 0,
            'time_to_99': 0,
        }
        
        # Improvement tracking with accuracy awareness
        self.improvement_tracker = deque(maxlen=30)
        self.accuracy_improvement_tracker = deque(maxlen=30)
        
        # Population statistics for normalization
        self.population_stats = {
            'latency_range': (0.0, 1.0),
            'flops_range': (0.0, 1.0),
            'memory_range': (0.0, 1.0),
            'fitness_std': 1.0,
        }
        
        # Acceptance statistics
        self.acceptance_stats = {
            'total_candidates': 0,
            'accepted_better': 0,
            'accepted_worse': 0,
            'rejected': 0
        }
        
        # Pre-calculate bounds for enforcement
        self._ops_len = len(ArchitectureGene.OPERATIONS) - 0.01
        self._kers_len = len(ArchitectureGene.KERNELS) - 0.01
        
        # Adaptive acceptance scaling
        self._recent_fitness_deltas = deque(maxlen=50)

    def initialize_population(self) -> None:
        agents_per_island = max(1, self.config.population_size // len(self.islands))
        self.logger.info(f"Initializing population: {self.config.population_size} agents")
        
        for island_idx, island in enumerate(self.islands):
            for _ in range(agents_per_island):
                gene = ArchitectureGene()
                # Create agent with persistent debt vector
                agent = SearchAgent(
                    gene=gene, 
                    island_id=island_idx,
                    debt_vector=np.zeros_like(gene.gene)
                )
                # Evaluate with accuracy-aware fitness - add warmup bias
                self._evaluate_agent(agent, iteration=0, is_initial=True)
                island.append(agent)
                
                # Update bests (accuracy tracked separately)
                if agent.fitness < self.best_fitness:
                    self.best_fitness = agent.fitness
                    self.best_agent = agent
                
                if agent.accuracy > self.best_accuracy:
                    self.best_accuracy = agent.accuracy
                
                if self.best_per_island[island_idx] is None or agent.fitness < self.best_per_island[island_idx].fitness:
                    self.best_per_island[island_idx] = agent
                
                # Initialize Pareto archive if enabled
                if self.config.fitness_mode == 'pareto_assisted':
                    self._update_pareto_archive(agent)

    def _evaluate_agent(self, agent: SearchAgent, iteration: int, is_initial: bool = False) -> None:
        """Evaluate agent with accuracy-aware fitness calculation."""
        arch_dict = agent.gene.to_architecture_dict()
        
        # Add iteration info for warmup clamping
        arch_dict['iter'] = iteration
        
        # During search, disable caching or add noise to cached results
        # For initial evaluation, also add warmup bias
        use_cache = self.config.cache_evaluations and not is_initial and iteration > 10
        search_mode = True  # Always in search mode during optimization
        
        loss, metrics = self.estimator.estimate(
            arch_dict, 
            use_cache=use_cache,
            search_mode=search_mode,
            iteration=iteration
        )
        
        # Extract accuracy if available, otherwise convert loss to pseudo-accuracy
        accuracy = metrics.get('accuracy', 1.0 - min(loss, 1.0))
        agent.accuracy = accuracy
        
        # Store cost metrics
        agent.cost_metrics = {
            'latency': metrics['latency_ms'],
            'flops': metrics['flops_m'],
            'memory': metrics['memory_mb']
        }
        
        # Dynamic normalization using population statistics
        if not is_initial and iteration > 5:
            lat_norm = self._normalize_cost(metrics['latency_ms'], 'latency')
            flop_norm = self._normalize_cost(metrics['flops_m'], 'flops')
            mem_norm = self._normalize_cost(metrics['memory_mb'], 'memory')
        else:
            # Initial normalization using constraints
            lat_norm = metrics['latency_ms'] / max(self.config.latency_constraint, 1.0)
            flop_norm = metrics['flops_m'] / max(self.config.flops_constraint, 1.0)
            mem_norm = metrics['memory_mb'] / max(self.config.memory_constraint, 1.0)
        
        # Combined cost term
        total_cost = (lat_norm + flop_norm + mem_norm) / 3.0
        
        # Constraint penalty
        penalty = self.constraint_handler.compute_adaptive_penalty(metrics, iteration, self.config.max_iterations)
        
        # FIX 1: Use accuracy-aware fitness by default
        # Only use loss-based fitness if explicitly configured
        if self.config.w_loss > 0:
            # Legacy mode: loss-based fitness (causes flat accuracy)
            loss_component = self.config.w_loss * loss
            cost_component = (
                self.config.w_latency * lat_norm +
                self.config.w_memory * mem_norm +
                self.config.w_flops * flop_norm
            )
            agent.fitness = loss_component + cost_component + penalty
        else:
            # Accuracy-aware fitness (recommended)
            agent.fitness = (
                self.config.w_accuracy * (1.0 - accuracy) +  # Lower is better for fitness
                self.config.w_cost * total_cost +
                self.config.w_penalty * penalty
            )
        
        agent.metrics = metrics
        agent.metrics['accuracy'] = accuracy  # Ensure accuracy is in metrics
        
        # Pareto rank if enabled
        if self.config.fitness_mode == 'pareto_assisted':
            self._compute_pareto_rank(agent)
            # Blend Pareto rank into fitness (normalized)
            if agent.pareto_rank > 0:
                normalized_rank = agent.pareto_rank / max(1, len(self.pareto_archive))
                agent.fitness += self.config.pareto_weight * normalized_rank

    def _normalize_cost(self, value: float, cost_type: str) -> float:
        """Normalize cost using population statistics."""
        min_val, max_val = self.population_stats.get(f'{cost_type}_range', (0.0, 1.0))
        if max_val - min_val > 1e-6:
            return (value - min_val) / (max_val - min_val)
        return value / max(1.0, max_val)

    def _update_population_stats(self) -> None:
        """Update population statistics for dynamic normalization."""
        all_agents = [a for island in self.islands for a in island]
        
        if len(all_agents) > 5:  # Wait until we have enough samples
            latencies = [a.cost_metrics['latency'] for a in all_agents]
            flops_list = [a.cost_metrics['flops'] for a in all_agents]
            memories = [a.cost_metrics['memory'] for a in all_agents]
            fitnesses = [a.fitness for a in all_agents]
            
            self.population_stats['latency_range'] = (min(latencies), max(latencies))
            self.population_stats['flops_range'] = (min(flops_list), max(flops_list))
            self.population_stats['memory_range'] = (min(memories), max(memories))
            self.population_stats['fitness_std'] = np.std(fitnesses) + 1e-8

    def _compute_pareto_rank(self, agent: SearchAgent) -> None:
        """Compute Pareto dominance rank for an agent."""
        all_agents = [a for island in self.islands for a in island]
        dominated_count = 0
        
        for other in all_agents:
            if other is agent:
                continue
            if other.is_dominated(agent):
                dominated_count += 1
        
        agent.pareto_rank = dominated_count

    def _update_pareto_archive(self, agent: SearchAgent) -> None:
        """Update Pareto archive with non-dominated solutions."""
        # Remove dominated solutions
        self.pareto_archive = [a for a in self.pareto_archive if not agent.is_dominated(a)]
        
        # Add if not dominated by any in archive
        if not any(a.is_dominated(agent) for a in self.pareto_archive):
            self.pareto_archive.append(agent)
        
        # Limit archive size
        if len(self.pareto_archive) > self.config.pareto_archive_size:
            # Remove solutions with worst combined metrics
            self.pareto_archive.sort(key=lambda a: a.fitness)
            self.pareto_archive = self.pareto_archive[:self.config.pareto_archive_size]

    def _get_adaptive_parameters(self, iteration: int) -> Dict[str, float]:
        """Get DPO parameters with exploration phase control."""
        t = iteration / max(1, self.config.max_iterations)
        
        # FIX: Power-law decay for slower parameter reduction
        decay = (1 - t) ** self.config.decay_power
        
        # Phase-based parameter adjustment
        if t < self.config.exploration_phase_ratio:
            # Early phase: favor debt accumulation and exploration
            alpha = self.config.alpha_0 * 1.2  # Slightly higher exploration
            beta = self.config.beta_0 * 0.8    # Lower repayment
            gamma = self.config.gamma_0 * 0.9  # Lower overshoot
            delta = self.config.delta_0 * 0.8  # Lower global pull
        elif t < self.config.debt_accumulation_phase:
            # Middle phase: balance accumulation and repayment
            alpha = self.config.alpha_0 * decay
            beta = self.config.beta_0 + 0.3 * t
            gamma = self.config.gamma_0 * (1 - 0.3 * t)
            delta = self.config.delta_0 * (1 - 0.2 * t)
        else:
            # Late phase: aggressive repayment and refinement
            alpha = self.config.alpha_0 * decay * 0.7
            beta = self.config.beta_0 + 0.8 * t
            gamma = self.config.gamma_0 * (1 - 0.8 * t)
            delta = self.config.delta_0 * (1 - 0.1 * t)
        
        # Adaptive adjustment based on improvement rate
        if self.config.adaptive_alpha and len(self.improvement_tracker) > 5:
            recent_avg = sum(list(self.improvement_tracker)[-5:]) / 5.0
            if recent_avg < 1e-6:  # Stagnation
                alpha *= 1.3  # Increase exploration
                beta *= 0.9   # Reduce repayment
            elif recent_avg > 0.01:  # Rapid improvement
                alpha *= 0.9  # Reduce noise
                beta *= 1.1   # Increase repayment
        
        return {
            'alpha': float(np.clip(alpha, 0.05, 0.3)),
            'beta': float(np.clip(beta, 0.6, 2.0)),
            'gamma': float(np.clip(gamma, 0.3, 1.8)),
            'delta': float(np.clip(delta, 0.05, 0.5)),
            'debt_memory': float(np.clip(
                self.config.debt_memory_lambda, 
                self.config.min_debt_memory, 
                self.config.max_debt_memory
            )),
        }

    def _clip_gene_array(self, gene_arr: np.ndarray, num_layers: int, num_cells: int) -> None:
        """Helper to enforce bounds in-place on numpy array"""
        # Operations
        np.clip(gene_arr[:num_layers], 0, self._ops_len, out=gene_arr[:num_layers])
        # Kernels
        np.clip(gene_arr[num_layers:2*num_layers], 0, self._kers_len, out=gene_arr[num_layers:2*num_layers])
        # Skip connections
        np.clip(gene_arr[2*num_layers:2*num_layers+num_cells], 0, 1, out=gene_arr[2*num_layers:2*num_layers+num_cells])
        # Multipliers
        np.clip(gene_arr[-2:], 0.3, 2.0, out=gene_arr[-2:])

    def _accept_candidate(self, current: SearchAgent, candidate: SearchAgent) -> bool:
        """Probabilistic acceptance with adaptive temperature schedule."""
        self.acceptance_stats['total_candidates'] += 1
        
        if candidate.fitness < current.fitness:
            self.acceptance_stats['accepted_better'] += 1
            return True
        
        # Allow worse candidates with probability exp(-Δfitness / T)
        delta_fitness = candidate.fitness - current.fitness
        
        # Track delta for adaptive scaling
        self._recent_fitness_deltas.append(delta_fitness)
        
        if delta_fitness > 0 and self.temperature > 0:
            # FIX: Adaptive scaling using population statistics
            if self.config.adaptive_acceptance_scaling and len(self._recent_fitness_deltas) > 10:
                # Scale by recent standard deviation of deltas
                delta_std = np.std(list(self._recent_fitness_deltas)) + 1e-8
                scaled_delta = delta_fitness / delta_std
            else:
                # Fallback to fixed scaling
                scaled_delta = delta_fitness * self.config.acceptance_scaling_factor
            
            # Ensure scaled delta is reasonable
            scaled_delta = min(scaled_delta, 10.0)  # Cap to avoid underflow
            
            probability = math.exp(-scaled_delta / max(self.temperature, 1e-8))
            accept = np.random.random() < probability
            
            if accept:
                self.acceptance_stats['accepted_worse'] += 1
                # Update agent's acceptance rate
                current.acceptance_rate = 0.9 * current.acceptance_rate + 0.1 * probability
            else:
                self.acceptance_stats['rejected'] += 1
                current.acceptance_rate = 0.9 * current.acceptance_rate + 0.1 * 0.0
            
            return accept
        
        self.acceptance_stats['rejected'] += 1
        return False

    def _dpo_step(self, agent: SearchAgent, params: Dict, iteration: int) -> SearchAgent:
        """
        DPO step with persistent debt memory and proper repayment semantics.
        
        Tyrion's Law:
        1. Borrow (accept worse move) → accumulate debt
        2. Repay (find better move) → reduce debt
        3. Double Pay (overshoot) → move beyond repayment
        4. Smart Move → learn from global best
        """
        current_vec = agent.gene.gene
        
        # 1. Debt Gene Logic (Agent + Perturbation)
        perturbation = np.random.randn(agent.gene.D) * params['alpha']
        debt_vec = current_vec + perturbation
        self._clip_gene_array(debt_vec, agent.gene.num_layers, agent.gene.num_cells)
        
        # Compute new debt component
        new_debt_component = debt_vec - current_vec
        
        # Create candidate agent
        smart_gene = ArchitectureGene(agent.gene.num_layers, agent.gene.num_cells)
        smart_gene.gene = debt_vec  # Start with debt vector
        
        candidate = SearchAgent(
            gene=smart_gene, 
            island_id=agent.island_id,
            debt_vector=agent.debt_vector.copy() if agent.debt_vector is not None else None,
            mutation_magnitude=agent.mutation_magnitude,
            acceptance_rate=agent.acceptance_rate
        )
        self._evaluate_agent(candidate, iteration)
        
        # Probabilistic acceptance
        if self._accept_candidate(agent, candidate):
            # Candidate accepted
            if candidate.fitness < agent.fitness:
                # Better move: Tyrion repays debt
                
                # FIX: Accuracy improvement triggers stronger repayment
                accuracy_improved = candidate.accuracy > agent.accuracy + self.config.accuracy_improvement_threshold
                
                # 2. Repay Gene Logic (Agent - Beta * CurrentDebt)
                if candidate.debt_vector is not None and np.linalg.norm(candidate.debt_vector) > 1e-6:
                    # Scale repayment by existing debt
                    debt_magnitude = np.linalg.norm(candidate.debt_vector)
                    effective_beta = params['beta'] * min(1.0, debt_magnitude)
                    
                    # Stronger repayment if accuracy improved
                    if accuracy_improved:
                        effective_beta *= 1.5
                    
                    repay_vec = current_vec - (effective_beta * candidate.debt_vector)
                    self._clip_gene_array(repay_vec, agent.gene.num_layers, agent.gene.num_cells)
                    
                    # 3. Double Gene Logic (Repay - Gamma * CurrentDebt)
                    # Overshoot only when sufficient debt exists
                    if debt_magnitude > 1e-6 and params['gamma'] > 0.1:
                        double_vec = repay_vec - (params['gamma'] * candidate.debt_vector)
                        self._clip_gene_array(double_vec, agent.gene.num_layers, agent.gene.num_cells)
                    else:
                        double_vec = repay_vec.copy()
                    
                    # 4. Smart Gene Logic (Double + Delta * (GlobalBest - Current))
                    best_global = self.best_agent or agent
                    smart_vec = double_vec + params['delta'] * (best_global.gene.gene - current_vec)
                    self._clip_gene_array(smart_vec, agent.gene.num_layers, agent.gene.num_cells)
                    
                    # Update gene and reduce debt
                    candidate.gene.gene = smart_vec
                    repayment_strength = 0.3 + 0.7 * (1.0 - iteration/self.config.max_iterations)
                    if accuracy_improved:
                        repayment_strength = min(1.0, repayment_strength * 2.0)  # Extra repayment for accuracy
                    candidate.debt_vector *= (1.0 - repayment_strength)
                
                candidate.improvements = agent.improvements + 1
                candidate.last_improvement = iteration
                candidate.debt_history.append(float(np.linalg.norm(candidate.debt_vector)))
            else:
                # Worse move accepted: Tyrion accumulates debt
                # FIX: Only accumulate debt when worse move is accepted
                if candidate.debt_vector is not None:
                    # Accumulate debt in the direction of the worse move
                    candidate.update_debt(new_debt_component, params['debt_memory'] * 0.9, accumulate_only=True)
                candidate.debt_history.append(float(np.linalg.norm(candidate.debt_vector)))
            
            # Update mutation magnitude adaptively (smoother updates)
            if self.config.adaptive_mutation:
                if candidate.fitness < agent.fitness:
                    candidate.mutation_magnitude = max(0.05, agent.mutation_magnitude * 0.98)
                else:
                    candidate.mutation_magnitude = min(0.3, agent.mutation_magnitude * 1.02)
            
            return candidate
        
        # Rejected: age the current agent
        agent.age += 1
        if self.config.adaptive_mutation and agent.age % 10 == 0:
            # Smooth mutation magnitude increase
            agent.mutation_magnitude = min(0.3, agent.mutation_magnitude * 1.02)
        
        return agent

    def _compute_diversity_scores(self) -> None:
        """Compute diversity scores for all agents."""
        all_agents = [a for island in self.islands for a in island]
        
        if len(all_agents) < 2:
            return
        
        # Normalize gene vectors
        gene_vectors = np.array([a.gene.gene for a in all_agents])
        gene_norms = np.linalg.norm(gene_vectors, axis=1, keepdims=True)
        gene_norms[gene_norms == 0] = 1.0
        normalized_vectors = gene_vectors / gene_norms
        
        # Compute pairwise distances
        for i, agent in enumerate(all_agents):
            distances = np.linalg.norm(normalized_vectors[i] - normalized_vectors, axis=1)
            agent.diversity_score = np.mean(distances)

    def _migrate_between_islands(self, iteration: int) -> None:
        """Migration with preserved optimizer dynamics."""
        if not self.config.island_model or len(self.islands) < 2:
            return
            
        num_migrate = max(1, self.config.population_size // 20)
        
        for island_idx in range(len(self.islands)):
            # Find best neighbors (preserving their state)
            best_neighbors = [
                self.best_per_island[o] 
                for o in range(len(self.islands)) 
                if o != island_idx and self.best_per_island[o]
            ]
            
            if best_neighbors:
                best_neighbor = min(best_neighbors, key=lambda a: a.fitness)
                
                # Sort current island (worst first)
                self.islands[island_idx].sort(key=lambda a: a.fitness, reverse=True)
                
                # Replace worst agents with migrated copies
                for i in range(num_migrate):
                    if i < len(self.islands[island_idx]):
                        # Deep copy with preserved state
                        new_gene = best_neighbor.gene.copy()
                        
                        # FIX: Inflate debt on migration to create new obligations
                        new_debt = best_neighbor.debt_vector.copy() if best_neighbor.debt_vector is not None else np.zeros_like(new_gene.gene)
                        new_debt *= 1.2  # Inflate debt by 20%
                        
                        new_agent = SearchAgent(
                            gene=new_gene, 
                            island_id=island_idx,
                            debt_vector=new_debt,
                            accuracy=best_neighbor.accuracy,
                            cost_metrics=best_neighbor.cost_metrics.copy(),
                            mutation_magnitude=best_neighbor.mutation_magnitude,
                            acceptance_rate=best_neighbor.acceptance_rate
                        )
                        # Evaluate in new island context
                        self._evaluate_agent(new_agent, iteration)
                        self.islands[island_idx][i] = new_agent

    def _inject_diversity(self, iteration: int) -> None:
        """Real diversity injection using debt direction and orthogonal exploration."""
        for island_idx, island in enumerate(self.islands):
            n = len(island)
            if n < 2:
                continue
            
            # Compute current diversity for this island only
            island_agents = island
            if len(island_agents) < 2:
                continue
                
            # Compute diversity within this island
            gene_vectors = np.array([a.gene.gene for a in island_agents])
            gene_norms = np.linalg.norm(gene_vectors, axis=1, keepdims=True)
            gene_norms[gene_norms == 0] = 1.0
            normalized_vectors = gene_vectors / gene_norms
            
            diversity_scores = []
            for i in range(len(island_agents)):
                distances = np.linalg.norm(normalized_vectors[i] - normalized_vectors, axis=1)
                diversity_scores.append(np.mean(distances))
            
            avg_diversity = np.mean(diversity_scores)
            
            # FIX: Only skip this island if it's diverse, not all islands
            if avg_diversity > self.config.min_diversity_threshold:
                continue  # Skip only this island, not all
            
            elite_count = max(1, int(n * self.config.elite_ratio))
            island.sort(key=lambda a: a.fitness)
            elites = island[:elite_count]
            non_elites = island[elite_count:]
            
            # Inject diversity into non-elites
            for i, agent in enumerate(non_elites):
                # Select diverse parent (not necessarily elite)
                if elites and np.random.random() < 0.7:
                    parent = elites[np.random.randint(0, len(elites))]
                else:
                    parent = island[np.random.randint(0, len(island))]
                
                # Generate orthogonal debt direction
                parent_vec = parent.gene.gene
                orthogonal_noise = np.random.randn(len(parent_vec))
                # Make orthogonal to current direction
                if parent.debt_vector is not None and np.linalg.norm(parent.debt_vector) > 1e-6:
                    debt_dir = parent.debt_vector / np.linalg.norm(parent.debt_vector)
                    orthogonal_noise = orthogonal_noise - np.dot(orthogonal_noise, debt_dir) * debt_dir
                
                # Apply mutation with adaptive magnitude
                mutation_strength = agent.mutation_magnitude * (1.0 + 0.3 * np.random.randn())
                mutant_gene = parent.gene.gene + mutation_strength * orthogonal_noise
                
                # Clip and create new agent
                self._clip_gene_array(mutant_gene, parent.gene.num_layers, parent.gene.num_cells)
                
                new_gene = ArchitectureGene(parent.gene.num_layers, parent.gene.num_cells)
                new_gene.gene = mutant_gene
                
                # Inherit debt with perturbation
                new_debt = parent.debt_vector.copy() if parent.debt_vector is not None else np.zeros_like(mutant_gene)
                new_debt += 0.3 * np.random.randn(*new_debt.shape)
                
                new_agent = SearchAgent(
                    gene=new_gene, 
                    island_id=agent.island_id,
                    debt_vector=new_debt,
                    mutation_magnitude=min(0.3, agent.mutation_magnitude * 1.1),
                    acceptance_rate=agent.acceptance_rate * 0.9
                )
                self._evaluate_agent(new_agent, iteration)
                island[elite_count + i] = new_agent

    def _compute_auc_metrics(self) -> None:
        """Compute AUC metrics for accuracy progression."""
        if not self.history['iterations']:
            return
            
        iterations = self.history['iterations']
        accuracies = self.history['best_accuracy']
        
        # AUC@10: Area under curve for first 10 iterations
        if len(iterations) >= 10:
            idx_10 = min(10, len(iterations))
            self.history['auc_10'] = np.trapz(accuracies[:idx_10], iterations[:idx_10])
        
        # AUC@25
        if len(iterations) >= 25:
            idx_25 = min(25, len(iterations))
            self.history['auc_25'] = np.trapz(accuracies[:idx_25], iterations[:idx_25])
        
        # AUC@50
        if len(iterations) >= 50:
            idx_50 = min(50, len(iterations))
            self.history['auc_50'] = np.trapz(accuracies[:idx_50], iterations[:idx_50])
        
        # Time to 95% and 99% of best accuracy
        if accuracies:
            best_acc = max(accuracies)
            target_95 = best_acc * 0.95
            target_99 = best_acc * 0.99
            
            # Find first iteration where accuracy reaches target
            for i, acc in enumerate(accuracies):
                if acc >= target_95 and self.history['time_to_95'] == 0:
                    self.history['time_to_95'] = i
                if acc >= target_99 and self.history['time_to_99'] == 0:
                    self.history['time_to_99'] = i
                    break

    def optimize(self) -> Dict:
        self.logger.info("=" * 70)
        self.logger.info("Starting DPO-NAS Optimization (Accuracy-Aware)")
        self.logger.info(f"Strategy: {self.config.eval_strategy}")
        self.logger.info(f"Fitness Mode: {self.config.fitness_mode}")
        self.logger.info(f"Accuracy-aware: {self.config.w_loss == 0.0}")
        self.logger.info(f"Population: {self.config.population_size} | Islands: {len(self.islands)}")
        self.logger.info("=" * 70)
        
        # Set estimator to search mode
        if hasattr(self.estimator, 'set_search_mode'):
            self.estimator.set_search_mode(True)
        
        self.initialize_population()
        self.temperature = self.config.temperature_start
        
        for iteration in range(self.config.max_iterations):
            # Update temperature (exponential decay)
            self.temperature = max(
                self.config.temperature_min,
                self.temperature * self.config.temperature_decay
            )
            
            # Update population statistics for normalization
            self._update_population_stats()
            
            # Get adaptive parameters for current phase
            params = self._get_adaptive_parameters(iteration)
            
            # Process each agent in each island
            for island in self.islands:
                for idx, agent in enumerate(island):
                    new_agent = self._dpo_step(agent, params, iteration)
                    island[idx] = new_agent
                    
                    # Update best agents
                    if new_agent.fitness < self.best_fitness:
                        self.best_fitness = new_agent.fitness
                        self.best_agent = new_agent
                        self.logger.info(f"[Iter {iteration}] New best fitness: {self.best_fitness:.4f}")
                    
                    if new_agent.accuracy > self.best_accuracy:
                        self.best_accuracy = new_agent.accuracy
                        self.logger.info(f"[Iter {iteration}] New best accuracy: {self.best_accuracy:.4f}")
            
            # Update island bests
            for island_idx, island in enumerate(self.islands):
                if island:
                    island_best = min(island, key=lambda a: a.fitness)
                    self.best_per_island[island_idx] = island_best
            
            # Periodic operations
            if (iteration + 1) % self.config.migration_freq == 0 and self.config.island_model:
                self._migrate_between_islands(iteration)
                
            if (iteration + 1) % self.config.diversity_inject_freq == 0:
                self._inject_diversity(iteration)
            
            # Update Pareto archive if enabled
            if self.config.fitness_mode == 'pareto_assisted':
                for island in self.islands:
                    for agent in island:
                        self._update_pareto_archive(agent)
            
            # Tracking and statistics
            all_agents = [a for island in self.islands for a in island]
            all_fitness = np.array([a.fitness for a in all_agents])
            
            # Track improvements
            if self.history['best_fitness']:
                improvement = self.history['best_fitness'][-1] - self.best_fitness
                accuracy_improvement = self.best_accuracy - (self.history['best_accuracy'][-1] if self.history['best_accuracy'] else 0.0)
            else:
                improvement = 0.0
                accuracy_improvement = 0.0
            
            self.improvement_tracker.append(improvement)
            self.accuracy_improvement_tracker.append(accuracy_improvement)
            
            # Compute debt statistics
            debt_norms = [float(np.linalg.norm(a.debt_vector)) for a in all_agents if a.debt_vector is not None]
            avg_debt_norm = np.mean(debt_norms) if debt_norms else 0.0
            
            # Compute acceptance statistics
            total = self.acceptance_stats['total_candidates']
            acceptance_rate = (self.acceptance_stats['accepted_better'] + self.acceptance_stats['accepted_worse']) / max(total, 1)
            
            # Update history
            self.history['iterations'].append(iteration)
            self.history['best_fitness'].append(self.best_fitness)
            self.history['best_accuracy'].append(self.best_accuracy)
            self.history['avg_fitness'].append(float(np.mean(all_fitness)))
            self.history['worst_fitness'].append(float(np.max(all_fitness)))
            self.history['improvement_rate'].append(float(improvement))
            self.history['temperature'].append(self.temperature)
            self.history['debt_norms'].append(avg_debt_norm)
            self.history['diversity_scores'].append(np.mean([a.diversity_score for a in all_agents]))
            self.history['acceptance_rates'].append(acceptance_rate)
            
            # Logging
            if iteration % 10 == 0 or iteration == self.config.max_iterations - 1:
                self.logger.info(
                    f"[Iter {iteration:3d}] "
                    f"BestFit: {self.best_fitness:.4f} | "
                    f"BestAcc: {self.best_accuracy:.4f} | "
                    f"AvgFit: {np.mean(all_fitness):.4f} | "
                    f"Temp: {self.temperature:.3f} | "
                    f"Debt: {avg_debt_norm:.3f} | "
                    f"Accept: {acceptance_rate:.3f}"
                )
            
            # Early stopping check
            if self.config.adaptive_early_stop and iteration > 50:
                recent_improvements = list(self.improvement_tracker)[-20:]
                if all(abs(imp) < self.config.convergence_threshold for imp in recent_improvements):
                    self.logger.info(f"Early stopping at iteration {iteration}")
                    break

        # Finalize with accurate evaluation
        if self.best_agent:
            # Re-evaluate best agent with ensemble averaging and caching
            if hasattr(self.estimator, 'set_search_mode'):
                self.estimator.set_search_mode(False)
            
            # Final evaluation with ensemble averaging
            arch_dict = self.best_agent.gene.to_architecture_dict()
            loss, metrics = self.estimator.estimate(
                arch_dict, 
                use_cache=True,
                search_mode=False,
                iteration=self.config.max_iterations
            )
            
            # Update best agent with final metrics
            accuracy = metrics.get('accuracy', 1.0 - min(loss, 1.0))
            self.best_agent.accuracy = accuracy
            self.best_agent.metrics = metrics
            self.best_accuracy = accuracy
            
            self.history['best_architecture'] = self.best_agent.gene.to_architecture_dict()
            
            # Compute AUC metrics
            self._compute_auc_metrics()
            
            self.logger.info(f"Final Best Accuracy: {self.best_accuracy:.4f}")
            self.logger.info(f"Final Best Fitness: {self.best_fitness:.4f}")
            self.logger.info(f"AUC@10: {self.history['auc_10']:.4f}")
            self.logger.info(f"AUC@25: {self.history['auc_25']:.4f}")
            self.logger.info(f"Time to 95%: {self.history['time_to_95']} iterations")

        self.logger.info("=" * 70)
        self.logger.info("Optimization Complete!")
        self.logger.info(f"Best Accuracy: {self.best_accuracy:.4f}")
        self.logger.info(f"Best Fitness: {self.best_fitness:.4f}")
        if self.config.fitness_mode == 'pareto_assisted':
            self.logger.info(f"Pareto Archive Size: {len(self.pareto_archive)}")
        self.logger.info(f"Final Acceptance Rate: {acceptance_rate:.3f}")
        self.logger.info(f"Worse moves accepted: {self.acceptance_stats['accepted_worse']}")
        self.logger.info("=" * 70)

        return {
            'best_fitness': self.best_fitness,
            'best_accuracy': self.best_accuracy,
            'best_architecture': self.history.get('best_architecture'),
            'best_metrics': getattr(self.best_agent, 'metrics', {}),
            'history': self.history,
            'pareto_archive_size': len(self.pareto_archive),
            'acceptance_stats': self.acceptance_stats,
            'config': {
                'population_size': self.config.population_size,
                'islands': len(self.islands),
                'eval_strategy': self.config.eval_strategy,
                'fitness_mode': self.config.fitness_mode,
                'w_loss': self.config.w_loss,  # Indicate which fitness mode was used
                'max_iterations': len(self.history['iterations']),
            }
        }