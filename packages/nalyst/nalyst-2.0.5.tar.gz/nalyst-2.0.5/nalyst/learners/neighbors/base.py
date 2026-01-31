"""
Base classes for nearest neighbors algorithms.
"""

from __future__ import annotations

from typing import Optional, Literal, Tuple, Union
from abc import abstractmethod

import numpy as np
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


def _compute_distances(
    X: np.ndarray,
    Y: np.ndarray,
    metric: str = "euclidean",
    **metric_params,
) -> np.ndarray:
    """
    Compute pairwise distances between X and Y.

    Parameters
    ----------
    X : ndarray of shape (n_samples_X, n_features)
        First set of points.
    Y : ndarray of shape (n_samples_Y, n_features)
        Second set of points.
    metric : str, default="euclidean"
        Distance metric to use.

    Returns
    -------
    distances : ndarray of shape (n_samples_X, n_samples_Y)
        Pairwise distances.
    """
    if metric == "euclidean":
        # Efficient euclidean distance computation
        X_sq = np.sum(X ** 2, axis=1).reshape(-1, 1)
        Y_sq = np.sum(Y ** 2, axis=1).reshape(1, -1)
        distances = X_sq + Y_sq - 2 * np.dot(X, Y.T)
        distances = np.maximum(distances, 0)  # Numerical stability
        return np.sqrt(distances)
    elif metric == "manhattan":
        return cdist(X, Y, metric="cityblock")
    elif metric == "chebyshev":
        return cdist(X, Y, metric="chebyshev")
    elif metric == "minkowski":
        p = metric_params.get("p", 2)
        return cdist(X, Y, metric="minkowski", p=p)
    elif metric == "cosine":
        X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-10)
        Y_norm = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-10)
        similarity = np.dot(X_norm, Y_norm.T)
        return 1 - similarity
    else:
        return cdist(X, Y, metric=metric)


class NeighborsBase(BaseLearner):
    """
    Base class for nearest neighbors algorithms.

    Parameters
    ----------
    n_neighbors : int, default=5
        Number of neighbors to use.
    radius : float, default=1.0
        Range of parameter space for radius queries.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm used to compute nearest neighbors.
    leaf_size : int, default=30
        Leaf size passed to tree algorithms.
    metric : str, default="euclidean"
        Distance metric.
    p : int, default=2
        Power parameter for Minkowski metric.
    n_jobs : int, optional
        Number of parallel jobs.
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        *,
        radius: float = 1.0,
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        metric: str = "euclidean",
        p: int = 2,
        n_jobs: Optional[int] = None,
    ):
        self.n_neighbors = n_neighbors
        self.radius = radius
        self.algorithm = algorithm
        self.leaf_size = leaf_size
        self.metric = metric
        self.p = p
        self.n_jobs = n_jobs

    def _validate_data(self, X: np.ndarray, y: Optional[np.ndarray] = None):
        """Validate input data."""
        X = check_array(X)
        if y is not None:
            y = np.asarray(y)
            if len(X) != len(y):
                raise ValueError("X and y must have the same number of samples")
        return X, y

    def _kneighbors(
        self,
        X: np.ndarray,
        n_neighbors: Optional[int] = None,
        return_distance: bool = True,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Find the K-neighbors of a point.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Query points.
        n_neighbors : int, optional
            Number of neighbors. Uses self.n_neighbors if None.
        return_distance : bool, default=True
            Whether to return distances.

        Returns
        -------
        neigh_dist : ndarray of shape (n_queries, n_neighbors)
            Distances to neighbors (if return_distance=True).
        neigh_ind : ndarray of shape (n_queries, n_neighbors)
            Indices of neighbors.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        if n_neighbors is None:
            n_neighbors = self.n_neighbors

        # Compute distances
        distances = _compute_distances(X, self._train_X, self.metric, p=self.p)

        # Get k nearest neighbors
        neigh_ind = np.argpartition(distances, n_neighbors - 1, axis=1)[:, :n_neighbors]

        # Sort by distance
        row_idx = np.arange(len(X))[:, np.newaxis]
        neigh_dist = distances[row_idx, neigh_ind]
        sort_idx = np.argsort(neigh_dist, axis=1)
        neigh_ind = neigh_ind[row_idx, sort_idx]
        neigh_dist = neigh_dist[row_idx, sort_idx]

        if return_distance:
            return neigh_dist, neigh_ind
        return neigh_ind

    def _radius_neighbors(
        self,
        X: np.ndarray,
        radius: Optional[float] = None,
        return_distance: bool = True,
        sort_results: bool = False,
    ):
        """
        Find all neighbors within a given radius.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Query points.
        radius : float, optional
            Limiting radius. Uses self.radius if None.
        return_distance : bool, default=True
            Whether to return distances.
        sort_results : bool, default=False
            Whether to sort by distance.

        Returns
        -------
        neigh_dist : list of ndarrays
            Distances to neighbors (if return_distance=True).
        neigh_ind : list of ndarrays
            Indices of neighbors.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        if radius is None:
            radius = self.radius

        # Compute distances
        distances = _compute_distances(X, self._train_X, self.metric, p=self.p)

        neigh_ind = []
        neigh_dist = []

        for i in range(len(X)):
            mask = distances[i] <= radius
            indices = np.where(mask)[0]
            dists = distances[i, mask]

            if sort_results:
                sort_idx = np.argsort(dists)
                indices = indices[sort_idx]
                dists = dists[sort_idx]

            neigh_ind.append(indices)
            neigh_dist.append(dists)

        if return_distance:
            return neigh_dist, neigh_ind
        return neigh_ind


class KNeighborsMixin:
    """Mixin for K-Neighbors based methods."""

    def kneighbors(
        self,
        X: Optional[np.ndarray] = None,
        n_neighbors: Optional[int] = None,
        return_distance: bool = True,
    ):
        """
        Find the K-neighbors of a point.

        Parameters
        ----------
        X : ndarray, optional
            Query points. Uses training data if None.
        n_neighbors : int, optional
            Number of neighbors.
        return_distance : bool, default=True
            Whether to return distances.

        Returns
        -------
        neigh_dist : ndarray
            Distances (if return_distance=True).
        neigh_ind : ndarray
            Indices.
        """
        if X is None:
            X = self._train_X
        return self._kneighbors(X, n_neighbors, return_distance)

    def kneighbors_graph(
        self,
        X: Optional[np.ndarray] = None,
        n_neighbors: Optional[int] = None,
        mode: Literal["connectivity", "distance"] = "connectivity",
    ) -> np.ndarray:
        """
        Compute the weighted graph of k-Neighbors.

        Parameters
        ----------
        X : ndarray, optional
            Query points.
        n_neighbors : int, optional
            Number of neighbors.
        mode : {"connectivity", "distance"}, default="connectivity"
            Type of returned matrix.

        Returns
        -------
        A : ndarray of shape (n_queries, n_samples_fit)
            Sparse adjacency matrix.
        """
        if X is None:
            X = self._train_X

        n_neighbors = n_neighbors or self.n_neighbors
        neigh_dist, neigh_ind = self._kneighbors(X, n_neighbors, return_distance=True)

        n_queries = len(X)
        n_samples_fit = len(self._train_X)

        # Build adjacency matrix
        A = np.zeros((n_queries, n_samples_fit))

        for i in range(n_queries):
            if mode == "connectivity":
                A[i, neigh_ind[i]] = 1
            else:  # distance
                A[i, neigh_ind[i]] = neigh_dist[i]

        return A


class RadiusNeighborsMixin:
    """Mixin for radius-based neighbor methods."""

    def radius_neighbors(
        self,
        X: Optional[np.ndarray] = None,
        radius: Optional[float] = None,
        return_distance: bool = True,
        sort_results: bool = False,
    ):
        """
        Find all neighbors within a radius.

        Parameters
        ----------
        X : ndarray, optional
            Query points.
        radius : float, optional
            Limiting radius.
        return_distance : bool, default=True
            Whether to return distances.
        sort_results : bool, default=False
            Whether to sort by distance.

        Returns
        -------
        neigh_dist : list of ndarrays
            Distances (if return_distance=True).
        neigh_ind : list of ndarrays
            Indices.
        """
        if X is None:
            X = self._train_X
        return self._radius_neighbors(X, radius, return_distance, sort_results)

    def radius_neighbors_graph(
        self,
        X: Optional[np.ndarray] = None,
        radius: Optional[float] = None,
        mode: Literal["connectivity", "distance"] = "connectivity",
        sort_results: bool = False,
    ) -> np.ndarray:
        """
        Compute the weighted graph of neighbors within a radius.

        Parameters
        ----------
        X : ndarray, optional
            Query points.
        radius : float, optional
            Limiting radius.
        mode : {"connectivity", "distance"}, default="connectivity"
            Type of returned matrix.
        sort_results : bool, default=False
            Whether to sort by distance.

        Returns
        -------
        A : ndarray
            Adjacency matrix.
        """
        if X is None:
            X = self._train_X

        radius = radius or self.radius
        result = self._radius_neighbors(X, radius, return_distance=True, sort_results=sort_results)
        neigh_dist, neigh_ind = result

        n_queries = len(X)
        n_samples_fit = len(self._train_X)

        A = np.zeros((n_queries, n_samples_fit))

        for i in range(n_queries):
            if mode == "connectivity":
                A[i, neigh_ind[i]] = 1
            else:
                A[i, neigh_ind[i]] = neigh_dist[i]

        return A
