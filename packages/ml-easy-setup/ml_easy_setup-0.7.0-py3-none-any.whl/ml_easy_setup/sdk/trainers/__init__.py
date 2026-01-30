"""SDK 训练器模块"""

from .auto import (
    AutoTrainer,
    TrainerConfig,
    TrainingHistory,
    fit,
    accuracy_score,
)

__all__ = [
    "AutoTrainer",
    "TrainerConfig",
    "TrainingHistory",
    "fit",
    "accuracy_score",
]
