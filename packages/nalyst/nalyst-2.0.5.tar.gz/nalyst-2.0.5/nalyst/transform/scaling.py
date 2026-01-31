"""
Feature scaling transformers.

Provides methods for standardizing or normalizing features
to improve model performance.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.core.tags import LearnerTags, TargetTags, TransformerTags


class StandardScaler(TransformerMixin, BaseLearner):
    """
    Standardize features by removing mean and scaling to unit variance.

    The standard score of a sample x is: z = (x - mean) / std

    Parameters
    ----------
    copy : bool, default=True
        Copy data before transforming.
    with_mean : bool, default=True
        Center data before scaling.
    with_std : bool, default=True
        Scale data to unit variance.

    Attributes
    ----------
    scale_ : ndarray of shape (n_features,)
        Per-feature scale (std).
    mean_ : ndarray of shape (n_features,)
        Per-feature mean.
    var_ : ndarray of shape (n_features,)
        Per-feature variance.
    n_features_in_ : int
        Number of features.
    n_samples_seen_ : int
        Number of samples processed.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import StandardScaler
    >>> X = np.array([[0, 0], [0, 0], [1, 1], [1, 1]])
    >>> scaler = StandardScaler()
    >>> scaler.train(X)
    StandardScaler()
    >>> scaler.transform(X)
    array([[-1., -1.],
           [-1., -1.],
           [ 1.,  1.],
           [ 1.,  1.]])
    """

    def __init__(
        self,
        *,
        copy: bool = True,
        with_mean: bool = True,
        with_std: bool = True,
    ):
        self.copy = copy
        self.with_mean = with_mean
        self.with_std = with_std

    def train(self, X: np.ndarray, y=None) -> "StandardScaler":
        """
        Compute mean and standard deviation for scaling.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : StandardScaler
        """
        X = check_array(X)

        self.n_features_in_ = X.shape[1]
        self.n_samples_seen_ = X.shape[0]

        if self.with_mean:
            self.mean_ = np.mean(X, axis=0)
        else:
            self.mean_ = np.zeros(X.shape[1])

        if self.with_std:
            self.var_ = np.var(X, axis=0)
            self.scale_ = np.sqrt(self.var_)
            # Handle zero variance
            self.scale_[self.scale_ == 0] = 1.0
        else:
            self.var_ = np.ones(X.shape[1])
            self.scale_ = np.ones(X.shape[1])

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Standardize data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_scaled : ndarray of shape (n_samples, n_features)
            Standardized data.
        """
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        if self.with_mean:
            X = X - self.mean_

        if self.with_std:
            X = X / self.scale_

        return X

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Undo standardization.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Scaled data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Original scale data.
        """
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        if self.with_std:
            X = X * self.scale_

        if self.with_mean:
            X = X + self.mean_

        return X

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
            transformer_tags=TransformerTags(
                preserves_dtype=["float64", "float32"],
            ),
        )


class MinMaxScaler(TransformerMixin, BaseLearner):
    """
    Scale features to a given range (default [0, 1]).

    X_scaled = (X - X_min) / (X_max - X_min) * (max - min) + min

    Parameters
    ----------
    feature_range : tuple (min, max), default=(0, 1)
        Desired range of transformed data.
    copy : bool, default=True
        Copy data before transforming.
    clip : bool, default=False
        Clip transformed values to feature_range.

    Attributes
    ----------
    min_ : ndarray of shape (n_features,)
        Per-feature adjustment for minimum.
    scale_ : ndarray of shape (n_features,)
        Per-feature relative scaling.
    data_min_ : ndarray of shape (n_features,)
        Per-feature minimum in training data.
    data_max_ : ndarray of shape (n_features,)
        Per-feature maximum in training data.
    data_range_ : ndarray of shape (n_features,)
        Per-feature range in training data.
    n_features_in_ : int
        Number of features.
    n_samples_seen_ : int
        Number of samples processed.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import MinMaxScaler
    >>> X = np.array([[1, 2], [2, 3], [3, 4]])
    >>> scaler = MinMaxScaler()
    >>> scaler.train(X)
    MinMaxScaler()
    >>> scaler.transform(X)
    array([[0. , 0. ],
           [0.5, 0.5],
           [1. , 1. ]])
    """

    def __init__(
        self,
        feature_range: tuple = (0, 1),
        *,
        copy: bool = True,
        clip: bool = False,
    ):
        self.feature_range = feature_range
        self.copy = copy
        self.clip = clip

    def train(self, X: np.ndarray, y=None) -> "MinMaxScaler":
        """
        Compute min and max for scaling.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : MinMaxScaler
        """
        X = check_array(X)

        feature_min, feature_max = self.feature_range
        if feature_min >= feature_max:
            raise ValueError("feature_range[0] must be less than feature_range[1]")

        self.n_features_in_ = X.shape[1]
        self.n_samples_seen_ = X.shape[0]

        self.data_min_ = np.min(X, axis=0)
        self.data_max_ = np.max(X, axis=0)
        self.data_range_ = self.data_max_ - self.data_min_

        # Handle zero range
        self.data_range_[self.data_range_ == 0] = 1.0

        self.scale_ = (feature_max - feature_min) / self.data_range_
        self.min_ = feature_min - self.data_min_ * self.scale_

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Scale features to range.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_scaled : ndarray of shape (n_samples, n_features)
            Scaled data.
        """
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        X = X * self.scale_ + self.min_

        if self.clip:
            feature_min, feature_max = self.feature_range
            X = np.clip(X, feature_min, feature_max)

        return X

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Undo scaling.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Scaled data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Original scale data.
        """
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        X = (X - self.min_) / self.scale_

        return X

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
            transformer_tags=TransformerTags(),
        )


class MaxAbsScaler(TransformerMixin, BaseLearner):
    """
    Scale features by their maximum absolute value.

    Data will be in range [-1, 1].

    Parameters
    ----------
    copy : bool, default=True
        Copy data before transforming.

    Attributes
    ----------
    scale_ : ndarray of shape (n_features,)
        Per-feature max absolute value.
    max_abs_ : ndarray of shape (n_features,)
        Per-feature max absolute value.
    n_features_in_ : int
        Number of features.
    n_samples_seen_ : int
        Number of samples processed.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import MaxAbsScaler
    >>> X = np.array([[1, -2], [2, -1], [0, 0]])
    >>> scaler = MaxAbsScaler()
    >>> scaler.train(X)
    MaxAbsScaler()
    >>> scaler.transform(X)
    array([[ 0.5, -1. ],
           [ 1. , -0.5],
           [ 0. ,  0. ]])
    """

    def __init__(self, *, copy: bool = True):
        self.copy = copy

    def train(self, X: np.ndarray, y=None) -> "MaxAbsScaler":
        """
        Compute max absolute value for scaling.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : MaxAbsScaler
        """
        X = check_array(X)

        self.n_features_in_ = X.shape[1]
        self.n_samples_seen_ = X.shape[0]

        self.max_abs_ = np.max(np.abs(X), axis=0)
        self.scale_ = self.max_abs_.copy()
        self.scale_[self.scale_ == 0] = 1.0

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale by maximum absolute value."""
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        return X / self.scale_

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Undo scaling."""
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        return X * self.scale_

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
        )


class RobustScaler(TransformerMixin, BaseLearner):
    """
    Scale features using statistics robust to outliers.

    Uses median and interquartile range (IQR).

    Parameters
    ----------
    with_centering : bool, default=True
        Center data by subtracting median.
    with_scaling : bool, default=True
        Scale by IQR.
    quantile_range : tuple (q_min, q_max), default=(25.0, 75.0)
        Quantile range for computing scale.
    copy : bool, default=True
        Copy data before transforming.
    unit_variance : bool, default=False
        Scale to unit variance.

    Attributes
    ----------
    center_ : ndarray of shape (n_features,)
        Median of each feature.
    scale_ : ndarray of shape (n_features,)
        IQR of each feature.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import RobustScaler
    >>> X = np.array([[1, 2], [2, 3], [3, 4], [100, 100]])
    >>> scaler = RobustScaler()
    >>> scaler.train(X)
    RobustScaler()
    """

    def __init__(
        self,
        *,
        with_centering: bool = True,
        with_scaling: bool = True,
        quantile_range: tuple = (25.0, 75.0),
        copy: bool = True,
        unit_variance: bool = False,
    ):
        self.with_centering = with_centering
        self.with_scaling = with_scaling
        self.quantile_range = quantile_range
        self.copy = copy
        self.unit_variance = unit_variance

    def train(self, X: np.ndarray, y=None) -> "RobustScaler":
        """
        Compute median and IQR for scaling.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : RobustScaler
        """
        X = check_array(X)

        self.n_features_in_ = X.shape[1]

        q_min, q_max = self.quantile_range

        if self.with_centering:
            self.center_ = np.median(X, axis=0)

        if self.with_scaling:
            q_min_values = np.percentile(X, q_min, axis=0)
            q_max_values = np.percentile(X, q_max, axis=0)
            self.scale_ = q_max_values - q_min_values
            self.scale_[self.scale_ == 0] = 1.0

            if self.unit_variance:
                # Adjust for unit variance
                from scipy.stats import norm
                adjust = norm.ppf(q_max / 100) - norm.ppf(q_min / 100)
                self.scale_ = self.scale_ / adjust

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply robust scaling."""
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        if self.with_centering:
            X = X - self.center_

        if self.with_scaling:
            X = X / self.scale_

        return X

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Undo robust scaling."""
        check_is_trained(self)
        X = check_array(X)

        if self.copy:
            X = X.copy()

        if self.with_scaling:
            X = X * self.scale_

        if self.with_centering:
            X = X + self.center_

        return X

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
        )


class Normalizer(TransformerMixin, BaseLearner):
    """
    Normalize samples individually to unit norm.

    Parameters
    ----------
    norm : {"l1", "l2", "max"}, default="l2"
        Norm to use: L1, L2, or max.
    copy : bool, default=True
        Copy data before transforming.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import Normalizer
    >>> X = np.array([[1, 2], [3, 4]])
    >>> normalizer = Normalizer()
    >>> normalizer.transform(X)
    array([[0.4472..., 0.8944...],
           [0.6   , 0.8   ]])
    """

    def __init__(
        self,
        norm: Literal["l1", "l2", "max"] = "l2",
        *,
        copy: bool = True,
    ):
        self.norm = norm
        self.copy = copy

    def train(self, X: np.ndarray, y=None) -> "Normalizer":
        """
        No-op (stateless transformer).

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : Ignored
            Not used.

        Returns
        -------
        self : Normalizer
        """
        X = check_array(X)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Normalize samples to unit norm.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to normalize.

        Returns
        -------
        X_normalized : ndarray of shape (n_samples, n_features)
            Normalized data.
        """
        X = check_array(X)

        if self.copy:
            X = X.copy()

        if self.norm == "l1":
            norms = np.sum(np.abs(X), axis=1, keepdims=True)
        elif self.norm == "l2":
            norms = np.sqrt(np.sum(X ** 2, axis=1, keepdims=True))
        else:  # max
            norms = np.max(np.abs(X), axis=1, keepdims=True)

        norms[norms == 0] = 1.0
        return X / norms

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
            transformer_tags=TransformerTags(stateless=True),
        )
