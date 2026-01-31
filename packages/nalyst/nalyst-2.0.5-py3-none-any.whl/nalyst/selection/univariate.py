"""
Univariate feature selectors.
"""

from __future__ import annotations

from typing import Optional, Callable, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.selection.score_functions import f_classif


class _BaseFilter(TransformerMixin, BaseLearner):
    """Base class for univariate filter feature selection."""

    def __init__(self, score_func: Callable = f_classif):
        self.score_func = score_func

    def train(self, X: np.ndarray, y: np.ndarray) -> "_BaseFilter":
        """
        Run the univariate tests.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self
            Fitted transformer.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.scores_, self.pvalues_ = self.score_func(X, y)
        self.n_features_in_ = X.shape[1]

        return self

    def _get_support_mask(self) -> np.ndarray:
        """Get the boolean mask of selected features."""
        raise NotImplementedError

    def get_support(self, indices: bool = False) -> np.ndarray:
        """
        Get a mask or integer index of selected features.

        Parameters
        ----------
        indices : bool, default=False
            If True, returns indices.

        Returns
        -------
        support : ndarray
            Mask or indices.
        """
        check_is_trained(self, "scores_")
        mask = self._get_support_mask()

        if indices:
            return np.where(mask)[0]
        return mask

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Reduce X to selected features.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        X_r : ndarray of shape (n_samples, n_selected_features)
            Input samples with selected features.
        """
        check_is_trained(self, "scores_")
        X = check_array(X)
        return X[:, self.get_support()]

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Reverse the transformation operation.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_selected_features)
            Input samples.

        Returns
        -------
        X_r : ndarray of shape (n_samples, n_features)
            Zeros in unselected positions.
        """
        check_is_trained(self, "scores_")
        support = self.get_support()

        X_r = np.zeros((X.shape[0], self.n_features_in_))
        X_r[:, support] = X

        return X_r


class SelectKBest(_BaseFilter):
    """
    Select features according to the k highest scores.

    Parameters
    ----------
    score_func : callable, default=f_classif
        Function taking X and y, returning (scores, pvalues).
    k : int or "all", default=10
        Number of top features to select.

    Attributes
    ----------
    scores_ : ndarray of shape (n_features,)
        Scores of features.
    pvalues_ : ndarray of shape (n_features,)
        P-values of feature scores.

    Examples
    --------
    >>> from nalyst.selection import SelectKBest, f_classif
    >>> X = np.random.randn(100, 20)
    >>> y = np.random.randint(0, 2, 100)
    >>> selector = SelectKBest(f_classif, k=10)
    >>> X_new = selector.train_apply(X, y)
    >>> X_new.shape
    (100, 10)
    """

    def __init__(self, score_func: Callable = f_classif, k: int = 10):
        super().__init__(score_func)
        self.k = k

    def _get_support_mask(self) -> np.ndarray:
        if self.k == "all":
            return np.ones(len(self.scores_), dtype=bool)

        k = min(self.k, len(self.scores_))
        indices = np.argsort(self.scores_)[-k:]
        mask = np.zeros(len(self.scores_), dtype=bool)
        mask[indices] = True
        return mask


class SelectPercentile(_BaseFilter):
    """
    Select features based on percentile of highest scores.

    Parameters
    ----------
    score_func : callable, default=f_classif
        Function taking X and y, returning (scores, pvalues).
    percentile : int, default=10
        Percent of features to keep.

    Attributes
    ----------
    scores_ : ndarray of shape (n_features,)
        Scores of features.
    pvalues_ : ndarray of shape (n_features,)
        P-values of feature scores.

    Examples
    --------
    >>> from nalyst.selection import SelectPercentile, f_classif
    >>> selector = SelectPercentile(f_classif, percentile=20)
    """

    def __init__(self, score_func: Callable = f_classif, percentile: int = 10):
        super().__init__(score_func)
        self.percentile = percentile

    def _get_support_mask(self) -> np.ndarray:
        n_features = len(self.scores_)
        n_keep = max(1, int(n_features * self.percentile / 100))

        indices = np.argsort(self.scores_)[-n_keep:]
        mask = np.zeros(n_features, dtype=bool)
        mask[indices] = True
        return mask


class SelectFpr(_BaseFilter):
    """
    Filter: Select features based on a false positive rate test.

    Parameters
    ----------
    score_func : callable, default=f_classif
        Function taking X and y, returning (scores, pvalues).
    alpha : float, default=0.05
        Maximum allowed false positive rate.

    Examples
    --------
    >>> from nalyst.selection import SelectFpr, f_classif
    >>> selector = SelectFpr(f_classif, alpha=0.05)
    """

    def __init__(self, score_func: Callable = f_classif, alpha: float = 0.05):
        super().__init__(score_func)
        self.alpha = alpha

    def _get_support_mask(self) -> np.ndarray:
        return self.pvalues_ < self.alpha


class SelectFdr(_BaseFilter):
    """
    Filter: Select features based on false discovery rate.

    Uses Benjamini-Hochberg procedure.

    Parameters
    ----------
    score_func : callable, default=f_classif
        Function taking X and y, returning (scores, pvalues).
    alpha : float, default=0.05
        Maximum allowed false discovery rate.
    """

    def __init__(self, score_func: Callable = f_classif, alpha: float = 0.05):
        super().__init__(score_func)
        self.alpha = alpha

    def _get_support_mask(self) -> np.ndarray:
        n_features = len(self.pvalues_)

        # Sort p-values
        sorted_idx = np.argsort(self.pvalues_)
        sorted_pvals = self.pvalues_[sorted_idx]

        # Benjamini-Hochberg procedure
        thresholds = np.arange(1, n_features + 1) / n_features * self.alpha

        # Find cutoff
        below = sorted_pvals <= thresholds
        if not below.any():
            return np.zeros(n_features, dtype=bool)

        cutoff_idx = np.max(np.where(below)[0])

        mask = np.zeros(n_features, dtype=bool)
        mask[sorted_idx[:cutoff_idx + 1]] = True

        return mask


class SelectFwe(_BaseFilter):
    """
    Filter: Select features based on family-wise error rate.

    Uses Bonferroni correction.

    Parameters
    ----------
    score_func : callable, default=f_classif
        Function taking X and y, returning (scores, pvalues).
    alpha : float, default=0.05
        Maximum allowed family-wise error rate.
    """

    def __init__(self, score_func: Callable = f_classif, alpha: float = 0.05):
        super().__init__(score_func)
        self.alpha = alpha

    def _get_support_mask(self) -> np.ndarray:
        n_features = len(self.pvalues_)
        corrected_alpha = self.alpha / n_features
        return self.pvalues_ < corrected_alpha


class GenericUnivariateSelect(_BaseFilter):
    """
    Univariate feature selector with configurable strategy.

    Parameters
    ----------
    score_func : callable, default=f_classif
        Function taking X and y, returning (scores, pvalues).
    mode : {"percentile", "k_best", "fpr", "fdr", "fwe"}, default="percentile"
        Feature selection mode.
    param : float or int, default=1e-5
        Parameter of the corresponding mode.
    """

    def __init__(
        self,
        score_func: Callable = f_classif,
        *,
        mode: Literal["percentile", "k_best", "fpr", "fdr", "fwe"] = "percentile",
        param: float = 1e-5,
    ):
        super().__init__(score_func)
        self.mode = mode
        self.param = param

    def _get_support_mask(self) -> np.ndarray:
        if self.mode == "percentile":
            return SelectPercentile(
                self.score_func, percentile=self.param
            )._set_scores(self)._get_support_mask()
        elif self.mode == "k_best":
            return SelectKBest(
                self.score_func, k=int(self.param)
            )._set_scores(self)._get_support_mask()
        elif self.mode == "fpr":
            return SelectFpr(
                self.score_func, alpha=self.param
            )._set_scores(self)._get_support_mask()
        elif self.mode == "fdr":
            return SelectFdr(
                self.score_func, alpha=self.param
            )._set_scores(self)._get_support_mask()
        elif self.mode == "fwe":
            return SelectFwe(
                self.score_func, alpha=self.param
            )._set_scores(self)._get_support_mask()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _set_scores(self, other: "_BaseFilter") -> "GenericUnivariateSelect":
        """Copy scores from another selector."""
        self.scores_ = other.scores_
        self.pvalues_ = other.pvalues_
        self.n_features_in_ = other.n_features_in_
        return self
