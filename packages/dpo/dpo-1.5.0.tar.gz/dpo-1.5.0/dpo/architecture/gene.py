# import numpy as np
# from typing import Dict
# from collections import deque
# import hashlib

# class ArchitectureGene:
#     OPERATIONS = ['conv_3x3', 'conv_5x5', 'dw_conv', 'sep_conv', 'avg_pool', 'max_pool', 'skip_connect']
#     KERNELS = [1, 3, 5, 7]
#     CHANNELS = [16, 32, 64, 128, 256]

#     def __init__(self, num_layers: int = 12, num_cells: int = 5):
#         self.num_layers = num_layers
#         self.num_cells = num_cells
#         self.D = num_layers * 3 + num_cells + 2
#         self.gene = self._initialize_random()
#         self.mutation_history = deque(maxlen=50)

#     def _initialize_random(self) -> np.ndarray:
#         gene = np.zeros(self.D)
#         ops_bias = np.array([3, 3, 2, 2, 1, 1, 0.5])
#         ops_bias = ops_bias / ops_bias.sum()
#         gene[:self.num_layers] = np.random.choice(len(self.OPERATIONS), self.num_layers, p=ops_bias)
#         gene[self.num_layers:2*self.num_layers] = np.random.randint(0, len(self.KERNELS), self.num_layers)
#         skip_count = np.random.randint(0, int(self.num_cells * 0.3))
#         if skip_count > 0:
#             skip_indices = np.random.choice(self.num_cells, skip_count, replace=False)
#             gene[2*self.num_layers:2*self.num_layers+self.num_cells][skip_indices] = 1
#         gene[-2] = np.random.uniform(0.6, 1.0)
#         gene[-1] = np.random.uniform(0.6, 1.0)
#         return gene

#     def mutate(self, mutation_type: str = 'adaptive') -> 'ArchitectureGene':
#         mutant = self.copy()
#         if mutation_type == 'adaptive':
#             mutation_type = np.random.choice(['local', 'crossover', 'swap'], p=[0.6, 0.3, 0.1])
#         if mutation_type == 'local':
#             idx = np.random.randint(0, self.D)
#             if idx < self.num_layers:
#                 mutant.gene[idx] = np.random.randint(0, len(self.OPERATIONS))
#             elif idx < 2*self.num_layers:
#                 mutant.gene[idx] = np.random.randint(0, len(self.KERNELS))
#             else:
#                 mutant.gene[idx] = np.clip(mutant.gene[idx] + np.random.randn() * 0.05, 0, 1)
#         elif mutation_type == 'crossover':
#             if self.num_layers > 2:
#                 start = np.random.randint(0, max(1, self.num_layers - 2))
#                 length = np.random.randint(2, min(5, self.num_layers - start + 1))
#                 other = ArchitectureGene(self.num_layers, self.num_cells)
#                 mutant.gene[start:start+length] = other.gene[start:start+length]
#         elif mutation_type == 'swap':
#             if self.num_layers >= 2:
#                 i, j = np.random.choice(self.num_layers, 2, replace=False)
#                 mutant.gene[[i, j]] = mutant.gene[[j, i]]
#         self.mutation_history.append(mutation_type)
#         return mutant

#     def crossover(self, other: 'ArchitectureGene') -> 'ArchitectureGene':
#         offspring = self.copy()
#         crossover_point = np.random.randint(1, self.D)
#         offspring.gene[crossover_point:] = other.gene[crossover_point:]
#         return offspring

#     def copy(self) -> 'ArchitectureGene':
#         new_gene = ArchitectureGene(self.num_layers, self.num_cells)
#         new_gene.gene = self.gene.copy()
#         return new_gene

#     def to_architecture_dict(self) -> Dict:
#         ops_idx = self.gene[:self.num_layers].astype(int)
#         kernels_idx = self.gene[self.num_layers:2*self.num_layers].astype(int)
#         skip_flags = self.gene[2*self.num_layers:2*self.num_layers+self.num_cells].astype(int)
#         return {
#             'operations': [self.OPERATIONS[int(min(idx, len(self.OPERATIONS)-1))] for idx in ops_idx],
#             'kernels': [self.KERNELS[int(min(idx, len(self.KERNELS)-1))] for idx in kernels_idx],
#             'skip_connections': skip_flags.tolist(),
#             'depth_multiplier': float(np.clip(self.gene[-2], 0.3, 1.5)),
#             'channel_multiplier': float(np.clip(self.gene[-1], 0.3, 1.5)),
#             'num_layers': self.num_layers,
#         }

#     def get_hash(self) -> str:
#         return hashlib.md5(self.gene.tobytes()).hexdigest()

import numpy as np
from typing import Dict
from collections import deque
import hashlib

class ArchitectureGene:
    __slots__ = ('num_layers', 'num_cells', 'D', 'gene', 'mutation_history', '_hash_cache')

    OPERATIONS = ['conv_3x3', 'conv_5x5', 'dw_conv', 'sep_conv', 'avg_pool', 'max_pool', 'skip_connect']
    KERNELS = [1, 3, 5, 7]
    CHANNELS = [16, 32, 64, 128, 256]

    def __init__(self, num_layers: int = 12, num_cells: int = 5):
        self.num_layers = num_layers
        self.num_cells = num_cells
        self.D = num_layers * 3 + num_cells + 2
        self.gene = self._initialize_random()
        self.mutation_history = deque(maxlen=50)
        self._hash_cache = None

    def _initialize_random(self) -> np.ndarray:
        gene = np.zeros(self.D, dtype=np.float32)
        # Reduced bias for wider sampling - increase entropy early
        p = [0.18, 0.18, 0.16, 0.16, 0.12, 0.12, 0.08]  # More uniform, less conv bias
        
        gene[:self.num_layers] = np.random.choice(len(self.OPERATIONS), self.num_layers, p=p)
        gene[self.num_layers:2*self.num_layers] = np.random.randint(0, len(self.KERNELS), self.num_layers)
        
        # Increase skip connection entropy
        skip_count = np.random.randint(0, int(self.num_cells * 0.4) + 1)
        if skip_count > 0:
            skip_indices = np.random.choice(self.num_cells, skip_count, replace=False)
            gene[2*self.num_layers : 2*self.num_layers+self.num_cells][skip_indices] = 1
            
        # Wider multiplier range for more diversity
        gene[-2] = np.random.uniform(0.5, 1.2)
        gene[-1] = np.random.uniform(0.5, 1.2)
        return gene

    def mutate(self, mutation_type: str = 'adaptive', debt_norm: float = 0.0) -> 'ArchitectureGene':
        mutant = self.copy()
        
        # A. Debt-conditioned mutation types
        if mutation_type == 'adaptive':
            if debt_norm > 0.1:
                # High debt: favor cross-layer swaps, kernel changes, skip toggles
                r = np.random.random()
                if r < 0.2: mutation_type = 'local'  # Still some local
                elif r < 0.6: mutation_type = 'crossover'  # Cross-layer
                else: mutation_type = 'swap'  # Swaps
            else:
                # Low debt: local refinements
                r = np.random.random()
                if r < 0.8: mutation_type = 'local'
                elif r < 0.9: mutation_type = 'crossover'
                else: mutation_type = 'swap'

        if mutation_type == 'local':
            idx = np.random.randint(0, self.D)
            if idx < self.num_layers:
                mutant.gene[idx] = np.random.randint(0, len(self.OPERATIONS))
            elif idx < 2*self.num_layers:
                mutant.gene[idx] = np.random.randint(0, len(self.KERNELS))
            else:
                mutant.gene[idx] = np.clip(mutant.gene[idx] + np.random.randn() * 0.05, 0, 1)
        
        elif mutation_type == 'crossover':
            if self.num_layers > 2:
                start = np.random.randint(0, max(1, self.num_layers - 2))
                length = np.random.randint(2, min(5, self.num_layers - start + 1))
                # Create random gene for crossover directly without full object overhead
                other_gene_array = self._initialize_random()
                mutant.gene[start:start+length] = other_gene_array[start:start+length]
        
        elif mutation_type == 'swap':
            if self.num_layers >= 2:
                i, j = np.random.choice(self.num_layers, 2, replace=False)
                mutant.gene[[i, j]] = mutant.gene[[j, i]]
        
        self.mutation_history.append(mutation_type)
        mutant._hash_cache = None
        return mutant

    def crossover(self, other: 'ArchitectureGene') -> 'ArchitectureGene':
        offspring = self.copy()
        crossover_point = np.random.randint(1, self.D)
        offspring.gene[crossover_point:] = other.gene[crossover_point:]
        offspring._hash_cache = None
        return offspring

    def copy(self) -> 'ArchitectureGene':
        new_gene = ArchitectureGene(self.num_layers, self.num_cells)
        new_gene.gene = self.gene.copy()
        # History is technically per-agent evolution, usually empty on copy or copied
        # Keeping deque empty for new separate timeline or copy if needed
        return new_gene

    def to_architecture_dict(self) -> Dict:
        # Optimized casting
        ops_idx = self.gene[:self.num_layers].astype(np.int32)
        kernels_idx = self.gene[self.num_layers:2*self.num_layers].astype(np.int32)
        skip_flags = self.gene[2*self.num_layers:2*self.num_layers+self.num_cells].astype(np.int32)
        
        # Pre-cache lengths
        len_ops = len(self.OPERATIONS) - 1
        len_kers = len(self.KERNELS) - 1
        
        return {
            'operations': [self.OPERATIONS[min(idx, len_ops)] for idx in ops_idx],
            'kernels': [self.KERNELS[min(idx, len_kers)] for idx in kernels_idx],
            'skip_connections': skip_flags.tolist(),
            'depth_multiplier': float(np.clip(self.gene[-2], 0.3, 1.5)),
            'channel_multiplier': float(np.clip(self.gene[-1], 0.3, 1.5)),
            'num_layers': self.num_layers,
        }

    def get_hash(self) -> str:
        if self._hash_cache is None:
            self._hash_cache = hashlib.md5(self.gene.tobytes()).hexdigest()
        return self._hash_cache