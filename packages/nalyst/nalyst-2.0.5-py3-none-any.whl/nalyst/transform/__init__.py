"""
Data transformation and preprocessing for Nalyst.

This module provides transformers for scaling, encoding,
imputation, and feature extraction.
"""

from nalyst.transform.scaling import (
    StandardScaler,
    MinMaxScaler,
    MaxAbsScaler,
    RobustScaler,
    Normalizer,
)
from nalyst.transform.encoding import (
    LabelEncoder,
    OneHotEncoder,
    OrdinalEncoder,
)
from nalyst.transform.imputation import (
    SimpleImputer,
    KNNImputer,
)
from nalyst.transform.discretization import (
    KBinsDiscretizer,
    Binarizer,
)

__all__ = [
    # Scaling
    "StandardScaler",
    "MinMaxScaler",
    "MaxAbsScaler",
    "RobustScaler",
    "Normalizer",
    # Encoding
    "LabelEncoder",
    "OneHotEncoder",
    "OrdinalEncoder",
    # Imputation
    "SimpleImputer",
    "KNNImputer",
    # Discretization
    "KBinsDiscretizer",
    "Binarizer",
]
