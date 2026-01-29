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
        self.seen_hashes = set()  # Track seen architectures to penalize clones
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
        
        # Detect stagnation for noise modulation
        stagnation_detected = self.best_agent is not None and (iteration - self.best_agent.last_improvement) > 10
        
        loss, metrics = self.estimator.estimate(
            arch_dict, 
            use_cache=use_cache,
            search_mode=search_mode,
            iteration=iteration,
            max_iterations=self.config.max_iterations,
            stagnation_detected=stagnation_detected
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
        
        # C. Pareto rank influences survival even in scalar mode
        self._compute_pareto_rank(agent)
        # Penalize dominated agents to keep Pareto front wide
        agent.fitness += 0.01 * agent.pareto_rank
        
        # Pareto rank if enabled
        if self.config.fitness_mode == 'pareto_assisted':
            # Blend Pareto rank into fitness (normalized)
            if agent.pareto_rank > 0:
                normalized_rank = agent.pareto_rank / max(1, len(self.pareto_archive))
                agent.fitness += self.config.pareto_weight * normalized_rank
        
        # C. Regret-aware fitness - keep pressure on final accuracy
        if self.best_fitness < float('inf'):
            agent.fitness += 0.05 * max(0, agent.fitness - self.best_fitness)
        
        # B. Penalize architecture clones
        gene_hash = agent.gene.get_hash()
        if gene_hash in self.seen_hashes:
            agent.fitness += 0.02  # Penalize clones to encourage diversity
        self.seen_hashes.add(gene_hash)

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
        """Enhanced acceptance with debt-awareness and phase-dependent strategy."""
        self.acceptance_stats['total_candidates'] += 1
        
        t = self.history['iterations'][-1] / self.config.max_iterations if self.history['iterations'] else 0.0
        
        # Always accept better candidates
        if candidate.fitness < current.fitness:
            self.acceptance_stats['accepted_better'] += 1
            return True
        
        # Worse candidate: consider with debt-aware probability
        delta_fitness = candidate.fitness - current.fitness
        
        # Track delta
        self._recent_fitness_deltas.append(delta_fitness)
        
        if delta_fitness > 0 and self.temperature > 0:
            # DEBT-AWARE ACCEPTANCE: Higher debt = more likely to accept worse moves
            debt_factor = 1.0
            if current.debt_vector is not None:
                debt_norm = np.linalg.norm(current.debt_vector)
                debt_factor = 1.0 + min(2.0, debt_norm * 5.0)  # Up to 3x more likely with high debt
            
            # PHASE-AWARE ACCEPTANCE: More accepting early, less late
            phase_factor = 1.5 - t  # 1.5 early → 0.5 late
            
            # DIVERSITY-AWARE ACCEPTANCE: Accept diverse candidates
            diversity_factor = 1.0 + current.diversity_score * 0.5
            
            # Calculate acceptance probability
            if self.config.adaptive_acceptance_scaling and len(self._recent_fitness_deltas) > 10:
                delta_std = np.std(list(self._recent_fitness_deltas)) + 1e-8
                scaled_delta = delta_fitness / delta_std
            else:
                scaled_delta = delta_fitness * self.config.acceptance_scaling_factor
            
            # Apply all factors
            scaled_delta = scaled_delta / (debt_factor * phase_factor * diversity_factor)
            scaled_delta = min(scaled_delta, 10.0)  # Cap to avoid underflow
            
            # Calculate probability
            probability = math.exp(-scaled_delta / max(self.temperature, 1e-8))
            
            # Phase-dependent minimum acceptance probability
            min_probability = 0.1
            probability = max(probability, min_probability)
            
            accept = np.random.random() < probability
            
            if accept:
                self.acceptance_stats['accepted_worse'] += 1
                # Update agent's acceptance rate with smoothing
                current.acceptance_rate = 0.95 * current.acceptance_rate + 0.05 * probability
                # Soft clamp acceptance rate
                current.acceptance_rate = np.clip(current.acceptance_rate, 0.2, 0.6)
            else:
                self.acceptance_stats['rejected'] += 1
                current.acceptance_rate = 0.95 * current.acceptance_rate + 0.05 * 0.0
                # Soft clamp acceptance rate
                current.acceptance_rate = np.clip(current.acceptance_rate, 0.2, 0.6)
            
            return accept
        
        self.acceptance_stats['rejected'] += 1
        return False

    def _dpo_step(self, agent: SearchAgent, params: Dict, iteration: int) -> SearchAgent:
        """DPO step with persistent debt memory and delayed repayment."""
        current_vec = agent.gene.gene
        
        # Forced late-stage debt (NON-NEGOTIABLE)
        no_improvement_steps = iteration - agent.last_improvement
        if self.config.force_late_debt and iteration > self.config.late_debt_start_ratio * self.config.max_iterations:
            random_unit = np.random.randn(agent.gene.D)
            random_unit /= np.linalg.norm(random_unit) + 1e-8
            agent.debt_vector += self.config.late_debt_epsilon * random_unit
        
        # 1. Debt Gene Logic with STAGNATION AWARE exploration
        base_alpha = params['alpha']
        
        # A. Make mutation debt-coupled - increase directional variance when debt is high
        debt_norm = np.linalg.norm(agent.debt_vector) if agent.debt_vector is not None else 0.0
        if debt_norm > 0.1:
            base_alpha *= 1.2  # More aggressive exploration when debt is high
        
        # If agent stagnating, increase exploration
        stagnation = iteration - agent.last_improvement
        if stagnation > 10:  # Stagnating for 10+ iterations
            base_alpha *= 1.5  # More aggressive exploration
            if agent.debt_vector is not None:
                # Inject fresh debt direction when stagnating
                fresh_debt = np.random.randn(agent.gene.D) * 0.1
                agent.debt_vector = agent.debt_vector * 0.5 + fresh_debt * 0.5
        
        perturbation = np.random.randn(agent.gene.D) * base_alpha
        debt_vec = current_vec + perturbation
        self._clip_gene_array(debt_vec, agent.gene.num_layers, agent.gene.num_cells)
        
        # 2. DEBT MEMORY with exponential persistence
        new_debt_component = debt_vec - current_vec
        
        # Create candidate
        smart_gene = ArchitectureGene(agent.gene.num_layers, agent.gene.num_cells)
        smart_gene.gene = debt_vec
        candidate = SearchAgent(
            gene=smart_gene, 
            island_id=agent.island_id,
            debt_vector=agent.debt_vector.copy() if agent.debt_vector is not None else None,
            mutation_magnitude=agent.mutation_magnitude,
            acceptance_rate=agent.acceptance_rate
        )
        self._evaluate_agent(candidate, iteration)
        
        # 3. DELAYED REPAYMENT SCHEDULE (NEW)
        t = iteration / self.config.max_iterations
        repayment_delay_factor = max(0.3, 1.0 - 0.8 * t)  # Start at 1.0, end at 0.3
        
        # Probabilistic acceptance
        if self._accept_candidate(agent, candidate):
            if candidate.fitness < agent.fitness:
                # Better move found
                
                # FIX #2: Continuous repayment based on accuracy delta
                delta_acc = candidate.accuracy - agent.accuracy
                
                # Use sigmoid function for continuous repayment strength
                # Sensitivity parameter (how sharply repayment responds to accuracy changes)
                sensitivity = 50.0  # Higher = more sensitive to small changes
                sigmoid_value = 1.0 / (1.0 + math.exp(-delta_acc * sensitivity))
                repayment_strength = 0.1 + 0.8 * sigmoid_value  # ∈ (0.1, 0.9)
                
                # Scale repayment by continuous strength instead of binary threshold
                if candidate.debt_vector is not None and np.linalg.norm(candidate.debt_vector) > 1e-6:
                    debt_magnitude = np.linalg.norm(candidate.debt_vector)
                    
                    # Base repayment scaled by continuous strength
                    effective_beta = params['beta'] * repayment_strength
                    
                    # Capped repayment
                    if iteration < 0.3 * self.config.max_iterations:
                        max_repayment_ratio = self.config.repayment_cap_early
                    elif iteration < 0.7 * self.config.max_iterations:
                        max_repayment_ratio = self.config.repayment_cap_mid
                    else:
                        max_repayment_ratio = self.config.repayment_cap_late
                    effective_beta = min(effective_beta, max_repayment_ratio * debt_magnitude)
                    
                    repay_vec = current_vec - (effective_beta * candidate.debt_vector)
                    self._clip_gene_array(repay_vec, agent.gene.num_layers, agent.gene.num_cells)
                    
                    # Overshoot also scaled by repayment strength
                    if debt_magnitude > 1e-6 and params['gamma'] > 0.1:
                        overshoot_factor = params['gamma'] * repayment_strength
                        double_vec = repay_vec - (overshoot_factor * candidate.debt_vector)
                        self._clip_gene_array(double_vec, agent.gene.num_layers, agent.gene.num_cells)
                    else:
                        double_vec = repay_vec.copy()
                    
                    # Smart move
                    best_global = self.best_agent or agent
                    smart_vec = double_vec + params['delta'] * (best_global.gene.gene - current_vec)
                    self._clip_gene_array(smart_vec, agent.gene.num_layers, agent.gene.num_cells)
                    
                    # Update gene
                    candidate.gene.gene = smart_vec
                    
                    # Debt decay scaled by repayment strength
                    t = iteration / self.config.max_iterations
                    base_decay = 0.8  # 20% decay minimum
                    max_decay = 0.1   # 90% decay maximum for strong improvements
                    decay_factor = base_decay + (max_decay - base_decay) * repayment_strength
                    candidate.debt_vector *= decay_factor
                    
                    # A. Make debt repayment incomplete - leave financial stress
                    candidate.debt_vector = np.sign(candidate.debt_vector) * np.maximum(np.abs(candidate.debt_vector), 0.01)
                    
                    # B. Add irrational repayment noise - small random rotation
                    if np.linalg.norm(candidate.debt_vector) > 1e-6:
                        original_norm = np.linalg.norm(candidate.debt_vector)
                        candidate.debt_vector += 0.1 * np.random.randn(agent.gene.D)
                        candidate.debt_vector /= np.linalg.norm(candidate.debt_vector) + 1e-8
                        candidate.debt_vector *= original_norm
                    
                    # Clear debt only on very strong improvements (repayment_strength > 0.9)
                    if repayment_strength > 0.9:
                        candidate.debt_vector = np.zeros_like(candidate.debt_vector)
                
                candidate.improvements = agent.improvements + 1
                candidate.last_improvement = iteration
                
            else:
                # Worse move accepted: accumulate debt
                if candidate.debt_vector is not None:
                    # FIX #2: No repayment for negative delta_acc
                    candidate.update_debt(
                        new_debt_component, 
                        params['debt_memory'] * 0.8,
                        accumulate_only=True
                    )
            
            # Update mutation magnitude
            if self.config.adaptive_mutation:
                improvement = candidate.fitness < agent.fitness
                candidate.update_mutation_magnitude(improvement, smoothing=0.9)
            
            return candidate
        
        # Rejected: Age and potentially inject mini-debt
        agent.age += 1
        if agent.age % 5 == 0 and agent.debt_vector is not None:
            # Small debt injection to prevent total stagnation
            agent.debt_vector += np.random.randn(agent.gene.D) * 0.05
        
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
        """Enhanced migration with debt diversity preservation."""
        if not self.config.island_model or len(self.islands) < 2:
            return
            
        t = iteration / self.config.max_iterations
        num_migrate = max(1, self.config.population_size // 15)  # More frequent migration
        
        for island_idx in range(len(self.islands)):
            # Find diverse candidates from other islands (not just best)
            migration_candidates = []
            for other_idx in range(len(self.islands)):
                if other_idx == island_idx:
                    continue
                    
                other_island = self.islands[other_idx]
                if not other_island:
                    continue
                    
                # Select agents based on diversity to current island
                for agent in other_island[:3]:  # Consider top 3 from each island
                    # Check if agent brings diversity
                    similarity_score = 0.0
                    for local_agent in self.islands[island_idx][:5]:  # Compare to local top 5
                        # Compare genes and debt directions
                        gene_sim = np.dot(
                            agent.gene.gene / (np.linalg.norm(agent.gene.gene) + 1e-8),
                            local_agent.gene.gene / (np.linalg.norm(local_agent.gene.gene) + 1e-8)
                        )
                        
                        # Compare debt directions if available
                        debt_sim = 0.0
                        if (agent.debt_vector is not None and local_agent.debt_vector is not None and
                            np.linalg.norm(agent.debt_vector) > 1e-6 and np.linalg.norm(local_agent.debt_vector) > 1e-6):
                            debt_sim = np.dot(
                                agent.debt_vector / (np.linalg.norm(agent.debt_vector) + 1e-8),
                                local_agent.debt_vector / (np.linalg.norm(local_agent.debt_vector) + 1e-8)
                            )
                        
                        similarity_score += 0.7 * gene_sim + 0.3 * debt_sim
                    
                    # Lower similarity = more diverse
                    diversity_score = 1.0 - (similarity_score / 5.0)  # Normalize
                    migration_candidates.append((agent, diversity_score))
            
            if not migration_candidates:
                continue
                
            # Sort by diversity (most diverse first)
            migration_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Sort current island (worst first)
            self.islands[island_idx].sort(key=lambda a: a.fitness, reverse=True)
            
            # Replace worst agents with diverse migrants
            for i in range(min(num_migrate, len(migration_candidates), len(self.islands[island_idx]))):
                migrant, diversity = migration_candidates[i]
                
                # Create migrated agent with debt inheritance
                new_gene = migrant.gene.copy()
                
                # Inherit debt with phase-dependent adjustment
                if migrant.debt_vector is not None:
                    if t < 0.5:  # Early phase: preserve debt for exploration
                        debt_inheritance = 1.0
                    else:  # Late phase: reduce inherited debt
                        debt_inheritance = 0.7
                    new_debt = migrant.debt_vector.copy() * debt_inheritance
                else:
                    new_debt = np.zeros_like(new_gene.gene)
                
                # Add migration noise to debt
                new_debt += np.random.randn(*new_debt.shape) * 0.1
                
                # FIX #3: Orthogonalize migrated debt
                island_debts = []
                for agent in self.islands[island_idx]:
                    if agent.debt_vector is not None and np.linalg.norm(agent.debt_vector) > 1e-6:
                        island_debts.append(agent.debt_vector)
                
                if island_debts:
                    new_debt = self._orthogonalize_debt(new_debt, island_debts)
                
                new_agent = SearchAgent(
                    gene=new_gene, 
                    island_id=island_idx,
                    debt_vector=new_debt,
                    accuracy=migrant.accuracy,
                    cost_metrics=migrant.cost_metrics.copy(),
                    mutation_magnitude=migrant.mutation_magnitude,
                    acceptance_rate=migrant.acceptance_rate
                )
                
                # Evaluate in new context
                self._evaluate_agent(new_agent, iteration)
                self.islands[island_idx][i] = new_agent

    def _inject_diversity(self, iteration: int) -> None:
        """Enhanced diversity injection with debt-guided exploration."""
        t = iteration / self.config.max_iterations
        
        for island_idx, island in enumerate(self.islands):
            n = len(island)
            if n < 2:
                continue
            
            # Calculate diversity with debt-aware metric
            island_agents = island
            if len(island_agents) < 2:
                continue
            
            # Compute diversity including debt directions
            diversity_scores = []
            for i, agent in enumerate(island_agents):
                # Combine gene and debt for diversity calculation
                if agent.debt_vector is not None and np.linalg.norm(agent.debt_vector) > 1e-6:
                    # Normalize debt vector
                    debt_dir = agent.debt_vector / (np.linalg.norm(agent.debt_vector) + 1e-8)
                    agent_vector = np.concatenate([agent.gene.gene, debt_dir * 0.3])
                else:
                    agent_vector = agent.gene.gene
                
                # Calculate distance to other agents
                distances = []
                for j, other in enumerate(island_agents):
                    if i == j:
                        continue
                    if other.debt_vector is not None and np.linalg.norm(other.debt_vector) > 1e-6:
                        other_debt_dir = other.debt_vector / (np.linalg.norm(other.debt_vector) + 1e-8)
                        other_vector = np.concatenate([other.gene.gene, other_debt_dir * 0.3])
                    else:
                        other_vector = other.gene.gene
                    
                    # Ensure vectors have same length
                    min_len = min(len(agent_vector), len(other_vector))
                    dist = np.linalg.norm(agent_vector[:min_len] - other_vector[:min_len])
                    distances.append(dist)
                
                diversity_scores.append(np.mean(distances) if distances else 0.0)
            
            avg_diversity = np.mean(diversity_scores)
            
            # Dynamic diversity threshold based on phase
            phase_threshold = self.config.min_diversity_threshold
            if t < 0.3:  # Early: require less diversity
                phase_threshold *= 0.7
            elif t > 0.7:  # Late: require more diversity
                phase_threshold *= 1.3
            
            if avg_diversity > phase_threshold:
                continue  # Island is diverse enough
            
            # Enhanced diversity injection
            elite_count = max(1, int(n * self.config.elite_ratio))
            island.sort(key=lambda a: a.fitness)
            elites = island[:elite_count]
            
            # Inject into worst-performing agents
            for i in range(elite_count, n):
                if np.random.random() < 0.6:  # 60% chance to inject
                    # Select parent (prefer elites with high debt for exploration)
                    eligible_parents = []
                    for elite in elites:
                        if elite.debt_vector is not None and np.linalg.norm(elite.debt_vector) > 0.1:
                            eligible_parents.append((elite, 2.0))  # Higher weight for indebted elites
                        else:
                            eligible_parents.append((elite, 1.0))
                    
                    if eligible_parents:
                        parents, weights = zip(*eligible_parents)
                        parent = np.random.choice(parents, p=np.array(weights)/sum(weights))
                    else:
                        parent = island[np.random.randint(0, n)]
                    
                    # Create mutant with debt-guided exploration
                    parent_vec = parent.gene.gene
                    
                    # Use parent's debt direction for exploration
                    if parent.debt_vector is not None and np.linalg.norm(parent.debt_vector) > 1e-6:
                        # Explore in debt direction (repayment direction)
                        exploration_dir = -parent.debt_vector  # Opposite of debt = repayment direction
                        exploration_dir = exploration_dir / (np.linalg.norm(exploration_dir) + 1e-8)
                    else:
                        # Random exploration
                        exploration_dir = np.random.randn(len(parent_vec))
                        exploration_dir = exploration_dir / (np.linalg.norm(exploration_dir) + 1e-8)
                    
                    # Add orthogonal noise
                    noise = np.random.randn(len(parent_vec))
                    if np.linalg.norm(exploration_dir) > 1e-6:
                        # Make noise orthogonal to exploration direction
                        noise = noise - np.dot(noise, exploration_dir) * noise
                    
                    # Adaptive mutation strength
                    mutation_strength = island[i].mutation_magnitude
                    if t > 0.7:  # Late phase: stronger exploration
                        mutation_strength *= self.config.late_phase_exploration_boost
                    
                    # Combine exploration direction and orthogonal noise
                    mutant_gene = parent_vec + mutation_strength * (
                        0.7 * exploration_dir + 0.3 * noise / (np.linalg.norm(noise) + 1e-8)
                    )
                    
                    # Clip
                    self._clip_gene_array(mutant_gene, parent.gene.num_layers, parent.gene.num_cells)
                    
                    # Create new agent with inherited debt
                    new_gene = ArchitectureGene(parent.gene.num_layers, parent.gene.num_cells)
                    new_gene.gene = mutant_gene
                    
                    # Inherit and amplify debt for exploration
                    new_debt = parent.debt_vector.copy() if parent.debt_vector is not None else np.zeros_like(mutant_gene)
                    new_debt = new_debt * 0.8 + np.random.randn(*new_debt.shape) * 0.2
                    
                    # FIX #3: Orthogonalize debt against island's existing debts
                    island_debts = []
                    for agent in island:
                        if agent.debt_vector is not None and np.linalg.norm(agent.debt_vector) > 1e-6:
                            island_debts.append(agent.debt_vector)
                    
                    if island_debts:
                        new_debt = self._orthogonalize_debt(new_debt, island_debts)
                    
                    new_agent = SearchAgent(
                        gene=new_gene, 
                        island_id=island_idx,
                        debt_vector=new_debt,
                        mutation_magnitude=min(0.3, mutation_strength * 1.1),
                        acceptance_rate=island[i].acceptance_rate * 0.9
                    )
                    self._evaluate_agent(new_agent, iteration)
                    island[i] = new_agent

    def _force_diversity(self, island_idx: int, iteration: int) -> None:
        """Force diversity in a stagnated island."""
        island = self.islands[island_idx]
        if len(island) < 3:
            return
        
        # Keep best agent
        island.sort(key=lambda a: a.fitness)
        best_agent = island[0]
        
        # Generate completely new agents with strategic debt
        new_agents = [best_agent]
        for i in range(1, len(island)):
            # Create new gene
            gene = ArchitectureGene(best_agent.gene.num_layers, best_agent.gene.num_cells)
            
            # Strategic debt: opposite direction of best agent's debt
            if best_agent.debt_vector is not None and np.linalg.norm(best_agent.debt_vector) > 1e-6:
                # Explore in opposite direction of current debt
                debt_dir = best_agent.debt_vector / np.linalg.norm(best_agent.debt_vector)
                exploration_dir = -debt_dir  # Opposite direction
            else:
                exploration_dir = np.random.randn(gene.D)
                exploration_dir = exploration_dir / (np.linalg.norm(exploration_dir) + 1e-8)
            
            # Apply exploration
            mutation_strength = 0.3  # Strong mutation for restart
            gene.gene = best_agent.gene.gene + mutation_strength * exploration_dir
            self._clip_gene_array(gene.gene, gene.num_layers, gene.num_cells)
            
            # Create new agent with fresh debt
            new_debt = exploration_dir * 0.5  # Debt in exploration direction
            
            # FIX #3: Orthogonalize restart debt
            island_debts = []
            for agent in self.islands[island_idx]:
                if agent.debt_vector is not None and np.linalg.norm(agent.debt_vector) > 1e-6:
                    island_debts.append(agent.debt_vector)
            
            if island_debts:
                new_debt = self._orthogonalize_debt(new_debt, island_debts)
            
            new_agent = SearchAgent(
                gene=gene,
                island_id=island_idx,
                debt_vector=new_debt,
                mutation_magnitude=0.25,  # Reset to moderate
                acceptance_rate=0.4  # Reset acceptance
            )
            self._evaluate_agent(new_agent, iteration)
            new_agents.append(new_agent)
        
        self.islands[island_idx] = new_agents

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
        
        # Track stagnation per island
        island_stagnation = [0] * len(self.islands)
        
        for iteration in range(self.config.max_iterations):
            # Update temperature with phase-dependent decay
            t = iteration / self.config.max_iterations
            if t < 0.3:
                decay = 0.98  # Slow decay early
            elif t < 0.7:
                decay = 0.97  # Moderate decay mid
            else:
                decay = 0.96  # Faster decay late
            
            self.temperature = max(
                self.config.temperature_min,
                self.temperature * decay
            )
            
            # Update population statistics for normalization
            self._update_population_stats()
            
            # Compute diversity scores for penalty
            self._compute_diversity_scores()
            
            # B. Penalize over-confidence - reward diversity
            for island in self.islands:
                for agent in island:
                    if agent.diversity_score < 0.1:
                        agent.fitness += 0.01
            
            # Get adaptive parameters for current phase
            params = self._get_adaptive_parameters(iteration)
            
            # Process each island with stagnation awareness
            for island_idx, island in enumerate(self.islands):
                island_improved = False
                
                for idx, agent in enumerate(island):
                    # Check for stagnation-driven debt injection
                    if (agent.debt_vector is not None and 
                        np.linalg.norm(agent.debt_vector) < self.config.min_debt_for_exploration and
                        iteration - agent.last_improvement > self.config.stagnation_threshold):
                        # Inject exploration debt
                        exploration_debt = np.random.randn(agent.gene.D) * self.config.stagnation_debt_injection
                        agent.debt_vector = agent.debt_vector * 0.5 + exploration_debt * 0.5
                    
                    new_agent = self._dpo_step(agent, params, iteration)
                    island[idx] = new_agent
                    
                    # Check if island improved
                    if new_agent.fitness < agent.fitness:
                        island_improved = True
                    
                    # Update best agents
                    if new_agent.fitness < self.best_fitness:
                        self.best_fitness = new_agent.fitness
                        self.best_agent = new_agent
                        self.logger.info(f"[Iter {iteration}] New best fitness: {self.best_fitness:.4f}")
                    
                    if new_agent.accuracy > self.best_accuracy:
                        self.best_accuracy = new_agent.accuracy
                        self.logger.info(f"[Iter {iteration}] New best accuracy: {self.best_accuracy:.4f}")
                
                # Update island stagnation counter
                if island_improved:
                    island_stagnation[island_idx] = 0
                else:
                    island_stagnation[island_idx] += 1
                
                # If island severely stagnated, force diversity
                if island_stagnation[island_idx] > 20:
                    self.logger.info(f"Island {island_idx} stagnated, forcing diversity")
                    self._force_diversity(island_idx, iteration)
                    island_stagnation[island_idx] = 0
            
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
            
            # Acceptance rate sanity band: adjust temperature
            if acceptance_rate < 0.2:
                self.temperature *= 1.05  # increase slightly if too low
            elif acceptance_rate > 0.6:
                self.temperature *= 0.95  # decay faster if too high
            self.temperature = max(self.config.temperature_min, min(self.config.temperature_start, self.temperature))
            
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
                iteration=self.config.max_iterations,
                max_iterations=self.config.max_iterations,
                stagnation_detected=False  # No noise in final evaluation
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

    def _orthogonalize_debt(self, new_debt: np.ndarray, reference_debts: List[np.ndarray]) -> np.ndarray:
        """Make new debt orthogonal to mean of reference debts."""
        if not reference_debts:
            return new_debt
        
        # Compute mean debt direction
        mean_debt = np.zeros_like(new_debt)
        valid_debts = 0
        
        for ref_debt in reference_debts:
            if ref_debt is not None and np.linalg.norm(ref_debt) > 1e-6:
                # Normalize each debt vector
                norm_ref = np.linalg.norm(ref_debt)
                mean_debt += ref_debt / norm_ref
                valid_debts += 1
        
        if valid_debts == 0:
            return new_debt
        
        mean_debt /= valid_debts
        
        # Orthogonalize: remove projection onto mean debt direction
        if np.linalg.norm(mean_debt) > 1e-6:
            mean_debt_norm = mean_debt / np.linalg.norm(mean_debt)
            projection = np.dot(new_debt, mean_debt_norm) * mean_debt_norm
            orthogonal_debt = new_debt - projection
            
            # Preserve original magnitude
            original_norm = np.linalg.norm(new_debt)
            if np.linalg.norm(orthogonal_debt) > 1e-6:
                orthogonal_debt = orthogonal_debt / np.linalg.norm(orthogonal_debt) * original_norm
            
            return orthogonal_debt
        
        return new_debt