"""
Dimensionality Reduction algorithms for Nalyst.

This module provides various matrix decomposition and
dimensionality reduction techniques.
"""

from nalyst.reduction.pca import (
    PrincipalComponentAnalysis,
    IncrementalPCA,
    KernelPCA,
    SparsePCA,
)
from nalyst.reduction.svd import TruncatedSVD
from nalyst.reduction.nmf import NonNegativeMatrixFactorization
from nalyst.reduction.ica import FastICA
from nalyst.reduction.factor import FactorAnalysis
from nalyst.reduction.lda import LatentDirichletAllocation

__all__ = [
    # PCA variants
    "PrincipalComponentAnalysis",
    "IncrementalPCA",
    "KernelPCA",
    "SparsePCA",
    # SVD
    "TruncatedSVD",
    # Matrix factorization
    "NonNegativeMatrixFactorization",
    # ICA
    "FastICA",
    # Factor Analysis
    "FactorAnalysis",
    # Topic modeling
    "LatentDirichletAllocation",
]
