# Quickstart

```python
from dpo import DPO_NAS_V2, DPO_ConfigV2

config = DPO_ConfigV2.fast()
optimizer = DPO_NAS_V2(config)
results = optimizer.optimize()
print(results['best_fitness'])
```
