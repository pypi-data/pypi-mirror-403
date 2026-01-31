"""
Gaussian Process Classification.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import linalg
from scipy.special import expit, erf

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.gaussian_process.kernels import RBF, Kernel


class GaussianProcessClassifier(ClassifierMixin, BaseLearner):
    """
    Gaussian Process Classification (GPC).

    Uses Laplace approximation for binary classification.

    Parameters
    ----------
    kernel : Kernel, optional
        The kernel function. Defaults to RBF.
    optimizer : {"fmin_l_bfgs_b"} or None, default="fmin_l_bfgs_b"
        Optimizer for kernel hyperparameters.
    n_restarts_optimizer : int, default=0
        Number of restarts for optimizer.
    max_iter_predict : int, default=100
        Maximum iterations for prediction.
    warm_start : bool, default=False
        Use previous solution as starting point.
    random_state : int, optional
        Random seed.
    multi_class : {"one_vs_rest", "one_vs_one"}, default="one_vs_rest"
        Multi-class strategy.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    kernel_ : Kernel
        Kernel used for prediction.
    X_train_ : ndarray of shape (n_samples, n_features)
        Training data.
    y_train_ : ndarray of shape (n_samples,)
        Training labels.
    f_cached_ : ndarray of shape (n_samples,)
        Cached latent function values.

    Examples
    --------
    >>> from nalyst.gaussian_process import GaussianProcessClassifier, RBF
    >>> kernel = RBF(length_scale=1.0)
    >>> gpc = GaussianProcessClassifier(kernel=kernel)
    >>> gpc.train(X, y)
    >>> proba = gpc.infer_proba(X_test)
    """

    def __init__(
        self,
        kernel: Optional[Kernel] = None,
        *,
        optimizer: Optional[str] = "fmin_l_bfgs_b",
        n_restarts_optimizer: int = 0,
        max_iter_predict: int = 100,
        warm_start: bool = False,
        random_state: Optional[int] = None,
        multi_class: str = "one_vs_rest",
    ):
        self.kernel = kernel
        self.optimizer = optimizer
        self.n_restarts_optimizer = n_restarts_optimizer
        self.max_iter_predict = max_iter_predict
        self.warm_start = warm_start
        self.random_state = random_state
        self.multi_class = multi_class

    def train(self, X: np.ndarray, y: np.ndarray) -> "GaussianProcessClassifier":
        """
        Fit Gaussian process classification model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature vectors.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : GaussianProcessClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.atleast_1d(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)

        if n_classes == 2:
            # Binary classification
            self._train_binary(X, y)
        else:
            # Multi-class using one-vs-rest
            self._train_multiclass(X, y)

        return self

    def _train_binary(self, X: np.ndarray, y: np.ndarray):
        """Train binary classifier."""
        self.kernel_ = self.kernel if self.kernel is not None else RBF()

        # Convert labels to +1/-1
        y_binary = np.where(y == self.classes_[1], 1, -1)

        self.X_train_ = X
        self.y_train_ = y_binary

        # Compute kernel matrix
        K = self.kernel_(X)

        # Laplace approximation
        n = len(X)
        f = np.zeros(n)  # Initial latent function

        for _ in range(self.max_iter_predict):
            # Compute pi = sigmoid(f)
            pi = expit(f)

            # Compute W = diag(pi * (1 - pi))
            W = pi * (1 - pi)
            W = np.clip(W, 1e-10, 1 - 1e-10)
            W_sqrt = np.sqrt(W)

            # Compute B = I + sqrt(W) @ K @ sqrt(W)
            B = np.eye(n) + W_sqrt[:, np.newaxis] * K * W_sqrt[np.newaxis, :]

            # Cholesky decomposition
            try:
                L = linalg.cholesky(B, lower=True)
            except linalg.LinAlgError:
                B += 1e-6 * np.eye(n)
                L = linalg.cholesky(B, lower=True)

            # Newton update
            b = W * f + (y_binary + 1) / 2 - pi
            a = b - W_sqrt * linalg.cho_solve((L, True), W_sqrt * (K @ b))
            f_new = K @ a

            if np.max(np.abs(f_new - f)) < 1e-6:
                f = f_new
                break
            f = f_new

        self.f_cached_ = f
        self.L_ = L
        self.W_sqrt_ = W_sqrt

    def _train_multiclass(self, X: np.ndarray, y: np.ndarray):
        """Train multi-class classifier using one-vs-rest."""
        self.kernel_ = self.kernel if self.kernel is not None else RBF()
        self.X_train_ = X

        self._classifiers = []

        for c in self.classes_:
            y_binary = np.where(y == c, 1, -1)

            # Create a copy of self for binary classification
            clf = GaussianProcessClassifier(
                kernel=self.kernel_,
                max_iter_predict=self.max_iter_predict,
            )
            clf.classes_ = np.array([-1, 1])
            clf._train_binary(X, np.where(y == c, self.classes_[1], self.classes_[0]))

            self._classifiers.append(clf)

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Return probability estimates.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Query points.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Probability of each class.
        """
        check_is_trained(self, "kernel_")
        X = check_array(X)

        if len(self.classes_) == 2:
            return self._predict_proba_binary(X)
        else:
            return self._predict_proba_multiclass(X)

    def _predict_proba_binary(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for binary classification."""
        # Compute cross-covariance
        K_trans = self.kernel_(X, self.X_train_)

        # Mean prediction
        pi_train = expit(self.f_cached_)
        W = pi_train * (1 - pi_train)

        f_star = K_trans @ (self.y_train_ / 2 + 0.5 - pi_train)

        # Variance
        v = linalg.solve_triangular(self.L_, self.W_sqrt_ * K_trans.T, lower=True)
        var_f = self.kernel_.diag(X) - np.sum(v ** 2, axis=0)
        var_f = np.maximum(var_f, 0)

        # Probit approximation
        gamma = 1.0 / np.sqrt(1 + np.pi * var_f / 8)
        proba_pos = expit(gamma * f_star)

        return np.column_stack([1 - proba_pos, proba_pos])

    def _predict_proba_multiclass(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for multi-class."""
        n_samples = X.shape[0]
        n_classes = len(self.classes_)

        proba = np.zeros((n_samples, n_classes))

        for i, clf in enumerate(self._classifiers):
            proba[:, i] = clf.infer_proba(X)[:, 1]

        # Normalize
        proba /= proba.sum(axis=1, keepdims=True)

        return proba

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Query points.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels.
        """
        proba = self.infer_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]
