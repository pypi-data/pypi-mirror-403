"""
Manifold Learning algorithms for Nalyst.

This module provides various non-linear dimensionality
reduction techniques.
"""

from nalyst.manifold.tsne import TSNE
from nalyst.manifold.isomap import Isomap
from nalyst.manifold.mds import MDS
from nalyst.manifold.lle import LocallyLinearEmbedding
from nalyst.manifold.spectral import SpectralEmbedding

__all__ = [
    "TSNE",
    "Isomap",
    "MDS",
    "LocallyLinearEmbedding",
    "SpectralEmbedding",
]
