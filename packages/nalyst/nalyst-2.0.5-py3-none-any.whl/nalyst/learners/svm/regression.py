"""
Support Vector Machine regression.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import RegressorMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.learners.svm.base import SVMBase


class SupportVectorRegressor(RegressorMixin, SVMBase):
    """
    Epsilon-Support Vector Regression.

    Parameters
    ----------
    kernel : {"linear", "poly", "rbf", "sigmoid"}, default="rbf"
        Kernel type.
    degree : int, default=3
        Degree of polynomial kernel.
    gamma : {"scale", "auto"} or float, default="scale"
        Kernel coefficient.
    coef0 : float, default=0.0
        Independent term in kernel.
    tol : float, default=1e-3
        Tolerance for stopping criterion.
    C : float, default=1.0
        Regularization parameter.
    epsilon : float, default=0.1
        Epsilon in epsilon-SVR model.
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
        Constant in decision function.

    Examples
    --------
    >>> from nalyst.learners.svm import SupportVectorRegressor
    >>> X = [[0, 0], [2, 2]]
    >>> y = [0.5, 2.5]
    >>> reg = SupportVectorRegressor()
    >>> reg.train(X, y)
    SupportVectorRegressor()
    >>> reg.infer([[1, 1]])
    array([1.5])
    """

    def __init__(
        self,
        kernel: Literal["linear", "poly", "rbf", "sigmoid"] = "rbf",
        *,
        degree: int = 3,
        gamma: str = "scale",
        coef0: float = 0.0,
        tol: float = 1e-3,
        C: float = 1.0,
        epsilon: float = 0.1,
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
            C=C,
            max_iter=max_iter,
        )
        self.epsilon = epsilon
        self.shrinking = shrinking
        self.cache_size = cache_size

    def train(self, X: np.ndarray, y: np.ndarray) -> "SupportVectorRegressor":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : SupportVectorRegressor
            Fitted regressor.
        """
        X = check_array(X)
        y = np.asarray(y).ravel()

        n_samples = len(X)
        self._train_X = X
        self._train_y = y

        # Get kernel function
        self._kernel_func = self._get_kernel(X)

        # Compute kernel matrix
        K = self._compute_kernel_matrix(X)

        # Initialize dual variables (alpha, alpha*)
        alpha = np.zeros(n_samples)
        alpha_star = np.zeros(n_samples)

        # SMO for SVR
        for iteration in range(self.max_iter):
            alpha_prev = alpha.copy()
            alpha_star_prev = alpha_star.copy()

            for i in range(n_samples):
                # Compute prediction
                f_i = np.sum((alpha - alpha_star) * K[i]) + self._b if hasattr(self, '_b') else np.sum((alpha - alpha_star) * K[i])

                # Compute error
                error = f_i - y[i]

                # Update alphas based on error
                if abs(error) > self.epsilon:
                    if error > 0:
                        # Increase alpha_star
                        delta = min(self.C - alpha_star[i], 0.1)
                        alpha_star[i] += delta
                    else:
                        # Increase alpha
                        delta = min(self.C - alpha[i], 0.1)
                        alpha[i] += delta

            # Update bias
            support_mask = (alpha > 1e-7) | (alpha_star > 1e-7)
            if np.any(support_mask):
                residuals = y[support_mask] - np.dot(K[support_mask][:, support_mask],
                                                       (alpha - alpha_star)[support_mask])
                # Adjust for epsilon tube
                self._b = np.mean(residuals)
            else:
                self._b = 0.0

            # Check convergence
            if np.allclose(alpha, alpha_prev, atol=self.tol) and \
               np.allclose(alpha_star, alpha_star_prev, atol=self.tol):
                break

        # Store support vectors
        support_mask = (alpha > 1e-7) | (alpha_star > 1e-7)
        self.support_ = np.where(support_mask)[0]
        self.support_vectors_ = X[support_mask]
        self.dual_coef_ = (alpha - alpha_star)[support_mask].reshape(1, -1)
        self.intercept_ = np.array([self._b])

        # Store for prediction
        self._alpha = alpha
        self._alpha_star = alpha_star

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Perform regression on samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted values.
        """
        check_is_trained(self, "support_vectors_")
        X = check_array(X)

        K = self._kernel_func(X, self.support_vectors_)
        return np.dot(K, self.dual_coef_.T).ravel() + self.intercept_[0]


class LinearSVR(RegressorMixin, SVMBase):
    """
    Linear Support Vector Regression.

    Parameters
    ----------
    epsilon : float, default=0.0
        Epsilon in epsilon-insensitive loss function.
    tol : float, default=1e-4
        Tolerance for stopping criterion.
    C : float, default=1.0
        Regularization parameter.
    loss : {"epsilon_insensitive", "squared_epsilon_insensitive"}, default="epsilon_insensitive"
        Loss function.
    fit_intercept : bool, default=True
        Whether to fit an intercept.
    intercept_scaling : float, default=1.0
        Scaling for intercept.
    dual : bool, default=True
        Solve dual or primal problem.
    max_iter : int, default=1000
        Maximum iterations.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Feature weights.
    intercept_ : float
        Intercept term.

    Examples
    --------
    >>> from nalyst.learners.svm import LinearSVR
    >>> X = [[0], [1], [2], [3]]
    >>> y = [0, 1, 2, 3]
    >>> reg = LinearSVR()
    >>> reg.train(X, y)
    LinearSVR()
    """

    def __init__(
        self,
        epsilon: float = 0.0,
        *,
        tol: float = 1e-4,
        C: float = 1.0,
        loss: Literal["epsilon_insensitive", "squared_epsilon_insensitive"] = "epsilon_insensitive",
        fit_intercept: bool = True,
        intercept_scaling: float = 1.0,
        dual: bool = True,
        max_iter: int = 1000,
        random_state: Optional[int] = None,
    ):
        super().__init__(
            kernel="linear",
            C=C,
            tol=tol,
            max_iter=max_iter,
            random_state=random_state,
        )
        self.epsilon = epsilon
        self.loss = loss
        self.fit_intercept = fit_intercept
        self.intercept_scaling = intercept_scaling
        self.dual = dual

    def train(self, X: np.ndarray, y: np.ndarray) -> "LinearSVR":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : LinearSVR
            Fitted regressor.
        """
        X = check_array(X)
        y = np.asarray(y).ravel()

        n_samples, n_features = X.shape

        # Initialize weights
        w = np.zeros(n_features)
        b = 0.0

        learning_rate = 0.01

        for iteration in range(self.max_iter):
            # Compute predictions
            pred = np.dot(X, w) + b

            # Compute residuals
            residuals = pred - y

            # Compute gradient
            if self.loss == "epsilon_insensitive":
                # Epsilon-insensitive loss
                mask_pos = residuals > self.epsilon
                mask_neg = residuals < -self.epsilon

                grad = np.zeros(n_samples)
                grad[mask_pos] = 1
                grad[mask_neg] = -1

                dw = w + self.C * np.dot(X.T, grad)
                db = self.C * np.sum(grad)
            else:
                # Squared epsilon-insensitive loss
                violations = np.maximum(0, np.abs(residuals) - self.epsilon)
                signs = np.sign(residuals)

                dw = w + 2 * self.C * np.dot(X.T, signs * violations)
                db = 2 * self.C * np.sum(signs * violations)

            # Update
            w -= learning_rate * dw
            if self.fit_intercept:
                b -= learning_rate * db

            # Check convergence
            if np.linalg.norm(dw) < self.tol:
                break

        self.coef_ = w
        self.intercept_ = b

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted values.
        """
        check_is_trained(self, "coef_")
        X = check_array(X)

        return np.dot(X, self.coef_) + self.intercept_


class NuSVR(RegressorMixin, SVMBase):
    """
    Nu-Support Vector Regression.

    Uses parameter nu to control the number of support vectors.

    Parameters
    ----------
    nu : float, default=0.5
        Upper bound on fraction of training errors and lower bound
        on fraction of support vectors.
    C : float, default=1.0
        Penalty parameter.
    kernel : {"linear", "poly", "rbf", "sigmoid"}, default="rbf"
        Kernel type.
    degree : int, default=3
        Polynomial degree.
    gamma : {"scale", "auto"} or float, default="scale"
        Kernel coefficient.
    coef0 : float, default=0.0
        Independent term.
    shrinking : bool, default=True
        Use shrinking heuristic.
    tol : float, default=1e-3
        Tolerance.
    cache_size : float, default=200
        Kernel cache size.
    max_iter : int, default=1000
        Maximum iterations.

    Examples
    --------
    >>> from nalyst.learners.svm import NuSVR
    >>> X = [[0, 0], [2, 2]]
    >>> y = [0.5, 2.5]
    >>> reg = NuSVR()
    >>> reg.train(X, y)
    NuSVR()
    """

    def __init__(
        self,
        nu: float = 0.5,
        *,
        C: float = 1.0,
        kernel: Literal["linear", "poly", "rbf", "sigmoid"] = "rbf",
        degree: int = 3,
        gamma: str = "scale",
        coef0: float = 0.0,
        shrinking: bool = True,
        tol: float = 1e-3,
        cache_size: float = 200,
        max_iter: int = 1000,
    ):
        super().__init__(
            kernel=kernel,
            degree=degree,
            gamma=gamma,
            coef0=coef0,
            C=C,
            tol=tol,
            max_iter=max_iter,
        )
        self.nu = nu
        self.shrinking = shrinking
        self.cache_size = cache_size

    def train(self, X: np.ndarray, y: np.ndarray) -> "NuSVR":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : NuSVR
            Fitted regressor.
        """
        X = check_array(X)
        y = np.asarray(y).ravel()

        # Compute epsilon from nu
        n_samples = len(X)
        epsilon = self.nu * np.std(y)

        # Use SVR with computed epsilon
        self._svr = SupportVectorRegressor(
            kernel=self.kernel,
            degree=self.degree,
            gamma=self.gamma,
            coef0=self.coef0,
            C=self.C,
            epsilon=epsilon,
            tol=self.tol,
            max_iter=self.max_iter,
        )
        self._svr.train(X, y)

        # Copy attributes
        self.support_ = self._svr.support_
        self.support_vectors_ = self._svr.support_vectors_
        self.dual_coef_ = self._svr.dual_coef_
        self.intercept_ = self._svr.intercept_

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict target values."""
        check_is_trained(self, "_svr")
        return self._svr.infer(X)
