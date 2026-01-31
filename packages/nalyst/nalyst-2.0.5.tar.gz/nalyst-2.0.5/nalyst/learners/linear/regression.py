"""
Linear regression models.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union

import numpy as np
from scipy import linalg

from nalyst.core.foundation import BaseLearner, RegressorMixin
from nalyst.core.validation import check_X_y, check_array, check_is_trained
from nalyst.core.tags import LearnerTags, TargetTags, RegressorTags, InputTags
from nalyst.learners.linear.base import LinearModel, _rescale_data


class OrdinaryLinearRegressor(RegressorMixin, LinearModel):
    """
    Ordinary least squares linear regression.

    Fits a linear model to minimize the residual sum of squares:
    ||y - Xw||^2

    Parameters
    ----------
    fit_intercept : bool, default=True
        Whether to calculate the intercept for this model.
    copy_X : bool, default=True
        If True, X will be copied; else it may be overwritten.
    n_jobs : int, optional
        Number of jobs for computation.
    positive : bool, default=False
        If True, force coefficients to be positive (uses NNLS).

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,) or (n_targets, n_features)
        Estimated coefficients.
    intercept_ : float or ndarray of shape (n_targets,)
        Independent term in the model.
    rank_ : int
        Rank of X matrix.
    singular_ : ndarray of shape (min(X, y),)
        Singular values of X.
    n_features_in_ : int
        Number of features seen during training.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.linear import OrdinaryLinearRegressor
    >>> X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    >>> y = np.dot(X, np.array([1, 2])) + 3
    >>> reg = OrdinaryLinearRegressor()
    >>> reg.train(X, y)
    OrdinaryLinearRegressor()
    >>> reg.coef_
    array([1., 2.])
    >>> reg.intercept_
    3.0
    >>> reg.infer([[3, 5]])
    array([16.])
    """

    def __init__(
        self,
        *,
        fit_intercept: bool = True,
        copy_X: bool = True,
        n_jobs: Optional[int] = None,
        positive: bool = False,
    ):
        self.fit_intercept = fit_intercept
        self.copy_X = copy_X
        self.n_jobs = n_jobs
        self.positive = positive

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "OrdinaryLinearRegressor":
        """
        Fit linear model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,) or (n_samples, n_targets)
            Target values.
        sample_weight : array-like of shape (n_samples,), optional
            Individual weights for each sample.

        Returns
        -------
        self : OrdinaryLinearRegressor
            Fitted learner.
        """
        X, y = check_X_y(X, y, multi_output=True, y_numeric=True)

        self.n_features_in_ = X.shape[1]

        if hasattr(X, "columns"):
            self.feature_names_in_ = np.asarray(X.columns)

        if sample_weight is not None:
            sample_weight = np.asarray(sample_weight)
            X, y, _ = _rescale_data(X, y, sample_weight)

        X, y, X_offset, y_offset, X_scale = self._preprocess_data(
            X, y,
            fit_intercept=self.fit_intercept,
            copy=self.copy_X,
            sample_weight=sample_weight,
        )

        if self.positive:
            # Non-negative least squares
            from scipy.optimize import nnls
            if y.ndim == 1:
                self.coef_, _ = nnls(X, y)
            else:
                self.coef_ = np.vstack([nnls(X, y[:, i])[0] for i in range(y.shape[1])])
            self.rank_ = X.shape[1]
            self.singular_ = None
        else:
            # Standard least squares using SVD
            self.coef_, residues, self.rank_, self.singular_ = linalg.lstsq(X, y)
            self.coef_ = self.coef_.T

        if y.ndim == 1:
            self.coef_ = self.coef_.ravel()

        self._set_intercept(X_offset, y_offset, X_scale)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the linear model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Predicted values.
        """
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True, multi_output=True),
            regressor_tags=RegressorTags(multi_target=True),
            input_tags=InputTags(sparse=True),
        )


class RidgeRegressor(RegressorMixin, LinearModel):
    """
    Ridge regression with L2 regularization.

    Minimizes: ||y - Xw||^2 + alpha * ||w||^2

    Parameters
    ----------
    alpha : float or array-like, default=1.0
        Regularization strength. Larger values specify stronger
        regularization. Can be an array for per-target alphas.
    fit_intercept : bool, default=True
        Whether to calculate the intercept.
    copy_X : bool, default=True
        If True, X will be copied.
    max_iter : int, optional
        Maximum iterations for iterative solvers.
    tol : float, default=1e-4
        Precision of the solution for iterative solvers.
    solver : {"auto", "svd", "cholesky", "lsqr", "sparse_cg", "sag", "saga", "lbfgs"}
        Solver to use.
    positive : bool, default=False
        Force positive coefficients (requires lbfgs solver).
    random_state : int, RandomState, or None
        Random state for solvers that use randomization.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,) or (n_targets, n_features)
        Weight vector(s).
    intercept_ : float or ndarray of shape (n_targets,)
        Independent term.
    n_iter_ : int or None
        Number of iterations (for iterative solvers).
    n_features_in_ : int
        Number of features seen during training.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.linear import RidgeRegressor
    >>> X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
    >>> y = np.dot(X, np.array([1, 2])) + 3
    >>> reg = RidgeRegressor(alpha=0.5)
    >>> reg.train(X, y)
    RidgeRegressor(alpha=0.5)
    >>> reg.infer([[3, 5]])
    array([15.89...])
    """

    def __init__(
        self,
        *,
        alpha: Union[float, np.ndarray] = 1.0,
        fit_intercept: bool = True,
        copy_X: bool = True,
        max_iter: Optional[int] = None,
        tol: float = 1e-4,
        solver: str = "auto",
        positive: bool = False,
        random_state: Optional[int] = None,
    ):
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.copy_X = copy_X
        self.max_iter = max_iter
        self.tol = tol
        self.solver = solver
        self.positive = positive
        self.random_state = random_state

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "RidgeRegressor":
        """
        Fit Ridge regression model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,) or (n_samples, n_targets)
            Target values.
        sample_weight : array-like of shape (n_samples,), optional
            Individual weights.

        Returns
        -------
        self : RidgeRegressor
        """
        X, y = check_X_y(X, y, multi_output=True, y_numeric=True)

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        if sample_weight is not None:
            sample_weight = np.asarray(sample_weight)
            X, y, _ = _rescale_data(X, y, sample_weight)

        X, y, X_offset, y_offset, X_scale = self._preprocess_data(
            X, y,
            fit_intercept=self.fit_intercept,
            copy=self.copy_X,
        )

        # Use Cholesky decomposition for efficiency
        alpha = np.atleast_1d(self.alpha)

        if len(alpha) == 1:
            alpha = alpha[0]

        if y.ndim == 1:
            y = y.reshape(-1, 1)
            squeeze_output = True
        else:
            squeeze_output = False

        n_targets = y.shape[1]

        # Compute XtX + alpha*I and Xty
        A = X.T @ X
        Xy = X.T @ y

        if isinstance(alpha, (int, float)):
            A.flat[::n_features + 1] += alpha
        else:
            # Different alpha per target - solve separately
            coefs = []
            for i in range(n_targets):
                A_i = A.copy()
                A_i.flat[::n_features + 1] += alpha[min(i, len(alpha) - 1)]
                coefs.append(linalg.solve(A_i, Xy[:, i], assume_a="pos"))
            self.coef_ = np.vstack(coefs)

        if not hasattr(self, "coef_"):
            self.coef_ = linalg.solve(A, Xy, assume_a="pos").T

        if squeeze_output:
            self.coef_ = self.coef_.ravel()

        self._set_intercept(X_offset, y_offset, X_scale)
        self.n_iter_ = None

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using Ridge regression model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,) or (n_samples, n_targets)
            Predicted values.
        """
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True, multi_output=True),
            regressor_tags=RegressorTags(multi_target=True),
            input_tags=InputTags(sparse=True),
        )


class LassoRegressor(RegressorMixin, LinearModel):
    """
    Lasso regression with L1 regularization.

    Minimizes: (1/2n) * ||y - Xw||^2 + alpha * ||w||_1

    The L1 penalty produces sparse solutions, setting some
    coefficients exactly to zero.

    Parameters
    ----------
    alpha : float, default=1.0
        Regularization strength.
    fit_intercept : bool, default=True
        Whether to calculate the intercept.
    max_iter : int, default=1000
        Maximum number of iterations.
    tol : float, default=1e-4
        Tolerance for optimization convergence.
    warm_start : bool, default=False
        Whether to reuse solution from previous call as init.
    positive : bool, default=False
        Force positive coefficients.
    random_state : int, optional
        Random state for reproducibility.
    selection : {"cyclic", "random"}, default="cyclic"
        Feature selection order for coordinate descent.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Estimated coefficients.
    intercept_ : float
        Independent term.
    n_iter_ : int
        Number of iterations run.
    n_features_in_ : int
        Number of features seen during training.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.linear import LassoRegressor
    >>> X = np.array([[1, 1], [1, 2], [2, 2]])
    >>> y = np.array([1, 2, 3])
    >>> reg = LassoRegressor(alpha=0.1)
    >>> reg.train(X, y)
    LassoRegressor(alpha=0.1)
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        fit_intercept: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-4,
        warm_start: bool = False,
        positive: bool = False,
        random_state: Optional[int] = None,
        selection: Literal["cyclic", "random"] = "cyclic",
    ):
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.tol = tol
        self.warm_start = warm_start
        self.positive = positive
        self.random_state = random_state
        self.selection = selection

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "LassoRegressor":
        """
        Fit Lasso model with coordinate descent.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : LassoRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        # Preprocessing
        X, y, X_offset, y_offset, X_scale = self._preprocess_data(
            X, y,
            fit_intercept=self.fit_intercept,
            copy=True,
        )

        # Initialize coefficients
        if self.warm_start and hasattr(self, "coef_"):
            coef = self.coef_.copy()
        else:
            coef = np.zeros(n_features)

        # Coordinate descent
        l1_reg = self.alpha * n_samples

        rng = np.random.RandomState(self.random_state)

        for iteration in range(self.max_iter):
            coef_old = coef.copy()

            if self.selection == "random":
                feature_order = rng.permutation(n_features)
            else:
                feature_order = np.arange(n_features)

            for j in feature_order:
                # Compute partial residual
                residual = y - X @ coef + X[:, j] * coef[j]

                # Update coefficient using soft thresholding
                rho = X[:, j] @ residual
                z = X[:, j] @ X[:, j]

                if self.positive:
                    coef[j] = self._soft_threshold(rho, l1_reg) / z
                    coef[j] = max(0, coef[j])
                else:
                    coef[j] = self._soft_threshold(rho, l1_reg) / z

            # Check convergence
            coef_change = np.abs(coef - coef_old).max()
            if coef_change < self.tol:
                break

        self.coef_ = coef
        self.n_iter_ = iteration + 1

        self._set_intercept(X_offset, y_offset, X_scale)

        return self

    @staticmethod
    def _soft_threshold(x: float, threshold: float) -> float:
        """Apply soft thresholding operator."""
        if x > threshold:
            return x - threshold
        elif x < -threshold:
            return x + threshold
        else:
            return 0.0

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using Lasso model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted values.
        """
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )


class ElasticNetRegressor(RegressorMixin, LinearModel):
    """
    Elastic Net regression combining L1 and L2 regularization.

    Minimizes: (1/2n) * ||y - Xw||^2 + alpha * l1_ratio * ||w||_1
               + 0.5 * alpha * (1 - l1_ratio) * ||w||^2

    Parameters
    ----------
    alpha : float, default=1.0
        Overall regularization strength.
    l1_ratio : float, default=0.5
        Mixing parameter. 0 = pure L2 (Ridge), 1 = pure L1 (Lasso).
    fit_intercept : bool, default=True
        Whether to calculate the intercept.
    max_iter : int, default=1000
        Maximum iterations.
    tol : float, default=1e-4
        Convergence tolerance.
    warm_start : bool, default=False
        Reuse previous solution.
    positive : bool, default=False
        Force positive coefficients.
    random_state : int, optional
        Random state.
    selection : {"cyclic", "random"}, default="cyclic"
        Feature selection order.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Estimated coefficients.
    intercept_ : float
        Independent term.
    n_iter_ : int
        Number of iterations.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.linear import ElasticNetRegressor
    >>> X = np.array([[1, 1], [1, 2], [2, 2]])
    >>> y = np.array([1, 2, 3])
    >>> reg = ElasticNetRegressor(alpha=0.5, l1_ratio=0.5)
    >>> reg.train(X, y)
    ElasticNetRegressor(alpha=0.5)
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        l1_ratio: float = 0.5,
        fit_intercept: bool = True,
        max_iter: int = 1000,
        tol: float = 1e-4,
        warm_start: bool = False,
        positive: bool = False,
        random_state: Optional[int] = None,
        selection: Literal["cyclic", "random"] = "cyclic",
    ):
        self.alpha = alpha
        self.l1_ratio = l1_ratio
        self.fit_intercept = fit_intercept
        self.max_iter = max_iter
        self.tol = tol
        self.warm_start = warm_start
        self.positive = positive
        self.random_state = random_state
        self.selection = selection

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "ElasticNetRegressor":
        """
        Fit Elastic Net model.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : ElasticNetRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        n_samples, n_features = X.shape
        self.n_features_in_ = n_features

        X, y, X_offset, y_offset, X_scale = self._preprocess_data(
            X, y,
            fit_intercept=self.fit_intercept,
            copy=True,
        )

        if self.warm_start and hasattr(self, "coef_"):
            coef = self.coef_.copy()
        else:
            coef = np.zeros(n_features)

        l1_reg = self.alpha * self.l1_ratio * n_samples
        l2_reg = self.alpha * (1 - self.l1_ratio) * n_samples

        rng = np.random.RandomState(self.random_state)

        for iteration in range(self.max_iter):
            coef_old = coef.copy()

            if self.selection == "random":
                feature_order = rng.permutation(n_features)
            else:
                feature_order = np.arange(n_features)

            for j in feature_order:
                residual = y - X @ coef + X[:, j] * coef[j]

                rho = X[:, j] @ residual
                z = X[:, j] @ X[:, j] + l2_reg

                if self.positive:
                    coef[j] = max(0, self._soft_threshold(rho, l1_reg)) / z
                else:
                    coef[j] = self._soft_threshold(rho, l1_reg) / z

            coef_change = np.abs(coef - coef_old).max()
            if coef_change < self.tol:
                break

        self.coef_ = coef
        self.n_iter_ = iteration + 1

        self._set_intercept(X_offset, y_offset, X_scale)

        return self

    @staticmethod
    def _soft_threshold(x: float, threshold: float) -> float:
        """Apply soft thresholding."""
        if x > threshold:
            return x - threshold
        elif x < -threshold:
            return x + threshold
        return 0.0

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict using Elastic Net model."""
        return self._decision_function(X)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )
