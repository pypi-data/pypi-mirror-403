from typing import Dict, Optional, Tuple

class EvaluationCache:
    def __init__(self, max_size: int = 10000):
        self.cache: Dict[str, Tuple[float, Dict]] = {}
        self.access_count: Dict[str, int] = {}
        self.max_size = max_size

    def get(self, arch_hash: str) -> Optional[Tuple[float, Dict]]:
        if arch_hash in self.cache:
            self.access_count[arch_hash] += 1
            return self.cache[arch_hash]
        return None

    def put(self, arch_hash: str, result: Tuple[float, Dict]) -> None:
        if len(self.cache) >= self.max_size:
            lru_key = min(self.access_count, key=self.access_count.get)
            del self.cache[lru_key]
            del self.access_count[lru_key]
        self.cache[arch_hash] = result
        self.access_count[arch_hash] = 1

    def clear(self) -> None:
        self.cache.clear()
        self.access_count.clear()
