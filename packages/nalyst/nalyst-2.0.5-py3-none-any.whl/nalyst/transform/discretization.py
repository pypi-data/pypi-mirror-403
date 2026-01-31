"""
Discretization transformers.

Provides methods for binning continuous features
into discrete intervals.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained
from nalyst.core.tags import LearnerTags, TargetTags, TransformerTags


class KBinsDiscretizer(TransformerMixin, BaseLearner):
    """
    Bin continuous data into intervals.

    Parameters
    ----------
    n_bins : int or array-like of shape (n_features,), default=5
        Number of bins per feature.
    encode : {"onehot", "onehot-dense", "ordinal"}, default="onehot"
        Method for encoding output.
    strategy : {"uniform", "quantile", "kmeans"}, default="quantile"
        Strategy for determining bin edges.
    dtype : dtype, optional
        Output dtype.
    subsample : int or None, default=200000
        Number of samples for computing quantiles.
    random_state : int, optional
        Random seed for subsampling.

    Attributes
    ----------
    n_bins_ : ndarray of shape (n_features,)
        Number of bins per feature.
    bin_edges_ : list of ndarray
        Bin edges for each feature.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import KBinsDiscretizer
    >>> X = np.array([[0], [1], [2], [3], [4], [5]])
    >>> disc = KBinsDiscretizer(n_bins=3, encode="ordinal")
    >>> disc.train(X)
    KBinsDiscretizer(encode='ordinal', n_bins=3)
    >>> disc.transform(X)
    array([[0.],
           [0.],
           [1.],
           [1.],
           [2.],
           [2.]])
    """

    def __init__(
        self,
        n_bins: int = 5,
        *,
        encode: Literal["onehot", "onehot-dense", "ordinal"] = "onehot",
        strategy: Literal["uniform", "quantile", "kmeans"] = "quantile",
        dtype=None,
        subsample: Optional[int] = 200000,
        random_state: Optional[int] = None,
    ):
        self.n_bins = n_bins
        self.encode = encode
        self.strategy = strategy
        self.dtype = dtype
        self.subsample = subsample
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "KBinsDiscretizer":
        """
        Fit discretizer by computing bin edges.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to discretize.
        y : Ignored
            Not used.

        Returns
        -------
        self : KBinsDiscretizer
        """
        X = check_array(X)

        self.n_features_in_ = X.shape[1]

        # Handle n_bins
        if isinstance(self.n_bins, int):
            n_bins = np.full(self.n_features_in_, self.n_bins, dtype=int)
        else:
            n_bins = np.asarray(self.n_bins, dtype=int)

        self.n_bins_ = n_bins
        self.bin_edges_ = []

        for i in range(self.n_features_in_):
            col = X[:, i]
            n = n_bins[i]

            if self.strategy == "uniform":
                edges = np.linspace(col.min(), col.max(), n + 1)

            elif self.strategy == "quantile":
                percentiles = np.linspace(0, 100, n + 1)
                edges = np.percentile(col, percentiles)
                # Handle duplicate edges
                edges = np.unique(edges)
                if len(edges) < n + 1:
                    # Adjust number of bins
                    self.n_bins_[i] = len(edges) - 1

            elif self.strategy == "kmeans":
                from nalyst.clustering.kmeans import KMeansClustering

                # Use k-means to find bin centers
                col_2d = col.reshape(-1, 1)
                kmeans = KMeansClustering(
                    n_clusters=n,
                    random_state=self.random_state,
                    n_init=1,
                )
                kmeans.train(col_2d)

                centers = np.sort(kmeans.cluster_centers_.ravel())
                edges = np.zeros(n + 1)
                edges[0] = col.min()
                edges[-1] = col.max()
                for j in range(1, n):
                    edges[j] = (centers[j - 1] + centers[j]) / 2

            # Extend edges slightly for numerical stability
            edges[0] = -np.inf
            edges[-1] = np.inf

            self.bin_edges_.append(edges)

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Discretize data into bins.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to discretize.

        Returns
        -------
        X_binned : ndarray
            Binned data.
        """
        check_is_trained(self)
        X = check_array(X)

        n_samples = X.shape[0]

        # Get bin indices
        Xt = np.zeros((n_samples, self.n_features_in_), dtype=int)

        for i in range(self.n_features_in_):
            Xt[:, i] = np.searchsorted(self.bin_edges_[i][1:-1], X[:, i])

        if self.encode == "ordinal":
            return Xt.astype(float if self.dtype is None else self.dtype)

        # One-hot encoding
        n_cols = np.sum(self.n_bins_)
        result = np.zeros((n_samples, n_cols), dtype=float if self.dtype is None else self.dtype)

        col_offset = 0
        for i in range(self.n_features_in_):
            for j in range(n_samples):
                bin_idx = Xt[j, i]
                result[j, col_offset + bin_idx] = 1.0
            col_offset += self.n_bins_[i]

        return result

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Convert binned data back to original space (bin centers).

        Parameters
        ----------
        X : array-like
            Binned data.

        Returns
        -------
        X_inverse : ndarray
            Data with bin centers.
        """
        check_is_trained(self)
        X = np.asarray(X)

        if self.encode == "ordinal":
            Xt = X.astype(int)
        else:
            # Decode one-hot
            n_samples = X.shape[0]
            Xt = np.zeros((n_samples, self.n_features_in_), dtype=int)

            col_offset = 0
            for i in range(self.n_features_in_):
                feature_cols = X[:, col_offset:col_offset + self.n_bins_[i]]
                Xt[:, i] = np.argmax(feature_cols, axis=1)
                col_offset += self.n_bins_[i]

        # Convert to bin centers
        result = np.zeros_like(Xt, dtype=float)

        for i in range(self.n_features_in_):
            edges = self.bin_edges_[i]
            # Replace inf with data bounds
            edges = edges.copy()
            for j in range(len(Xt)):
                bin_idx = Xt[j, i]
                left = edges[bin_idx] if edges[bin_idx] != -np.inf else edges[1]
                right = edges[bin_idx + 1] if edges[bin_idx + 1] != np.inf else edges[-2]
                result[j, i] = (left + right) / 2

        return result

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
        )


class Binarizer(TransformerMixin, BaseLearner):
    """
    Binarize data according to a threshold.

    Values greater than threshold become 1, else 0.

    Parameters
    ----------
    threshold : float, default=0.0
        Values <= threshold become 0, > threshold become 1.
    copy : bool, default=True
        Copy data before transforming.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.transform import Binarizer
    >>> X = np.array([[1.0, -1.0, 2.0], [2.0, 0.0, 0.0], [0.0, 1.0, -1.0]])
    >>> binarizer = Binarizer(threshold=0.0)
    >>> binarizer.transform(X)
    array([[1., 0., 1.],
           [1., 0., 0.],
           [0., 1., 0.]])
    """

    def __init__(
        self,
        *,
        threshold: float = 0.0,
        copy: bool = True,
    ):
        self.threshold = threshold
        self.copy = copy

    def train(self, X: np.ndarray, y=None) -> "Binarizer":
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
        self : Binarizer
        """
        X = check_array(X)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Binarize data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data to binarize.

        Returns
        -------
        X_binarized : ndarray of shape (n_samples, n_features)
            Binarized data.
        """
        X = check_array(X)

        if self.copy:
            X = X.copy()

        return (X > self.threshold).astype(float)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="transformer",
            target_tags=TargetTags(required=False),
            transformer_tags=TransformerTags(stateless=True),
        )
