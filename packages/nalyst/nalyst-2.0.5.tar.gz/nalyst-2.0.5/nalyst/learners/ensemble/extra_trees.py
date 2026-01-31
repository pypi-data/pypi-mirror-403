"""
Extra Trees (Extremely Randomized Trees).
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin, RegressorMixin
from nalyst.core.validation import check_array, check_is_trained


class ExtraTreesClassifier(ClassifierMixin, BaseLearner):
    """
    Extra-Trees classifier.

    Extremely randomized trees. Uses random splits instead of best splits.

    Parameters
    ----------
    n_estimators : int, default=100
        Number of trees.
    criterion : {"gini", "entropy"}, default="gini"
        Splitting criterion.
    max_depth : int, optional
        Maximum depth of trees.
    min_samples_split : int, default=2
        Minimum samples to split a node.
    min_samples_leaf : int, default=1
        Minimum samples in a leaf node.
    max_features : {"sqrt", "log2"} or int or float, default="sqrt"
        Number of features to consider for splits.
    bootstrap : bool, default=False
        Whether to bootstrap samples.
    random_state : int, optional
        Random seed.

    Attributes
    ----------
    estimators_ : list
        List of fitted trees.
    classes_ : ndarray
        Class labels.
    feature_importances_ : ndarray
        Feature importances.

    Examples
    --------
    >>> from nalyst.learners.ensemble import ExtraTreesClassifier
    >>> clf = ExtraTreesClassifier(n_estimators=100)
    >>> clf.train(X, y)
    >>> predictions = clf.infer(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 100,
        *,
        criterion: Literal["gini", "entropy"] = "gini",
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: str = "sqrt",
        bootstrap: bool = False,
        random_state: Optional[int] = None,
    ):
        self.n_estimators = n_estimators
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "ExtraTreesClassifier":
        """
        Build the forest of extra trees.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : ExtraTreesClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        self.classes_ = np.unique(y)
        n_samples, n_features = X.shape

        # Determine max_features
        self.max_features_ = self._get_max_features(n_features)

        # Build trees
        self.estimators_ = []
        self.feature_importances_ = np.zeros(n_features)

        for _ in range(self.n_estimators):
            # Bootstrap or full sample
            if self.bootstrap:
                indices = np.random.choice(n_samples, n_samples, replace=True)
                X_sample, y_sample = X[indices], y[indices]
            else:
                X_sample, y_sample = X, y

            # Build extremely randomized tree
            tree = _ExtraTree(
                criterion=self.criterion,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                max_features=self.max_features_,
                task="classification",
            )
            tree.fit(X_sample, y_sample, self.classes_)

            self.estimators_.append(tree)
            self.feature_importances_ += tree.feature_importances_

        self.feature_importances_ /= self.n_estimators

        return self

    def _get_max_features(self, n_features: int) -> int:
        if self.max_features == "sqrt":
            return max(1, int(np.sqrt(n_features)))
        elif self.max_features == "log2":
            return max(1, int(np.log2(n_features)))
        elif isinstance(self.max_features, float):
            return max(1, int(self.max_features * n_features))
        elif isinstance(self.max_features, int):
            return self.max_features
        else:
            return n_features

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        proba = self.infer_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        check_is_trained(self, "estimators_")
        X = check_array(X)

        # Average predictions
        proba = np.zeros((X.shape[0], len(self.classes_)))

        for tree in self.estimators_:
            proba += tree.predict_proba(X)

        proba /= len(self.estimators_)
        return proba


class ExtraTreesRegressor(RegressorMixin, BaseLearner):
    """
    Extra-Trees regressor.

    Parameters
    ----------
    n_estimators : int, default=100
        Number of trees.
    criterion : {"squared_error", "absolute_error"}, default="squared_error"
        Splitting criterion.
    max_depth : int, optional
        Maximum depth of trees.
    min_samples_split : int, default=2
        Minimum samples to split a node.
    min_samples_leaf : int, default=1
        Minimum samples in a leaf node.
    max_features : {"sqrt", "log2"} or int or float, default=1.0
        Number of features to consider for splits.
    bootstrap : bool, default=False
        Whether to bootstrap samples.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> from nalyst.learners.ensemble import ExtraTreesRegressor
    >>> reg = ExtraTreesRegressor(n_estimators=100)
    >>> reg.train(X, y)
    >>> predictions = reg.infer(X_test)
    """

    def __init__(
        self,
        n_estimators: int = 100,
        *,
        criterion: Literal["squared_error", "absolute_error"] = "squared_error",
        max_depth: Optional[int] = None,
        min_samples_split: int = 2,
        min_samples_leaf: int = 1,
        max_features: float = 1.0,
        bootstrap: bool = False,
        random_state: Optional[int] = None,
    ):
        self.n_estimators = n_estimators
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.random_state = random_state

    def train(self, X: np.ndarray, y: np.ndarray) -> "ExtraTreesRegressor":
        """Build the forest."""
        X = check_array(X)
        y = np.asarray(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        n_samples, n_features = X.shape

        # Determine max_features
        if isinstance(self.max_features, float):
            max_features = max(1, int(self.max_features * n_features))
        elif self.max_features == "sqrt":
            max_features = max(1, int(np.sqrt(n_features)))
        elif self.max_features == "log2":
            max_features = max(1, int(np.log2(n_features)))
        else:
            max_features = self.max_features or n_features

        self.max_features_ = max_features

        # Build trees
        self.estimators_ = []
        self.feature_importances_ = np.zeros(n_features)

        for _ in range(self.n_estimators):
            if self.bootstrap:
                indices = np.random.choice(n_samples, n_samples, replace=True)
                X_sample, y_sample = X[indices], y[indices]
            else:
                X_sample, y_sample = X, y

            tree = _ExtraTree(
                criterion=self.criterion,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                max_features=max_features,
                task="regression",
            )
            tree.fit(X_sample, y_sample, None)

            self.estimators_.append(tree)
            self.feature_importances_ += tree.feature_importances_

        self.feature_importances_ /= self.n_estimators

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict target values."""
        check_is_trained(self, "estimators_")
        X = check_array(X)

        predictions = np.zeros(X.shape[0])

        for tree in self.estimators_:
            predictions += tree.predict(X)

        return predictions / len(self.estimators_)


class _ExtraTree:
    """Single extremely randomized tree."""

    def __init__(
        self,
        criterion: str,
        max_depth: Optional[int],
        min_samples_split: int,
        min_samples_leaf: int,
        max_features: int,
        task: str,
    ):
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.task = task

    def fit(self, X: np.ndarray, y: np.ndarray, classes):
        """Build the tree."""
        self.n_features_ = X.shape[1]
        self.classes_ = classes
        self.feature_importances_ = np.zeros(self.n_features_)

        self.root_ = self._build_tree(X, y, depth=0)

        if self.feature_importances_.sum() > 0:
            self.feature_importances_ /= self.feature_importances_.sum()

        return self

    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int):
        """Recursively build tree."""
        n_samples = len(y)

        # Stopping conditions
        if (self.max_depth is not None and depth >= self.max_depth) or \
           n_samples < self.min_samples_split or \
           n_samples < 2 * self.min_samples_leaf:
            return self._create_leaf(y)

        # For classification, stop if pure
        if self.task == "classification" and len(np.unique(y)) == 1:
            return self._create_leaf(y)

        # Select random features
        feature_indices = np.random.choice(
            self.n_features_,
            min(self.max_features, self.n_features_),
            replace=False
        )

        # Find best random split
        best_feature, best_split, best_impurity = None, None, float('inf')

        for feature in feature_indices:
            values = X[:, feature]
            min_val, max_val = values.min(), values.max()

            if min_val == max_val:
                continue

            # Random split point
            split = np.random.uniform(min_val, max_val)

            left_mask = values <= split
            right_mask = ~left_mask

            if left_mask.sum() < self.min_samples_leaf or \
               right_mask.sum() < self.min_samples_leaf:
                continue

            # Compute impurity
            impurity = self._compute_impurity(y[left_mask], y[right_mask])

            if impurity < best_impurity:
                best_impurity = impurity
                best_feature = feature
                best_split = split

        if best_feature is None:
            return self._create_leaf(y)

        # Record feature importance
        self.feature_importances_[best_feature] += n_samples

        # Split
        left_mask = X[:, best_feature] <= best_split

        return {
            "type": "node",
            "feature": best_feature,
            "split": best_split,
            "left": self._build_tree(X[left_mask], y[left_mask], depth + 1),
            "right": self._build_tree(X[~left_mask], y[~left_mask], depth + 1),
        }

    def _compute_impurity(self, y_left: np.ndarray, y_right: np.ndarray) -> float:
        """Compute weighted impurity."""
        n_left, n_right = len(y_left), len(y_right)
        n_total = n_left + n_right

        if self.task == "classification":
            if self.criterion == "gini":
                impurity_left = 1 - np.sum((np.bincount(y_left.astype(int)) / n_left) ** 2)
                impurity_right = 1 - np.sum((np.bincount(y_right.astype(int)) / n_right) ** 2)
            else:  # entropy
                p_left = np.bincount(y_left.astype(int)) / n_left
                p_right = np.bincount(y_right.astype(int)) / n_right
                impurity_left = -np.sum(p_left * np.log(p_left + 1e-10))
                impurity_right = -np.sum(p_right * np.log(p_right + 1e-10))
        else:  # regression
            if self.criterion == "squared_error":
                impurity_left = np.var(y_left)
                impurity_right = np.var(y_right)
            else:  # absolute_error
                impurity_left = np.mean(np.abs(y_left - np.median(y_left)))
                impurity_right = np.mean(np.abs(y_right - np.median(y_right)))

        return (n_left * impurity_left + n_right * impurity_right) / n_total

    def _create_leaf(self, y: np.ndarray):
        """Create leaf node."""
        if self.task == "classification":
            counts = np.bincount(y.astype(int), minlength=len(self.classes_))
            return {"type": "leaf", "value": counts / counts.sum()}
        else:
            return {"type": "leaf", "value": np.mean(y)}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict values."""
        return np.array([self._predict_single(x, self.root_) for x in X])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        return np.array([self._predict_single(x, self.root_) for x in X])

    def _predict_single(self, x: np.ndarray, node: dict):
        """Predict for single sample."""
        if node["type"] == "leaf":
            return node["value"]

        if x[node["feature"]] <= node["split"]:
            return self._predict_single(x, node["left"])
        else:
            return self._predict_single(x, node["right"])
