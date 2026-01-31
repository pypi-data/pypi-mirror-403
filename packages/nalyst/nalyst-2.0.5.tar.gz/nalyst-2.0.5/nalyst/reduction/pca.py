"""
Principal Component Analysis (PCA) and variants.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained


class PrincipalComponentAnalysis(TransformerMixin, BaseLearner):
    """
    Principal Component Analysis (PCA).

    Linear dimensionality reduction using Singular Value Decomposition
    to project data to a lower dimensional space.

    Parameters
    ----------
    n_components : int, float, or None, default=None
        Number of components to keep. If float in (0, 1), select number
        that explains at least that proportion of variance.
    whiten : bool, default=False
        Whether to whiten the data (unit variance).
    svd_solver : {"auto", "full", "arpack", "randomized"}, default="auto"
        SVD solver to use.
    tol : float, default=0.0
        Tolerance for singular values.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Principal axes in feature space.
    explained_variance_ : ndarray of shape (n_components,)
        Variance explained by each component.
    explained_variance_ratio_ : ndarray of shape (n_components,)
        Percentage of variance explained by each component.
    singular_values_ : ndarray of shape (n_components,)
        Singular values corresponding to each component.
    mean_ : ndarray of shape (n_features,)
        Per-feature empirical mean.
    n_components_ : int
        Actual number of components.
    n_features_in_ : int
        Number of features.
    n_samples_ : int
        Number of training samples.

    Examples
    --------
    >>> from nalyst.reduction import PrincipalComponentAnalysis
    >>> X = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    >>> pca = PrincipalComponentAnalysis(n_components=2)
    >>> pca.train(X)
    PrincipalComponentAnalysis(n_components=2)
    >>> X_reduced = pca.apply(X)
    >>> X_reduced.shape
    (3, 2)
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        whiten: bool = False,
        svd_solver: Literal["auto", "full", "arpack", "randomized"] = "auto",
        tol: float = 0.0,
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.whiten = whiten
        self.svd_solver = svd_solver
        self.tol = tol
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "PrincipalComponentAnalysis":
        """
        Fit the model with X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : PrincipalComponentAnalysis
            Fitted transformer.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        self.n_samples_ = n_samples
        self.n_features_in_ = n_features

        # Center data
        self.mean_ = np.mean(X, axis=0)
        X_centered = X - self.mean_

        # Determine number of components
        if self.n_components is None:
            n_components = min(n_samples, n_features)
        elif isinstance(self.n_components, float):
            n_components = min(n_samples, n_features)
        else:
            n_components = min(self.n_components, n_samples, n_features)

        # Perform SVD
        U, S, Vt = linalg.svd(X_centered, full_matrices=False)

        # Handle variance ratio selection
        if isinstance(self.n_components, float):
            total_var = np.sum(S ** 2)
            explained_variance_ratio = (S ** 2) / total_var
            cumsum = np.cumsum(explained_variance_ratio)
            n_components = np.searchsorted(cumsum, self.n_components) + 1

        # Store results
        self.components_ = Vt[:n_components]
        self.n_components_ = n_components

        # Compute explained variance
        self.explained_variance_ = (S[:n_components] ** 2) / (n_samples - 1)
        total_var = np.sum(S ** 2) / (n_samples - 1)
        self.explained_variance_ratio_ = self.explained_variance_ / total_var
        self.singular_values_ = S[:n_components]

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Apply dimensionality reduction to X.

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

        X_centered = X - self.mean_
        X_transformed = np.dot(X_centered, self.components_.T)

        if self.whiten:
            X_transformed /= np.sqrt(self.explained_variance_)

        return X_transformed

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data back to original space.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_components)
            Transformed data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Original data approximation.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        if self.whiten:
            X = X * np.sqrt(self.explained_variance_)

        return np.dot(X, self.components_) + self.mean_

    def get_covariance(self) -> np.ndarray:
        """
        Compute data covariance with the generative model.

        Returns
        -------
        cov : ndarray of shape (n_features, n_features)
            Estimated covariance matrix.
        """
        check_is_trained(self, "components_")

        components = self.components_
        exp_var = self.explained_variance_

        return np.dot(components.T * exp_var, components)

    def get_precision(self) -> np.ndarray:
        """
        Compute data precision matrix with the generative model.

        Returns
        -------
        precision : ndarray of shape (n_features, n_features)
            Estimated precision matrix.
        """
        check_is_trained(self, "components_")

        components = self.components_
        exp_var = self.explained_variance_

        return np.dot(components.T / exp_var, components)

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Return the log-likelihood of each sample.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        ll : ndarray of shape (n_samples,)
            Log-likelihood of each sample.
        """
        check_is_trained(self, "components_")
        X = check_array(X)

        X_transformed = self.apply(X)
        n_features = self.n_features_in_

        # Compute log-likelihood under Gaussian model
        log_like = -0.5 * (
            np.sum(X_transformed ** 2 / self.explained_variance_, axis=1) +
            np.sum(np.log(self.explained_variance_)) +
            n_features * np.log(2 * np.pi)
        )

        return log_like

    def score(self, X: np.ndarray, y=None) -> float:
        """
        Return average log-likelihood of all samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.
        y : ignored

        Returns
        -------
        ll : float
            Average log-likelihood.
        """
        return float(np.mean(self.score_samples(X)))


class IncrementalPCA(TransformerMixin, BaseLearner):
    """
    Incremental Principal Component Analysis.

    Allows fitting PCA on large datasets by processing data in batches.

    Parameters
    ----------
    n_components : int, optional
        Number of components. If None, min(n_samples, n_features).
    whiten : bool, default=False
        Whether to whiten the data.
    batch_size : int, optional
        Number of samples per batch.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Principal components.
    explained_variance_ : ndarray of shape (n_components,)
        Explained variance.
    explained_variance_ratio_ : ndarray of shape (n_components,)
        Percentage of variance explained.
    singular_values_ : ndarray of shape (n_components,)
        Singular values.
    mean_ : ndarray of shape (n_features,)
        Per-feature mean.
    var_ : ndarray of shape (n_features,)
        Per-feature variance.
    n_samples_seen_ : int
        Number of samples processed.

    Examples
    --------
    >>> from nalyst.reduction import IncrementalPCA
    >>> X = np.random.randn(100, 10)
    >>> ipca = IncrementalPCA(n_components=2, batch_size=20)
    >>> ipca.train(X)
    IncrementalPCA(n_components=2)
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        whiten: bool = False,
        batch_size: Optional[int] = None,
    ):
        self.n_components = n_components
        self.whiten = whiten
        self.batch_size = batch_size

    def train(self, X: np.ndarray, y=None) -> "IncrementalPCA":
        """
        Fit the model with X using batches.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : IncrementalPCA
            Fitted transformer.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.batch_size is None:
            batch_size = max(5 * n_features, 100)
        else:
            batch_size = self.batch_size

        for start in range(0, n_samples, batch_size):
            end = min(start + batch_size, n_samples)
            self.partial_train(X[start:end])

        return self

    def partial_train(self, X: np.ndarray, y=None) -> "IncrementalPCA":
        """
        Incremental fit on a batch.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Batch of training data.
        y : ignored

        Returns
        -------
        self : IncrementalPCA
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if not hasattr(self, "n_samples_seen_"):
            # First batch - initialize
            self.n_samples_seen_ = 0
            self.mean_ = np.zeros(n_features)
            self.var_ = np.zeros(n_features)

            if self.n_components is None:
                self.n_components_ = n_features
            else:
                self.n_components_ = self.n_components

        # Update mean incrementally
        col_mean = np.mean(X, axis=0)
        col_var = np.var(X, axis=0)

        n_total = self.n_samples_seen_ + n_samples

        # Welford's algorithm for incremental variance
        delta = col_mean - self.mean_
        new_mean = self.mean_ + delta * n_samples / n_total

        new_var = (
            self.var_ * self.n_samples_seen_ +
            col_var * n_samples +
            delta ** 2 * self.n_samples_seen_ * n_samples / n_total
        ) / n_total

        # Update components using SVD
        X_centered = X - new_mean

        if hasattr(self, "components_"):
            # Combine old components with new data
            components_scaled = self.components_ * np.sqrt(
                self.explained_variance_.reshape(-1, 1) * self.n_samples_seen_
            )
            combined = np.vstack([components_scaled, X_centered])
            U, S, Vt = linalg.svd(combined, full_matrices=False)
        else:
            U, S, Vt = linalg.svd(X_centered, full_matrices=False)

        self.components_ = Vt[:self.n_components_]
        self.explained_variance_ = (S[:self.n_components_] ** 2) / (n_total - 1)

        total_var = np.sum(S ** 2) / (n_total - 1)
        self.explained_variance_ratio_ = self.explained_variance_ / total_var
        self.singular_values_ = S[:self.n_components_]

        self.mean_ = new_mean
        self.var_ = new_var
        self.n_samples_seen_ = n_total

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """Apply dimensionality reduction."""
        check_is_trained(self, "components_")
        X = check_array(X)

        X_centered = X - self.mean_
        X_transformed = np.dot(X_centered, self.components_.T)

        if self.whiten:
            X_transformed /= np.sqrt(self.explained_variance_)

        return X_transformed

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """Transform back to original space."""
        check_is_trained(self, "components_")
        X = check_array(X)

        if self.whiten:
            X = X * np.sqrt(self.explained_variance_)

        return np.dot(X, self.components_) + self.mean_


class KernelPCA(TransformerMixin, BaseLearner):
    """
    Kernel Principal Component Analysis.

    Non-linear dimensionality reduction through the use of kernels.

    Parameters
    ----------
    n_components : int, optional
        Number of components. If None, all are kept.
    kernel : {"linear", "poly", "rbf", "sigmoid", "cosine"}, default="linear"
        Kernel used for PCA.
    gamma : float, optional
        Kernel coefficient for rbf, poly, sigmoid.
    degree : int, default=3
        Degree for polynomial kernel.
    coef0 : float, default=1
        Independent term in poly and sigmoid kernels.
    alpha : float, default=1.0
        Hyperparameter for ridge regression.
    fit_inverse_transform : bool, default=False
        Learn the inverse transform.
    remove_zero_eig : bool, default=False
        Remove zero eigenvalues.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    eigenvalues_ : ndarray of shape (n_components,)
        Eigenvalues of the centered kernel matrix.
    eigenvectors_ : ndarray of shape (n_samples, n_components)
        Eigenvectors of the centered kernel matrix.
    X_fit_ : ndarray of shape (n_samples, n_features)
        Training data.

    Examples
    --------
    >>> from nalyst.reduction import KernelPCA
    >>> X = [[1, 2], [3, 4], [5, 6], [7, 8]]
    >>> kpca = KernelPCA(n_components=2, kernel='rbf')
    >>> kpca.train(X)
    KernelPCA(n_components=2, kernel='rbf')
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        kernel: Literal["linear", "poly", "rbf", "sigmoid", "cosine"] = "linear",
        gamma: Optional[float] = None,
        degree: int = 3,
        coef0: float = 1,
        alpha: float = 1.0,
        fit_inverse_transform: bool = False,
        remove_zero_eig: bool = False,
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.kernel = kernel
        self.gamma = gamma
        self.degree = degree
        self.coef0 = coef0
        self.alpha = alpha
        self.fit_inverse_transform = fit_inverse_transform
        self.remove_zero_eig = remove_zero_eig
        self.random_state = random_state

    def _compute_kernel(self, X: np.ndarray, Y: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute the kernel matrix."""
        if Y is None:
            Y = X

        if self.kernel == "linear":
            return np.dot(X, Y.T)

        gamma = self.gamma or (1.0 / X.shape[1])

        if self.kernel == "poly":
            return (gamma * np.dot(X, Y.T) + self.coef0) ** self.degree
        elif self.kernel == "rbf":
            X_sq = np.sum(X ** 2, axis=1).reshape(-1, 1)
            Y_sq = np.sum(Y ** 2, axis=1).reshape(1, -1)
            sq_dist = X_sq + Y_sq - 2 * np.dot(X, Y.T)
            return np.exp(-gamma * sq_dist)
        elif self.kernel == "sigmoid":
            return np.tanh(gamma * np.dot(X, Y.T) + self.coef0)
        elif self.kernel == "cosine":
            X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-10)
            Y_norm = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-10)
            return np.dot(X_norm, Y_norm.T)
        else:
            raise ValueError(f"Unknown kernel: {self.kernel}")

    def train(self, X: np.ndarray, y=None) -> "KernelPCA":
        """
        Fit the model with X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : KernelPCA
            Fitted transformer.
        """
        X = check_array(X)
        self.X_fit_ = X
        n_samples = len(X)

        # Compute kernel matrix
        K = self._compute_kernel(X)

        # Center kernel matrix
        K_mean_rows = np.mean(K, axis=0)
        K_mean_cols = np.mean(K, axis=1, keepdims=True)
        K_mean = np.mean(K)
        K_centered = K - K_mean_rows - K_mean_cols + K_mean

        self._K_mean_rows = K_mean_rows
        self._K_mean = K_mean

        # Eigendecomposition
        eigenvalues, eigenvectors = linalg.eigh(K_centered)

        # Sort by decreasing eigenvalue
        indices = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[indices]
        eigenvectors = eigenvectors[:, indices]

        # Remove zero eigenvalues
        if self.remove_zero_eig:
            non_zero = eigenvalues > 1e-10
            eigenvalues = eigenvalues[non_zero]
            eigenvectors = eigenvectors[:, non_zero]

        # Select components
        if self.n_components is not None:
            n_components = min(self.n_components, len(eigenvalues))
        else:
            n_components = len(eigenvalues)

        self.eigenvalues_ = eigenvalues[:n_components]
        self.eigenvectors_ = eigenvectors[:, :n_components]

        # Normalize eigenvectors
        self.eigenvectors_ = self.eigenvectors_ / np.sqrt(self.eigenvalues_)

        if self.fit_inverse_transform:
            # Fit inverse transform using ridge regression
            X_transformed = np.dot(K_centered, self.eigenvectors_)
            A = np.dot(X_transformed.T, X_transformed) + self.alpha * np.eye(n_components)
            B = np.dot(X_transformed.T, X)
            self._inverse_transform_matrix = linalg.solve(A, B)

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Apply the dimensionality reduction on X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_new : ndarray of shape (n_samples, n_components)
            Transformed data.
        """
        check_is_trained(self, "eigenvectors_")
        X = check_array(X)

        K = self._compute_kernel(X, self.X_fit_)

        # Center kernel
        K_pred_rows = np.mean(K, axis=1, keepdims=True)
        K_centered = K - self._K_mean_rows - K_pred_rows + self._K_mean

        return np.dot(K_centered, self.eigenvectors_)

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X back to original space.

        Only available if fit_inverse_transform=True.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_components)
            Transformed data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Approximate original data.
        """
        if not self.fit_inverse_transform:
            raise ValueError("fit_inverse_transform=True required")

        check_is_trained(self, "_inverse_transform_matrix")
        X = check_array(X)

        return np.dot(X, self._inverse_transform_matrix)


class SparsePCA(TransformerMixin, BaseLearner):
    """
    Sparse Principal Components Analysis.

    Finds sparse components that can optimally reconstruct the data.

    Parameters
    ----------
    n_components : int, optional
        Number of sparse atoms.
    alpha : float, default=1.0
        Sparsity controlling parameter.
    ridge_alpha : float, default=0.01
        Ridge regression regularization.
    max_iter : int, default=1000
        Maximum number of iterations.
    tol : float, default=1e-8
        Tolerance for stopping criterion.
    method : {"lars", "cd"}, default="lars"
        Algorithm: lars or coordinate descent.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    components_ : ndarray of shape (n_components, n_features)
        Sparse components.
    error_ : ndarray
        Vector of errors at each iteration.
    n_iter_ : int
        Number of iterations run.
    mean_ : ndarray of shape (n_features,)
        Per-feature mean.

    Examples
    --------
    >>> from nalyst.reduction import SparsePCA
    >>> X = np.random.randn(10, 5)
    >>> spca = SparsePCA(n_components=3)
    >>> spca.train(X)
    SparsePCA(n_components=3)
    """

    def __init__(
        self,
        n_components: Optional[int] = None,
        *,
        alpha: float = 1.0,
        ridge_alpha: float = 0.01,
        max_iter: int = 1000,
        tol: float = 1e-8,
        method: Literal["lars", "cd"] = "lars",
        random_state: Optional[int] = None,
    ):
        self.n_components = n_components
        self.alpha = alpha
        self.ridge_alpha = ridge_alpha
        self.max_iter = max_iter
        self.tol = tol
        self.method = method
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "SparsePCA":
        """
        Fit the model with X.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : SparsePCA
            Fitted transformer.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        self.mean_ = np.mean(X, axis=0)
        X_centered = X - self.mean_

        n_components = self.n_components or n_features

        # Initialize with PCA
        U, S, Vt = linalg.svd(X_centered, full_matrices=False)
        components = Vt[:n_components].copy()

        self.error_ = []

        # Alternating minimization
        for iteration in range(self.max_iter):
            # Update dictionary (fix codes, update components)
            # Ridge regression: components = (X.T @ X + ridge_alpha * I)^-1 @ X.T @ codes
            codes = np.dot(X_centered, components.T)

            for j in range(n_components):
                # Compute residual
                residual = X_centered - np.dot(codes, components)
                residual += np.outer(codes[:, j], components[j])

                # Update component using soft thresholding
                component = np.dot(residual.T, codes[:, j])
                component = np.sign(component) * np.maximum(
                    np.abs(component) - self.alpha, 0
                )

                # Normalize
                norm = np.linalg.norm(component)
                if norm > 1e-10:
                    components[j] = component / norm

            # Compute error
            reconstruction = np.dot(codes, components)
            error = np.sum((X_centered - reconstruction) ** 2)
            self.error_.append(error)

            if iteration > 0 and abs(self.error_[-1] - self.error_[-2]) < self.tol:
                break

        self.components_ = components
        self.n_iter_ = iteration + 1

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """Apply dimensionality reduction."""
        check_is_trained(self, "components_")
        X = check_array(X)

        X_centered = X - self.mean_
        return np.dot(X_centered, self.components_.T)

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """Transform back to original space."""
        check_is_trained(self, "components_")
        X = check_array(X)

        return np.dot(X, self.components_) + self.mean_
