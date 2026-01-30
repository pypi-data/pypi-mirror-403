# OMNIMIND Training Package
# High-performance model training, distillation, and fine-tuning

from .trainer import Trainer, TrainingConfig
from .distillation import Distiller, DistillationConfig
from .moe_trainer import train_moe_ssm
from .fast_lora import apply_fast_lora
from .finetune import FineTuner, FineTuneConfig

__all__ = [
    "Trainer",
    "TrainingConfig",
    "Distiller",
    "DistillationConfig",
    "train_moe_ssm",
    "apply_fast_lora",
    "FineTuner",
    "FineTuneConfig",
]
