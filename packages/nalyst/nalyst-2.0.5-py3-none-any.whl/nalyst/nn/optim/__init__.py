"""
Optimization algorithms and learning rate schedulers.
"""

from nalyst.nn.optim.optimizer import Optimizer
from nalyst.nn.optim.sgd import SGD
from nalyst.nn.optim.adam import Adam, AdamW
from nalyst.nn.optim.rmsprop import RMSprop
from nalyst.nn.optim.adagrad import Adagrad
from nalyst.nn.optim.lr_scheduler import (
    LRScheduler,
    StepLR,
    MultiStepLR,
    ExponentialLR,
    CosineAnnealingLR,
    ReduceLROnPlateau,
    WarmupLR,
    OneCycleLR,
)

__all__ = [
    # Base
    "Optimizer",
    # Optimizers
    "SGD",
    "Adam",
    "AdamW",
    "RMSprop",
    "Adagrad",
    # Schedulers
    "LRScheduler",
    "StepLR",
    "MultiStepLR",
    "ExponentialLR",
    "CosineAnnealingLR",
    "ReduceLROnPlateau",
    "WarmupLR",
    "OneCycleLR",
]
