# file name: config.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class DPO_Config:
    # Population settings
    population_size: int = 40
    max_iterations: int = 200
    num_workers: int = 4

    # Algorithm parameters with adaptive modes
    alpha_0: float = 0.15
    beta_0: float = 1.0
    gamma_0: float = 1.0
    delta_0: float = 0.2
    
    # FIX: Power-law decay instead of aggressive exponential
    decay_power: float = 0.5  # Changed from 2.0 to 0.5 for slower decay
    
    # Debt memory for persistent debt accumulation
    debt_memory_lambda: float = 0.85  # λ in [0.7, 0.95]
    min_debt_memory: float = 0.7
    max_debt_memory: float = 0.95

    # Adaptive modes
    adaptive_alpha: bool = True
    adaptive_beta: bool = True
    adaptive_patience: bool = True

    # Diversity management
    elite_ratio: float = 0.1
    diversity_inject_freq: int = 5
    island_model: bool = True
    num_islands: int = 3
    migration_freq: int = 10
    
    # Minimum diversity threshold (L2 distance normalized)
    min_diversity_threshold: float = 0.05
    adaptive_mutation: bool = True

    # Constraints
    latency_constraint: float = 100.0
    memory_constraint: float = 50.0
    flops_constraint: float = 300.0
    constraint_penalty_scale: float = 2.0

    # FIX: Explicit objective weights for accuracy-cost-penalty decomposition
    # WARNING: Set w_loss = 0.0 to use accuracy-aware fitness
    # If w_loss > 0, it will override accuracy-aware fitness
    w_accuracy: float = 0.6  # Primary signal for NAS performance
    w_cost: float = 0.3      # Combined cost terms (latency, memory, flops)
    w_penalty: float = 0.1   # Constraint violations
    
    # Backward compatibility with original weights - SET w_loss = 0.0 FOR ACCURACY-AWARE MODE
    w_loss: float = 0.0      # MUST BE 0.0 to use accuracy-aware fitness
    w_latency: float = 0.15
    w_memory: float = 0.1
    w_flops: float = 0.05
    
    # FIX: Temperature schedule for probabilistic acceptance
    temperature_start: float = 1.0
    temperature_min: float = 0.05
    temperature_decay: float = 0.98  # Multiplicative decay per iteration
    
    # Acceptance probability formula: P = exp(-Δfitness / T)
    acceptance_scaling_factor: float = 1.0  # Will be dynamically adjusted

    # Evaluation strategy
    eval_strategy: str = 'ensemble'
    cache_evaluations: bool = True
    use_gpu_eval: bool = True
    
    # FIX: Pareto-assisted mode (keeps scalar fitness as default)
    fitness_mode: Literal['scalar', 'pareto_assisted'] = 'scalar'
    pareto_archive_size: int = 50
    pareto_weight: float = 0.3  # Weight for Pareto rank in scalar fitness
    
    # FIX: Accuracy improvement threshold for debt repayment
    accuracy_improvement_threshold: float = 0.001  # Minimum accuracy improvement to trigger repayment

    # Convergence detection
    patience: int = 30
    convergence_window: int = 20
    convergence_threshold: float = 1e-4
    adaptive_early_stop: bool = True
    
    # Exploration phases control
    exploration_phase_ratio: float = 0.3  # First 30% iterations favor exploration
    debt_accumulation_phase: float = 0.4  # Middle 40% for debt accumulation
    repayment_phase: float = 0.7          # Last 30% for aggressive repayment

    # Logging & tracking
    verbose: bool = True
    save_history: bool = True
    history_path: str = './nas_history.json'
    checkpoint_freq: int = 10
    checkpoint_dir: str = './checkpoints'
    
    # Track accuracy progression
    track_accuracy_curve: bool = True
    
    # FIX: Acceptance probability adaptive scaling
    adaptive_acceptance_scaling: bool = True
    
    # NEW: Debt persistence controls
    debt_persistence_start: float = 0.8  # Start with 80% debt persistence
    debt_persistence_end: float = 0.2    # End with 20% persistence
    debt_persistence_decay: str = 'linear'  # 'linear', 'exponential', 'cosine'
    
    # NEW: Stagnation handling
    stagnation_threshold: int = 15  # Iterations without improvement
    stagnation_debt_injection: float = 0.15  # Debt to inject when stagnating
    stagnation_exploration_boost: float = 1.5  # Alpha multiplier when stagnating
    
    # NEW: Accuracy-driven debt reset
    accuracy_reset_threshold: float = 0.01  # Accuracy improvement to trigger reset
    reset_debt_on_major_improvement: bool = True
    
    # NEW: Late-phase exploration boost
    late_phase_exploration_boost: float = 1.3  # Boost exploration in last 30%
    min_debt_for_exploration: float = 0.05  # Minimum debt to force exploration
    
    # NEW: Behavioral switches for TL-DPO dynamics
    force_late_debt: bool = True
    late_debt_start_ratio: float = 0.6
    late_debt_epsilon: float = 0.03
    
    repayment_cap_early: float = 0.3
    repayment_cap_mid: float = 0.6
    repayment_cap_late: float = 0.9
    
    # Presets with accuracy-aware mode enforced
    @classmethod
    def fast(cls):
        config = cls(
            population_size=20, 
            max_iterations=50, 
            num_islands=2, 
            migration_freq=5,
        )
        # Force accuracy-aware mode
        config.w_loss = 0.0
        return config

    @classmethod
    def balanced(cls):
        config = cls(
            population_size=40, 
            max_iterations=150, 
            num_islands=3, 
            migration_freq=10,
        )
        # Force accuracy-aware mode
        config.w_loss = 0.0
        return config

    @classmethod
    def thorough(cls):
        config = cls(
            population_size=80, 
            max_iterations=300, 
            num_islands=4, 
            migration_freq=15,
            temperature_decay=0.995,  # Slower decay for thorough search
            decay_power=0.8,
        )
        # B. Reduce late-phase discipline - more chaos for thorough
        config.late_debt_epsilon = 0.05  # More irrational debt
        config.late_debt_start_ratio = 0.5  # Earlier forced debt
        config.repayment_cap_late = 0.95  # Less repayment discipline
        # Force accuracy-aware mode
        config.w_loss = 0.0
        return config
    
    def validate(self):
        """Validate configuration for accuracy-aware mode"""
        if self.w_loss > 0 and self.w_accuracy < 0.5:
            print("WARNING: w_loss > 0 activates legacy loss-based fitness. "
                  "For accuracy-aware mode, set w_loss = 0.0")