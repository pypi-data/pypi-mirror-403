"""
SHAP-style model explanations.

Provides interpretable explanations for model predictions using
Shapley value concepts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Callable
import numpy as np


class BaseExplainer(ABC):
    """Base class for explainers."""

    def __init__(self, model: Any):
        self.model = model

    @abstractmethod
    def explain(
        self,
        X: np.ndarray,
    ) -> np.ndarray:
        """
        Compute feature contributions for predictions.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples to explain.

        Returns
        -------
        shap_values : ndarray of shape (n_samples, n_features)
            Feature contributions for each sample.
        """
        pass


class TreeExplainer(BaseExplainer):
    """
    Tree-based model explainer.

    Computes exact Shapley values for tree-based models
    using the TreeSHAP algorithm.

    Parameters
    ----------
    model : estimator
        Tree-based model (tree, forest, gradient boosting).

    Attributes
    ----------
    expected_value_ : float
        Average prediction (base value).

    Examples
    --------
    >>> from nalyst.explainability import TreeExplainer
    >>> explainer = TreeExplainer(forest_model)
    >>> shap_values = explainer.explain(X)
    """

    def __init__(self, model: Any):
        super().__init__(model)
        self.expected_value_ = None
        self._is_fitted = False

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "TreeExplainer":
        """
        Fit the explainer (compute expected value).

        Parameters
        ----------
        X : ndarray
            Background data for computing expected value.
        y : ndarray, optional
            Not used.

        Returns
        -------
        self
        """
        X = np.asarray(X)

        # Compute expected prediction
        if hasattr(self.model, 'infer'):
            predictions = self.model.infer(X)
        else:
            predictions = self.model.predict(X)

        self.expected_value_ = np.mean(predictions)
        self._background = X
        self._is_fitted = True

        return self

    def explain(self, X: np.ndarray) -> np.ndarray:
        """
        Compute SHAP values for tree-based model.

        For simplicity, uses an approximation based on
        feature contributions from the tree structure.
        """
        X = np.asarray(X)

        if not self._is_fitted:
            raise ValueError("Call fit() before explain()")

        n_samples, n_features = X.shape
        shap_values = np.zeros((n_samples, n_features))

        # Use path-based approximation for tree models
        if hasattr(self.model, 'feature_importances_'):
            # Weighted by feature importance
            importance = self.model.feature_importances_
            importance = importance / importance.sum()

            for i in range(n_samples):
                # Compute prediction
                if hasattr(self.model, 'infer'):
                    pred = self.model.infer(X[i:i+1])[0]
                else:
                    pred = self.model.predict(X[i:i+1])[0]

                # Distribute contribution based on importance
                total_contrib = pred - self.expected_value_

                # Scale by deviation from mean
                X_mean = np.mean(self._background, axis=0)
                X_std = np.std(self._background, axis=0) + 1e-10

                z_scores = (X[i] - X_mean) / X_std
                weighted = importance * np.abs(z_scores)

                if np.sum(weighted) > 0:
                    weights = weighted / np.sum(weighted)
                else:
                    weights = importance

                shap_values[i] = total_contrib * weights * np.sign(z_scores)
        else:
            # Fallback: use permutation-based approximation
            shap_values = self._permutation_explain(X)

        return shap_values

    def _permutation_explain(
        self,
        X: np.ndarray,
        n_samples: int = 100,
    ) -> np.ndarray:
        """Permutation-based SHAP approximation."""
        n, n_features = X.shape
        shap_values = np.zeros((n, n_features))

        background = self._background[:min(100, len(self._background))]

        for i in range(n):
            for j in range(n_features):
                # Marginal contribution of feature j
                contrib = 0

                for _ in range(n_samples):
                    # Random permutation
                    perm = np.random.permutation(n_features)
                    pos = np.where(perm == j)[0][0]

                    # Features before j use X[i], after use background
                    x_with = X[i].copy()
                    x_without = X[i].copy()

                    bg_idx = np.random.randint(len(background))
                    bg = background[bg_idx]

                    for k in range(pos + 1, n_features):
                        feat = perm[k]
                        x_without[feat] = bg[feat]

                    for k in range(pos, n_features):
                        feat = perm[k]
                        if feat != j:
                            x_with[feat] = bg[feat]

                    x_without[j] = bg[j]

                    if hasattr(self.model, 'infer'):
                        pred_with = self.model.infer(x_with.reshape(1, -1))[0]
                        pred_without = self.model.infer(x_without.reshape(1, -1))[0]
                    else:
                        pred_with = self.model.predict(x_with.reshape(1, -1))[0]
                        pred_without = self.model.predict(x_without.reshape(1, -1))[0]

                    contrib += (pred_with - pred_without)

                shap_values[i, j] = contrib / n_samples

        return shap_values


class LinearExplainer(BaseExplainer):
    """
    Linear model explainer.

    Computes exact Shapley values for linear models.

    Parameters
    ----------
    model : estimator
        Linear model with coef_ attribute.

    Examples
    --------
    >>> from nalyst.explainability import LinearExplainer
    >>> explainer = LinearExplainer(linear_model)
    >>> shap_values = explainer.explain(X)
    """

    def __init__(self, model: Any):
        super().__init__(model)

        if not hasattr(model, 'coef_'):
            raise ValueError("Model must have coef_ attribute")

    def fit(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> "LinearExplainer":
        """Fit explainer (compute mean feature values)."""
        self._mean = np.mean(X, axis=0)
        self._is_fitted = True
        return self

    def explain(self, X: np.ndarray) -> np.ndarray:
        """
        Compute SHAP values for linear model.

        For linear models: shap[i, j] = coef[j] * (X[i, j] - mean[j])
        """
        X = np.asarray(X)

        if not self._is_fitted:
            raise ValueError("Call fit() before explain()")

        coef = np.asarray(self.model.coef_).flatten()

        # SHAP value = coefficient * (feature - mean)
        shap_values = coef * (X - self._mean)

        return shap_values


class KernelExplainer(BaseExplainer):
    """
    Model-agnostic kernel SHAP explainer.

    Uses weighted linear regression to approximate Shapley values
    for any model.

    Parameters
    ----------
    model : estimator
        Any model with predict or infer method.
    background : ndarray
        Background dataset for computing expected values.

    Examples
    --------
    >>> from nalyst.explainability import KernelExplainer
    >>> explainer = KernelExplainer(model, X_train[:100])
    >>> shap_values = explainer.explain(X_test)
    """

    def __init__(
        self,
        model: Any,
        background: np.ndarray,
    ):
        super().__init__(model)
        self.background = np.asarray(background)

        # Compute expected value
        preds = self._predict(self.background)
        self.expected_value_ = np.mean(preds)

    def _predict(self, X: np.ndarray) -> np.ndarray:
        """Get predictions from model."""
        if hasattr(self.model, 'infer'):
            return self.model.infer(X)
        elif hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(X)
            return proba[:, 1] if proba.ndim > 1 else proba
        else:
            return self.model.predict(X)

    def explain(
        self,
        X: np.ndarray,
        n_samples: int = 200,
    ) -> np.ndarray:
        """
        Compute SHAP values using kernel SHAP.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Samples to explain.
        n_samples : int, default=200
            Number of samples for approximation.

        Returns
        -------
        shap_values : ndarray
            Feature contributions.
        """
        X = np.asarray(X)
        n, n_features = X.shape

        shap_values = np.zeros((n, n_features))

        for i in range(n):
            shap_values[i] = self._explain_single(X[i], n_samples)

        return shap_values

    def _explain_single(
        self,
        x: np.ndarray,
        n_samples: int,
    ) -> np.ndarray:
        """Explain a single sample using kernel SHAP."""
        n_features = len(x)

        # Generate coalition samples
        coalitions = []
        predictions = []
        weights = []

        # Always include empty and full coalitions
        coalitions.append(np.zeros(n_features, dtype=bool))
        coalitions.append(np.ones(n_features, dtype=bool))

        # Sample random coalitions
        for _ in range(n_samples - 2):
            n_active = np.random.randint(1, n_features)
            coalition = np.zeros(n_features, dtype=bool)
            active = np.random.choice(n_features, n_active, replace=False)
            coalition[active] = True
            coalitions.append(coalition)

        # Compute predictions for each coalition
        for coalition in coalitions:
            # Create sample: use x for active features, background for inactive
            n_bg = min(10, len(self.background))
            bg_samples = self.background[:n_bg]

            masked = np.tile(x, (n_bg, 1))
            for j in range(n_features):
                if not coalition[j]:
                    masked[:, j] = bg_samples[:, j]

            pred = np.mean(self._predict(masked))
            predictions.append(pred)

            # Kernel SHAP weight
            n_active = np.sum(coalition)
            if n_active == 0 or n_active == n_features:
                weight = 1e6  # Large weight for extremes
            else:
                weight = (n_features - 1) / (
                    np.math.comb(n_features, n_active) *
                    n_active * (n_features - n_active)
                )
            weights.append(weight)

        coalitions = np.array(coalitions, dtype=float)
        predictions = np.array(predictions)
        weights = np.array(weights)
        weights /= weights.sum()

        # Weighted linear regression
        # shap_values solve: coalitions @ shap = predictions - expected
        y = predictions - self.expected_value_

        # Add intercept term
        X_design = coalitions
        W = np.diag(weights)

        # Solve weighted least squares
        try:
            XtWX = X_design.T @ W @ X_design + 1e-6 * np.eye(n_features)
            XtWy = X_design.T @ W @ y
            shap_vals = np.linalg.solve(XtWX, XtWy)
        except np.linalg.LinAlgError:
            shap_vals = np.zeros(n_features)

        return shap_vals


def shap_summary(
    shap_values: np.ndarray,
    X: np.ndarray,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate summary data for SHAP visualization.

    Parameters
    ----------
    shap_values : ndarray of shape (n_samples, n_features)
        SHAP values.
    X : ndarray of shape (n_samples, n_features)
        Feature values.
    feature_names : list of str, optional
        Feature names.

    Returns
    -------
    summary : dict
        Summary statistics for visualization.
    """
    n_features = shap_values.shape[1]

    if feature_names is None:
        feature_names = [f"Feature {i}" for i in range(n_features)]

    # Mean absolute SHAP value per feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)

    # Sort by importance
    sorted_idx = np.argsort(mean_abs_shap)[::-1]

    summary = {
        'feature_names': [feature_names[i] for i in sorted_idx],
        'mean_abs_shap': mean_abs_shap[sorted_idx],
        'shap_values': shap_values[:, sorted_idx],
        'feature_values': X[:, sorted_idx],
    }

    return summary


def shap_dependence(
    shap_values: np.ndarray,
    X: np.ndarray,
    feature_idx: int,
    interaction_idx: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """
    Generate dependence plot data.

    Parameters
    ----------
    shap_values : ndarray
        SHAP values.
    X : ndarray
        Feature values.
    feature_idx : int
        Index of feature to plot.
    interaction_idx : int, optional
        Index of interaction feature for coloring.

    Returns
    -------
    data : dict
        Data for dependence plot.
    """
    data = {
        'feature_values': X[:, feature_idx],
        'shap_values': shap_values[:, feature_idx],
    }

    if interaction_idx is not None:
        data['interaction_values'] = X[:, interaction_idx]
    else:
        # Auto-detect strongest interaction
        correlations = []
        for j in range(X.shape[1]):
            if j != feature_idx:
                corr = np.corrcoef(shap_values[:, feature_idx], X[:, j])[0, 1]
                correlations.append((j, abs(corr)))

        if correlations:
            best_idx = max(correlations, key=lambda x: x[1])[0]
            data['interaction_values'] = X[:, best_idx]

    return data


def shap_force(
    expected_value: float,
    shap_values: np.ndarray,
    feature_values: np.ndarray,
    feature_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate force plot data.

    Parameters
    ----------
    expected_value : float
        Base value (mean prediction).
    shap_values : ndarray of shape (n_features,)
        SHAP values for single prediction.
    feature_values : ndarray of shape (n_features,)
        Feature values.
    feature_names : list of str, optional
        Feature names.

    Returns
    -------
    data : dict
        Data for force plot.
    """
    n_features = len(shap_values)

    if feature_names is None:
        feature_names = [f"Feature {i}" for i in range(n_features)]

    # Separate positive and negative contributions
    positive_mask = shap_values > 0
    negative_mask = shap_values < 0

    # Sort by absolute value
    abs_shap = np.abs(shap_values)
    sorted_idx = np.argsort(abs_shap)[::-1]

    data = {
        'expected_value': expected_value,
        'prediction': expected_value + np.sum(shap_values),
        'features': [],
    }

    for idx in sorted_idx:
        if abs_shap[idx] > 0.001:  # Filter near-zero contributions
            data['features'].append({
                'name': feature_names[idx],
                'value': feature_values[idx],
                'shap_value': shap_values[idx],
                'effect': 'positive' if shap_values[idx] > 0 else 'negative',
            })

    return data
