"""
Recursive Feature Elimination.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class RFE(TransformerMixin, BaseLearner):
    """
    Feature ranking with recursive feature elimination.

    Parameters
    ----------
    estimator : object
        A supervised learning estimator with train/infer methods
        and either coef_ or feature_importances_ attribute.
    n_features_to_select : int or float, optional
        Number of features to select. If None, half are selected.
    step : int or float, default=1
        Features to remove at each iteration.

    Attributes
    ----------
    estimator_ : object
        Fitted estimator.
    n_features_ : int
        Number of selected features.
    support_ : ndarray of shape (n_features,)
        Mask of selected features.
    ranking_ : ndarray of shape (n_features,)
        Feature ranking (1 = selected).

    Examples
    --------
    >>> from nalyst.selection import RFE
    >>> from nalyst.learners.linear import LogisticLearner
    >>> estimator = LogisticLearner()
    >>> selector = RFE(estimator, n_features_to_select=5)
    >>> selector.train(X, y)
    >>> X_new = selector.apply(X)
    """

    def __init__(
        self,
        estimator,
        n_features_to_select: Optional[int] = None,
        step: int = 1,
    ):
        self.estimator = estimator
        self.n_features_to_select = n_features_to_select
        self.step = step

    def train(self, X: np.ndarray, y: np.ndarray) -> "RFE":
        """
        Fit the RFE model and rank features.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : RFE
            Fitted transformer.
        """
        X = check_array(X)
        y = np.asarray(y)

        n_features = X.shape[1]

        # Determine number of features to select
        if self.n_features_to_select is None:
            n_features_to_select = n_features // 2
        elif isinstance(self.n_features_to_select, float):
            n_features_to_select = int(n_features * self.n_features_to_select)
        else:
            n_features_to_select = self.n_features_to_select

        # Determine step
        if isinstance(self.step, float):
            step = max(1, int(n_features * self.step))
        else:
            step = self.step

        # Initialize
        support = np.ones(n_features, dtype=bool)
        ranking = np.ones(n_features, dtype=int)

        while np.sum(support) > n_features_to_select:
            # Get active features
            features = np.where(support)[0]

            # Fit estimator on remaining features
            estimator = duplicate(self.estimator)
            estimator.train(X[:, features], y)

            # Get feature importances
            if hasattr(estimator, "coef_"):
                importances = np.abs(estimator.coef_).ravel()
                if len(importances) > len(features):
                    # Multi-class case
                    importances = np.sum(np.abs(estimator.coef_), axis=0)
            elif hasattr(estimator, "feature_importances_"):
                importances = estimator.feature_importances_
            else:
                raise ValueError(
                    "Estimator must have coef_ or feature_importances_"
                )

            # Determine features to remove
            n_to_remove = min(step, np.sum(support) - n_features_to_select)
            indices_to_remove = np.argsort(importances)[:n_to_remove]

            # Update support and ranking
            threshold = ranking.max() + 1
            support[features[indices_to_remove]] = False
            ranking[features[indices_to_remove]] = threshold

        # Final fit with selected features
        self.estimator_ = duplicate(self.estimator)
        self.estimator_.train(X[:, support], y)

        self.support_ = support
        self.ranking_ = ranking
        self.n_features_ = np.sum(support)
        self.n_features_in_ = n_features

        return self

    def get_support(self, indices: bool = False) -> np.ndarray:
        """Get a mask or index of selected features."""
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

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the selected features.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        y_pred : ndarray
            Predicted values.
        """
        check_is_trained(self, "estimator_")
        X = check_array(X)
        return self.estimator_.infer(X[:, self.support_])


class RFECV(RFE):
    """
    Feature ranking with recursive feature elimination and cross-validation.

    Parameters
    ----------
    estimator : object
        A supervised learning estimator.
    step : int or float, default=1
        Features to remove at each iteration.
    min_features_to_select : int, default=1
        Minimum number of features to select.
    cv : int, default=5
        Cross-validation folds.
    scoring : str, optional
        Scoring metric.

    Attributes
    ----------
    n_features_ : int
        Number of selected features.
    support_ : ndarray of shape (n_features,)
        Mask of selected features.
    ranking_ : ndarray of shape (n_features,)
        Feature ranking.
    cv_results_ : dict
        Cross-validation results.

    Examples
    --------
    >>> from nalyst.selection import RFECV
    >>> from nalyst.learners.linear import LogisticLearner
    >>> selector = RFECV(LogisticLearner(), step=1, cv=5)
    >>> selector.train(X, y)
    """

    def __init__(
        self,
        estimator,
        step: int = 1,
        min_features_to_select: int = 1,
        cv: int = 5,
        scoring: Optional[str] = None,
    ):
        super().__init__(estimator, n_features_to_select=min_features_to_select, step=step)
        self.min_features_to_select = min_features_to_select
        self.cv = cv
        self.scoring = scoring

    def train(self, X: np.ndarray, y: np.ndarray) -> "RFECV":
        """
        Fit and determine optimal number of features.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : RFECV
            Fitted transformer.
        """
        X = check_array(X)
        y = np.asarray(y)

        n_features = X.shape[1]

        # Step size
        if isinstance(self.step, float):
            step = max(1, int(n_features * self.step))
        else:
            step = self.step

        # Feature counts to try
        n_features_list = list(
            range(self.min_features_to_select, n_features + 1, step)
        )
        if n_features not in n_features_list:
            n_features_list.append(n_features)

        # Cross-validation for each feature count
        from nalyst.evaluation import cross_val_score

        cv_scores = []
        for n_feat in reversed(n_features_list):
            rfe = RFE(self.estimator, n_features_to_select=n_feat, step=self.step)
            rfe.train(X, y)
            X_selected = rfe.apply(X)

            estimator = duplicate(self.estimator)
            scores = cross_val_score(estimator, X_selected, y, cv=self.cv)
            cv_scores.append((n_feat, np.mean(scores), np.std(scores)))

        # Find best
        best_idx = np.argmax([s[1] for s in cv_scores])
        best_n_features = cv_scores[best_idx][0]

        # Store results
        self.cv_results_ = {
            "n_features": [s[0] for s in cv_scores],
            "mean_test_score": [s[1] for s in cv_scores],
            "std_test_score": [s[2] for s in cv_scores],
        }

        # Final fit
        self.n_features_to_select = best_n_features
        super().train(X, y)

        return self
