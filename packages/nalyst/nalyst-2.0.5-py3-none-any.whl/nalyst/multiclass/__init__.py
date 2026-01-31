"""
Multiclass classification strategies for Nalyst.
"""

from nalyst.multiclass.ovr import OneVsRestClassifier
from nalyst.multiclass.ovo import OneVsOneClassifier
from nalyst.multiclass.output_code import OutputCodeClassifier

__all__ = [
    "OneVsRestClassifier",
    "OneVsOneClassifier",
    "OutputCodeClassifier",
]
