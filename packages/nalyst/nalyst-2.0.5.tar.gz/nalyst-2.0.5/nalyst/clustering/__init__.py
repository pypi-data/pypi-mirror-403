"""
Clustering algorithms for Nalyst.

This module provides unsupervised clustering methods for
grouping similar data points together.
"""

from nalyst.clustering.kmeans import KMeansClustering, MiniBatchKMeans
from nalyst.clustering.hierarchical import AgglomerativeClustering
from nalyst.clustering.density import DBSCAN, OPTICS
from nalyst.clustering.spectral import SpectralClustering
from nalyst.clustering.extra import MeanShift, AffinityPropagation, BIRCH

# Alias for convenience
KMeans = KMeansClustering

__all__ = [
    "KMeansClustering",
    "KMeans",
    "MiniBatchKMeans",
    "AgglomerativeClustering",
    "DBSCAN",
    "OPTICS",
    "SpectralClustering",
    "MeanShift",
    "AffinityPropagation",
    "BIRCH",
]
