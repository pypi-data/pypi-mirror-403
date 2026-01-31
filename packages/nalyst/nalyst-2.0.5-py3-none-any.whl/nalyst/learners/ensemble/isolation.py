"""
Isolation Forest for anomaly detection.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner
from nalyst.core.validation import check_array, check_is_trained


class IsolationForest(BaseLearner):
    """
    Isolation Forest for anomaly detection.

    Parameters
    ----------
    n_estimators : int, default=100
        Number of base estimators (trees).
    max_samples : int or float, default="auto"
        Number of samples to draw for each tree.
    contamination : float, default="auto"
        Expected proportion of outliers.
    max_features : int or float, default=1.0
        Number of features to draw for each tree.
    bootstrap : bool, default=False
        Whether to use bootstrap sampling.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    estimators_ : list
        List of fitted isolation trees.
    offset_ : float
        Offset for decision function.

    Examples
    --------
    >>> from nalyst.learners.ensemble import IsolationForest
    >>> clf = IsolationForest(n_estimators=100)
    >>> clf.train(X)
    >>> predictions = clf.infer(X)  # -1 for outliers, 1 for inliers
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_samples: str = "auto",
        contamination: float = "auto",
        max_features: float = 1.0,
        bootstrap: bool = False,
        random_state: Optional[int] = None,
    ):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.random_state = random_state

    def train(self, X: np.ndarray, y=None) -> "IsolationForest":
        """
        Fit the model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ignored

        Returns
        -------
        self : IsolationForest
            Fitted estimator.
        """
        X = check_array(X)
        n_samples, n_features = X.shape

        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Determine max_samples
        if self.max_samples == "auto":
            max_samples = min(256, n_samples)
        elif isinstance(self.max_samples, float):
            max_samples = int(self.max_samples * n_samples)
        else:
            max_samples = self.max_samples

        self.max_samples_ = max_samples

        # Determine max_features
        if isinstance(self.max_features, float):
            max_features = max(1, int(self.max_features * n_features))
        else:
            max_features = self.max_features

        # Build isolation trees
        self.estimators_ = []

        for _ in range(self.n_estimators):
            # Sample data
            if self.bootstrap:
                indices = np.random.choice(n_samples, max_samples, replace=True)
            else:
                indices = np.random.choice(n_samples, max_samples, replace=False)

            X_sample = X[indices]

            # Sample features
            feature_indices = np.random.choice(
                n_features, max_features, replace=False
            )

            # Build tree
            tree = _IsolationTree(max_depth=int(np.ceil(np.log2(max_samples))))
            tree.fit(X_sample[:, feature_indices])
            tree.feature_indices_ = feature_indices

            self.estimators_.append(tree)

        # Compute offset
        if self.contamination == "auto":
            self.offset_ = -0.5
        else:
            scores = self._score_samples(X)
            self.offset_ = np.percentile(scores, 100 * self.contamination)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict if samples are outliers or inliers.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            +1 for inliers, -1 for outliers.
        """
        scores = self.decision_function(X)
        return np.where(scores >= 0, 1, -1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Raw anomaly score.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        scores : ndarray of shape (n_samples,)
            Anomaly score. Negative = outlier.
        """
        return self._score_samples(X) - self.offset_

    def _score_samples(self, X: np.ndarray) -> np.ndarray:
        """Compute anomaly score."""
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]

        # Average path length
        avg_path_length = np.zeros(n_samples)

        for tree in self.estimators_:
            X_subset = X[:, tree.feature_indices_]
            path_lengths = tree.path_lengths(X_subset)
            avg_path_length += path_lengths

        avg_path_length /= len(self.estimators_)

        # Normalize by expected path length
        c_n = _average_path_length(self.max_samples_)

        # Anomaly score
        scores = -2 ** (-avg_path_length / c_n)

        return scores


class _IsolationTree:
    """Single isolation tree."""

    def __init__(self, max_depth: int):
        self.max_depth = max_depth

    def fit(self, X: np.ndarray):
        """Build the tree."""
        self.root_ = self._build_tree(X, depth=0)
        return self

    def _build_tree(self, X: np.ndarray, depth: int):
        """Recursively build tree."""
        n_samples, n_features = X.shape

        # Stopping conditions
        if depth >= self.max_depth or n_samples <= 1:
            return {"type": "leaf", "size": n_samples}

        # Select random feature and split
        feature = np.random.randint(n_features)
        min_val, max_val = X[:, feature].min(), X[:, feature].max()

        if min_val == max_val:
            return {"type": "leaf", "size": n_samples}

        split_value = np.random.uniform(min_val, max_val)

        left_mask = X[:, feature] < split_value
        right_mask = ~left_mask

        return {
            "type": "node",
            "feature": feature,
            "split": split_value,
            "left": self._build_tree(X[left_mask], depth + 1),
            "right": self._build_tree(X[right_mask], depth + 1),
        }

    def path_lengths(self, X: np.ndarray) -> np.ndarray:
        """Compute path length for each sample."""
        return np.array([self._path_length(x, self.root_, 0) for x in X])

    def _path_length(self, x: np.ndarray, node: dict, depth: int) -> float:
        """Compute path length for single sample."""
        if node["type"] == "leaf":
            return depth + _average_path_length(node["size"])

        if x[node["feature"]] < node["split"]:
            return self._path_length(x, node["left"], depth + 1)
        else:
            return self._path_length(x, node["right"], depth + 1)


def _average_path_length(n: int) -> float:
    """Expected path length in a random binary tree."""
    if n <= 1:
        return 0
    elif n == 2:
        return 1
    else:
        return 2 * (np.log(n - 1) + 0.5772156649) - 2 * (n - 1) / n
