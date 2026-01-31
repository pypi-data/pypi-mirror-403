"""
Model Inspection tools for Nalyst.
"""

from nalyst.inspection.importance import (
    permutation_importance,
)
from nalyst.inspection.partial_dependence import (
    partial_dependence,
    PartialDependenceDisplay,
)

__all__ = [
    "permutation_importance",
    "partial_dependence",
    "PartialDependenceDisplay",
]
