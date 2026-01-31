"""
Feature Union for combining transformers.
"""

from __future__ import annotations

from typing import Optional, List, Tuple, Any

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class FeatureUnion(TransformerMixin, BaseLearner):
    """
    Concatenates results of multiple transformer objects.

    This estimator applies a list of transformer objects in parallel
    to the input data, then concatenates the results.

    Parameters
    ----------
    transformer_list : list of (name, transformer) tuples
        List of transformers to apply.
    n_jobs : int, default=None
        Number of jobs to run in parallel.
    transformer_weights : dict, optional
        Weights for each transformer output.

    Attributes
    ----------
    n_features_in_ : int
        Number of features seen during fit.

    Examples
    --------
    >>> from nalyst.workflow import FeatureUnion
    >>> from nalyst.reduction import PrincipalComponentAnalysis
    >>> from nalyst.selection import SelectKBest
    >>> union = FeatureUnion([
    ...     ('pca', PrincipalComponentAnalysis(n_components=2)),
    ...     ('kbest', SelectKBest(k=1))
    ... ])
    >>> X_combined = union.train_apply(X, y)
    """

    def __init__(
        self,
        transformer_list: List[Tuple[str, Any]],
        *,
        n_jobs: Optional[int] = None,
        transformer_weights: Optional[dict] = None,
    ):
        self.transformer_list = transformer_list
        self.n_jobs = n_jobs
        self.transformer_weights = transformer_weights

    @property
    def named_transformers(self) -> dict:
        """Access transformers by name."""
        return dict(self.transformer_list)

    def train(self, X: np.ndarray, y: np.ndarray = None) -> "FeatureUnion":
        """
        Fit all transformers.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,), optional
            Target values.

        Returns
        -------
        self : FeatureUnion
            Fitted transformer.
        """
        X = check_array(X)
        self.n_features_in_ = X.shape[1]

        self._fitted_transformers = []

        for name, transformer in self.transformer_list:
            if transformer is None or transformer == "drop":
                self._fitted_transformers.append((name, None))
                continue

            fitted = duplicate(transformer)
            fitted.train(X, y)
            self._fitted_transformers.append((name, fitted))

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X and concatenate results.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        X_t : ndarray of shape (n_samples, n_total_features)
            Transformed data.
        """
        check_is_trained(self, "_fitted_transformers")
        X = check_array(X)

        transformed = []

        for name, transformer in self._fitted_transformers:
            if transformer is None:
                continue

            Xt = transformer.apply(X)

            # Apply weights
            if self.transformer_weights and name in self.transformer_weights:
                Xt = Xt * self.transformer_weights[name]

            transformed.append(Xt)

        if not transformed:
            return np.zeros((X.shape[0], 0))

        return np.hstack(transformed)

    def train_apply(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """
        Fit and transform.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,), optional
            Target values.

        Returns
        -------
        X_t : ndarray
            Transformed data.
        """
        self.train(X, y)
        return self.apply(X)

    def get_feature_names_out(self) -> np.ndarray:
        """
        Get output feature names.

        Returns
        -------
        feature_names : ndarray of str
            Feature names.
        """
        check_is_trained(self, "_fitted_transformers")

        names = []
        for name, transformer in self._fitted_transformers:
            if transformer is None:
                continue

            if hasattr(transformer, "get_feature_names_out"):
                trans_names = transformer.get_feature_names_out()
            else:
                # Generate generic names
                n_features = getattr(transformer, "n_components", None) or \
                            getattr(transformer, "n_features_", None) or 1
                trans_names = [f"{name}_{i}" for i in range(n_features)]

            names.extend(trans_names)

        return np.array(names)


def make_union(*transformers, n_jobs: Optional[int] = None) -> FeatureUnion:
    """
    Construct a FeatureUnion from the given transformers.

    Parameters
    ----------
    *transformers : list of transformers
        Transformers to combine.
    n_jobs : int, optional
        Number of parallel jobs.

    Returns
    -------
    union : FeatureUnion
        A FeatureUnion object.

    Examples
    --------
    >>> from nalyst.workflow import make_union
    >>> from nalyst.reduction import PrincipalComponentAnalysis
    >>> union = make_union(PrincipalComponentAnalysis(n_components=2))
    """
    named_transformers = []

    for idx, transformer in enumerate(transformers):
        name = type(transformer).__name__.lower()

        existing_names = [n for n, _ in named_transformers]
        if name in existing_names:
            count = sum(1 for n in existing_names if n.startswith(name))
            name = f"{name}-{count + 1}"

        named_transformers.append((name, transformer))

    return FeatureUnion(named_transformers, n_jobs=n_jobs)
