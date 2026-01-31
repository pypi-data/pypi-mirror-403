"""
Under-sampling techniques for imbalanced datasets.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union
import numpy as np

from nalyst.imbalance.oversampling import BaseSampler


class RandomUnderSampler(BaseSampler):
    """
    Random under-sampling of majority class.

    Randomly removes samples from majority class to balance dataset.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        If float, ratio of minority to majority after resampling.
        If 'auto', balance all classes to minority class size.
    random_state : int, optional
        Random seed.
    replacement : bool, default=False
        Whether to sample with replacement.

    Examples
    --------
    >>> rus = RandomUnderSampler(random_state=42)
    >>> X_resampled, y_resampled = rus.resample(X, y)
    """

    def __init__(
        self,
        sampling_strategy: Union[float, str] = 'auto',
        random_state: Optional[int] = None,
        replacement: bool = False,
    ):
        super().__init__(random_state)
        self.sampling_strategy = sampling_strategy
        self.replacement = replacement

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample the dataset by undersampling majority classes.
        """
        X, y = self._check_input(X, y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        classes, counts = np.unique(y, return_counts=True)
        min_count = np.min(counts)

        selected_indices = []

        for cls in classes:
            class_indices = np.where(y == cls)[0]

            if self.sampling_strategy == 'auto':
                n_samples = min_count
            else:
                n_samples = min(len(class_indices),
                               int(min_count / self.sampling_strategy))

            selected = np.random.choice(
                class_indices,
                size=n_samples,
                replace=self.replacement
            )
            selected_indices.extend(selected)

        selected_indices = np.array(selected_indices)

        return X[selected_indices], y[selected_indices]


class TomekLinks(BaseSampler):
    """
    Tomek links under-sampling.

    Removes majority class samples that form Tomek links with
    minority class samples. A Tomek link exists between two samples
    of different classes if they are each other's nearest neighbors.

    Parameters
    ----------
    random_state : int, optional
        Random seed.

    References
    ----------
    Tomek, I. "Two Modifications of CNN." IEEE Trans. SMC (1976).

    Examples
    --------
    >>> tomek = TomekLinks()
    >>> X_resampled, y_resampled = tomek.resample(X, y)
    """

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove Tomek links from dataset.
        """
        X, y = self._check_input(X, y)

        n_samples = len(X)

        # Find nearest neighbor for each sample
        nn_indices = np.zeros(n_samples, dtype=int)

        for i in range(n_samples):
            distances = np.linalg.norm(X - X[i], axis=1)
            distances[i] = np.inf  # Exclude self
            nn_indices[i] = np.argmin(distances)

        # Find Tomek links
        tomek_links = set()

        for i in range(n_samples):
            j = nn_indices[i]

            # Check if mutual nearest neighbors and different classes
            if nn_indices[j] == i and y[i] != y[j]:
                # This is a Tomek link - mark majority class sample
                classes, counts = np.unique(y, return_counts=True)
                majority_class = classes[np.argmax(counts)]

                if y[i] == majority_class:
                    tomek_links.add(i)
                else:
                    tomek_links.add(j)

        # Remove Tomek links
        keep_indices = [i for i in range(n_samples) if i not in tomek_links]

        return X[keep_indices], y[keep_indices]


class NearMiss(BaseSampler):
    """
    NearMiss under-sampling.

    Selects majority class samples based on their distance to
    minority class samples.

    Parameters
    ----------
    version : int, default=1
        NearMiss version:
        - 1: Select samples closest to minority class.
        - 2: Select samples farthest from minority class.
        - 3: Select samples closest to each minority sample.
    n_neighbors : int, default=3
        Number of neighbors.
    random_state : int, optional
        Random seed.

    References
    ----------
    Mani, I. and Zhang, I. "kNN Approach to Unbalanced Data
    Distributions." ICML Workshop (2003).

    Examples
    --------
    >>> nm = NearMiss(version=1, n_neighbors=3)
    >>> X_resampled, y_resampled = nm.resample(X, y)
    """

    def __init__(
        self,
        version: int = 1,
        n_neighbors: int = 3,
        random_state: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.version = version
        self.n_neighbors = n_neighbors

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample using NearMiss.
        """
        X, y = self._check_input(X, y)

        classes, counts = np.unique(y, return_counts=True)
        min_count = np.min(counts)
        minority_class = classes[np.argmin(counts)]
        majority_class = classes[np.argmax(counts)]

        minority_indices = np.where(y == minority_class)[0]
        majority_indices = np.where(y == majority_class)[0]

        minority_X = X[minority_indices]
        majority_X = X[majority_indices]

        k = min(self.n_neighbors, len(minority_X))

        # Calculate distances from each majority sample to minority samples
        scores = []

        for i, sample in enumerate(majority_X):
            distances = np.linalg.norm(minority_X - sample, axis=1)
            sorted_distances = np.sort(distances)

            if self.version == 1:
                # Average distance to k nearest minority samples
                score = np.mean(sorted_distances[:k])
            elif self.version == 2:
                # Average distance to k farthest minority samples
                score = np.mean(sorted_distances[-k:])
            else:  # version == 3
                # Average distance to all minority samples
                score = np.mean(distances)

            scores.append(score)

        scores = np.array(scores)

        # Select majority samples
        if self.version == 1:
            # Select closest to minority (smallest scores)
            selected = np.argsort(scores)[:min_count]
        elif self.version == 2:
            # Select farthest from minority (largest scores)
            selected = np.argsort(scores)[-min_count:]
        else:  # version == 3
            # Select closest to minority
            selected = np.argsort(scores)[:min_count]

        selected_majority_indices = majority_indices[selected]

        # Combine with minority samples
        final_indices = np.concatenate([minority_indices, selected_majority_indices])

        return X[final_indices], y[final_indices]


class EditedNearestNeighbors(BaseSampler):
    """
    Edited Nearest Neighbors (ENN) under-sampling.

    Removes samples whose class label differs from the majority
    of its k-nearest neighbors.

    Parameters
    ----------
    n_neighbors : int, default=3
        Number of neighbors.
    kind_sel : str, default='all'
        Strategy: 'all' (all neighbors must agree) or
        'mode' (majority must agree).
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> enn = EditedNearestNeighbors(n_neighbors=3)
    >>> X_resampled, y_resampled = enn.resample(X, y)
    """

    def __init__(
        self,
        n_neighbors: int = 3,
        kind_sel: str = 'all',
        random_state: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.n_neighbors = n_neighbors
        self.kind_sel = kind_sel

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Remove noisy samples using ENN.
        """
        X, y = self._check_input(X, y)

        n_samples = len(X)
        k = min(self.n_neighbors, n_samples - 1)

        keep = []

        for i in range(n_samples):
            distances = np.linalg.norm(X - X[i], axis=1)
            distances[i] = np.inf
            neighbor_indices = np.argsort(distances)[:k]
            neighbor_labels = y[neighbor_indices]

            if self.kind_sel == 'all':
                # Keep if all neighbors have same label
                if np.all(neighbor_labels == y[i]):
                    keep.append(i)
            else:  # 'mode'
                # Keep if majority of neighbors have same label
                unique, counts = np.unique(neighbor_labels, return_counts=True)
                mode_label = unique[np.argmax(counts)]
                if mode_label == y[i]:
                    keep.append(i)

        return X[keep], y[keep]


class ClusterCentroids(BaseSampler):
    """
    Cluster Centroids under-sampling.

    Under-samples by replacing clusters of majority class samples
    with their centroids.

    Parameters
    ----------
    sampling_strategy : float or str, default='auto'
        Sampling strategy.
    random_state : int, optional
        Random seed.
    n_clusters : int, optional
        Number of clusters. If None, uses target sample count.

    Examples
    --------
    >>> cc = ClusterCentroids(random_state=42)
    >>> X_resampled, y_resampled = cc.resample(X, y)
    """

    def __init__(
        self,
        sampling_strategy: Union[float, str] = 'auto',
        random_state: Optional[int] = None,
        n_clusters: Optional[int] = None,
    ):
        super().__init__(random_state)
        self.sampling_strategy = sampling_strategy
        self.n_clusters = n_clusters

    def resample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Resample using cluster centroids.
        """
        X, y = self._check_input(X, y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        classes, counts = np.unique(y, return_counts=True)
        min_count = np.min(counts)
        minority_class = classes[np.argmin(counts)]

        X_resampled = []
        y_resampled = []

        for cls in classes:
            class_indices = np.where(y == cls)[0]
            class_X = X[class_indices]

            if cls == minority_class:
                # Keep all minority samples
                X_resampled.append(class_X)
                y_resampled.append(np.full(len(class_X), cls))
            else:
                # Cluster majority class
                n_clusters = self.n_clusters or min_count
                n_clusters = min(n_clusters, len(class_X))

                centroids = self._kmeans(class_X, n_clusters)

                X_resampled.append(centroids)
                y_resampled.append(np.full(n_clusters, cls))

        return np.vstack(X_resampled), np.concatenate(y_resampled)

    def _kmeans(
        self,
        X: np.ndarray,
        n_clusters: int,
        max_iter: int = 100,
    ) -> np.ndarray:
        """Simple k-means clustering."""
        n_samples = len(X)

        # Initialize centroids randomly
        indices = np.random.choice(n_samples, size=n_clusters, replace=False)
        centroids = X[indices].copy()

        for _ in range(max_iter):
            # Assign to nearest centroid
            distances = np.array([
                np.linalg.norm(X - c, axis=1) for c in centroids
            ])
            labels = np.argmin(distances, axis=0)

            # Update centroids
            new_centroids = np.array([
                X[labels == k].mean(axis=0) if np.any(labels == k)
                else centroids[k]
                for k in range(n_clusters)
            ])

            # Check convergence
            if np.allclose(centroids, new_centroids):
                break

            centroids = new_centroids

        return centroids
