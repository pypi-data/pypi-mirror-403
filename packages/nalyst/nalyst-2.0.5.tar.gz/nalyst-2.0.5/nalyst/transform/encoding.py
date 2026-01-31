"""
Encoding transformers for categorical data.

Provides methods for converting categorical features
into numerical representations.
"""

from __future__ import annotations

from typing import Optional, List, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.core.tags import LearnerTags, TargetTags, TransformerTags


class LabelEncoder(BaseLearner):
    """
    Encode target labels with values between 0 and n_classes-1.

    Attributes
    ----------
    classes_ : ndarray
        Unique classes.

    Examples
    --------
    >>> from nalyst.transform import LabelEncoder
    >>> le = LabelEncoder()
    >>> le.train(["cat", "dog", "bird", "cat"])
    LabelEncoder()
    >>> le.transform(["cat", "bird"])
    array([1, 0])
    >>> le.inverse_transform([0, 1, 2])
    array(['bird', 'cat', 'dog'], dtype='<U4')
    """

    def train(self, y: np.ndarray) -> "LabelEncoder":
        """
        Fit label encoder.

        Parameters
        ----------
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        self : LabelEncoder
        """
        y = np.asarray(y)
        self.classes_ = np.unique(y)
        return self

    def transform(self, y: np.ndarray) -> np.ndarray:
        """
        Transform labels to encoded integers.

        Parameters
        ----------
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        y_encoded : ndarray of shape (n_samples,)
            Encoded labels.
        """
        check_is_trained(self)
        y = np.asarray(y)

        encoded = np.zeros(len(y), dtype=int)
        for i, val in enumerate(y):
            idx = np.where(self.classes_ == val)[0]
            if len(idx) == 0:
                raise ValueError(f"Unknown label: {val}")
            encoded[i] = idx[0]

        return encoded

    def inverse_transform(self, y: np.ndarray) -> np.ndarray:
        """
        Transform encoded labels back to original.

        Parameters
        ----------
        y : array-like of shape (n_samples,)
            Encoded target values.

        Returns
        -------
        y_original : ndarray of shape (n_samples,)
            Original labels.
        """
        check_is_trained(self)
        y = np.asarray(y)

        return self.classes_[y]

    def train_transform(self, y: np.ndarray) -> np.ndarray:
        """
        Fit and transform labels.

        Parameters
        ----------
        y : array-like of shape (n_samples,)
            Target values.

        Returns
        -------
        y_encoded : ndarray of shape (n_samples,)
            Encoded labels.
        """
        return self.train(y).transform(y)


class OneHotEncoder(TransformerMixin, BaseLearner):
    """
    Encode categorical features as one-hot numeric array.

    Parameters
    ----------
    categories : "auto" or list of arrays
        Categories per feature. "auto" determines from data.
    drop : {"first", "if_binary"} or array-like, optional
        Whether to drop a category.
    sparse_output : bool, default=False
        Return sparse matrix (not implemented).
    dtype : numpy dtype, default=np.float64
        Output dtype.
    handle_unknown : {"error", "ignore", "infrequent_if_exist"}, default="error"
        How to handle unknown categories.
    min_frequency : int or float, optional
        Minimum frequency for a category.
    max_categories : int, optional
        Maximum categories per feature.

    Attributes
    ----------
    categories_ : list of ndarray
        Categories for each feature.
    drop_idx_ : ndarray or None
        Indices of dropped categories.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import OneHotEncoder
    >>> X = np.array([["cat"], ["dog"], ["cat"], ["bird"]])
    >>> enc = OneHotEncoder()
    >>> enc.train(X)
    OneHotEncoder()
    >>> enc.transform(X)
    array([[0., 1., 0.],
           [0., 0., 1.],
           [0., 1., 0.],
           [1., 0., 0.]])
    """

    def __init__(
        self,
        *,
        categories: str = "auto",
        drop: Optional[str] = None,
        sparse_output: bool = False,
        dtype=np.float64,
        handle_unknown: Literal["error", "ignore", "infrequent_if_exist"] = "error",
        min_frequency: Optional[float] = None,
        max_categories: Optional[int] = None,
    ):
        self.categories = categories
        self.drop = drop
        self.sparse_output = sparse_output
        self.dtype = dtype
        self.handle_unknown = handle_unknown
        self.min_frequency = min_frequency
        self.max_categories = max_categories

    def train(self, X: np.ndarray, y=None) -> "OneHotEncoder":
        """
        Fit one-hot encoder.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data with categorical features.
        y : Ignored
            Not used.

        Returns
        -------
        self : OneHotEncoder
        """
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]

        # Determine categories
        if self.categories == "auto":
            self.categories_ = [np.unique(X[:, i]) for i in range(X.shape[1])]
        else:
            self.categories_ = [np.asarray(c) for c in self.categories]

        # Handle drop
        if self.drop is not None:
            if self.drop == "first":
                self.drop_idx_ = np.zeros(self.n_features_in_, dtype=int)
            elif self.drop == "if_binary":
                self.drop_idx_ = np.array([
                    0 if len(cats) == 2 else -1
                    for cats in self.categories_
                ])
            else:
                self.drop_idx_ = np.asarray(self.drop)
        else:
            self.drop_idx_ = None

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform categories to one-hot encoding.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_encoded : ndarray
            One-hot encoded data.
        """
        check_is_trained(self)
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        n_samples = X.shape[0]

        # Calculate output size
        n_cols = 0
        for i, cats in enumerate(self.categories_):
            n_cats = len(cats)
            if self.drop_idx_ is not None and self.drop_idx_[i] >= 0:
                n_cats -= 1
            n_cols += n_cats

        result = np.zeros((n_samples, n_cols), dtype=self.dtype)

        col_offset = 0
        for i, cats in enumerate(self.categories_):
            for j, sample in enumerate(X[:, i]):
                # Find category index
                cat_idx = np.where(cats == sample)[0]

                if len(cat_idx) == 0:
                    if self.handle_unknown == "error":
                        raise ValueError(f"Unknown category: {sample}")
                    # ignore: leave as zeros
                    continue

                idx = cat_idx[0]

                # Handle drop
                if self.drop_idx_ is not None and self.drop_idx_[i] >= 0:
                    if idx == self.drop_idx_[i]:
                        continue
                    if idx > self.drop_idx_[i]:
                        idx -= 1

                result[j, col_offset + idx] = 1.0

            # Update offset
            n_cats = len(cats)
            if self.drop_idx_ is not None and self.drop_idx_[i] >= 0:
                n_cats -= 1
            col_offset += n_cats

        return result

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Convert one-hot encoding back to categories.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_encoded_features)
            One-hot encoded data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Original categorical data.
        """
        check_is_trained(self)
        X = np.asarray(X)

        n_samples = X.shape[0]
        result = np.empty((n_samples, self.n_features_in_), dtype=object)

        col_offset = 0
        for i, cats in enumerate(self.categories_):
            n_cats = len(cats)
            if self.drop_idx_ is not None and self.drop_idx_[i] >= 0:
                n_cats -= 1

            feature_cols = X[:, col_offset:col_offset + n_cats]

            for j in range(n_samples):
                active = np.where(feature_cols[j] > 0)[0]
                if len(active) > 0:
                    idx = active[0]
                    if self.drop_idx_ is not None and self.drop_idx_[i] >= 0:
                        if idx >= self.drop_idx_[i]:
                            idx += 1
                    result[j, i] = cats[idx]
                else:
                    # Dropped category or unknown
                    if self.drop_idx_ is not None and self.drop_idx_[i] >= 0:
                        result[j, i] = cats[self.drop_idx_[i]]
                    else:
                        result[j, i] = None

            col_offset += n_cats

        return result

    def get_feature_names_out(
        self,
        input_features: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Get feature names for output.

        Parameters
        ----------
        input_features : list of str, optional
            Input feature names.

        Returns
        -------
        feature_names : ndarray
            Output feature names.
        """
        check_is_trained(self)

        if input_features is None:
            input_features = [f"x{i}" for i in range(self.n_features_in_)]

        names = []
        for i, cats in enumerate(self.categories_):
            for j, cat in enumerate(cats):
                if self.drop_idx_ is not None and self.drop_idx_[i] == j:
                    continue
                names.append(f"{input_features[i]}_{cat}")

        return np.array(names)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
        )


class OrdinalEncoder(TransformerMixin, BaseLearner):
    """
    Encode categorical features as ordinal integers.

    Parameters
    ----------
    categories : "auto" or list of arrays
        Categories per feature.
    dtype : numpy dtype, default=np.float64
        Output dtype.
    handle_unknown : {"error", "use_encoded_value"}, default="error"
        How to handle unknown categories.
    unknown_value : int or np.nan, optional
        Value for unknown categories.
    encoded_missing_value : int or np.nan, optional
        Value for missing data.

    Attributes
    ----------
    categories_ : list of ndarray
        Categories for each feature.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import OrdinalEncoder
    >>> X = np.array([["low"], ["medium"], ["high"], ["low"]])
    >>> enc = OrdinalEncoder()
    >>> enc.train(X)
    OrdinalEncoder()
    >>> enc.transform(X)
    array([[1.],
           [2.],
           [0.],
           [1.]])
    """

    def __init__(
        self,
        *,
        categories: str = "auto",
        dtype=np.float64,
        handle_unknown: Literal["error", "use_encoded_value"] = "error",
        unknown_value: Optional[float] = None,
        encoded_missing_value: Optional[float] = np.nan,
    ):
        self.categories = categories
        self.dtype = dtype
        self.handle_unknown = handle_unknown
        self.unknown_value = unknown_value
        self.encoded_missing_value = encoded_missing_value

    def train(self, X: np.ndarray, y=None) -> "OrdinalEncoder":
        """
        Fit ordinal encoder.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data with categorical features.
        y : Ignored
            Not used.

        Returns
        -------
        self : OrdinalEncoder
        """
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        self.n_features_in_ = X.shape[1]

        if self.categories == "auto":
            self.categories_ = [np.unique(X[:, i]) for i in range(X.shape[1])]
        else:
            self.categories_ = [np.asarray(c) for c in self.categories]

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform categories to ordinal integers.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to transform.

        Returns
        -------
        X_encoded : ndarray of shape (n_samples, n_features)
            Encoded data.
        """
        check_is_trained(self)
        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(-1, 1)

        result = np.zeros(X.shape, dtype=self.dtype)

        for i, cats in enumerate(self.categories_):
            for j, sample in enumerate(X[:, i]):
                cat_idx = np.where(cats == sample)[0]

                if len(cat_idx) == 0:
                    if self.handle_unknown == "error":
                        raise ValueError(f"Unknown category: {sample}")
                    result[j, i] = self.unknown_value
                else:
                    result[j, i] = cat_idx[0]

        return result

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Convert ordinal encoding back to categories.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Encoded data.

        Returns
        -------
        X_original : ndarray of shape (n_samples, n_features)
            Original categorical data.
        """
        check_is_trained(self)
        X = np.asarray(X)

        result = np.empty(X.shape, dtype=object)

        for i, cats in enumerate(self.categories_):
            for j, val in enumerate(X[:, i]):
                idx = int(val)
                if 0 <= idx < len(cats):
                    result[j, i] = cats[idx]
                else:
                    result[j, i] = None

        return result

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
        )
