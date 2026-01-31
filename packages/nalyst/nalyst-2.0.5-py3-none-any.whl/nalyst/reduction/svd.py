"""
Truncated Singular Value Decomposition (SVD).
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy import linalg
from scipy.sparse.linalg import svds

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class TruncatedSVD(TransformerMixin, BaseLearner):
    """
    Truncated Singular Value Decomposition (LSA).

    This transformer performs linear dimensionality reduction using
    truncated SVD. Unlike PCA, this estimator does not center the
    data before computing SVD, making it suitable for sparse matrices.

    Parameters
    ----------
    n_components : int, default=2
        Desired dimensionality of output data.
    algorithm : {"arpack", "randomized"}, default="randomized"
        SVD solver to use.
    n_iter : int, default=5
        Number of iterations for randomized SVD solver.
    random_state : int, optional
        Random seed.
    tol : float, default=0.0
        Tolerance for ARPACK.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        The right singular vectors.
    explained_variance_ : ndarray of shape (n_components,)
        Variance of the training data explained by each component.
    explained_variance_ratio_ : ndarray of shape (n_components,)
        Percentage of variance explained by each component.
    singular_values_ : ndarray of shape (n_components,)
        The singular values.

    Examples
    --------
    >>> from nalyst.reduction import TruncatedSVD
    >>> X = [[0, 1, 2], [2, 1, 0], [1, 2, 1], [2, 0, 1]]
    >>> svd = TruncatedSVD(n_components=2)
    >>> svd.train(X)
    TruncatedSVD(n_components=2)
    >>> X_reduced = svd.apply(X)
    """

    def __init__(
        self,
        n_components: int = 2,
        *,
        algorithm: Literal["arpack", "randomized"] = "randomized",
        n_iter: int = 5,
        random_state: Optional[int] = None,
        tol: float = 0.0,
    ):
        self.n_components = n_components
        self.algorithm = algorithm
        self.n_iter = n_iter
        self.random_state = random_state
        self.tol = tol

    def train(self, X: np.ndarray, y=None) -> "TruncatedSVD":
        """
        Fit model on training data X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : TruncatedSVD
            Fitted transformer.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        if self.algorithm == "arpack":
            # Use scipy sparse SVD
            k = min(self.n_components, min(n_samples, n_features) - 1)
            U, S, Vt = svds(X.astype(float), k=k, tol=self.tol)

            # svds returns in ascending order, reverse
            S = S[::-1]
            U = U[:, ::-1]
            Vt = Vt[::-1]
        else:
            # Randomized SVD
            U, S, Vt = self._randomized_svd(X, self.n_components, self.n_iter)

        self.components_ = Vt
        self.singular_values_ = S

        # Compute variance
        X_transformed = np.dot(X, Vt.T)
        self.explained_variance_ = np.var(X_transformed, axis=0)

        full_var = np.var(X, axis=0).sum()
        self.explained_variance_ratio_ = self.explained_variance_ / full_var

        return self

    def _randomized_svd(
        self,
        X: np.ndarray,
        n_components: int,
        n_iter: int,
    ) -> tuple:
        """Compute truncated randomized SVD."""
        n_samples, n_features = X.shape

        # Random projection
        Q = np.random.randn(n_features, n_components)

        # Power iteration
        for _ in range(n_iter):
            Q = np.dot(X, Q)
            Q = np.dot(X.T, Q)

        # QR decomposition
        Q, _ = linalg.qr(np.dot(X, Q), mode='economic')

        # Project and compute SVD
        B = np.dot(Q.T, X)
        Uhat, S, Vt = linalg.svd(B, full_matrices=False)

        U = np.dot(Q, Uhat)

        return U[:, :n_components], S[:n_components], Vt[:n_components]

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Perform dimensionality reduction on X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Transformed data.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        return np.dot(X, self.components_.T)

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X back to original space.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_components)
            Transformed data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Approximate original data.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        return np.dot(X, self.components_)
