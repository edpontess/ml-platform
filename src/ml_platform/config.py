from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingConfig:
    C: float = 1.0
    max_iter: int = 2000
    random_state: int = 42
    validation_size: float = 0.2