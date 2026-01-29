# from dataclasses import dataclass, field
# from typing import Dict
# from ..architecture.gene import ArchitectureGene

# @dataclass
# class SearchAgent:
#     gene: ArchitectureGene
#     fitness: float = float('inf')
#     metrics: Dict = field(default_factory=dict)
#     island_id: int = 0
#     age: int = 0
#     improvements: int = 0

#     def __lt__(self, other: 'SearchAgent'):
#         return self.fitness < other.fitness

#     def to_dict(self) -> Dict:
#         return {
#             'fitness': self.fitness,
#             'metrics': self.metrics,
#             'island_id': self.island_id,
#             'age': self.age,
#             'improvements': self.improvements,
#             'architecture': self.gene.to_architecture_dict(),
#         }


from dataclasses import dataclass, field
from typing import Dict
from ..architecture.gene import ArchitectureGene

@dataclass
class SearchAgent:
    # __slots__ optimization drastically reduces memory overhead for populations
    __slots__ = ('gene', 'fitness', 'metrics', 'island_id', 'age', 'improvements')
    
    gene: ArchitectureGene
    fitness: float
    metrics: Dict
    island_id: int
    age: int
    improvements: int

    def __init__(self, gene: ArchitectureGene, fitness: float = float('inf'), 
                 metrics: Dict = None, island_id: int = 0, age: int = 0, improvements: int = 0):
        self.gene = gene
        self.fitness = fitness
        self.metrics = metrics if metrics is not None else {}
        self.island_id = island_id
        self.age = age
        self.improvements = improvements

    def __lt__(self, other: 'SearchAgent'):
        return self.fitness < other.fitness

    def to_dict(self) -> Dict:
        return {
            'fitness': self.fitness,
            'metrics': self.metrics,
            'island_id': self.island_id,
            'age': self.age,
            'improvements': self.improvements,
            'architecture': self.gene.to_architecture_dict(),
        }