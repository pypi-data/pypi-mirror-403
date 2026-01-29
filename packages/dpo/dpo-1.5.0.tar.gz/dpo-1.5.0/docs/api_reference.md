# API Reference

## dpo.core.config

- DPO_ConfigV2: Configuration dataclass with presets `fast()`, `balanced()`, `thorough()`.

## dpo.core.agent

- SearchAgentV2: NAS search agent with `gene`, `fitness`, `metrics`.

## dpo.architecture.gene

- ArchitectureGeneV2: Architecture encoding, mutation, crossover, hashing.

## dpo.evaluation

- ZeroShotEstimatorV2
- SurrogateEstimatorV2
- EnsembleEstimator

## dpo.constraints.handler

- AdvancedConstraintHandler: Adaptive penalty computation and validation.

## dpo.core.optimizer

- DPO_NAS_V2: Main optimizer with `optimize()`.
