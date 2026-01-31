"""
Nearest neighbors classification.
"""

from __future__ import annotations

from typing import Optional, Literal
from collections import Counter

import numpy as np

from nalyst.core.foundation import ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.learners.neighbors.base import (
    NeighborsBase,
    KNeighborsMixin,
    RadiusNeighborsMixin,
    _compute_distances,
)


class KNeighborsClassifier(KNeighborsMixin, ClassifierMixin, NeighborsBase):
    """
    K-Nearest Neighbors Classifier.

    Classifies based on a majority vote of k nearest neighbors.

    Parameters
    ----------
    n_neighbors : int, default=5
        Number of neighbors to use.
    weights : {"uniform", "distance"}, default="uniform"
        Weight function used in prediction.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm used to compute nearest neighbors.
    leaf_size : int, default=30
        Leaf size passed to tree algorithms.
    p : int, default=2
        Power parameter for Minkowski metric.
    metric : str, default="minkowski"
        Distance metric.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    classes_ : ndarray
        Unique class labels.
    n_samples_fit_ : int
        Number of samples in the fitted data.

    Examples
    --------
    >>> from nalyst.learners.neighbors import KNeighborsClassifier
    >>> X = [[0, 0], [1, 1], [2, 2], [3, 3]]
    >>> y = [0, 0, 1, 1]
    >>> clf = KNeighborsClassifier(n_neighbors=3)
    >>> clf.train(X, y)
    KNeighborsClassifier(n_neighbors=3)
    >>> clf.infer([[1.5, 1.5]])
    array([0])
    """

    def __init__(
        self,
        n_neighbors: int = 5,
        *,
        weights: Literal["uniform", "distance"] = "uniform",
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        p: int = 2,
        metric: str = "minkowski",
        n_jobs: Optional[int] = None,
    ):
        super().__init__(
            n_neighbors=n_neighbors,
            algorithm=algorithm,
            leaf_size=leaf_size,
            p=p,
            metric=metric,
            n_jobs=n_jobs,
        )
        self.weights = weights

    def train(self, X: np.ndarray, y: np.ndarray) -> "KNeighborsClassifier":
        """
        Fit the k-nearest neighbors classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : KNeighborsClassifier
            Fitted classifier.
        """
        X, y = self._validate_data(X, y)

        self._train_X = X
        self._train_y = y
        self.classes_ = np.unique(y)
        self.n_samples_fit_ = len(X)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict the class labels for the provided data.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Test samples.

        Returns
        -------
        y : ndarray of shape (n_queries,)
            Class labels.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        neigh_dist, neigh_ind = self._kneighbors(X, self.n_neighbors, return_distance=True)

        y_pred = np.empty(len(X), dtype=self._train_y.dtype)

        for i in range(len(X)):
            neighbor_labels = self._train_y[neigh_ind[i]]

            if self.weights == "uniform":
                # Simple majority vote
                counts = Counter(neighbor_labels)
                y_pred[i] = counts.most_common(1)[0][0]
            else:
                # Distance-weighted vote
                weights = 1.0 / (neigh_dist[i] + 1e-10)
                class_weights = {}
                for label, w in zip(neighbor_labels, weights):
                    class_weights[label] = class_weights.get(label, 0) + w
                y_pred[i] = max(class_weights, key=class_weights.get)

        return y_pred

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Return probability estimates for the test data X.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Test samples.

        Returns
        -------
        p : ndarray of shape (n_queries, n_classes)
            Class probabilities.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        neigh_dist, neigh_ind = self._kneighbors(X, self.n_neighbors, return_distance=True)

        n_queries = len(X)
        n_classes = len(self.classes_)
        proba = np.zeros((n_queries, n_classes))

        class_to_idx = {c: i for i, c in enumerate(self.classes_)}

        for i in range(n_queries):
            neighbor_labels = self._train_y[neigh_ind[i]]

            if self.weights == "uniform":
                for label in neighbor_labels:
                    proba[i, class_to_idx[label]] += 1
                proba[i] /= self.n_neighbors
            else:
                weights = 1.0 / (neigh_dist[i] + 1e-10)
                for label, w in zip(neighbor_labels, weights):
                    proba[i, class_to_idx[label]] += w
                proba[i] /= proba[i].sum()

        return proba


class RadiusNeighborsClassifier(RadiusNeighborsMixin, ClassifierMixin, NeighborsBase):
    """
    Radius-based Neighbors Classifier.

    Classifies based on neighbors within a fixed radius.

    Parameters
    ----------
    radius : float, default=1.0
        Range of parameter space.
    weights : {"uniform", "distance"}, default="uniform"
        Weight function.
    algorithm : {"auto", "ball_tree", "kd_tree", "brute"}, default="auto"
        Algorithm for nearest neighbors.
    leaf_size : int, default=30
        Leaf size for tree algorithms.
    p : int, default=2
        Power parameter for Minkowski metric.
    metric : str, default="minkowski"
        Distance metric.
    outlier_label : any, optional
        Label for outliers with no neighbors.
    n_jobs : int, optional
        Number of parallel jobs.

    Examples
    --------
    >>> from nalyst.learners.neighbors import RadiusNeighborsClassifier
    >>> X = [[0, 0], [1, 1], [2, 2]]
    >>> y = [0, 0, 1]
    >>> clf = RadiusNeighborsClassifier(radius=1.5)
    >>> clf.train(X, y)
    RadiusNeighborsClassifier(radius=1.5)
    """

    def __init__(
        self,
        radius: float = 1.0,
        *,
        weights: Literal["uniform", "distance"] = "uniform",
        algorithm: Literal["auto", "ball_tree", "kd_tree", "brute"] = "auto",
        leaf_size: int = 30,
        p: int = 2,
        metric: str = "minkowski",
        outlier_label=None,
        n_jobs: Optional[int] = None,
    ):
        super().__init__(
            radius=radius,
            algorithm=algorithm,
            leaf_size=leaf_size,
            p=p,
            metric=metric,
            n_jobs=n_jobs,
        )
        self.weights = weights
        self.outlier_label = outlier_label

    def train(self, X: np.ndarray, y: np.ndarray) -> "RadiusNeighborsClassifier":
        """
        Fit the radius neighbors classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : RadiusNeighborsClassifier
            Fitted classifier.
        """
        X, y = self._validate_data(X, y)

        self._train_X = X
        self._train_y = y
        self.classes_ = np.unique(y)
        self.n_samples_fit_ = len(X)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels for the provided data.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Test samples.

        Returns
        -------
        y : ndarray of shape (n_queries,)
            Class labels.
        """
        check_is_trained(self, "_train_X")
        X = check_array(X)

        neigh_dist, neigh_ind = self._radius_neighbors(X, self.radius, return_distance=True)

        y_pred = np.empty(len(X), dtype=self._train_y.dtype)

        for i in range(len(X)):
            if len(neigh_ind[i]) == 0:
                if self.outlier_label is not None:
                    y_pred[i] = self.outlier_label
                else:
                    raise ValueError(f"No neighbors found for sample {i}")
                continue

            neighbor_labels = self._train_y[neigh_ind[i]]

            if self.weights == "uniform":
                counts = Counter(neighbor_labels)
                y_pred[i] = counts.most_common(1)[0][0]
            else:
                weights = 1.0 / (neigh_dist[i] + 1e-10)
                class_weights = {}
                for label, w in zip(neighbor_labels, weights):
                    class_weights[label] = class_weights.get(label, 0) + w
                y_pred[i] = max(class_weights, key=class_weights.get)

        return y_pred


class NearestCentroid(ClassifierMixin, NeighborsBase):
    """
    Nearest Centroid Classifier.

    Classification by computing centroids for each class.

    Parameters
    ----------
    metric : str, default="euclidean"
        Distance metric.
    shrink_threshold : float, optional
        Threshold for shrinking centroids.

    Attributes
    ----------
    classes_ : ndarray
        Unique class labels.
    centroids_ : ndarray of shape (n_classes, n_features)
        Centroid of each class.

    Examples
    --------
    >>> from nalyst.learners.neighbors import NearestCentroid
    >>> X = [[0, 0], [1, 1], [2, 2], [3, 3]]
    >>> y = [0, 0, 1, 1]
    >>> clf = NearestCentroid()
    >>> clf.train(X, y)
    NearestCentroid()
    >>> clf.infer([[1.1, 1.1]])
    array([0])
    """

    def __init__(
        self,
        metric: str = "euclidean",
        *,
        shrink_threshold: Optional[float] = None,
    ):
        super().__init__(metric=metric)
        self.shrink_threshold = shrink_threshold

    def train(self, X: np.ndarray, y: np.ndarray) -> "NearestCentroid":
        """
        Fit the nearest centroid classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : NearestCentroid
            Fitted classifier.
        """
        X, y = self._validate_data(X, y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        self.centroids_ = np.zeros((n_classes, n_features))

        for i, cls in enumerate(self.classes_):
            mask = y == cls
            self.centroids_[i] = np.mean(X[mask], axis=0)

        # Apply shrinkage if specified
        if self.shrink_threshold is not None:
            overall_centroid = np.mean(X, axis=0)

            # Compute within-class std
            variance = np.zeros(n_features)
            for cls in self.classes_:
                mask = y == cls
                variance += np.sum((X[mask] - self.centroids_[self.classes_ == cls]) ** 2, axis=0)
            variance /= (len(X) - n_classes)
            std = np.sqrt(variance)

            # Shrink centroids
            for i in range(n_classes):
                delta = (self.centroids_[i] - overall_centroid) / (std + 1e-10)
                delta = np.sign(delta) * np.maximum(np.abs(delta) - self.shrink_threshold, 0)
                self.centroids_[i] = overall_centroid + delta * std

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : ndarray of shape (n_queries, n_features)
            Test samples.

        Returns
        -------
        y : ndarray of shape (n_queries,)
            Predicted class labels.
        """
        check_is_trained(self, "centroids_")
        X = check_array(X)

        distances = _compute_distances(X, self.centroids_, self.metric)
        indices = np.argmin(distances, axis=1)

        return self.classes_[indices]
