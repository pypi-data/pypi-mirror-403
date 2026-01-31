"""
Semi-supervised learning algorithms for Nalyst.
"""

from nalyst.semi_supervised.label_propagation import (
    LabelPropagation,
    LabelSpreading,
)
from nalyst.semi_supervised.self_training import SelfTrainingClassifier

__all__ = [
    "LabelPropagation",
    "LabelSpreading",
    "SelfTrainingClassifier",
]
