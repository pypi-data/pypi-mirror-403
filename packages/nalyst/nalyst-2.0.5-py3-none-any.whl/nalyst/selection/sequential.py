"""
Sequential Feature Selection.
"""

from __future__ import annotations

from typing import Optional, Literal, Callable

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class SequentialFeatureSelector(TransformerMixin, BaseLearner):
    """
    Sequential Feature Selection (Forward or Backward).

    Parameters
    ----------
    estimator : object
        A supervised learning estimator.
    n_features_to_select : int or float, default="auto"
        Number of features to select.
    tol : float, optional
        Tolerance for stopping. If improvement is less than tol, stop.
    direction : {"forward", "backward"}, default="forward"
        Whether to add or remove features.
    scoring : str or callable, optional
        Scoring metric.
    cv : int, default=5
        Cross-validation folds.

    Attributes
    ----------
    n_features_to_select_ : int
        Number of features selected.
    support_ : ndarray of shape (n_features,)
        Mask of selected features.

    Examples
    --------
    >>> from nalyst.selection import SequentialFeatureSelector
    >>> from nalyst.learners.linear import LogisticLearner
    >>> selector = SequentialFeatureSelector(LogisticLearner(), n_features_to_select=5)
    >>> selector.train(X, y)
    >>> X_new = selector.apply(X)
    """

    def __init__(
        self,
        estimator,
        *,
        n_features_to_select: int = "auto",
        tol: Optional[float] = None,
        direction: Literal["forward", "backward"] = "forward",
        scoring: Optional[Callable] = None,
        cv: int = 5,
    ):
        self.estimator = estimator
        self.n_features_to_select = n_features_to_select
        self.tol = tol
        self.direction = direction
        self.scoring = scoring
        self.cv = cv

    def train(self, X: np.ndarray, y: np.ndarray) -> "SequentialFeatureSelector":
        """
        Perform feature selection.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : SequentialFeatureSelector
            Fitted transformer.
        """
        X = check_array(X)
        y = np.asarray(y)

        n_features = X.shape[1]
        self.n_features_in_ = n_features

        # Determine number of features to select
        if self.n_features_to_select == "auto":
            n_features_to_select = n_features // 2
        elif isinstance(self.n_features_to_select, float):
            n_features_to_select = int(n_features * self.n_features_to_select)
        else:
            n_features_to_select = self.n_features_to_select

        self.n_features_to_select_ = n_features_to_select

        if self.direction == "forward":
            self.support_ = self._forward_selection(X, y, n_features_to_select)
        else:
            self.support_ = self._backward_selection(X, y, n_features_to_select)

        return self

    def _evaluate_features(self, X: np.ndarray, y: np.ndarray, features: np.ndarray) -> float:
        """Evaluate feature subset using cross-validation."""
        from nalyst.evaluation import cross_val_score

        if len(features) == 0:
            return -np.inf

        X_selected = X[:, features]
        estimator = duplicate(self.estimator)

        scores = cross_val_score(estimator, X_selected, y, cv=self.cv)
        return np.mean(scores)

    def _forward_selection(
        self, X: np.ndarray, y: np.ndarray, n_features_to_select: int
    ) -> np.ndarray:
        """Forward feature selection."""
        n_features = X.shape[1]
        selected = []
        remaining = list(range(n_features))

        best_score = -np.inf

        while len(selected) < n_features_to_select and remaining:
            scores = []

            for feature in remaining:
                candidate = selected + [feature]
                score = self._evaluate_features(X, y, np.array(candidate))
                scores.append((feature, score))

            # Select best
            best_feature, best_new_score = max(scores, key=lambda x: x[1])

            # Check tolerance
            if self.tol is not None and best_new_score - best_score < self.tol:
                break

            selected.append(best_feature)
            remaining.remove(best_feature)
            best_score = best_new_score

        mask = np.zeros(n_features, dtype=bool)
        mask[selected] = True

        return mask

    def _backward_selection(
        self, X: np.ndarray, y: np.ndarray, n_features_to_select: int
    ) -> np.ndarray:
        """Backward feature selection."""
        n_features = X.shape[1]
        remaining = list(range(n_features))

        best_score = self._evaluate_features(X, y, np.array(remaining))

        while len(remaining) > n_features_to_select:
            scores = []

            for feature in remaining:
                candidate = [f for f in remaining if f != feature]
                score = self._evaluate_features(X, y, np.array(candidate))
                scores.append((feature, score))

            # Find feature whose removal gives best score
            worst_feature, best_new_score = max(scores, key=lambda x: x[1])

            # Check tolerance
            if self.tol is not None and best_score - best_new_score > self.tol:
                break

            remaining.remove(worst_feature)
            best_score = best_new_score

        mask = np.zeros(n_features, dtype=bool)
        mask[remaining] = True

        return mask

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get mask or indices of selected features."""
        check_is_trained(self, "support_")

        if indices:
            return np.where(self.support_)[0]
        return self.support_

    def apply(self, X: np.ndarray) -> np.ndarray:
        """Reduce X to selected features."""
        check_is_trained(self, "support_")
        X = check_array(X)
        return X[:, self.support_]

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """Reverse the transformation."""
        check_is_trained(self, "support_")

        X_r = np.zeros((X.shape[0], self.n_features_in_))
        X_r[:, self.support_] = X

        return X_r
