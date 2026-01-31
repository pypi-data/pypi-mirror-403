"""
Column Transformer for applying transformers to columns.
"""

from __future__ import annotations

from typing import Optional, List, Tuple, Any, Union

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class ColumnTransformer(TransformerMixin, BaseLearner):
    """
    Apply transformers to columns of an array.

    Parameters
    ----------
    transformers : list of (name, transformer, columns) tuples
        Transformers to apply to columns.
    remainder : {"drop", "passthrough"} or transformer, default="drop"
        How to handle unspecified columns.
    sparse_threshold : float, default=0.3
        Threshold for sparse matrix output.
    n_jobs : int, optional
        Number of parallel jobs.
    transformer_weights : dict, optional
        Weights for each transformer output.

    Attributes
    ----------
    transformers_ : list
        Fitted transformers.
    n_features_in_ : int
        Number of features seen during fit.

    Examples
    --------
    >>> from nalyst.workflow import ColumnTransformer
    >>> from nalyst.transform import StandardScaler, OneHotEncoder
    >>> ct = ColumnTransformer([
    ...     ('num', StandardScaler(), [0, 1]),
    ...     ('cat', OneHotEncoder(), [2, 3])
    ... ])
    >>> X_transformed = ct.train_apply(X)
    """

    def __init__(
        self,
        transformers: List[Tuple[str, Any, Any]],
        *,
        remainder: str = "drop",
        sparse_threshold: float = 0.3,
        n_jobs: Optional[int] = None,
        transformer_weights: Optional[dict] = None,
    ):
        self.transformers = transformers
        self.remainder = remainder
        self.sparse_threshold = sparse_threshold
        self.n_jobs = n_jobs
        self.transformer_weights = transformer_weights

    def _get_column_indices(
        self, columns: Any, n_features: int
    ) -> np.ndarray:
        """Convert column specification to indices."""
        if isinstance(columns, slice):
            return np.arange(n_features)[columns]
        elif isinstance(columns, (list, tuple, np.ndarray)):
            if len(columns) == 0:
                return np.array([], dtype=int)
            if isinstance(columns[0], bool):
                return np.where(columns)[0]
            return np.asarray(columns)
        elif callable(columns):
            return np.array([i for i in range(n_features) if columns(i)])
        else:
            return np.array([columns])

    def train(self, X: np.ndarray, y: np.ndarray = None) -> "ColumnTransformer":
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
        self : ColumnTransformer
            Fitted transformer.
        """
        X = check_array(X, allow_nd=True)
        n_features = X.shape[1]
        self.n_features_in_ = n_features

        self._transformers = []
        self._column_indices = []
        covered_columns = set()

        for name, transformer, columns in self.transformers:
            indices = self._get_column_indices(columns, n_features)
            self._column_indices.append(indices)
            covered_columns.update(indices)

            if transformer is None or transformer == "drop":
                self._transformers.append((name, "drop", indices))
            elif transformer == "passthrough":
                self._transformers.append((name, "passthrough", indices))
            else:
                fitted = duplicate(transformer)
                fitted.train(X[:, indices], y)
                self._transformers.append((name, fitted, indices))

        # Handle remainder
        remaining_columns = sorted(set(range(n_features)) - covered_columns)
        self._remainder_columns = np.array(remaining_columns)

        if self.remainder == "passthrough":
            self._transformers.append(
                ("remainder", "passthrough", self._remainder_columns)
            )
        elif self.remainder not in ("drop", None):
            # It's a transformer
            if len(remaining_columns) > 0:
                fitted = duplicate(self.remainder)
                fitted.train(X[:, remaining_columns], y)
                self._transformers.append(
                    ("remainder", fitted, self._remainder_columns)
                )

        return self

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X by applying fitted transformers.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        X_t : ndarray
            Transformed data.
        """
        check_is_trained(self, "_transformers")
        X = check_array(X, allow_nd=True)

        transformed = []

        for name, transformer, columns in self._transformers:
            if len(columns) == 0:
                continue

            if transformer == "drop":
                continue
            elif transformer == "passthrough":
                Xt = X[:, columns]
            else:
                Xt = transformer.apply(X[:, columns])

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
        check_is_trained(self, "_transformers")

        names = []
        for name, transformer, columns in self._transformers:
            if transformer == "drop":
                continue
            elif transformer == "passthrough":
                trans_names = [f"{name}_{i}" for i in columns]
            elif hasattr(transformer, "get_feature_names_out"):
                trans_names = transformer.get_feature_names_out()
            else:
                trans_names = [f"{name}_{i}" for i in range(len(columns))]

            names.extend(trans_names)

        return np.array(names)


def make_column_transformer(
    *transformers,
    remainder: str = "drop",
    sparse_threshold: float = 0.3,
    n_jobs: Optional[int] = None,
) -> ColumnTransformer:
    """
    Construct a ColumnTransformer from the given transformers.

    Parameters
    ----------
    *transformers : tuples
        Tuples of (transformer, columns).
    remainder : str, default="drop"
        How to handle remainder columns.
    sparse_threshold : float, default=0.3
        Threshold for sparse output.
    n_jobs : int, optional
        Number of parallel jobs.

    Returns
    -------
    ct : ColumnTransformer
        A ColumnTransformer object.

    Examples
    --------
    >>> from nalyst.workflow import make_column_transformer
    >>> from nalyst.transform import StandardScaler, OneHotEncoder
    >>> ct = make_column_transformer(
    ...     (StandardScaler(), [0, 1]),
    ...     (OneHotEncoder(), [2, 3])
    ... )
    """
    named_transformers = []

    for idx, (transformer, columns) in enumerate(transformers):
        name = type(transformer).__name__.lower()

        existing_names = [n for n, _, _ in named_transformers]
        if name in existing_names:
            count = sum(1 for n in existing_names if n.startswith(name))
            name = f"{name}-{count + 1}"

        named_transformers.append((name, transformer, columns))

    return ColumnTransformer(
        named_transformers,
        remainder=remainder,
        sparse_threshold=sparse_threshold,
        n_jobs=n_jobs,
    )
