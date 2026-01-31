"""
Imputation transformers for handling missing values.

Provides strategies for replacing missing data with
computed or learned values.
"""

from __future__ import annotations

from typing import Optional, Union, Literal

import numpy as np
from scipy.spatial.distance import cdist

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.core.tags import LearnerTags, TargetTags, TransformerTags


class SimpleImputer(TransformerMixin, BaseLearner):
    """
    Impute missing values using simple strategies.

    Parameters
    ----------
    missing_values : int, float, str, np.nan, None, default=np.nan
        The placeholder for missing values.
    strategy : {"mean", "median", "most_frequent", "constant"}, default="mean"
        The imputation strategy.
    fill_value : str or number, optional
        Value for constant strategy.
    copy : bool, default=True
        Copy data before transforming.
    add_indicator : bool, default=False
        Add missing indicator features.
    keep_empty_features : bool, default=False
        Keep features with all missing values.

    Attributes
    ----------
    statistics_ : ndarray of shape (n_features,)
        The imputation fill value for each feature.
    n_features_in_ : int
        Number of features.
    indicator_ : MissingIndicator, optional
        Indicator for missing values.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import SimpleImputer
    >>> X = np.array([[1, 2], [np.nan, 3], [7, 6]])
    >>> imp = SimpleImputer(strategy="mean")
    >>> imp.train(X)
    SimpleImputer()
    >>> imp.transform([[np.nan, 2], [6, np.nan]])
    array([[4. , 2. ],
           [6. , 3.66...]])
    """

    def __init__(
        self,
        *,
        missing_values=np.nan,
        strategy: Literal["mean", "median", "most_frequent", "constant"] = "mean",
        fill_value: Optional[Union[str, float]] = None,
        copy: bool = True,
        add_indicator: bool = False,
        keep_empty_features: bool = False,
    ):
        self.missing_values = missing_values
        self.strategy = strategy
        self.fill_value = fill_value
        self.copy = copy
        self.add_indicator = add_indicator
        self.keep_empty_features = keep_empty_features

    def _get_mask(self, X: np.ndarray) -> np.ndarray:
        """Get mask of missing values."""
        if self.missing_values is np.nan or (
            isinstance(self.missing_values, float) and np.isnan(self.missing_values)
        ):
            return np.isnan(X)
        else:
            return X == self.missing_values

    def train(self, X: np.ndarray, y=None) -> "SimpleImputer":
        """
        Fit imputer by computing statistics.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data with missing values.
        y : Ignored
            Not used.

        Returns
        -------
        self : SimpleImputer
        """
        X = check_array(X, force_all_finite=False)

        self.n_features_in_ = X.shape[1]

        mask = self._get_mask(X)

        statistics = np.zeros(X.shape[1])

        for i in range(X.shape[1]):
            col = X[:, i]
            valid_mask = ~mask[:, i]
            valid_data = col[valid_mask]

            if len(valid_data) == 0:
                if self.strategy == "constant" and self.fill_value is not None:
                    statistics[i] = self.fill_value
                else:
                    statistics[i] = 0
                continue

            if self.strategy == "mean":
                statistics[i] = np.mean(valid_data)
            elif self.strategy == "median":
                statistics[i] = np.median(valid_data)
            elif self.strategy == "most_frequent":
                values, counts = np.unique(valid_data, return_counts=True)
                statistics[i] = values[np.argmax(counts)]
            elif self.strategy == "constant":
                if self.fill_value is not None:
                    statistics[i] = self.fill_value
                else:
                    statistics[i] = 0

        self.statistics_ = statistics

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to impute.

        Returns
        -------
        X_imputed : ndarray of shape (n_samples, n_features)
            Imputed data.
        """
        check_is_trained(self)
        X = check_array(X, force_all_finite=False)

        if self.copy:
            X = X.copy()

        mask = self._get_mask(X)

        for i in range(X.shape[1]):
            X[mask[:, i], i] = self.statistics_[i]

        return X

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Cannot restore missing values (returns as-is).
        """
        return X

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
            transformer_tags=TransformerTags(
                allow_nan=True,
            ),
        )


class KNNImputer(TransformerMixin, BaseLearner):
    """
    Impute missing values using k-Nearest Neighbors.

    Uses weighted average of k nearest neighbors to impute missing values.

    Parameters
    ----------
    missing_values : int, float, np.nan, default=np.nan
        Placeholder for missing values.
    n_neighbors : int, default=5
        Number of neighbors.
    weights : {"uniform", "distance"} or callable, default="uniform"
        Weight function.
    metric : str, default="nan_euclidean"
        Distance metric.
    copy : bool, default=True
        Copy data before transforming.
    add_indicator : bool, default=False
        Add missing indicator features.
    keep_empty_features : bool, default=False
        Keep features with all missing.

    Attributes
    ----------
    n_features_in_ : int
        Number of features.
    indicator_ : MissingIndicator, optional
        Indicator for missing values.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import KNNImputer
    >>> X = np.array([[1, 2], [3, 4], [np.nan, 6], [8, 8]])
    >>> imputer = KNNImputer(n_neighbors=2)
    >>> imputer.train(X)
    KNNImputer(n_neighbors=2)
    >>> imputer.transform([[np.nan, 6]])
    array([[2., 6.]])
    """

    def __init__(
        self,
        *,
        missing_values=np.nan,
        n_neighbors: int = 5,
        weights: Union[str, callable] = "uniform",
        metric: str = "nan_euclidean",
        copy: bool = True,
        add_indicator: bool = False,
        keep_empty_features: bool = False,
    ):
        self.missing_values = missing_values
        self.n_neighbors = n_neighbors
        self.weights = weights
        self.metric = metric
        self.copy = copy
        self.add_indicator = add_indicator
        self.keep_empty_features = keep_empty_features

    def _get_mask(self, X: np.ndarray) -> np.ndarray:
        """Get mask of missing values."""
        if self.missing_values is np.nan or (
            isinstance(self.missing_values, float) and np.isnan(self.missing_values)
        ):
            return np.isnan(X)
        else:
            return X == self.missing_values

    def _nan_euclidean_distance(
        self,
        X: np.ndarray,
        Y: np.ndarray,
    ) -> np.ndarray:
        """Compute Euclidean distance handling NaN values."""
        n_X = X.shape[0]
        n_Y = Y.shape[0]
        distances = np.zeros((n_X, n_Y))

        for i in range(n_X):
            for j in range(n_Y):
                mask = ~(np.isnan(X[i]) | np.isnan(Y[j]))
                if np.sum(mask) == 0:
                    distances[i, j] = np.inf
                else:
                    sq_diff = (X[i, mask] - Y[j, mask]) ** 2
                    # Scale by ratio of features
                    distances[i, j] = np.sqrt(
                        np.sum(sq_diff) * X.shape[1] / np.sum(mask)
                    )

        return distances

    def train(self, X: np.ndarray, y=None) -> "KNNImputer":
        """
        Fit imputer by storing training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : KNNImputer
        """
        X = check_array(X, force_all_finite=False)

        self.n_features_in_ = X.shape[1]
        self._fit_X = X.copy()

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Impute missing values using k-NN.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to impute.

        Returns
        -------
        X_imputed : ndarray of shape (n_samples, n_features)
            Imputed data.
        """
        check_is_trained(self)
        X = check_array(X, force_all_finite=False)

        if self.copy:
            X = X.copy()

        mask = self._get_mask(X)

        # Find samples with missing values
        rows_with_missing = np.where(np.any(mask, axis=1))[0]

        if len(rows_with_missing) == 0:
            return X

        # Compute distances
        distances = self._nan_euclidean_distance(X[rows_with_missing], self._fit_X)

        for idx, row_idx in enumerate(rows_with_missing):
            missing_cols = np.where(mask[row_idx])[0]

            # Get k nearest neighbors
            dists = distances[idx]
            neighbor_indices = np.argsort(dists)[:self.n_neighbors]
            neighbor_dists = dists[neighbor_indices]

            # Compute weights
            if self.weights == "uniform":
                weights = np.ones(len(neighbor_indices))
            elif self.weights == "distance":
                # Avoid division by zero
                weights = 1.0 / (neighbor_dists + 1e-10)
            else:
                weights = self.weights(neighbor_dists)

            weights = weights / np.sum(weights)

            # Impute each missing feature
            for col in missing_cols:
                neighbor_values = self._fit_X[neighbor_indices, col]
                valid_mask = ~np.isnan(neighbor_values)

                if np.any(valid_mask):
                    valid_values = neighbor_values[valid_mask]
                    valid_weights = weights[valid_mask]
                    valid_weights = valid_weights / np.sum(valid_weights)
                    X[row_idx, col] = np.sum(valid_values * valid_weights)
                else:
                    # Fall back to column mean
                    col_values = self._fit_X[:, col]
                    X[row_idx, col] = np.nanmean(col_values)

        return X

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
            transformer_tags=TransformerTags(
                allow_nan=True,
            ),
        )
