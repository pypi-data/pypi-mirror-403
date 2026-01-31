"""
Random Forest ensemble learners.

Random forests combine multiple decision trees trained on
bootstrap samples with random feature selection.
"""

from __future__ import annotations

from typing import Any, Callable, List, Literal, Optional, Union

import numpy as np
from joblib import Parallel, delayed

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
)
from nalyst.learners.trees import DecisionTreeClassifier, DecisionTreeRegressor


class BaseForest(BaseLearner):
    """
    Base class for forest ensemble learners.

    Parameters
    ----------
    n_learners : int, default=100
        Number of trees in the forest.
    criterion : str
        Quality measure for splits.
    max_depth : int or None
        Maximum tree depth.
    min_samples_split : int or float, default=2
        Minimum samples to split.
    min_samples_leaf : int or float, default=1
        Minimum samples in leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in leaf.
    max_features : int, float, str, or None
        Features to consider for split.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease.
    bootstrap : bool, default=True
        Use bootstrap sampling.
    oob_score : bool, default=False
        Compute out-of-bag score.
    n_jobs : int or None
        Parallel jobs.
    random_state : int, optional
        Random state.
    verbose : int, default=0
        Verbosity.
    warm_start : bool, default=False
        Reuse previous trees.
    class_weight : dict, "balanced", "balanced_subsample", or None
        Class weights.
    ccp_alpha : float, default=0.0
        Pruning complexity parameter.
    max_samples : int, float, or None
        Samples per bootstrap.
    """

    def __init__(
        self,
        *,
        n_learners: int = 100,
        criterion: str,
        max_depth: Optional[int] = None,
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_features: Optional[Union[int, float, str]] = "sqrt",
        max_leaf_nodes: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        bootstrap: bool = True,
        oob_score: bool = False,
        n_jobs: Optional[int] = None,
        random_state: Optional[int] = None,
        verbose: int = 0,
        warm_start: bool = False,
        class_weight: Optional[Union[dict, str]] = None,
        ccp_alpha: float = 0.0,
        max_samples: Optional[Union[int, float]] = None,
    ):
        self.n_learners = n_learners
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.max_features = max_features
        self.max_leaf_nodes = max_leaf_nodes
        self.min_impurity_decrease = min_impurity_decrease
        self.bootstrap = bootstrap
        self.oob_score = oob_score
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.verbose = verbose
        self.warm_start = warm_start
        self.class_weight = class_weight
        self.ccp_alpha = ccp_alpha
        self.max_samples = max_samples

    def _get_n_samples_bootstrap(self, n_samples: int) -> int:
        """Get number of samples for bootstrap."""
        if self.max_samples is None:
            return n_samples
        elif isinstance(self.max_samples, int):
            return min(self.max_samples, n_samples)
        else:
            return int(self.max_samples * n_samples)

    def _make_tree(self) -> BaseLearner:
        """Create a single tree learner."""
        raise NotImplementedError

    def _train_single_tree(
        self,
        tree: BaseLearner,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
        tree_seed: int,
        n_samples_bootstrap: int,
    ) -> BaseLearner:
        """Train a single tree on bootstrap sample."""
        rng = check_random_state(tree_seed)
        n_samples = X.shape[0]

        if self.bootstrap:
            indices = rng.randint(0, n_samples, n_samples_bootstrap)
            X_train = X[indices]
            y_train = y[indices]
            if sample_weight is not None:
                sw_train = sample_weight[indices]
            else:
                sw_train = None
        else:
            X_train = X
            y_train = y
            sw_train = sample_weight

        tree.train(X_train, y_train, sample_weight=sw_train)
        return tree

    @property
    def feature_importances_(self) -> np.ndarray:
        """
        Compute mean feature importances across all trees.

        Returns
        -------
        importances : ndarray of shape (n_features,)
            Mean feature importances.
        """
        check_is_trained(self)

        importances = np.zeros(self.n_features_in_)
        for tree in self.learners_:
            importances += tree.feature_importances_
        importances /= len(self.learners_)

        return importances


class RandomForestClassifier(ClassifierMixin, BaseForest):
    """
    Random Forest classifier.

    Combines multiple decision trees trained on bootstrap samples
    with random feature selection. Predictions are made by majority
    voting.

    Parameters
    ----------
    n_learners : int, default=100
        Number of trees in the forest.
    criterion : {"gini", "entropy", "log_loss"}, default="gini"
        Quality measure for splits.
    max_depth : int or None
        Maximum tree depth.
    min_samples_split : int or float, default=2
        Minimum samples to split.
    min_samples_leaf : int or float, default=1
        Minimum samples in leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in leaf.
    max_features : int, float, str, or None, default="sqrt"
        Features to consider: int, float fraction, "sqrt", "log2".
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease.
    bootstrap : bool, default=True
        Use bootstrap sampling.
    oob_score : bool, default=False
        Compute out-of-bag score.
    n_jobs : int or None
        Parallel jobs (-1 for all cores).
    random_state : int, optional
        Random state.
    verbose : int, default=0
        Verbosity level.
    warm_start : bool, default=False
        Reuse previous trees.
    class_weight : dict, "balanced", "balanced_subsample", or None
        Class weights.
    ccp_alpha : float, default=0.0
        Pruning complexity parameter.
    max_samples : int, float, or None
        Samples per bootstrap.

    Attributes
    ----------
    learners_ : list of DecisionTreeClassifier
        The trained trees.
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    n_classes_ : int
        Number of classes.
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Mean feature importances.
    oob_score_ : float
        Out-of-bag score (if oob_score=True).

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import RandomForestClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 0], [0, 2]])
    >>> y = np.array([0, 1, 1, 0])
    >>> clf = RandomForestClassifier(n_learners=10, random_state=42)
    >>> clf.train(X, y)
    RandomForestClassifier(n_learners=10, random_state=42)
    >>> clf.infer([[1, 1]])
    array([1])
    """

    def __init__(
        self,
        *,
        n_learners: int = 100,
        criterion: Literal["gini", "entropy", "log_loss"] = "gini",
        max_depth: Optional[int] = None,
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_features: Optional[Union[int, float, str]] = "sqrt",
        max_leaf_nodes: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        bootstrap: bool = True,
        oob_score: bool = False,
        n_jobs: Optional[int] = None,
        random_state: Optional[int] = None,
        verbose: int = 0,
        warm_start: bool = False,
        class_weight: Optional[Union[dict, str]] = None,
        ccp_alpha: float = 0.0,
        max_samples: Optional[Union[int, float]] = None,
    ):
        super().__init__(
            n_learners=n_learners,
            criterion=criterion,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_weight_fraction_leaf=min_weight_fraction_leaf,
            max_features=max_features,
            max_leaf_nodes=max_leaf_nodes,
            min_impurity_decrease=min_impurity_decrease,
            bootstrap=bootstrap,
            oob_score=oob_score,
            n_jobs=n_jobs,
            random_state=random_state,
            verbose=verbose,
            warm_start=warm_start,
            class_weight=class_weight,
            ccp_alpha=ccp_alpha,
            max_samples=max_samples,
        )

    def _make_tree(self) -> DecisionTreeClassifier:
        """Create a single decision tree classifier."""
        return DecisionTreeClassifier(
            criterion=self.criterion,
            splitter="random",  # Use random splits for diversity
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            min_weight_fraction_leaf=self.min_weight_fraction_leaf,
            max_features=self.max_features,
            max_leaf_nodes=self.max_leaf_nodes,
            min_impurity_decrease=self.min_impurity_decrease,
            class_weight=self.class_weight,
            ccp_alpha=self.ccp_alpha,
        )

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "RandomForestClassifier":
        """
        Build a random forest classifier.

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
        self : RandomForestClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        n_samples = X.shape[0]
        n_samples_bootstrap = self._get_n_samples_bootstrap(n_samples)

        # Generate random seeds for each tree
        rng = check_random_state(self.random_state)
        tree_seeds = rng.randint(np.iinfo(np.int32).max, size=self.n_learners)

        # Create and train trees
        if self.warm_start and hasattr(self, "learners_"):
            trees = self.learners_
            n_existing = len(trees)
            n_new = self.n_learners - n_existing
            if n_new > 0:
                trees.extend([self._make_tree() for _ in range(n_new)])
                tree_seeds = tree_seeds[n_existing:]
            else:
                trees = trees[:self.n_learners]
        else:
            trees = [self._make_tree() for _ in range(self.n_learners)]

        # Train trees in parallel
        if self.n_jobs == 1:
            trained_trees = [
                self._train_single_tree(
                    tree, X, y, sample_weight, seed, n_samples_bootstrap
                )
                for tree, seed in zip(trees, tree_seeds)
            ]
        else:
            trained_trees = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                delayed(self._train_single_tree)(
                    tree, X, y, sample_weight, seed, n_samples_bootstrap
                )
                for tree, seed in zip(trees, tree_seeds)
            )

        self.learners_ = trained_trees

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels using majority voting.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels.
        """
        proba = self.infer_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities by averaging tree predictions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Mean class probabilities.
        """
        check_is_trained(self)
        X = check_array(X)

        # Collect predictions from all trees
        all_proba = np.zeros((X.shape[0], self.n_classes_))

        for tree in self.learners_:
            proba = tree.infer_proba(X)
            all_proba += proba

        all_proba /= len(self.learners_)
        return all_proba

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


class RandomForestRegressor(RegressorMixin, BaseForest):
    """
    Random Forest regressor.

    Combines multiple decision trees trained on bootstrap samples
    with random feature selection. Predictions are made by averaging.

    Parameters
    ----------
    n_learners : int, default=100
        Number of trees in the forest.
    criterion : {"squared_error", "absolute_error", "friedman_mse", "poisson"}
        Quality measure for splits.
    max_depth : int or None
        Maximum tree depth.
    min_samples_split : int or float, default=2
        Minimum samples to split.
    min_samples_leaf : int or float, default=1
        Minimum samples in leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in leaf.
    max_features : int, float, str, or None, default=1.0
        Features to consider for split.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease.
    bootstrap : bool, default=True
        Use bootstrap sampling.
    oob_score : bool, default=False
        Compute out-of-bag score.
    n_jobs : int or None
        Parallel jobs.
    random_state : int, optional
        Random state.
    verbose : int, default=0
        Verbosity level.
    warm_start : bool, default=False
        Reuse previous trees.
    ccp_alpha : float, default=0.0
        Pruning complexity parameter.
    max_samples : int, float, or None
        Samples per bootstrap.

    Attributes
    ----------
    learners_ : list of DecisionTreeRegressor
        The trained trees.
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Mean feature importances.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import RandomForestRegressor
    >>> X = np.array([[0], [1], [2], [3]])
    >>> y = np.array([0.0, 1.0, 2.0, 3.0])
    >>> reg = RandomForestRegressor(n_learners=10, random_state=42)
    >>> reg.train(X, y)
    RandomForestRegressor(n_learners=10, random_state=42)
    >>> reg.infer([[1.5]])
    array([1.5...])
    """

    def __init__(
        self,
        *,
        n_learners: int = 100,
        criterion: Literal["squared_error", "absolute_error", "friedman_mse", "poisson"] = "squared_error",
        max_depth: Optional[int] = None,
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_features: Optional[Union[int, float, str]] = 1.0,
        max_leaf_nodes: Optional[int] = None,
        min_impurity_decrease: float = 0.0,
        bootstrap: bool = True,
        oob_score: bool = False,
        n_jobs: Optional[int] = None,
        random_state: Optional[int] = None,
        verbose: int = 0,
        warm_start: bool = False,
        ccp_alpha: float = 0.0,
        max_samples: Optional[Union[int, float]] = None,
    ):
        super().__init__(
            n_learners=n_learners,
            criterion=criterion,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            min_weight_fraction_leaf=min_weight_fraction_leaf,
            max_features=max_features,
            max_leaf_nodes=max_leaf_nodes,
            min_impurity_decrease=min_impurity_decrease,
            bootstrap=bootstrap,
            oob_score=oob_score,
            n_jobs=n_jobs,
            random_state=random_state,
            verbose=verbose,
            warm_start=warm_start,
            class_weight=None,
            ccp_alpha=ccp_alpha,
            max_samples=max_samples,
        )

    def _make_tree(self) -> DecisionTreeRegressor:
        """Create a single decision tree regressor."""
        return DecisionTreeRegressor(
            criterion=self.criterion,
            splitter="random",
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            min_weight_fraction_leaf=self.min_weight_fraction_leaf,
            max_features=self.max_features,
            max_leaf_nodes=self.max_leaf_nodes,
            min_impurity_decrease=self.min_impurity_decrease,
            ccp_alpha=self.ccp_alpha,
        )

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "RandomForestRegressor":
        """
        Build a random forest regressor.

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
        self : RandomForestRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        self.n_features_in_ = X.shape[1]

        n_samples = X.shape[0]
        n_samples_bootstrap = self._get_n_samples_bootstrap(n_samples)

        rng = check_random_state(self.random_state)
        tree_seeds = rng.randint(np.iinfo(np.int32).max, size=self.n_learners)

        if self.warm_start and hasattr(self, "learners_"):
            trees = self.learners_
            n_existing = len(trees)
            n_new = self.n_learners - n_existing
            if n_new > 0:
                trees.extend([self._make_tree() for _ in range(n_new)])
                tree_seeds = tree_seeds[n_existing:]
            else:
                trees = trees[:self.n_learners]
        else:
            trees = [self._make_tree() for _ in range(self.n_learners)]

        if self.n_jobs == 1:
            trained_trees = [
                self._train_single_tree(
                    tree, X, y, sample_weight, seed, n_samples_bootstrap
                )
                for tree, seed in zip(trees, tree_seeds)
            ]
        else:
            trained_trees = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                delayed(self._train_single_tree)(
                    tree, X, y, sample_weight, seed, n_samples_bootstrap
                )
                for tree, seed in zip(trees, tree_seeds)
            )

        self.learners_ = trained_trees

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values by averaging tree predictions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Mean predicted values.
        """
        check_is_trained(self)
        X = check_array(X)

        predictions = np.zeros(X.shape[0])

        for tree in self.learners_:
            predictions += tree.infer(X)

        predictions /= len(self.learners_)
        return predictions

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )
