"""
Function Transformer for custom transformations.
"""

from __future__ import annotations

from typing import Optional, Callable

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array


class FunctionTransformer(TransformerMixin, BaseLearner):
    """
    Constructs a transformer from an arbitrary callable.

    Parameters
    ----------
    func : callable, optional
        The callable to use for the transformation.
        If None, the identity function is used.
    inverse_func : callable, optional
        The callable to use for the inverse transformation.
    validate : bool, default=False
        Indicate that the input X array should be checked before
        calling func.
    accept_sparse : bool, default=False
        Indicate that func accepts sparse matrix.
    check_inverse : bool, default=True
        Whether to check that inverse_func is inverse of func.
    feature_names_out : callable or "one-to-one", optional
        Determines the list of feature names.
    kw_args : dict, optional
        Additional keyword arguments to pass to func.
    inv_kw_args : dict, optional
        Additional keyword arguments to pass to inverse_func.

    Examples
    --------
    >>> from nalyst.workflow import FunctionTransformer
    >>> transformer = FunctionTransformer(func=np.log1p, inverse_func=np.expm1)
    >>> X = np.array([[1, 2], [3, 4]])
    >>> transformer.train_apply(X)
    array([[0.69314718, 1.09861229],
           [1.38629436, 1.60943791]])
    """

    def __init__(
        self,
        func: Optional[Callable] = None,
        inverse_func: Optional[Callable] = None,
        *,
        validate: bool = False,
        accept_sparse: bool = False,
        check_inverse: bool = True,
        feature_names_out: Optional[str] = None,
        kw_args: Optional[dict] = None,
        inv_kw_args: Optional[dict] = None,
    ):
        self.func = func
        self.inverse_func = inverse_func
        self.validate = validate
        self.accept_sparse = accept_sparse
        self.check_inverse = check_inverse
        self.feature_names_out = feature_names_out
        self.kw_args = kw_args or {}
        self.inv_kw_args = inv_kw_args or {}

    def train(self, X: np.ndarray, y=None) -> "FunctionTransformer":
        """
        Fit the transformer.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : FunctionTransformer
            Fitted transformer.
        """
        if self.validate:
            X = check_array(X)

        self.n_features_in_ = X.shape[1] if X.ndim > 1 else 1

        # Check inverse
        if self.check_inverse and self.inverse_func is not None:
            X_round_trip = self._inverse_transform(self._transform(X))
            if not np.allclose(X, X_round_trip, equal_nan=True):
                import warnings
                warnings.warn(
                    "The provided functions are not inverses of each other."
                )

        return self

    def _transform(self, X: np.ndarray) -> np.ndarray:
        """Apply the forward function."""
        if self.func is None:
            return X
        return self.func(X, **self.kw_args)

    def _inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Apply the inverse function."""
        if self.inverse_func is None:
            return X
        return self.inverse_func(X, **self.inv_kw_args)

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X using the callable.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        X_out : ndarray
            Transformed array.
        """
        if self.validate:
            X = check_array(X)

        return self._transform(X)

    def inverse_apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X using the inverse callable.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Transformed data.

        Returns
        -------
        X_out : ndarray
            Original array.
        """
        if self.validate:
            X = check_array(X)

        return self._inverse_transform(X)

    def train_apply(self, X: np.ndarray, y=None) -> np.ndarray:
        """
        Fit and transform.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        X_out : ndarray
            Transformed array.
        """
        self.train(X, y)
        return self.apply(X)

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        """
        Get output feature names.

        Parameters
        ----------
        input_features : array-like, optional
            Input feature names.

        Returns
        -------
        feature_names : ndarray of str
            Output feature names.
        """
        if input_features is None:
            input_features = [f"x{i}" for i in range(self.n_features_in_)]

        if self.feature_names_out == "one-to-one":
            return np.array(input_features)
        elif callable(self.feature_names_out):
            return np.array(self.feature_names_out(self, input_features))
        else:
            return np.array(input_features)
