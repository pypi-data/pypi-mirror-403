"""
Quantile Regression models.
"""

from __future__ import annotations

from typing import Optional, List, Union
import numpy as np


class QuantileRegressor:
    """
    Linear Quantile Regression.

    Estimates conditional quantiles using linear programming.

    Parameters
    ----------
    quantile : float, default=0.5
        Target quantile (0 < quantile < 1).
    alpha : float, default=0.0
        L1 regularization penalty.
    max_iter : int, default=1000
        Maximum iterations.
    tol : float, default=1e-5
        Convergence tolerance.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Coefficients.
    intercept_ : float
        Intercept.

    Examples
    --------
    >>> from nalyst.quantile import QuantileRegressor
    >>> qr = QuantileRegressor(quantile=0.5)  # Median regression
    >>> qr.train(X, y)
    >>> y_pred = qr.infer(X_new)
    """

    def __init__(
        self,
        quantile: float = 0.5,
        alpha: float = 0.0,
        max_iter: int = 1000,
        tol: float = 1e-5,
    ):
        if not 0 < quantile < 1:
            raise ValueError("quantile must be between 0 and 1")

        self.quantile = quantile
        self.alpha = alpha
        self.max_iter = max_iter
        self.tol = tol

    def train(self, X: np.ndarray, y: np.ndarray) -> "QuantileRegressor":
        """
        Fit quantile regression.

        Uses iteratively reweighted least squares (IRLS) approximation.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Feature matrix.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        n_samples, n_features = X.shape

        # Add intercept column
        X_design = np.column_stack([np.ones(n_samples), X])

        # Initialize with OLS
        beta = np.linalg.lstsq(X_design, y, rcond=None)[0]

        tau = self.quantile

        for iteration in range(self.max_iter):
            # Residuals
            residuals = y - X_design @ beta

            # IRLS weights for check loss
            # Weight = tau / |r| if r > 0, (1-tau) / |r| if r < 0
            eps = 1e-6
            weights = np.where(
                residuals >= 0,
                tau / (np.abs(residuals) + eps),
                (1 - tau) / (np.abs(residuals) + eps)
            )

            # Weighted least squares
            W = np.diag(weights)

            # L1 regularization via penalty
            reg = self.alpha * np.eye(len(beta))
            reg[0, 0] = 0  # Don't regularize intercept

            try:
                XtWX = X_design.T @ W @ X_design + reg
                XtWy = X_design.T @ W @ y
                beta_new = np.linalg.solve(XtWX, XtWy)
            except np.linalg.LinAlgError:
                break

            # Check convergence
            if np.max(np.abs(beta_new - beta)) < self.tol:
                beta = beta_new
                break

            beta = beta_new

        self.intercept_ = beta[0]
        self.coef_ = beta[1:]

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict quantiles.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted quantiles.
        """
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_

    def fit(self, X: np.ndarray, y: np.ndarray) -> "QuantileRegressor":
        """Alias for train."""
        return self.train(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Alias for infer."""
        return self.infer(X)


class QuantileForest:
    """
    Quantile Random Forest.

    Estimates conditional quantiles using random forest predictions.

    Parameters
    ----------
    n_estimators : int, default=100
        Number of trees.
    max_depth : int, optional
        Maximum tree depth.
    min_samples_leaf : int, default=1
        Minimum samples per leaf.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from nalyst.quantile import QuantileForest
    >>> qf = QuantileForest(n_estimators=100)
    >>> qf.train(X, y)
    >>> q50 = qf.predict(X_new, quantile=0.5)
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        min_samples_leaf: int = 1,
        random_state: Optional[int] = None,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "QuantileForest":
        """
        Fit the quantile forest.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        self.X_ = X
        self.y_ = y

        if self.random_state is not None:
            np.random.seed(self.random_state)

        n_samples, n_features = X.shape

        self.trees_ = []

        for _ in range(self.n_estimators):
            # Bootstrap sample
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_boot = X[indices]
            y_boot = y[indices]

            # Fit tree
            tree = self._build_tree(X_boot, y_boot, np.arange(n_samples))
            self.trees_.append((tree, indices))

        return self

    def _build_tree(
        self,
        X: np.ndarray,
        y: np.ndarray,
        original_indices: np.ndarray,
        depth: int = 0,
    ) -> dict:
        """Build a single tree."""
        n_samples, n_features = X.shape

        # Stopping criteria
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples <= self.min_samples_leaf:
            return {
                'leaf': True,
                'indices': original_indices,
            }

        # Find best split
        best_score = np.inf
        best_feature = 0
        best_threshold = 0

        for feature in range(n_features):
            thresholds = np.unique(X[:, feature])

            for threshold in thresholds[:-1]:
                left_mask = X[:, feature] <= threshold
                right_mask = ~left_mask

                if np.sum(left_mask) < self.min_samples_leaf or \
                   np.sum(right_mask) < self.min_samples_leaf:
                    continue

                # MSE score
                left_var = np.var(y[left_mask]) if np.sum(left_mask) > 0 else 0
                right_var = np.var(y[right_mask]) if np.sum(right_mask) > 0 else 0

                score = (np.sum(left_mask) * left_var +
                        np.sum(right_mask) * right_var)

                if score < best_score:
                    best_score = score
                    best_feature = feature
                    best_threshold = threshold

        # Check if we found a valid split
        if best_score == np.inf:
            return {
                'leaf': True,
                'indices': original_indices,
            }

        # Split
        left_mask = X[:, best_feature] <= best_threshold

        left_tree = self._build_tree(
            X[left_mask], y[left_mask],
            original_indices[left_mask], depth + 1
        )
        right_tree = self._build_tree(
            X[~left_mask], y[~left_mask],
            original_indices[~left_mask], depth + 1
        )

        return {
            'leaf': False,
            'feature': best_feature,
            'threshold': best_threshold,
            'left': left_tree,
            'right': right_tree,
        }

    def _get_leaf_indices(self, tree: dict, x: np.ndarray) -> np.ndarray:
        """Get leaf indices for a single sample."""
        if tree['leaf']:
            return tree['indices']

        if x[tree['feature']] <= tree['threshold']:
            return self._get_leaf_indices(tree['left'], x)
        else:
            return self._get_leaf_indices(tree['right'], x)

    def infer(
        self,
        X: np.ndarray,
        quantile: Union[float, List[float]] = 0.5,
    ) -> np.ndarray:
        """
        Predict quantiles.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.
        quantile : float or list of float
            Target quantile(s).

        Returns
        -------
        y_pred : ndarray
            Predicted quantiles.
        """
        X = np.asarray(X)
        n_samples = len(X)

        if isinstance(quantile, (int, float)):
            quantiles = [quantile]
        else:
            quantiles = list(quantile)

        predictions = np.zeros((n_samples, len(quantiles)))

        for i in range(n_samples):
            # Collect all y values in leaves across trees
            all_y = []

            for tree, boot_indices in self.trees_:
                leaf_indices = self._get_leaf_indices(tree, X[i])
                actual_indices = boot_indices[leaf_indices]
                all_y.extend(self.y_[actual_indices])

            all_y = np.array(all_y)

            # Compute quantiles
            for j, q in enumerate(quantiles):
                predictions[i, j] = np.percentile(all_y, q * 100)

        if len(quantiles) == 1:
            return predictions.flatten()

        return predictions

    def predict(
        self,
        X: np.ndarray,
        quantile: Union[float, List[float]] = 0.5,
    ) -> np.ndarray:
        """Alias for infer."""
        return self.infer(X, quantile)


class QuantileGradientBoosting:
    """
    Gradient Boosting for Quantile Regression.

    Uses pinball loss for quantile estimation.

    Parameters
    ----------
    quantile : float, default=0.5
        Target quantile.
    n_estimators : int, default=100
        Number of boosting stages.
    learning_rate : float, default=0.1
        Shrinkage factor.
    max_depth : int, default=3
        Maximum tree depth.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from nalyst.quantile import QuantileGradientBoosting
    >>> qgb = QuantileGradientBoosting(quantile=0.9)
    >>> qgb.train(X, y)
    >>> y_pred = qgb.infer(X_new)
    """

    def __init__(
        self,
        quantile: float = 0.5,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 3,
        random_state: Optional[int] = None,
    ):
        self.quantile = quantile
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "QuantileGradientBoosting":
        """
        Fit the quantile gradient boosting model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
        """
        X = np.asarray(X)
        y = np.asarray(y).flatten()

        if self.random_state is not None:
            np.random.seed(self.random_state)

        n_samples = len(y)
        tau = self.quantile

        # Initialize with target quantile
        self.init_pred_ = np.percentile(y, tau * 100)

        # Current predictions
        F = np.full(n_samples, self.init_pred_)

        self.trees_ = []

        for _ in range(self.n_estimators):
            # Negative gradient of pinball loss
            residuals = y - F
            pseudo_residuals = np.where(residuals >= 0, tau, -(1 - tau))

            # Fit tree to pseudo-residuals
            tree = self._build_tree(X, residuals, pseudo_residuals)
            self.trees_.append(tree)

            # Update predictions
            leaf_values = self._get_leaf_values(tree, X)
            F += self.learning_rate * leaf_values

        return self

    def _build_tree(
        self,
        X: np.ndarray,
        residuals: np.ndarray,
        pseudo_residuals: np.ndarray,
        depth: int = 0,
    ) -> dict:
        """Build a regression tree for pseudo-residuals."""
        n_samples = len(residuals)

        if depth >= self.max_depth or n_samples <= 5:
            # Leaf value: quantile of residuals in leaf
            return {
                'leaf': True,
                'value': np.percentile(residuals, self.quantile * 100),
            }

        best_score = np.inf
        best_feature = 0
        best_threshold = 0

        n_features = X.shape[1]

        for feature in range(n_features):
            thresholds = np.unique(X[:, feature])

            for threshold in thresholds[1:-1]:
                left_mask = X[:, feature] <= threshold

                if np.sum(left_mask) < 3 or np.sum(~left_mask) < 3:
                    continue

                # Variance reduction
                score = (np.sum(left_mask) * np.var(residuals[left_mask]) +
                        np.sum(~left_mask) * np.var(residuals[~left_mask]))

                if score < best_score:
                    best_score = score
                    best_feature = feature
                    best_threshold = threshold

        if best_score == np.inf:
            return {
                'leaf': True,
                'value': np.percentile(residuals, self.quantile * 100),
            }

        left_mask = X[:, best_feature] <= best_threshold

        return {
            'leaf': False,
            'feature': best_feature,
            'threshold': best_threshold,
            'left': self._build_tree(
                X[left_mask], residuals[left_mask],
                pseudo_residuals[left_mask], depth + 1
            ),
            'right': self._build_tree(
                X[~left_mask], residuals[~left_mask],
                pseudo_residuals[~left_mask], depth + 1
            ),
        }

    def _get_leaf_values(self, tree: dict, X: np.ndarray) -> np.ndarray:
        """Get leaf values for all samples."""
        values = np.zeros(len(X))

        for i, x in enumerate(X):
            node = tree
            while not node['leaf']:
                if x[node['feature']] <= node['threshold']:
                    node = node['left']
                else:
                    node = node['right']
            values[i] = node['value']

        return values

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict quantiles.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Features.

        Returns
        -------
        y_pred : ndarray
            Predicted quantiles.
        """
        X = np.asarray(X)

        F = np.full(len(X), self.init_pred_)

        for tree in self.trees_:
            F += self.learning_rate * self._get_leaf_values(tree, X)

        return F

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Alias for infer."""
        return self.infer(X)
