"""
Decision Tree learners.

This module implements decision tree algorithms for classification
and regression using recursive binary splitting.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import numpy as np

from nalyst.core.foundation import (
    BaseLearner,
    ClassifierMixin,
    RegressorMixin,
)
from nalyst.core.validation import (
    check_X_y,
    check_array,
    check_is_trained,
    check_random_state,
)
from nalyst.core.tags import (
    LearnerTags,
    TargetTags,
    ClassifierTags,
    RegressorTags,
    InputTags,
)


@dataclass
class TreeNode:
    """
    A node in the decision tree.

    Attributes
    ----------
    feature : int or None
        Feature index for split (None for leaves).
    threshold : float or None
        Split threshold (None for leaves).
    left : TreeNode or None
        Left child (samples where feature <= threshold).
    right : TreeNode or None
        Right child (samples where feature > threshold).
    value : ndarray or None
        Prediction value for leaves.
    n_samples : int
        Number of samples reaching this node.
    impurity : float
        Impurity at this node.
    """

    feature: Optional[int] = None
    threshold: Optional[float] = None
    left: Optional["TreeNode"] = None
    right: Optional["TreeNode"] = None
    value: Optional[np.ndarray] = None
    n_samples: int = 0
    impurity: float = 0.0

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return self.left is None and self.right is None


class DecisionTreeLearner(BaseLearner, ABC):
    """
    Base class for decision tree learners.

    Parameters
    ----------
    criterion : str
        Quality measure for splits.
    splitter : {"best", "random"}, default="best"
        Split finding strategy.
    max_depth : int or None
        Maximum tree depth. None = unlimited.
    min_samples_split : int or float, default=2
        Minimum samples to attempt split.
    min_samples_leaf : int or float, default=1
        Minimum samples in each leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in each leaf.
    max_features : int, float, str, or None
        Features to consider for best split.
    random_state : int, RandomState, or None
        Random state.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease for split.
    class_weight : dict, "balanced", or None
        Class weights (classification only).
    ccp_alpha : float, default=0.0
        Complexity parameter for pruning.
    """

    def __init__(
        self,
        *,
        criterion: str,
        splitter: Literal["best", "random"] = "best",
        max_depth: Optional[int] = None,
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_features: Optional[Union[int, float, str]] = None,
        random_state: Optional[int] = None,
        max_leaf_nodes: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        class_weight: Optional[Union[dict, str]] = None,
        ccp_alpha: float = 0.0,
    ):
        self.criterion = criterion
        self.splitter = splitter
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.max_features = max_features
        self.random_state = random_state
        self.max_leaf_nodes = max_leaf_nodes
        self.min_impurity_decrease = min_impurity_decrease
        self.class_weight = class_weight
        self.ccp_alpha = ccp_alpha

    @abstractmethod
    def _compute_impurity(
        self,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> float:
        """Compute impurity for a set of samples."""
        pass

    @abstractmethod
    def _compute_leaf_value(
        self,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Compute prediction value for a leaf node."""
        pass

    def _get_n_features(self, n_features: int) -> int:
        """Get number of features to consider for splits."""
        max_features = self.max_features

        if max_features is None:
            return n_features
        elif isinstance(max_features, int):
            return min(max_features, n_features)
        elif isinstance(max_features, float):
            return max(1, int(max_features * n_features))
        elif max_features == "sqrt":
            return max(1, int(np.sqrt(n_features)))
        elif max_features == "log2":
            return max(1, int(np.log2(n_features)))
        elif max_features == "auto":
            return n_features
        else:
            return n_features

    def _get_min_samples_split(self, n_samples: int) -> int:
        """Convert min_samples_split to integer."""
        if isinstance(self.min_samples_split, float):
            return max(2, int(self.min_samples_split * n_samples))
        return self.min_samples_split

    def _get_min_samples_leaf(self, n_samples: int) -> int:
        """Convert min_samples_leaf to integer."""
        if isinstance(self.min_samples_leaf, float):
            return max(1, int(self.min_samples_leaf * n_samples))
        return self.min_samples_leaf

    def _find_best_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
        feature_indices: np.ndarray,
        min_samples_leaf: int,
    ) -> Tuple[Optional[int], Optional[float], float]:
        """
        Find the best split for a node.

        Returns
        -------
        best_feature : int or None
            Best feature index.
        best_threshold : float or None
            Best threshold value.
        best_gain : float
            Information gain from best split.
        """
        n_samples = len(y)
        parent_impurity = self._compute_impurity(y, sample_weight)

        best_gain = 0.0
        best_feature = None
        best_threshold = None

        for feature in feature_indices:
            # Get unique thresholds
            feature_values = X[:, feature]
            sorted_indices = np.argsort(feature_values)
            sorted_values = feature_values[sorted_indices]
            sorted_y = y[sorted_indices]

            if sample_weight is not None:
                sorted_weights = sample_weight[sorted_indices]
            else:
                sorted_weights = None

            # Find potential split points (midpoints between unique values)
            unique_values = np.unique(sorted_values)
            if len(unique_values) == 1:
                continue

            thresholds = (unique_values[:-1] + unique_values[1:]) / 2

            for threshold in thresholds:
                left_mask = sorted_values <= threshold
                right_mask = ~left_mask

                n_left = np.sum(left_mask)
                n_right = np.sum(right_mask)

                if n_left < min_samples_leaf or n_right < min_samples_leaf:
                    continue

                y_left = sorted_y[left_mask]
                y_right = sorted_y[right_mask]

                if sorted_weights is not None:
                    w_left = sorted_weights[left_mask]
                    w_right = sorted_weights[right_mask]
                else:
                    w_left = w_right = None

                # Compute information gain
                left_impurity = self._compute_impurity(y_left, w_left)
                right_impurity = self._compute_impurity(y_right, w_right)

                gain = parent_impurity - (
                    (n_left / n_samples) * left_impurity +
                    (n_right / n_samples) * right_impurity
                )

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _build_tree(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
        depth: int,
        rng: np.random.RandomState,
    ) -> TreeNode:
        """Recursively build the decision tree."""
        n_samples, n_features = X.shape

        # Compute impurity and leaf value
        impurity = self._compute_impurity(y, sample_weight)
        leaf_value = self._compute_leaf_value(y, sample_weight)

        node = TreeNode(
            value=leaf_value,
            n_samples=n_samples,
            impurity=impurity,
        )

        # Check stopping conditions
        if (
            (self.max_depth is not None and depth >= self.max_depth) or
            n_samples < self._get_min_samples_split(n_samples) or
            impurity < 1e-10
        ):
            return node

        # Select features for splitting
        n_features_to_consider = self._get_n_features(n_features)
        if self.splitter == "random" or n_features_to_consider < n_features:
            feature_indices = rng.choice(
                n_features,
                size=n_features_to_consider,
                replace=False,
            )
        else:
            feature_indices = np.arange(n_features)

        # Find best split
        min_samples_leaf = self._get_min_samples_leaf(n_samples)
        best_feature, best_threshold, best_gain = self._find_best_split(
            X, y, sample_weight, feature_indices, min_samples_leaf
        )

        # Check if split is worthwhile
        if (
            best_feature is None or
            best_gain < self.min_impurity_decrease
        ):
            return node

        # Perform split
        left_mask = X[:, best_feature] <= best_threshold
        right_mask = ~left_mask

        node.feature = best_feature
        node.threshold = best_threshold
        node.value = None  # No longer a leaf

        left_weight = sample_weight[left_mask] if sample_weight is not None else None
        right_weight = sample_weight[right_mask] if sample_weight is not None else None

        node.left = self._build_tree(
            X[left_mask], y[left_mask], left_weight, depth + 1, rng
        )
        node.right = self._build_tree(
            X[right_mask], y[right_mask], right_weight, depth + 1, rng
        )

        return node

    def _predict_node(self, x: np.ndarray, node: TreeNode) -> np.ndarray:
        """Get prediction for a single sample by traversing tree."""
        if node.is_leaf:
            return node.value

        if x[node.feature] <= node.threshold:
            return self._predict_node(x, node.left)
        else:
            return self._predict_node(x, node.right)

    def _predict_tree(self, X: np.ndarray) -> np.ndarray:
        """Get predictions for all samples."""
        predictions = np.array([self._predict_node(x, self.tree_) for x in X])
        return predictions

    def get_depth(self) -> int:
        """Get the depth of the tree."""
        check_is_trained(self)
        return self._get_node_depth(self.tree_)

    def _get_node_depth(self, node: TreeNode) -> int:
        """Recursively compute tree depth."""
        if node.is_leaf:
            return 0
        return 1 + max(
            self._get_node_depth(node.left),
            self._get_node_depth(node.right),
        )

    def get_n_leaves(self) -> int:
        """Get the number of leaves in the tree."""
        check_is_trained(self)
        return self._count_leaves(self.tree_)

    def _count_leaves(self, node: TreeNode) -> int:
        """Recursively count leaves."""
        if node.is_leaf:
            return 1
        return self._count_leaves(node.left) + self._count_leaves(node.right)

    @property
    def feature_importances_(self) -> np.ndarray:
        """
        Compute feature importances based on impurity decrease.

        Returns
        -------
        importances : ndarray of shape (n_features,)
            Normalized feature importances.
        """
        check_is_trained(self)

        importances = np.zeros(self.n_features_in_)
        total_samples = self.tree_.n_samples

        def accumulate_importances(node: TreeNode) -> None:
            if node.is_leaf:
                return

            # Importance = weighted impurity decrease
            importance = (
                node.n_samples / total_samples * node.impurity -
                node.left.n_samples / total_samples * node.left.impurity -
                node.right.n_samples / total_samples * node.right.impurity
            )
            importances[node.feature] += importance

            accumulate_importances(node.left)
            accumulate_importances(node.right)

        accumulate_importances(self.tree_)

        # Normalize
        total = importances.sum()
        if total > 0:
            importances = importances / total

        return importances


class DecisionTreeClassifier(ClassifierMixin, DecisionTreeLearner):
    """
    Decision tree classifier.

    Builds a tree by recursively partitioning the feature space
    to maximize information gain or minimize impurity.

    Parameters
    ----------
    criterion : {"gini", "entropy", "log_loss"}, default="gini"
        Quality measure for splits.
    splitter : {"best", "random"}, default="best"
        Split finding strategy.
    max_depth : int or None
        Maximum tree depth.
    min_samples_split : int or float, default=2
        Minimum samples to attempt split.
    min_samples_leaf : int or float, default=1
        Minimum samples in each leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in each leaf.
    max_features : int, float, str, or None
        Features to consider for best split.
    random_state : int, optional
        Random state.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease for split.
    class_weight : dict, "balanced", or None
        Class weights.
    ccp_alpha : float, default=0.0
        Complexity parameter for pruning.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    n_classes_ : int
        Number of classes.
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Feature importances.
    tree_ : TreeNode
        The trained tree structure.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.trees import DecisionTreeClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 2], [3, 3]])
    >>> y = np.array([0, 0, 1, 1])
    >>> clf = DecisionTreeClassifier(max_depth=2)
    >>> clf.train(X, y)
    DecisionTreeClassifier(max_depth=2)
    >>> clf.infer([[1.5, 1.5]])
    array([1])
    """

    def __init__(
        self,
        *,
        criterion: Literal["gini", "entropy", "log_loss"] = "gini",
        splitter: Literal["best", "random"] = "best",
        max_depth: Optional[int] = None,
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_features: Optional[Union[int, float, str]] = None,
        random_state: Optional[int] = None,
        max_leaf_nodes: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        class_weight: Optional[Union[dict, str]] = None,
        ccp_alpha: float = 0.0,
    ):
        super().__init__(
            criterion=criterion,
            splitter=splitter,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_weight_fraction_leaf=min_weight_fraction_leaf,
            max_features=max_features,
            random_state=random_state,
            max_leaf_nodes=max_leaf_nodes,
            min_impurity_decrease=min_impurity_decrease,
            class_weight=class_weight,
            ccp_alpha=ccp_alpha,
        )

    def _compute_impurity(
        self,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> float:
        """Compute impurity (Gini or entropy)."""
        if len(y) == 0:
            return 0.0

        # Compute class probabilities
        if sample_weight is not None:
            class_counts = np.zeros(self.n_classes_)
            for i, c in enumerate(self.classes_):
                class_counts[i] = sample_weight[y == c].sum()
            total = sample_weight.sum()
        else:
            class_counts = np.array([np.sum(y == c) for c in self.classes_])
            total = len(y)

        if total == 0:
            return 0.0

        probs = class_counts / total

        if self.criterion == "gini":
            return 1.0 - np.sum(probs ** 2)
        elif self.criterion in ("entropy", "log_loss"):
            probs = probs[probs > 0]
            return -np.sum(probs * np.log2(probs))
        else:
            return 1.0 - np.sum(probs ** 2)

    def _compute_leaf_value(
        self,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Compute class probabilities for leaf."""
        if sample_weight is not None:
            class_counts = np.zeros(self.n_classes_)
            for i, c in enumerate(self.classes_):
                class_counts[i] = sample_weight[y == c].sum()
        else:
            class_counts = np.array([np.sum(y == c) for c in self.classes_])

        return class_counts / class_counts.sum()

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "DecisionTreeClassifier":
        """
        Build a decision tree classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target class labels.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : DecisionTreeClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        # Handle class weights
        if self.class_weight == "balanced":
            n_samples = len(y)
            class_counts = np.bincount(np.searchsorted(self.classes_, y))
            weights = n_samples / (self.n_classes_ * class_counts)
            label_indices = np.searchsorted(self.classes_, y)
            sample_weight_from_class = weights[label_indices]
            if sample_weight is not None:
                sample_weight = sample_weight * sample_weight_from_class
            else:
                sample_weight = sample_weight_from_class
        elif isinstance(self.class_weight, dict):
            weights = np.array([self.class_weight.get(c, 1.0) for c in self.classes_])
            label_indices = np.searchsorted(self.classes_, y)
            sample_weight_from_class = weights[label_indices]
            if sample_weight is not None:
                sample_weight = sample_weight * sample_weight_from_class
            else:
                sample_weight = sample_weight_from_class

        rng = check_random_state(self.random_state)
        self.tree_ = self._build_tree(X, y, sample_weight, depth=0, rng=rng)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels.
        """
        check_is_trained(self)
        X = check_array(X)

        proba = self._predict_tree(X)
        indices = np.argmax(proba, axis=1)
        return self.classes_[indices]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Class probabilities.
        """
        check_is_trained(self)
        X = check_array(X)
        return self._predict_tree(X)

    def infer_log_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict log-probabilities."""
        return np.log(self.infer_proba(X))

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                predict_proba=True,
            ),
        )


class DecisionTreeRegressor(RegressorMixin, DecisionTreeLearner):
    """
    Decision tree regressor.

    Builds a tree by recursively partitioning the feature space
    to minimize mean squared error or absolute error.

    Parameters
    ----------
    criterion : {"squared_error", "friedman_mse", "absolute_error", "poisson"}
        Quality measure for splits.
    splitter : {"best", "random"}, default="best"
        Split finding strategy.
    max_depth : int or None
        Maximum tree depth.
    min_samples_split : int or float, default=2
        Minimum samples to attempt split.
    min_samples_leaf : int or float, default=1
        Minimum samples in each leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in each leaf.
    max_features : int, float, str, or None
        Features to consider for best split.
    random_state : int, optional
        Random state.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease for split.
    ccp_alpha : float, default=0.0
        Complexity parameter for pruning.

    Attributes
    ----------
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Feature importances.
    tree_ : TreeNode
        The trained tree structure.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.trees import DecisionTreeRegressor
    >>> X = np.array([[0], [1], [2], [3]])
    >>> y = np.array([0.0, 1.0, 2.0, 3.0])
    >>> reg = DecisionTreeRegressor(max_depth=2)
    >>> reg.train(X, y)
    DecisionTreeRegressor(max_depth=2)
    >>> reg.infer([[1.5]])
    array([1.5])
    """

    def __init__(
        self,
        *,
        criterion: Literal["squared_error", "friedman_mse", "absolute_error", "poisson"] = "squared_error",
        splitter: Literal["best", "random"] = "best",
        max_depth: Optional[int] = None,
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_features: Optional[Union[int, float, str]] = None,
        random_state: Optional[int] = None,
        max_leaf_nodes: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        ccp_alpha: float = 0.0,
    ):
        super().__init__(
            criterion=criterion,
            splitter=splitter,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_weight_fraction_leaf=min_weight_fraction_leaf,
            max_features=max_features,
            random_state=random_state,
            max_leaf_nodes=max_leaf_nodes,
            min_impurity_decrease=min_impurity_decrease,
            class_weight=None,
            ccp_alpha=ccp_alpha,
        )

    def _compute_impurity(
        self,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> float:
        """Compute impurity (MSE or MAE)."""
        if len(y) == 0:
            return 0.0

        if sample_weight is not None:
            mean = np.average(y, weights=sample_weight)
        else:
            mean = np.mean(y)

        if self.criterion == "squared_error" or self.criterion == "friedman_mse":
            if sample_weight is not None:
                return np.average((y - mean) ** 2, weights=sample_weight)
            return np.mean((y - mean) ** 2)
        elif self.criterion == "absolute_error":
            if sample_weight is not None:
                return np.average(np.abs(y - mean), weights=sample_weight)
            return np.mean(np.abs(y - mean))
        elif self.criterion == "poisson":
            # Poisson deviance
            if sample_weight is not None:
                return np.average(2 * (y * np.log(y / mean + 1e-10) - (y - mean)),
                                  weights=sample_weight)
            return np.mean(2 * (y * np.log(y / mean + 1e-10) - (y - mean)))
        else:
            return np.mean((y - mean) ** 2)

    def _compute_leaf_value(
        self,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Compute prediction value for leaf (mean or median)."""
        if self.criterion == "absolute_error":
            if sample_weight is not None:
                # Weighted median
                sorted_idx = np.argsort(y)
                cumsum = np.cumsum(sample_weight[sorted_idx])
                median_idx = np.searchsorted(cumsum, cumsum[-1] / 2)
                return np.array([y[sorted_idx[median_idx]]])
            return np.array([np.median(y)])
        else:
            if sample_weight is not None:
                return np.array([np.average(y, weights=sample_weight)])
            return np.array([np.mean(y)])

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "DecisionTreeRegressor":
        """
        Build a decision tree regressor.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : DecisionTreeRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        self.n_features_in_ = X.shape[1]

        # For compatibility with base class
        self.classes_ = None
        self.n_classes_ = 1

        rng = check_random_state(self.random_state)
        self.tree_ = self._build_tree(X, y, sample_weight, depth=0, rng=rng)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted values.
        """
        check_is_trained(self)
        X = check_array(X)

        predictions = self._predict_tree(X)
        return predictions.ravel()

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )
