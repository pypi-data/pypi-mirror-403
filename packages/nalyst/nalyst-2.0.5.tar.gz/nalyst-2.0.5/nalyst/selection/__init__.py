"""
Feature Selection algorithms for Nalyst.

This module provides various feature selection methods.
"""

from nalyst.selection.univariate import (
    SelectKBest,
    SelectPercentile,
    SelectFpr,
    SelectFdr,
    SelectFwe,
    GenericUnivariateSelect,
)
from nalyst.selection.variance import VarianceThreshold
from nalyst.selection.rfe import RFE, RFECV
from nalyst.selection.model_based import SelectFromModel
from nalyst.selection.sequential import SequentialFeatureSelector
from nalyst.selection.score_functions import (
    chi2,
    f_classif,
    f_regression,
    mutual_info_classif,
    mutual_info_regression,
)

__all__ = [
    # Univariate
    "SelectKBest",
    "SelectPercentile",
    "SelectFpr",
    "SelectFdr",
    "SelectFwe",
    "GenericUnivariateSelect",
    # Variance
    "VarianceThreshold",
    # RFE
    "RFE",
    "RFECV",
    # Model-based
    "SelectFromModel",
    # Sequential
    "SequentialFeatureSelector",
    # Score functions
    "chi2",
    "f_classif",
    "f_regression",
    "mutual_info_classif",
    "mutual_info_regression",
]
