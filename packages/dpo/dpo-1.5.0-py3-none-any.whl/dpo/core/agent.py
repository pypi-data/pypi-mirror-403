# file name: agent.py
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from ..architecture.gene import ArchitectureGene

@dataclass
class SearchAgent:
    # __slots__ optimization drastically reduces memory overhead for populations
    __slots__ = ('gene', 'fitness', 'metrics', 'island_id', 'age', 'improvements',
                 'accuracy', 'cost_metrics', 'debt_vector', 'diversity_score',
                 'pareto_rank', 'last_improvement', 'mutation_magnitude',
                 'debt_history', 'acceptance_rate', 'mutation_history')
    
    gene: ArchitectureGene
    fitness: float
    metrics: Dict
    island_id: int
    age: int
    improvements: int
    
    # Accuracy-aware optimization
    accuracy: float
    cost_metrics: Dict[str, float]  # latency, flops, memory
    debt_vector: Optional[np.ndarray]  # Persistent debt memory
    diversity_score: float  # L2 distance in normalized gene space
    pareto_rank: int  # Pareto dominance rank (0 = non-dominated)
    last_improvement: int  # Iteration of last fitness improvement
    mutation_magnitude: float  # Adaptive mutation scale
    debt_history: List[float]  # Track debt magnitude over time
    acceptance_rate: float  # Probability of accepting worse moves
    mutation_history: List[float]  # Track mutation magnitude over time

    def __init__(self, gene: ArchitectureGene, fitness: float = float('inf'), 
                 metrics: Dict = None, island_id: int = 0, age: int = 0, 
                 improvements: int = 0, accuracy: float = 0.0, 
                 cost_metrics: Dict = None, debt_vector: np.ndarray = None,
                 mutation_magnitude: float = 0.15, acceptance_rate: float = 0.3):
        self.gene = gene
        self.fitness = fitness
        self.metrics = metrics if metrics is not None else {}
        self.island_id = island_id
        self.age = age
        self.improvements = improvements
        
        # Accuracy and cost tracking
        self.accuracy = accuracy if accuracy != 0.0 else self.metrics.get('accuracy', 0.0)
        self.cost_metrics = cost_metrics if cost_metrics is not None else {
            'latency': self.metrics.get('latency_ms', 0.0),
            'flops': self.metrics.get('flops_m', 0.0),
            'memory': self.metrics.get('memory_mb', 0.0)
        }
        
        # Persistent debt memory for DPO semantics
        self.debt_vector = debt_vector if debt_vector is not None else np.zeros_like(gene.gene)
        
        # Diversity and Pareto tracking
        self.diversity_score = 0.0
        self.pareto_rank = 0
        self.last_improvement = 0
        self.mutation_magnitude = mutation_magnitude
        self.debt_history = []
        self.acceptance_rate = acceptance_rate
        self.mutation_history = [mutation_magnitude]

    def __lt__(self, other: 'SearchAgent'):
        # Primary comparison by scalar fitness (preserving DPO semantics)
        return self.fitness < other.fitness
    
    def is_dominated(self, other: 'SearchAgent') -> bool:
        """
        Check if this agent is Pareto-dominated by another agent.
        Dominance: higher accuracy AND lower total cost is better.
        """
        total_cost_self = sum(self.cost_metrics.values())
        total_cost_other = sum(other.cost_metrics.values())
        
        # other dominates self if: other has better or equal accuracy AND lower cost
        accuracy_dominates = other.accuracy >= self.accuracy
        cost_dominates = total_cost_other <= total_cost_self
        
        # Strict dominance requires at least one strict inequality
        if accuracy_dominates and cost_dominates:
            return (other.accuracy > self.accuracy) or (total_cost_other < total_cost_self)
        return False

    def update_debt(self, new_debt: np.ndarray, debt_memory: float = 0.8, accumulate_only: bool = False) -> None:
        """
        Update persistent debt with memory decay.
        Debt accumulates across iterations: debt ← λ·debt + (1-λ)·new_debt
        
        Tyrion's Law: Only accumulate debt when worse moves are accepted
        """
        if self.debt_vector is None:
            self.debt_vector = new_debt.copy()
        else:
            if accumulate_only:
                # Only accumulate, don't decay existing debt
                self.debt_vector = self.debt_vector + (1.0 - debt_memory) * new_debt
            else:
                # Normal update with memory
                self.debt_vector = (debt_memory * self.debt_vector + 
                                  (1.0 - debt_memory) * new_debt)
        
        # Track debt history
        self.debt_history.append(float(np.linalg.norm(self.debt_vector)))
        if len(self.debt_history) > 10:
            self.debt_history.pop(0)
    
    def clear_debt(self) -> None:
        """Reset debt vector while preserving DPO semantics"""
        self.debt_vector = np.zeros_like(self.gene.gene)
        self.debt_history = []

    def update_mutation_magnitude(self, improvement: bool, smoothing: float = 0.95) -> None:
        """
        Smoothly update mutation magnitude based on improvement.
        """
        if improvement:
            # Reduce mutation when improving
            new_mag = max(0.05, self.mutation_magnitude * 0.98)
        else:
            # Increase mutation when stagnating
            new_mag = min(0.3, self.mutation_magnitude * 1.02)
        
        # Smooth update
        self.mutation_magnitude = smoothing * self.mutation_magnitude + (1 - smoothing) * new_mag
        
        # Debt-aware mutation scaling
        debt_norm = np.linalg.norm(self.debt_vector) if self.debt_vector is not None else 0.0
        if debt_norm > 0.1:  # threshold for significant debt
            self.mutation_magnitude = min(0.3, self.mutation_magnitude * 1.1)
        
        self.mutation_history.append(self.mutation_magnitude)
        if len(self.mutation_history) > 10:
            self.mutation_history.pop(0)

    def to_dict(self) -> Dict:
        return {
            'fitness': self.fitness,
            'accuracy': self.accuracy,
            'metrics': self.metrics,
            'island_id': self.island_id,
            'age': self.age,
            'improvements': self.improvements,
            'architecture': self.gene.to_architecture_dict(),
            'cost_metrics': self.cost_metrics,
            'debt_norm': float(np.linalg.norm(self.debt_vector)) if self.debt_vector is not None else 0.0,
            'diversity_score': self.diversity_score,
            'pareto_rank': self.pareto_rank,
            'acceptance_rate': self.acceptance_rate,
            'mutation_magnitude': self.mutation_magnitude,
        }