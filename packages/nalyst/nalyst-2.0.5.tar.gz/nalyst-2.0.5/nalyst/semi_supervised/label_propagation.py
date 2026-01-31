"""
Label Propagation algorithms.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained


class LabelPropagation(ClassifierMixin, BaseLearner):
    """
    Label Propagation classifier.

    Parameters
    ----------
    kernel : {"knn", "rbf"}, default="rbf"
        Kernel to construct affinity graph.
    gamma : float, default=20
        Kernel coefficient for rbf.
    n_neighbors : int, default=7
        Number of neighbors for knn kernel.
    max_iter : int, default=1000
        Maximum iterations.
    tol : float, default=1e-3
        Convergence tolerance.

    Attributes
    ----------
    classes_ : ndarray
        Class labels.
    label_distributions_ : ndarray
        Label distributions for each point.
    transduction_ : ndarray
        Labels of training samples.

    Examples
    --------
    >>> from nalyst.semi_supervised import LabelPropagation
    >>> # -1 indicates unlabeled samples
    >>> y_train = np.array([0, 0, 1, -1, -1, -1])
    >>> lp = LabelPropagation()
    >>> lp.train(X, y_train)
    >>> lp.transduction_  # Propagated labels
    """

    def __init__(
        self,
        kernel: Literal["knn", "rbf"] = "rbf",
        gamma: float = 20,
        n_neighbors: int = 7,
        max_iter: int = 1000,
        tol: float = 1e-3,
    ):
        self.kernel = kernel
        self.gamma = gamma
        self.n_neighbors = n_neighbors
        self.max_iter = max_iter
        self.tol = tol

    def train(self, X: np.ndarray, y: np.ndarray) -> "LabelPropagation":
        """
        Train the label propagation model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Labels with -1 for unlabeled samples.

        Returns
        -------
        self : LabelPropagation
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y)

        self._X = X
        n_samples = X.shape[0]

        # Get classes (excluding -1)
        labeled_mask = y != -1
        self.classes_ = np.unique(y[labeled_mask])
        n_classes = len(self.classes_)

        # Build affinity matrix
        if self.kernel == "rbf":
            affinity = self._rbf_kernel(X)
        else:
            affinity = self._knn_kernel(X)

        # Row normalize to get transition probability matrix
        row_sum = affinity.sum(axis=1, keepdims=True)
        T = affinity / (row_sum + 1e-10)

        # Initialize label distributions
        Y = np.zeros((n_samples, n_classes))

        for i, c in enumerate(self.classes_):
            Y[y == c, i] = 1

        Y_static = Y.copy()

        # Propagation
        for _ in range(self.max_iter):
            Y_new = T @ Y

            # Clamp labeled samples
            Y_new[labeled_mask] = Y_static[labeled_mask]

            # Check convergence
            if np.abs(Y_new - Y).max() < self.tol:
                break

            Y = Y_new

        self.label_distributions_ = Y
        self.transduction_ = self.classes_[np.argmax(Y, axis=1)]

        return self

    def _rbf_kernel(self, X: np.ndarray) -> np.ndarray:
        """Compute RBF kernel."""
        distances = cdist(X, X, metric='sqeuclidean')
        return np.exp(-self.gamma * distances)

    def _knn_kernel(self, X: np.ndarray) -> np.ndarray:
        """Compute kNN kernel."""
        n_samples = X.shape[0]
        distances = cdist(X, X)

        affinity = np.zeros((n_samples, n_samples))

        for i in range(n_samples):
            neighbors = np.argsort(distances[i])[1:self.n_neighbors + 1]
            affinity[i, neighbors] = 1

        # Make symmetric
        affinity = np.maximum(affinity, affinity.T)

        return affinity

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict labels."""
        proba = self.infer_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probability."""
        check_is_trained(self, "label_distributions_")
        X = check_array(X)

        # Compute kernel to training points
        if self.kernel == "rbf":
            distances = cdist(X, self._X, metric='sqeuclidean')
            weights = np.exp(-self.gamma * distances)
        else:
            distances = cdist(X, self._X)
            n_test = X.shape[0]
            weights = np.zeros((n_test, len(self._X)))

            for i in range(n_test):
                neighbors = np.argsort(distances[i])[:self.n_neighbors]
                weights[i, neighbors] = 1

        # Normalize and predict
        weights /= weights.sum(axis=1, keepdims=True) + 1e-10
        proba = weights @ self.label_distributions_

        return proba


class LabelSpreading(LabelPropagation):
    """
    Label Spreading classifier.

    Similar to LabelPropagation but with different normalization.

    Parameters
    ----------
    kernel : {"knn", "rbf"}, default="rbf"
        Kernel to construct affinity graph.
    gamma : float, default=20
        Kernel coefficient for rbf.
    n_neighbors : int, default=7
        Number of neighbors for knn kernel.
    alpha : float, default=0.2
        Clamping factor (0 = hard clamping, 1 = no clamping).
    max_iter : int, default=30
        Maximum iterations.
    tol : float, default=1e-3
        Convergence tolerance.

    Examples
    --------
    >>> from nalyst.semi_supervised import LabelSpreading
    >>> ls = LabelSpreading(alpha=0.2)
    >>> ls.train(X, y)
    """

    def __init__(
        self,
        kernel: Literal["knn", "rbf"] = "rbf",
        gamma: float = 20,
        n_neighbors: int = 7,
        alpha: float = 0.2,
        max_iter: int = 30,
        tol: float = 1e-3,
    ):
        super().__init__(
            kernel=kernel,
            gamma=gamma,
            n_neighbors=n_neighbors,
            max_iter=max_iter,
            tol=tol,
        )
        self.alpha = alpha

    def train(self, X: np.ndarray, y: np.ndarray) -> "LabelSpreading":
        """Train label spreading model."""
        X = check_array(X)
        y = np.asarray(y)

        self._X = X
        n_samples = X.shape[0]

        labeled_mask = y != -1
        self.classes_ = np.unique(y[labeled_mask])
        n_classes = len(self.classes_)

        # Build affinity matrix
        if self.kernel == "rbf":
            affinity = self._rbf_kernel(X)
        else:
            affinity = self._knn_kernel(X)

        # Normalized Laplacian
        D = np.diag(affinity.sum(axis=1))
        D_inv_sqrt = np.diag(1.0 / (np.sqrt(np.diag(D)) + 1e-10))
        S = D_inv_sqrt @ affinity @ D_inv_sqrt

        # Initialize label distributions
        Y = np.zeros((n_samples, n_classes))

        for i, c in enumerate(self.classes_):
            Y[y == c, i] = 1

        Y_static = Y.copy()

        # Spreading
        for _ in range(self.max_iter):
            Y_new = self.alpha * S @ Y + (1 - self.alpha) * Y_static

            if np.abs(Y_new - Y).max() < self.tol:
                break

            Y = Y_new

        # Normalize to get probabilities
        Y /= Y.sum(axis=1, keepdims=True) + 1e-10

        self.label_distributions_ = Y
        self.transduction_ = self.classes_[np.argmax(Y, axis=1)]

        return self
