"""
Outlier detection using nearest neighbors.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, OutlierMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.learners.neighbors.base import _compute_distances


class LocalOutlierFactor(OutlierMixin, BaseLearner):
    """
    Local Outlier Factor (LOF) for outlier detection.

    The anomaly score of each sample is called Local Outlier Factor.
    It measures the local deviation of density of a given sample with
    respect to its neighbors.

    Parameters
    ----------
    n_neighbors : int, default=20
        Number of neighbors to use for k-neighbors queries.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm used to compute nearest neighbors.
    leaf_size : int, default=30
        Leaf size for tree algorithms.
    metric : str, default="minkowski"
        Distance metric.
    p : int, default=2
        Power parameter for Minkowski metric.
    contamination : float or "auto", default="auto"
        Proportion of outliers in the data set.
    novelty : bool, default=False
        If True, enables predict/score on new unseen data.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    negative_outlier_factor_ : ndarray of shape (n_samples,)
        Opposite of the LOF of the training samples.
    n_neighbors_ : int
        Actual number of neighbors used.
    offset_ : float
        Offset used to obtain binary labels from scores.

    Examples
    --------
    >>> from nalyst.learners.neighbors import LocalOutlierFactor
    >>> X = [[-1.1], [0.2], [101.1], [0.3]]
    >>> clf = LocalOutlierFactor(n_neighbors=2)
    >>> clf.train_infer(X)
    array([ 1,  1, -1,  1])
    """

    def __init__(
        self,
        n_neighbors: int = 20,
        *,
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        metric: str = "minkowski",
        p: int = 2,
        contamination: float = "auto",
        novelty: bool = False,
        n_jobs: Optional[int] = None,
    ):
        self.n_neighbors = n_neighbors
        self.algorithm = algorithm
        self.leaf_size = leaf_size
        self.metric = metric
        self.p = p
        self.contamination = contamination
        self.novelty = novelty
        self.n_jobs = n_jobs

    def train(self, X: np.ndarray, y=None) -> "LocalOutlierFactor":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored
            Not used.

        Returns
        -------
        self : LocalOutlierFactor
            Fitted estimator.
        """
        X = check_array(X)
        self._train_X = X

        n_samples = len(X)
        self.n_neighbors_ = min(self.n_neighbors, n_samples - 1)

        # Compute k-distances and k-neighbors
        distances = _compute_distances(X, X, self.metric, p=self.p)

        # Set diagonal to infinity to exclude self
        np.fill_diagonal(distances, np.inf)

        # Get k nearest neighbors (indices sorted by distance)
        self._neighbors_indices = np.argpartition(
            distances, self.n_neighbors_, axis=1
        )[:, :self.n_neighbors_]

        # Get actual distances to k neighbors
        row_idx = np.arange(n_samples)[:, np.newaxis]
        self._distances_k = distances[row_idx, self._neighbors_indices]

        # k-distance: distance to k-th neighbor
        self._k_distances = np.max(self._distances_k, axis=1)

        # Compute reachability distances
        # reach-dist_k(A, B) = max(k-distance(B), d(A, B))

        # Compute local reachability density (LRD)
        self._lrd = self._compute_lrd(X)

        # Compute LOF
        self.negative_outlier_factor_ = -self._compute_lof()

        # Set offset
        if self.contamination == "auto":
            self.offset_ = -1.5
        else:
            self.offset_ = np.percentile(
                self.negative_outlier_factor_,
                100.0 * self.contamination
            )

        return self

    def _compute_lrd(self, X: np.ndarray) -> np.ndarray:
        """Compute local reachability density."""
        n_samples = len(X)
        lrd = np.zeros(n_samples)

        for i in range(n_samples):
            neighbors = self._neighbors_indices[i]
            reach_dists = np.maximum(
                self._distances_k[i],
                self._k_distances[neighbors]
            )
            lrd[i] = 1.0 / (np.mean(reach_dists) + 1e-10)

        return lrd

    def _compute_lof(self) -> np.ndarray:
        """Compute local outlier factor."""
        n_samples = len(self._train_X)
        lof = np.zeros(n_samples)

        for i in range(n_samples):
            neighbors = self._neighbors_indices[i]
            lof[i] = np.mean(self._lrd[neighbors]) / (self._lrd[i] + 1e-10)

        return lof

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit the model and predict labels.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored
            Not used.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Labels: 1 for inliers, -1 for outliers.
        """
        self.train(X)

        is_inlier = self.negative_outlier_factor_ >= self.offset_
        return np.where(is_inlier, 1, -1)

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict labels for new data (only if novelty=True).

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            New data.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Labels: 1 for inliers, -1 for outliers.
        """
        if not self.novelty:
            raise ValueError(
                "infer is not available when novelty=False. "
                "Use train_infer for outlier detection on training data."
            )

        check_is_trained(self, "_train_X")
        X = check_array(X)

        scores = self.score_samples(X)
        is_inlier = scores >= self.offset_

        return np.where(is_inlier, 1, -1)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the (opposite of) LOF for samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Query samples.

        Returns
        -------
        scores : ndarray of shape (n_samples,)
            Opposite of LOF (higher = more normal).
        """
        if not self.novelty:
            raise ValueError(
                "score_samples is not available when novelty=False."
            )

        check_is_trained(self, "_train_X")
        X = check_array(X)

        # Compute distances to training data
        distances = _compute_distances(X, self._train_X, self.metric, p=self.p)

        n_queries = len(X)
        lof_scores = np.zeros(n_queries)

        for i in range(n_queries):
            # Get k nearest neighbors
            neigh_idx = np.argpartition(distances[i], self.n_neighbors_)[:self.n_neighbors_]
            neigh_dist = distances[i, neigh_idx]

            # Compute reachability distances
            reach_dists = np.maximum(neigh_dist, self._k_distances[neigh_idx])

            # Compute LRD for query point
            lrd_query = 1.0 / (np.mean(reach_dists) + 1e-10)

            # Compute LOF
            lof_scores[i] = np.mean(self._lrd[neigh_idx]) / (lrd_query + 1e-10)

        return -lof_scores

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Shifted opposite of LOF for threshold-based decision.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Query samples.

        Returns
        -------
        scores : ndarray of shape (n_samples,)
            Shifted scores (negative = outlier).
        """
        return self.score_samples(X) - self.offset_
