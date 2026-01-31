"""
Unsupervised nearest neighbors.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.validation import check_array
from nalyst.learners.neighbors.base import (
    NeighborsBase,
    KNeighborsMixin,
    RadiusNeighborsMixin,
)


class NearestNeighbors(KNeighborsMixin, RadiusNeighborsMixin, NeighborsBase):
    """
    Unsupervised learner for implementing neighbor searches.

    Parameters
    ----------
    n_neighbors : int, default=5
        Number of neighbors to use for k-neighbors queries.
    radius : float, default=1.0
        Range of parameter space for radius-based queries.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm used to compute nearest neighbors.
    leaf_size : int, default=30
        Leaf size passed to tree algorithms.
    metric : str, default="minkowski"
        Distance metric.
    p : int, default=2
        Power parameter for Minkowski metric.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    n_samples_fit_ : int
        Number of samples in the fitted data.

    Examples
    --------
    >>> from nalyst.learners.neighbors import NearestNeighbors
    >>> X = [[0, 0], [1, 1], [2, 2]]
    >>> neigh = NearestNeighbors(n_neighbors=2)
    >>> neigh.train(X)
    NearestNeighbors(n_neighbors=2)
    >>> distances, indices = neigh.kneighbors([[1.5, 1.5]])
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        *,
        radius: float = 1.0,
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        metric: str = "minkowski",
        p: int = 2,
        n_jobs: Optional[int] = None,
    ):
        super().__init__(
            n_neighbors=n_neighbors,
            radius=radius,
            algorithm=algorithm,
            leaf_size=leaf_size,
            metric=metric,
            p=p,
            n_jobs=n_jobs,
        )

    def train(self, X: np.ndarray, y=None) -> "NearestNeighbors":
        """
        Fit the nearest neighbors estimator.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored
            Not used, present for API consistency.

        Returns
        -------
        self : NearestNeighbors
            Fitted estimator.
        """
        X = check_array(X)
        self._train_X = X
        self.n_samples_fit_ = len(X)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Find the K-neighbors of a point.

        This is an alias for kneighbors for API consistency.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Query points.

        Returns
        -------
        neigh_ind : ndarray of shape (n_queries, n_neighbors)
            Indices of neighbors.
        """
        return self.kneighbors(X, return_distance=False)
