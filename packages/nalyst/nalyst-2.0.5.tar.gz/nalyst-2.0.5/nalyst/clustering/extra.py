"""
Additional clustering algorithms.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class MeanShift(BaseLearner):
    """
    Mean Shift clustering.

    Parameters
    ----------
    bandwidth : float, optional
        Bandwidth for the kernel. If None, estimated from data.
    seeds : ndarray, optional
        Initial seed points.
    bin_seeding : bool, default=False
        Use binning to speed up seeding.
    min_bin_freq : int, default=1
        Minimum frequency for a bin.
    cluster_all : bool, default=True
        Whether to cluster all points or only seeds.
    max_iter : int, default=300
        Maximum iterations.

    Attributes
    ----------
    cluster_centers_ : ndarray of shape (n_clusters, n_features)
        Cluster centers.
    labels_ : ndarray of shape (n_samples,)
        Cluster labels.

    Examples
    --------
    >>> from nalyst.clustering import MeanShift
    >>> ms = MeanShift(bandwidth=0.5)
    >>> ms.train(X)
    >>> labels = ms.labels_
    """

    def __init__(
        self,
        bandwidth: Optional[float] = None,
        seeds: Optional[np.ndarray] = None,
        bin_seeding: bool = False,
        min_bin_freq: int = 1,
        cluster_all: bool = True,
        max_iter: int = 300,
    ):
        self.bandwidth = bandwidth
        self.seeds = seeds
        self.bin_seeding = bin_seeding
        self.min_bin_freq = min_bin_freq
        self.cluster_all = cluster_all
        self.max_iter = max_iter

    def train(self, X: np.ndarray, y=None) -> "MeanShift":
        """
        Perform mean shift clustering.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        self : MeanShift
            Fitted estimator.
        """
        X = check_array(X)
        n_samples = X.shape[0]

        # Estimate bandwidth
        if self.bandwidth is None:
            self.bandwidth_ = self._estimate_bandwidth(X)
        else:
            self.bandwidth_ = self.bandwidth

        # Get seeds
        if self.seeds is not None:
            seeds = self.seeds
        else:
            seeds = X.copy()

        # Mean shift for each seed
        cluster_centers = []

        for seed in seeds:
            center = seed.copy()

            for _ in range(self.max_iter):
                # Find points within bandwidth
                distances = np.linalg.norm(X - center, axis=1)
                within_bandwidth = distances <= self.bandwidth_

                if not within_bandwidth.any():
                    break

                # Update center (mean of points)
                new_center = X[within_bandwidth].mean(axis=0)

                if np.linalg.norm(new_center - center) < 1e-6:
                    break

                center = new_center

            cluster_centers.append(center)

        cluster_centers = np.array(cluster_centers)

        # Merge nearby centers
        self.cluster_centers_ = self._merge_centers(cluster_centers)

        # Assign labels
        if len(self.cluster_centers_) > 0:
            distances = cdist(X, self.cluster_centers_)
            self.labels_ = np.argmin(distances, axis=1)
        else:
            self.labels_ = np.zeros(n_samples, dtype=int)

        return self

    def _estimate_bandwidth(self, X: np.ndarray) -> float:
        """Estimate bandwidth using Scott's rule."""
        n_samples, n_features = X.shape
        sigma = np.std(X, axis=0).mean()
        return sigma * (n_samples * (n_features + 2) / 4) ** (-1 / (n_features + 4))

    def _merge_centers(self, centers: np.ndarray, tol: float = None) -> np.ndarray:
        """Merge nearby cluster centers."""
        if len(centers) == 0:
            return centers

        if tol is None:
            tol = self.bandwidth_ / 2

        unique_centers = []

        for center in centers:
            is_unique = True
            for unique_center in unique_centers:
                if np.linalg.norm(center - unique_center) < tol:
                    is_unique = False
                    break

            if is_unique:
                unique_centers.append(center)

        return np.array(unique_centers)

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        check_is_trained(self, "cluster_centers_")
        X = check_array(X)

        distances = cdist(X, self.cluster_centers_)
        return np.argmin(distances, axis=1)


class AffinityPropagation(BaseLearner):
    """
    Affinity Propagation clustering.

    Parameters
    ----------
    damping : float, default=0.5
        Damping factor between 0.5 and 1.
    max_iter : int, default=200
        Maximum iterations.
    convergence_iter : int, default=15
        Iterations without change for convergence.
    preference : float, optional
        Preference for each point to be an exemplar.
    affinity : {"euclidean", "precomputed"}, default="euclidean"
        How to compute affinities.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    cluster_centers_indices_ : ndarray
        Indices of cluster centers.
    cluster_centers_ : ndarray
        Cluster centers.
    labels_ : ndarray
        Cluster labels.
    affinity_matrix_ : ndarray
        Affinity matrix.

    Examples
    --------
    >>> from nalyst.clustering import AffinityPropagation
    >>> ap = AffinityPropagation(damping=0.9)
    >>> ap.train(X)
    >>> labels = ap.labels_
    """

    def __init__(
        self,
        damping: float = 0.5,
        max_iter: int = 200,
        convergence_iter: int = 15,
        preference: Optional[float] = None,
        affinity: str = "euclidean",
        random_state: Optional[int] = None,
    ):
        self.damping = damping
        self.max_iter = max_iter
        self.convergence_iter = convergence_iter
        self.preference = preference
        self.affinity = affinity
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "AffinityPropagation":
        """
        Perform Affinity Propagation clustering.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features) or (n_samples, n_samples)
            Input data or precomputed affinity matrix.
        y : ignored

        Returns
        -------
        self : AffinityPropagation
            Fitted estimator.
        """
        X = check_array(X)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Compute affinity matrix
        if self.affinity == "precomputed":
            S = X
            self._X = None
        else:
            S = -cdist(X, X, metric='sqeuclidean')
            self._X = X

        n_samples = S.shape[0]

        # Set preference (diagonal)
        if self.preference is None:
            preference = np.median(S)
        else:
            preference = self.preference

        np.fill_diagonal(S, preference)
        self.affinity_matrix_ = S

        # Initialize messages
        R = np.zeros((n_samples, n_samples))  # Responsibility
        A = np.zeros((n_samples, n_samples))  # Availability

        converged = False
        old_exemplars = np.zeros(n_samples, dtype=int)
        convergence_count = 0

        for iteration in range(self.max_iter):
            # Update responsibility
            AS = A + S
            I = np.argmax(AS, axis=1)
            max_AS = AS[np.arange(n_samples), I]

            AS[np.arange(n_samples), I] = -np.inf
            max_AS2 = np.max(AS, axis=1)

            R_new = S - max_AS[:, np.newaxis]
            R_new[np.arange(n_samples), I] = S[np.arange(n_samples), I] - max_AS2

            R = self.damping * R + (1 - self.damping) * R_new

            # Update availability
            R_pos = np.maximum(R, 0)
            np.fill_diagonal(R_pos, R.diagonal())

            A_new = np.sum(R_pos, axis=0)[np.newaxis, :] - R_pos
            diag_A = np.sum(np.maximum(R, 0), axis=0) - np.maximum(R.diagonal(), 0)
            A_new = np.minimum(A_new, 0)
            np.fill_diagonal(A_new, diag_A)

            A = self.damping * A + (1 - self.damping) * A_new

            # Check convergence
            exemplars = np.argmax(A + R, axis=1)

            if np.array_equal(exemplars, old_exemplars):
                convergence_count += 1
                if convergence_count >= self.convergence_iter:
                    converged = True
                    break
            else:
                convergence_count = 0

            old_exemplars = exemplars.copy()

        # Extract clusters
        E = A + R
        exemplar_mask = E.diagonal() > 0

        if not exemplar_mask.any():
            self.cluster_centers_indices_ = np.array([0])
            self.labels_ = np.zeros(n_samples, dtype=int)
        else:
            self.cluster_centers_indices_ = np.where(exemplar_mask)[0]

            # Assign points to nearest exemplar
            S_exemplars = S[:, self.cluster_centers_indices_]
            self.labels_ = np.argmax(S_exemplars, axis=1)

        if self._X is not None:
            self.cluster_centers_ = self._X[self.cluster_centers_indices_]
        else:
            self.cluster_centers_ = self.cluster_centers_indices_

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        check_is_trained(self, "cluster_centers_")
        X = check_array(X)

        distances = cdist(X, self.cluster_centers_)
        return np.argmin(distances, axis=1)


class BIRCH(BaseLearner):
    """
    BIRCH clustering.

    Balanced Iterative Reducing and Clustering using Hierarchies.

    Parameters
    ----------
    threshold : float, default=0.5
        Radius of subcluster for merging.
    branching_factor : int, default=50
        Maximum subclusters in each node.
    n_clusters : int, default=3
        Number of clusters after global clustering.
    compute_labels : bool, default=True
        Whether to compute labels.

    Attributes
    ----------
    labels_ : ndarray
        Cluster labels.
    subcluster_centers_ : ndarray
        Subcluster centroids.

    Examples
    --------
    >>> from nalyst.clustering import BIRCH
    >>> birch = BIRCH(n_clusters=5)
    >>> birch.train(X)
    >>> labels = birch.labels_
    """

    def __init__(
        self,
        threshold: float = 0.5,
        branching_factor: int = 50,
        n_clusters: int = 3,
        compute_labels: bool = True,
    ):
        self.threshold = threshold
        self.branching_factor = branching_factor
        self.n_clusters = n_clusters
        self.compute_labels = compute_labels

    def train(self, X: np.ndarray, y=None) -> "BIRCH":
        """
        Build the CF tree.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.
        y : ignored

        Returns
        -------
        self : BIRCH
            Fitted estimator.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        # Build CF tree (simplified implementation)
        subclusters = []

        for x in X:
            added = False
            for sc in subclusters:
                if np.linalg.norm(x - sc["center"]) < self.threshold:
                    # Add to subcluster
                    n = sc["n"]
                    sc["center"] = (sc["center"] * n + x) / (n + 1)
                    sc["n"] += 1
                    added = True
                    break

            if not added:
                subclusters.append({"center": x.copy(), "n": 1})

                # Merge if too many subclusters
                if len(subclusters) > self.branching_factor:
                    subclusters = self._merge_subclusters(subclusters)

        # Store subcluster centers
        self.subcluster_centers_ = np.array([sc["center"] for sc in subclusters])
        self.subcluster_counts_ = np.array([sc["n"] for sc in subclusters])

        # Global clustering using k-means on subclusters
        if self.n_clusters is not None and len(self.subcluster_centers_) > self.n_clusters:
            from nalyst.clustering import KMeans
            kmeans = KMeans(n_clusters=self.n_clusters)
            kmeans.train(self.subcluster_centers_)
            self.cluster_centers_ = kmeans.cluster_centers_
            subcluster_labels = kmeans.labels_
        else:
            self.cluster_centers_ = self.subcluster_centers_
            subcluster_labels = np.arange(len(self.subcluster_centers_))

        # Assign labels to original data
        if self.compute_labels:
            distances = cdist(X, self.subcluster_centers_)
            nearest_subcluster = np.argmin(distances, axis=1)
            self.labels_ = subcluster_labels[nearest_subcluster]

        return self

    def _merge_subclusters(self, subclusters: list) -> list:
        """Merge closest subclusters."""
        if len(subclusters) <= 2:
            return subclusters

        # Find closest pair
        centers = np.array([sc["center"] for sc in subclusters])
        distances = cdist(centers, centers)
        np.fill_diagonal(distances, np.inf)

        i, j = np.unravel_index(np.argmin(distances), distances.shape)

        # Merge
        n_i, n_j = subclusters[i]["n"], subclusters[j]["n"]
        new_center = (subclusters[i]["center"] * n_i + subclusters[j]["center"] * n_j) / (n_i + n_j)

        # Remove old, add new
        new_subclusters = [sc for k, sc in enumerate(subclusters) if k not in (i, j)]
        new_subclusters.append({"center": new_center, "n": n_i + n_j})

        return new_subclusters

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster labels."""
        check_is_trained(self, "cluster_centers_")
        X = check_array(X)

        distances = cdist(X, self.cluster_centers_)
        return np.argmin(distances, axis=1)
