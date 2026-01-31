"""
Clustering metrics.

Provides scoring functions for evaluating
clustering algorithms.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import sparse
from scipy.special import comb


def silhouette_score(
    X: np.ndarray,
    labels: np.ndarray,
    *,
    metric: str = "euclidean",
    sample_size: Optional[int] = None,
    random_state: Optional[int] = None,
) -> float:
    """
    Compute the mean Silhouette Coefficient of all samples.

    The Silhouette Coefficient is calculated using the mean intra-cluster
    distance (a) and the mean nearest-cluster distance (b) for each sample.
    The Silhouette Coefficient for a sample is (b - a) / max(a, b).

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature array.
    labels : array-like of shape (n_samples,)
        Cluster labels for each sample.
    metric : str, default="euclidean"
        Distance metric to use.
    sample_size : int, optional
        Size of sample to use for computation.
    random_state : int, optional
        Random state for sampling.

    Returns
    -------
    silhouette : float
        Mean Silhouette Coefficient (-1 to 1, higher is better).

    Examples
    --------
    >>> from nalyst.metrics import silhouette_score
    >>> X = [[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]]
    >>> labels = [0, 0, 0, 1, 1, 1]
    >>> silhouette_score(X, labels)
    0.79...
    """
    X = np.asarray(X)
    labels = np.asarray(labels)

    if sample_size is not None and sample_size < len(X):
        rng = np.random.RandomState(random_state)
        indices = rng.choice(len(X), sample_size, replace=False)
        X = X[indices]
        labels = labels[indices]

    n_samples = len(X)
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters == 1 or n_clusters >= n_samples:
        return 0.0

    # Compute pairwise distances
    if metric == "euclidean":
        distances = _euclidean_distances(X, X)
    elif metric == "manhattan":
        distances = _manhattan_distances(X, X)
    elif metric == "cosine":
        distances = _cosine_distances(X, X)
    else:
        distances = _euclidean_distances(X, X)

    silhouette_values = np.zeros(n_samples)

    for i in range(n_samples):
        cluster_label = labels[i]

        # Intra-cluster distance (a)
        same_cluster = labels == cluster_label
        n_same = np.sum(same_cluster) - 1  # Exclude self

        if n_same == 0:
            silhouette_values[i] = 0
            continue

        a = np.sum(distances[i, same_cluster]) / n_same

        # Nearest-cluster distance (b)
        b = np.inf
        for other_label in unique_labels:
            if other_label == cluster_label:
                continue

            other_cluster = labels == other_label
            mean_dist = np.mean(distances[i, other_cluster])
            b = min(b, mean_dist)

        silhouette_values[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0

    return float(np.mean(silhouette_values))


def silhouette_samples(
    X: np.ndarray,
    labels: np.ndarray,
    *,
    metric: str = "euclidean",
) -> np.ndarray:
    """
    Compute the Silhouette Coefficient for each sample.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature array.
    labels : array-like of shape (n_samples,)
        Cluster labels for each sample.
    metric : str, default="euclidean"
        Distance metric to use.

    Returns
    -------
    silhouette : ndarray of shape (n_samples,)
        Silhouette Coefficient for each sample.
    """
    X = np.asarray(X)
    labels = np.asarray(labels)

    n_samples = len(X)
    unique_labels = np.unique(labels)

    # Compute pairwise distances
    if metric == "euclidean":
        distances = _euclidean_distances(X, X)
    else:
        distances = _euclidean_distances(X, X)

    silhouette_values = np.zeros(n_samples)

    for i in range(n_samples):
        cluster_label = labels[i]
        same_cluster = labels == cluster_label
        n_same = np.sum(same_cluster) - 1

        if n_same == 0:
            continue

        a = np.sum(distances[i, same_cluster]) / n_same

        b = np.inf
        for other_label in unique_labels:
            if other_label == cluster_label:
                continue
            other_cluster = labels == other_label
            mean_dist = np.mean(distances[i, other_cluster])
            b = min(b, mean_dist)

        silhouette_values[i] = (b - a) / max(a, b) if max(a, b) > 0 else 0

    return silhouette_values


def calinski_harabasz_score(
    X: np.ndarray,
    labels: np.ndarray,
) -> float:
    """
    Compute the Calinski-Harabasz Index (Variance Ratio Criterion).

    The score is defined as ratio of the sum of between-clusters
    dispersion and of within-cluster dispersion.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature array.
    labels : array-like of shape (n_samples,)
        Cluster labels for each sample.

    Returns
    -------
    score : float
        Calinski-Harabasz Index (higher is better).

    Examples
    --------
    >>> from nalyst.metrics import calinski_harabasz_score
    >>> X = [[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]]
    >>> labels = [0, 0, 0, 1, 1, 1]
    >>> calinski_harabasz_score(X, labels)
    120.99...
    """
    X = np.asarray(X)
    labels = np.asarray(labels)

    n_samples, n_features = X.shape
    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters == 1 or n_clusters >= n_samples:
        return 0.0

    # Overall mean
    mean_total = np.mean(X, axis=0)

    # Between-cluster dispersion
    bgss = 0.0
    # Within-cluster dispersion
    wgss = 0.0

    for label in unique_labels:
        cluster_mask = labels == label
        cluster_points = X[cluster_mask]
        n_k = len(cluster_points)

        cluster_mean = np.mean(cluster_points, axis=0)

        # Between-group sum of squares
        bgss += n_k * np.sum((cluster_mean - mean_total) ** 2)

        # Within-group sum of squares
        wgss += np.sum((cluster_points - cluster_mean) ** 2)

    if wgss == 0:
        return 0.0

    score = (bgss / (n_clusters - 1)) / (wgss / (n_samples - n_clusters))

    return float(score)


def davies_bouldin_score(
    X: np.ndarray,
    labels: np.ndarray,
) -> float:
    """
    Compute the Davies-Bouldin Index.

    The index is defined as the average similarity measure of each
    cluster with its most similar cluster. Lower values are better.

    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature array.
    labels : array-like of shape (n_samples,)
        Cluster labels for each sample.

    Returns
    -------
    score : float
        Davies-Bouldin Index (lower is better).

    Examples
    --------
    >>> from nalyst.metrics import davies_bouldin_score
    >>> X = [[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]]
    >>> labels = [0, 0, 0, 1, 1, 1]
    >>> davies_bouldin_score(X, labels)
    0.18...
    """
    X = np.asarray(X)
    labels = np.asarray(labels)

    unique_labels = np.unique(labels)
    n_clusters = len(unique_labels)

    if n_clusters == 1:
        return 0.0

    # Compute cluster centroids and dispersions
    centroids = []
    dispersions = []

    for label in unique_labels:
        cluster_mask = labels == label
        cluster_points = X[cluster_mask]
        centroid = np.mean(cluster_points, axis=0)
        centroids.append(centroid)

        # Dispersion: average distance to centroid
        dispersion = np.mean(np.sqrt(np.sum((cluster_points - centroid) ** 2, axis=1)))
        dispersions.append(dispersion)

    centroids = np.array(centroids)
    dispersions = np.array(dispersions)

    # Compute similarity matrix
    db_indices = np.zeros(n_clusters)

    for i in range(n_clusters):
        max_ratio = 0
        for j in range(n_clusters):
            if i == j:
                continue

            # Distance between centroids
            centroid_dist = np.sqrt(np.sum((centroids[i] - centroids[j]) ** 2))

            if centroid_dist == 0:
                ratio = 0
            else:
                ratio = (dispersions[i] + dispersions[j]) / centroid_dist

            max_ratio = max(max_ratio, ratio)

        db_indices[i] = max_ratio

    return float(np.mean(db_indices))


def adjusted_rand_score(
    labels_true: np.ndarray,
    labels_pred: np.ndarray,
) -> float:
    """
    Compute Adjusted Rand Index.

    The Rand Index computes similarity between two clusterings,
    adjusted for chance. Ranges from -1 to 1, where 1 is perfect.

    Parameters
    ----------
    labels_true : array-like of shape (n_samples,)
        Ground truth class labels.
    labels_pred : array-like of shape (n_samples,)
        Cluster labels to evaluate.

    Returns
    -------
    ari : float
        Adjusted Rand Index (-1 to 1).

    Examples
    --------
    >>> from nalyst.metrics import adjusted_rand_score
    >>> labels_true = [0, 0, 0, 1, 1, 1]
    >>> labels_pred = [0, 0, 1, 1, 2, 2]
    >>> adjusted_rand_score(labels_true, labels_pred)
    0.24...
    """
    labels_true = np.asarray(labels_true)
    labels_pred = np.asarray(labels_pred)

    n_samples = len(labels_true)

    # Build contingency matrix
    classes = np.unique(labels_true)
    clusters = np.unique(labels_pred)

    contingency = np.zeros((len(classes), len(clusters)), dtype=np.int64)

    class_to_idx = {c: i for i, c in enumerate(classes)}
    cluster_to_idx = {c: i for i, c in enumerate(clusters)}

    for true_label, pred_label in zip(labels_true, labels_pred):
        contingency[class_to_idx[true_label], cluster_to_idx[pred_label]] += 1

    # Sum of combinations
    sum_comb_c = sum(comb(n, 2) for n in np.sum(contingency, axis=1))
    sum_comb_k = sum(comb(n, 2) for n in np.sum(contingency, axis=0))
    sum_comb = sum(comb(n, 2) for n in contingency.flatten())

    total_comb = comb(n_samples, 2)

    if total_comb == 0:
        return 0.0

    expected_index = sum_comb_c * sum_comb_k / total_comb
    max_index = (sum_comb_c + sum_comb_k) / 2

    if max_index == expected_index:
        return 0.0

    ari = (sum_comb - expected_index) / (max_index - expected_index)

    return float(ari)


def normalized_mutual_info_score(
    labels_true: np.ndarray,
    labels_pred: np.ndarray,
    *,
    average_method: str = "arithmetic",
) -> float:
    """
    Compute Normalized Mutual Information between two clusterings.

    Parameters
    ----------
    labels_true : array-like of shape (n_samples,)
        Ground truth class labels.
    labels_pred : array-like of shape (n_samples,)
        Cluster labels to evaluate.
    average_method : {"min", "geometric", "arithmetic", "max"}, default="arithmetic"
        How to compute normalizer.

    Returns
    -------
    nmi : float
        Normalized Mutual Information (0 to 1).

    Examples
    --------
    >>> from nalyst.metrics import normalized_mutual_info_score
    >>> labels_true = [0, 0, 0, 1, 1, 1]
    >>> labels_pred = [0, 0, 1, 1, 2, 2]
    >>> normalized_mutual_info_score(labels_true, labels_pred)
    0.51...
    """
    labels_true = np.asarray(labels_true)
    labels_pred = np.asarray(labels_pred)

    n_samples = len(labels_true)

    # Compute entropies and mutual information
    classes, class_counts = np.unique(labels_true, return_counts=True)
    clusters, cluster_counts = np.unique(labels_pred, return_counts=True)

    # Entropy of true labels
    h_true = -np.sum((class_counts / n_samples) * np.log(class_counts / n_samples + 1e-10))

    # Entropy of predicted labels
    h_pred = -np.sum((cluster_counts / n_samples) * np.log(cluster_counts / n_samples + 1e-10))

    # Build contingency matrix
    contingency = np.zeros((len(classes), len(clusters)))
    class_to_idx = {c: i for i, c in enumerate(classes)}
    cluster_to_idx = {c: i for i, c in enumerate(clusters)}

    for true_label, pred_label in zip(labels_true, labels_pred):
        contingency[class_to_idx[true_label], cluster_to_idx[pred_label]] += 1

    # Mutual information
    mi = 0.0
    for i in range(len(classes)):
        for j in range(len(clusters)):
            if contingency[i, j] > 0:
                p_ij = contingency[i, j] / n_samples
                p_i = class_counts[i] / n_samples
                p_j = cluster_counts[j] / n_samples
                mi += p_ij * np.log(p_ij / (p_i * p_j) + 1e-10)

    # Normalize
    if average_method == "min":
        normalizer = min(h_true, h_pred)
    elif average_method == "geometric":
        normalizer = np.sqrt(h_true * h_pred)
    elif average_method == "arithmetic":
        normalizer = (h_true + h_pred) / 2
    elif average_method == "max":
        normalizer = max(h_true, h_pred)
    else:
        normalizer = (h_true + h_pred) / 2

    if normalizer == 0:
        return 0.0

    return float(mi / normalizer)


def homogeneity_score(
    labels_true: np.ndarray,
    labels_pred: np.ndarray,
) -> float:
    """
    Compute homogeneity score.

    A clustering result satisfies homogeneity if all of its clusters
    contain only data points which are members of a single class.

    Parameters
    ----------
    labels_true : array-like of shape (n_samples,)
        Ground truth class labels.
    labels_pred : array-like of shape (n_samples,)
        Cluster labels to evaluate.

    Returns
    -------
    homogeneity : float
        Homogeneity score (0 to 1).
    """
    labels_true = np.asarray(labels_true)
    labels_pred = np.asarray(labels_pred)

    n_samples = len(labels_true)

    classes, class_counts = np.unique(labels_true, return_counts=True)
    clusters, cluster_counts = np.unique(labels_pred, return_counts=True)

    # Entropy of classes
    h_c = -np.sum((class_counts / n_samples) * np.log(class_counts / n_samples + 1e-10))

    if h_c == 0:
        return 1.0

    # Conditional entropy H(C|K)
    contingency = np.zeros((len(classes), len(clusters)))
    class_to_idx = {c: i for i, c in enumerate(classes)}
    cluster_to_idx = {c: i for i, c in enumerate(clusters)}

    for true_label, pred_label in zip(labels_true, labels_pred):
        contingency[class_to_idx[true_label], cluster_to_idx[pred_label]] += 1

    h_c_k = 0.0
    for j in range(len(clusters)):
        if cluster_counts[j] == 0:
            continue
        for i in range(len(classes)):
            if contingency[i, j] > 0:
                p = contingency[i, j] / cluster_counts[j]
                h_c_k -= (cluster_counts[j] / n_samples) * p * np.log(p + 1e-10)

    return float(1 - h_c_k / h_c)


def completeness_score(
    labels_true: np.ndarray,
    labels_pred: np.ndarray,
) -> float:
    """
    Compute completeness score.

    A clustering result satisfies completeness if all the data points
    that are members of a given class are elements of the same cluster.

    Parameters
    ----------
    labels_true : array-like of shape (n_samples,)
        Ground truth class labels.
    labels_pred : array-like of shape (n_samples,)
        Cluster labels to evaluate.

    Returns
    -------
    completeness : float
        Completeness score (0 to 1).
    """
    # Completeness is homogeneity with labels swapped
    return homogeneity_score(labels_pred, labels_true)


def v_measure_score(
    labels_true: np.ndarray,
    labels_pred: np.ndarray,
    *,
    beta: float = 1.0,
) -> float:
    """
    Compute V-measure (harmonic mean of homogeneity and completeness).

    Parameters
    ----------
    labels_true : array-like of shape (n_samples,)
        Ground truth class labels.
    labels_pred : array-like of shape (n_samples,)
        Cluster labels to evaluate.
    beta : float, default=1.0
        Weight of homogeneity in the calculation.

    Returns
    -------
    v_measure : float
        V-measure score (0 to 1).
    """
    h = homogeneity_score(labels_true, labels_pred)
    c = completeness_score(labels_true, labels_pred)

    if h + c == 0:
        return 0.0

    v = (1 + beta) * h * c / (beta * h + c)

    return float(v)


# Helper distance functions
def _euclidean_distances(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Compute pairwise Euclidean distances."""
    X_sq = np.sum(X ** 2, axis=1).reshape(-1, 1)
    Y_sq = np.sum(Y ** 2, axis=1).reshape(1, -1)
    distances = X_sq + Y_sq - 2 * np.dot(X, Y.T)
    distances = np.maximum(distances, 0)  # Numerical stability
    return np.sqrt(distances)


def _manhattan_distances(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Compute pairwise Manhattan distances."""
    n_X = X.shape[0]
    n_Y = Y.shape[0]
    distances = np.zeros((n_X, n_Y))

    for i in range(n_X):
        distances[i] = np.sum(np.abs(X[i] - Y), axis=1)

    return distances


def _cosine_distances(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine distances."""
    X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-10)
    Y_norm = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-10)

    similarity = np.dot(X_norm, Y_norm.T)
    distances = 1 - similarity

    return distances
