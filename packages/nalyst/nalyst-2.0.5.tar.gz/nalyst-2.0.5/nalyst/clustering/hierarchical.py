"""
Hierarchical clustering algorithms.

Provides bottom-up (agglomerative) clustering methods that
build a hierarchy of clusters.
"""

from __future__ import annotations

from typing import Optional, Union, Literal, Callable

import numpy as np
from scipy.spatial.distance import pdist, squareform

from nalyst.core.foundation import BaseLearner, ClusterMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.core.tags import LearnerTags, TargetTags


class AgglomerativeClustering(ClusterMixin, BaseLearner):
    """
    Agglomerative Hierarchical Clustering.

    Recursively merges clusters based on a linkage criterion.

    Parameters
    ----------
    n_clusters : int or None, default=2
        Number of clusters. None if using distance_threshold.
    metric : str or callable, default="euclidean"
        Distance metric.
    memory : optional
        Caching backend.
    connectivity : array-like or callable, optional
        Connectivity constraints.
    compute_full_tree : "auto" or bool, default="auto"
        Whether to compute full dendrogram.
    linkage : {"ward", "complete", "average", "single"}, default="ward"
        Linkage criterion.
    distance_threshold : float, optional
        Distance threshold for clustering.
    compute_distances : bool, default=False
        Compute distances for dendrogram.

    Attributes
    ----------
    n_clusters_ : int
        Number of clusters found.
    labels_ : ndarray of shape (n_samples,)
        Cluster labels.
    n_leaves_ : int
        Number of leaves.
    n_connected_components_ : int
        Number of connected components.
    children_ : ndarray of shape (n_samples-1, 2)
        Children of each non-leaf node.
    distances_ : ndarray
        Distances between merged clusters.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.clustering import AgglomerativeClustering
    >>> X = np.array([[1, 2], [1, 4], [1, 0], [4, 2], [4, 4], [4, 0]])
    >>> clustering = AgglomerativeClustering(n_clusters=2)
    >>> clustering.train(X)
    AgglomerativeClustering(n_clusters=2)
    >>> clustering.labels_
    array([1, 1, 1, 0, 0, 0])
    """

    def __init__(
        self,
        n_clusters: Optional[int] = 2,
        *,
        metric: Union[str, Callable] = "euclidean",
        memory=None,
        connectivity=None,
        compute_full_tree: Union[str, bool] = "auto",
        linkage: Literal["ward", "complete", "average", "single"] = "ward",
        distance_threshold: Optional[float] = None,
        compute_distances: bool = False,
    ):
        self.n_clusters = n_clusters
        self.metric = metric
        self.memory = memory
        self.connectivity = connectivity
        self.compute_full_tree = compute_full_tree
        self.linkage = linkage
        self.distance_threshold = distance_threshold
        self.compute_distances = compute_distances

    def _compute_distance_matrix(self, X: np.ndarray) -> np.ndarray:
        """Compute pairwise distance matrix."""
        if callable(self.metric):
            distances = pdist(X, metric=self.metric)
        else:
            distances = pdist(X, metric=self.metric)
        return squareform(distances)

    def _linkage_distance(
        self,
        cluster_a: np.ndarray,
        cluster_b: np.ndarray,
        distance_matrix: np.ndarray,
    ) -> float:
        """Compute distance between two clusters."""
        if self.linkage == "single":
            # Minimum distance
            distances = []
            for i in cluster_a:
                for j in cluster_b:
                    distances.append(distance_matrix[i, j])
            return np.min(distances)

        elif self.linkage == "complete":
            # Maximum distance
            distances = []
            for i in cluster_a:
                for j in cluster_b:
                    distances.append(distance_matrix[i, j])
            return np.max(distances)

        elif self.linkage == "average":
            # Average distance
            total = 0.0
            count = 0
            for i in cluster_a:
                for j in cluster_b:
                    total += distance_matrix[i, j]
                    count += 1
            return total / count

        else:  # ward
            # Increase in variance
            # Approximated using centroid distance weighted by size
            size_a = len(cluster_a)
            size_b = len(cluster_b)

            # Average distance as approximation
            total = 0.0
            for i in cluster_a:
                for j in cluster_b:
                    total += distance_matrix[i, j]
            avg_dist = total / (size_a * size_b)

            # Ward criterion
            return np.sqrt(2 * size_a * size_b / (size_a + size_b)) * avg_dist

    def train(self, X: np.ndarray, y=None) -> "AgglomerativeClustering":
        """
        Fit the hierarchical clustering.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : AgglomerativeClustering
        """
        X = check_array(X)
        n_samples = X.shape[0]
        self.n_features_in_ = X.shape[1]
        self.n_leaves_ = n_samples

        # Compute distance matrix
        distance_matrix = self._compute_distance_matrix(X)

        # Initialize: each sample is its own cluster
        clusters = {i: [i] for i in range(n_samples)}
        cluster_labels = np.arange(n_samples)

        children = []
        distances = []

        next_cluster_id = n_samples

        # Determine stopping criterion
        if self.distance_threshold is not None:
            target_n_clusters = 1
            use_threshold = True
        else:
            target_n_clusters = self.n_clusters if self.n_clusters else 1
            use_threshold = False

        # Merge until target number of clusters
        while len(clusters) > target_n_clusters:
            # Find closest pair of clusters
            min_dist = np.inf
            merge_pair = None

            cluster_ids = list(clusters.keys())
            for i, cid_a in enumerate(cluster_ids):
                for cid_b in cluster_ids[i + 1:]:
                    dist = self._linkage_distance(
                        clusters[cid_a],
                        clusters[cid_b],
                        distance_matrix
                    )
                    if dist < min_dist:
                        min_dist = dist
                        merge_pair = (cid_a, cid_b)

            if merge_pair is None:
                break

            # Check distance threshold
            if use_threshold and min_dist > self.distance_threshold:
                break

            cid_a, cid_b = merge_pair

            # Record merge
            children.append([cid_a, cid_b])
            distances.append(min_dist)

            # Merge clusters
            new_cluster = clusters[cid_a] + clusters[cid_b]
            del clusters[cid_a]
            del clusters[cid_b]
            clusters[next_cluster_id] = new_cluster

            # Update labels
            for idx in new_cluster:
                cluster_labels[idx] = next_cluster_id

            next_cluster_id += 1

        self.children_ = np.array(children) if children else np.array([]).reshape(0, 2)
        self.distances_ = np.array(distances) if distances else np.array([])

        # Assign final cluster labels
        final_labels = np.zeros(n_samples, dtype=int)
        for i, (cid, members) in enumerate(clusters.items()):
            for idx in members:
                final_labels[idx] = i

        self.labels_ = final_labels
        self.n_clusters_ = len(clusters)
        self.n_connected_components_ = 1

        return self

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit and return cluster labels.

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
