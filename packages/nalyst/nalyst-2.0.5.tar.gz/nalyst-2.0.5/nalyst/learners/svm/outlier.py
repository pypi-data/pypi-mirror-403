"""
One-class SVM for outlier detection.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import OutlierMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.learners.svm.base import SVMBase


class OneClassSVM(OutlierMixin, SVMBase):
    """
    Unsupervised Outlier Detection using One-Class SVM.

    Estimates the support of a high-dimensional distribution.

    Parameters
    ----------
    kernel : {"linear", "poly", "rbf", "sigmoid"}, default="rbf"
        Kernel type.
    degree : int, default=3
        Polynomial degree.
    gamma : {"scale", "auto"} or float, default="scale"
        Kernel coefficient.
    coef0 : float, default=0.0
        Independent term.
    tol : float, default=1e-3
        Tolerance.
    nu : float, default=0.5
        Upper bound on fraction of training errors and lower bound
        on fraction of support vectors.
    shrinking : bool, default=True
        Whether to use shrinking heuristic.
    cache_size : float, default=200
        Kernel cache size (MB).
    max_iter : int, default=1000
        Maximum iterations.

    Attributes
    ----------
    support_ : ndarray
        Indices of support vectors.
    support_vectors_ : ndarray
        Support vectors.
    dual_coef_ : ndarray
        Coefficients of support vectors.
    intercept_ : ndarray
        Offset used for detection threshold.
    offset_ : float
        Offset for the sample.

    Examples
    --------
    >>> from nalyst.learners.svm import OneClassSVM
    >>> X = [[0, 0], [0.1, 0.1], [0.2, 0], [100, 100]]
    >>> clf = OneClassSVM(nu=0.1)
    >>> clf.train(X)
    OneClassSVM(nu=0.1)
    >>> clf.infer([[0, 0], [100, 100]])
    array([ 1, -1])
    """

    def __init__(
        self,
        kernel: Literal["linear", "poly", "rbf", "sigmoid"] = "rbf",
        *,
        degree: int = 3,
        gamma: str = "scale",
        coef0: float = 0.0,
        tol: float = 1e-3,
        nu: float = 0.5,
        shrinking: bool = True,
        cache_size: float = 200,
        max_iter: int = 1000,
    ):
        super().__init__(
            kernel=kernel,
            degree=degree,
            gamma=gamma,
            coef0=coef0,
            tol=tol,
            max_iter=max_iter,
        )
        self.nu = nu
        self.shrinking = shrinking
        self.cache_size = cache_size

    def train(self, X: np.ndarray, y=None) -> "OneClassSVM":
        """
        Train the one-class model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored
            Not used.

        Returns
        -------
        self : OneClassSVM
            Fitted detector.
        """
        X = check_array(X)
        n_samples = len(X)

        self._train_X = X
        self._kernel_func = self._get_kernel(X)

        # Compute kernel matrix
        K = self._compute_kernel_matrix(X)

        # Initialize alphas
        alpha = np.zeros(n_samples)

        # Upper bound derived from nu
        C = 1.0 / (n_samples * self.nu)

        # SMO algorithm for one-class SVM
        for iteration in range(self.max_iter):
            alpha_prev = alpha.copy()

            for i in range(n_samples):
                # Compute decision value
                f_i = np.sum(alpha * K[i])

                # Select j randomly
                j = np.random.randint(n_samples)
                while j == i:
                    j = np.random.randint(n_samples)

                f_j = np.sum(alpha * K[j])

                # Compute eta
                eta = K[i, i] + K[j, j] - 2 * K[i, j]
                if eta <= 0:
                    continue

                # Compute new alpha values
                L = max(0, alpha[i] + alpha[j] - C)
                H = min(C, alpha[i] + alpha[j])

                if L == H:
                    continue

                # Update
                delta = (f_i - f_j) / eta
                alpha_j_new = np.clip(alpha[j] + delta, L, H)
                alpha_i_new = alpha[i] + alpha[j] - alpha_j_new

                alpha[i] = alpha_i_new
                alpha[j] = alpha_j_new

            # Check convergence
            if np.allclose(alpha, alpha_prev, atol=self.tol):
                break

        # Store support vectors
        support_mask = alpha > 1e-7
        self.support_ = np.where(support_mask)[0]
        self.support_vectors_ = X[support_mask]
        self.dual_coef_ = alpha[support_mask].reshape(1, -1)

        # Compute offset (rho)
        # Choose support vectors with 0 < alpha < C
        free_sv_mask = (alpha > 1e-7) & (alpha < C - 1e-7)
        if np.any(free_sv_mask):
            free_sv_idx = np.where(free_sv_mask)[0]
            # rho = K(sv, free_sv).T @ alpha
            self.offset_ = np.mean([np.sum(alpha * K[i]) for i in free_sv_idx])
        else:
            self.offset_ = np.mean([np.sum(alpha * K[i]) for i in self.support_])

        self.intercept_ = np.array([-self.offset_])

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Perform outlier detection on X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to classify.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            +1 for inliers, -1 for outliers.
        """
        scores = self.decision_function(X)
        return np.where(scores >= 0, 1, -1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Signed distance to the separating hyperplane.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data.

        Returns
        -------
        scores : ndarray of shape (n_samples,)
            Signed distance (positive = inlier).
        """
        check_is_trained(self, "support_vectors_")
        X = check_array(X)

        K = self._kernel_func(X, self.support_vectors_)
        scores = np.dot(K, self.dual_coef_.T).ravel() - self.offset_

        return scores

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Raw scoring function of the samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data.

        Returns
        -------
        scores : ndarray of shape (n_samples,)
            Unshifted scores.
        """
        check_is_trained(self, "support_vectors_")
        X = check_array(X)

        K = self._kernel_func(X, self.support_vectors_)
        return np.dot(K, self.dual_coef_.T).ravel()

    def train_infer(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit and predict on X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored
            Not used.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Labels.
        """
        self.train(X)
        return self.infer(X)
