"""
Density-based clustering algorithms.

Provides clustering methods that find regions of high density
separated by regions of low density.
"""

from __future__ import annotations

from typing import Optional, Union, Literal

import numpy as np
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner, ClusterMixin
from nalyst.core.validation import (
    check_array,
    check_is_trained,
    check_random_state,
)
from nalyst.core.tags import LearnerTags, TargetTags


class DBSCAN(ClusterMixin, BaseLearner):
    """
    Density-Based Spatial Clustering of Applications with Noise.

    Finds core samples of high density and expands clusters from them.

    Parameters
    ----------
    eps : float, default=0.5
        Maximum distance for two samples to be neighbors.
    min_samples : int, default=5
        Minimum samples in a neighborhood to be a core point.
    metric : str, default="euclidean"
        Distance metric.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm for computing neighbors.
    leaf_size : int, default=30
        Leaf size for tree algorithms.
    p : float, optional
        Power for Minkowski metric.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    core_sample_indices_ : ndarray
        Indices of core samples.
    components_ : ndarray
        Core sample coordinates.
    labels_ : ndarray of shape (n_samples,)
        Cluster labels. -1 indicates noise.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.clustering import DBSCAN
    >>> X = np.array([[1, 2], [2, 2], [2, 3], [8, 7], [8, 8], [25, 80]])
    >>> clustering = DBSCAN(eps=3, min_samples=2)
    >>> clustering.train(X)
    DBSCAN(eps=3, min_samples=2)
    >>> clustering.labels_
    array([0, 0, 0, 1, 1, -1])
    """

    def __init__(
        self,
        eps: float = 0.5,
        *,
        min_samples: int = 5,
        metric: str = "euclidean",
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        p: Optional[float] = None,
        n_jobs: Optional[int] = None,
    ):
        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric
        self.algorithm = algorithm
        self.leaf_size = leaf_size
        self.p = p
        self.n_jobs = n_jobs

    def _compute_neighbors(self, X: np.ndarray) -> list:
        """Compute neighbors for each point within eps distance."""
        if self.metric == "euclidean":
            distances = cdist(X, X, metric="euclidean")
        elif self.metric == "minkowski" and self.p is not None:
            distances = cdist(X, X, metric="minkowski", p=self.p)
        else:
            distances = cdist(X, X, metric=self.metric)

        neighbors = []
        for i in range(len(X)):
            neighbor_indices = np.where(distances[i] <= self.eps)[0]
            neighbors.append(neighbor_indices)

        return neighbors

    def train(self, X: np.ndarray, y=None) -> "DBSCAN":
        """
        Perform DBSCAN clustering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : DBSCAN
        """
        X = check_array(X)
        n_samples = X.shape[0]
        self.n_features_in_ = X.shape[1]

        # Compute neighborhoods
        neighbors = self._compute_neighbors(X)

        # Identify core points
        n_neighbors = np.array([len(n) for n in neighbors])
        is_core = n_neighbors >= self.min_samples

        # Initialize labels
        labels = np.full(n_samples, -1, dtype=int)
        cluster_id = 0

        # Iterate through core points
        for i in range(n_samples):
            if labels[i] != -1:
                continue
            if not is_core[i]:
                continue

            # Start new cluster
            labels[i] = cluster_id

            # Expand cluster
            seed_set = set(neighbors[i])
            seed_set.discard(i)

            while seed_set:
                q = seed_set.pop()

                if labels[q] == -1:
                    labels[q] = cluster_id

                    if is_core[q]:
                        for neighbor in neighbors[q]:
                            if labels[neighbor] == -1:
                                seed_set.add(neighbor)

            cluster_id += 1

        # Handle border points (non-core points in eps of core)
        for i in range(n_samples):
            if labels[i] == -1 and not is_core[i]:
                for neighbor in neighbors[i]:
                    if is_core[neighbor] and labels[neighbor] != -1:
                        labels[i] = labels[neighbor]
                        break

        self.labels_ = labels
        self.core_sample_indices_ = np.where(is_core)[0]
        self.components_ = X[self.core_sample_indices_]

        return self

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Perform clustering and return labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        labels : ndarray of shape (n_samples,)
            Cluster labels.
        """
        return self.train(X, y).labels_

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="clusterer",
            target_tags=TargetTags(required=False),
        )


class OPTICS(ClusterMixin, BaseLearner):
    """
    Ordering Points To Identify the Clustering Structure.

    Similar to DBSCAN but handles varying densities and
    provides a reachability plot.

    Parameters
    ----------
    min_samples : int or float, default=5
        Minimum samples for core point.
    max_eps : float, default=np.inf
        Maximum distance for neighborhood.
    metric : str, default="euclidean"
        Distance metric.
    p : float, optional
        Power for Minkowski metric.
    cluster_method : {"xi", "dbscan"}, default="xi"
        Method for extracting clusters.
    eps : float, optional
        Maximum distance for DBSCAN extraction.
    xi : float, default=0.05
        Minimum steepness for xi method.
    predecessor_correction : bool, default=True
        Correct clusters using predecessor.
    min_cluster_size : int or float, optional
        Minimum cluster size.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm for computing neighbors.
    leaf_size : int, default=30
        Leaf size for tree algorithms.
    memory : optional
        Caching backend.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    labels_ : ndarray of shape (n_samples,)
        Cluster labels. -1 indicates noise.
    reachability_ : ndarray of shape (n_samples,)
        Reachability distances.
    ordering_ : ndarray of shape (n_samples,)
        Sample indices in cluster order.
    core_distances_ : ndarray of shape (n_samples,)
        Distance to min_samples-th neighbor.
    predecessor_ : ndarray of shape (n_samples,)
        Point that set reachability distance.
    cluster_hierarchy_ : ndarray
        Cluster hierarchy for xi method.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.clustering import OPTICS
    >>> X = np.array([[1, 2], [2, 5], [3, 6], [8, 7], [8, 8], [7, 3]])
    >>> clustering = OPTICS(min_samples=2)
    >>> clustering.train(X)
    OPTICS(min_samples=2)
    >>> clustering.labels_
    array([...])
    """

    def __init__(
        self,
        *,
        min_samples: Union[int, float] = 5,
        max_eps: float = np.inf,
        metric: str = "euclidean",
        p: Optional[float] = None,
        cluster_method: Literal["xi", "dbscan"] = "xi",
        eps: Optional[float] = None,
        xi: float = 0.05,
        predecessor_correction: bool = True,
        min_cluster_size: Optional[Union[int, float]] = None,
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        memory=None,
        n_jobs: Optional[int] = None,
    ):
        self.min_samples = min_samples
        self.max_eps = max_eps
        self.metric = metric
        self.p = p
        self.cluster_method = cluster_method
        self.eps = eps
        self.xi = xi
        self.predecessor_correction = predecessor_correction
        self.min_cluster_size = min_cluster_size
        self.algorithm = algorithm
        self.leaf_size = leaf_size
        self.memory = memory
        self.n_jobs = n_jobs

    def _compute_core_distances(
        self,
        X: np.ndarray,
        min_samples: int,
    ) -> np.ndarray:
        """Compute core distance for each point."""
        if self.metric == "euclidean":
            distances = cdist(X, X, metric="euclidean")
        elif self.metric == "minkowski" and self.p is not None:
            distances = cdist(X, X, metric="minkowski", p=self.p)
        else:
            distances = cdist(X, X, metric=self.metric)

        # Sort distances and get min_samples-th neighbor distance
        sorted_distances = np.sort(distances, axis=1)
        core_distances = sorted_distances[:, min_samples - 1]

        return core_distances, distances

    def train(self, X: np.ndarray, y=None) -> "OPTICS":
        """
        Perform OPTICS ordering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : OPTICS
        """
        X = check_array(X)
        n_samples = X.shape[0]
        self.n_features_in_ = X.shape[1]

        # Determine min_samples
        if isinstance(self.min_samples, float):
            min_samples = max(1, int(self.min_samples * n_samples))
        else:
            min_samples = self.min_samples

        # Compute core distances
        core_distances, all_distances = self._compute_core_distances(X, min_samples)

        # Initialize
        reachability = np.full(n_samples, np.inf)
        predecessor = np.full(n_samples, -1)
        processed = np.zeros(n_samples, dtype=bool)
        ordering = []

        # Process all points
        while len(ordering) < n_samples:
            # Get unprocessed point with smallest reachability
            unprocessed = ~processed
            if len(ordering) == 0:
                # Start with first unprocessed point
                current = np.where(unprocessed)[0][0]
            else:
                # Get point with minimum reachability
                candidates = np.where(unprocessed)[0]
                current = candidates[np.argmin(reachability[candidates])]

            ordering.append(current)
            processed[current] = True

            # Update reachability distances
            if core_distances[current] <= self.max_eps:
                for neighbor in range(n_samples):
                    if processed[neighbor]:
                        continue

                    # Compute reachability distance
                    new_reach = max(
                        core_distances[current],
                        all_distances[current, neighbor]
                    )

                    if new_reach < reachability[neighbor]:
                        reachability[neighbor] = new_reach
                        predecessor[neighbor] = current

        self.ordering_ = np.array(ordering)
        self.reachability_ = reachability
        self.core_distances_ = core_distances
        self.predecessor_ = predecessor

        # Extract clusters
        if self.cluster_method == "dbscan":
            self._extract_dbscan()
        else:
            self._extract_xi()

        return self

    def _extract_dbscan(self):
        """Extract clusters using DBSCAN method."""
        if self.eps is None:
            eps = self.max_eps
        else:
            eps = self.eps

        labels = np.full(len(self.ordering_), -1)
        cluster_id = 0

        for i, idx in enumerate(self.ordering_):
            if self.reachability_[idx] > eps:
                if self.core_distances_[idx] <= eps:
                    cluster_id += 1
                    labels[idx] = cluster_id
            else:
                labels[idx] = cluster_id

        self.labels_ = labels

    def _extract_xi(self):
        """Extract clusters using xi method."""
        n_samples = len(self.ordering_)

        # Simplified xi extraction
        labels = np.full(n_samples, -1)

        # Use reachability threshold
        threshold = np.percentile(
            self.reachability_[self.reachability_ < np.inf],
            (1 - self.xi) * 100
        ) if np.any(self.reachability_ < np.inf) else np.inf

        cluster_id = 0
        in_cluster = False

        for i, idx in enumerate(self.ordering_):
            reach = self.reachability_[idx]

            if reach <= threshold:
                if not in_cluster:
                    cluster_id += 1
                    in_cluster = True
                labels[idx] = cluster_id - 1
            else:
                in_cluster = False

        self.labels_ = labels
        self.cluster_hierarchy_ = None  # Simplified

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Perform OPTICS and return labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        labels : ndarray of shape (n_samples,)
            Cluster labels.
        """
        return self.train(X, y).labels_

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="clusterer",
            target_tags=TargetTags(required=False),
        )
