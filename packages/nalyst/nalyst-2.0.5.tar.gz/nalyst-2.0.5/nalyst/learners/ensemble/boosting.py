"""
Gradient Boosting and AdaBoost ensemble learners.
"""

from __future__ import annotations

from typing import Any, Callable, List, Literal, Optional, Union

import numpy as np
from scipy.special import expit, softmax

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
from nalyst.learners.trees import DecisionTreeRegressor


class GradientBoostingClassifier(ClassifierMixin, BaseLearner):
    """
    Gradient Boosting classifier.

    Builds an additive model by sequentially fitting weak learners
    (typically shallow trees) to the negative gradient of the loss.

    Parameters
    ----------
    loss : {"log_loss", "exponential"}, default="log_loss"
        Loss function. "log_loss" for logistic regression,
        "exponential" for AdaBoost-like boosting.
    learning_rate : float, default=0.1
        Shrinkage factor applied to each tree.
    n_learners : int, default=100
        Number of boosting stages.
    subsample : float, default=1.0
        Fraction of samples for fitting trees.
    criterion : {"friedman_mse", "squared_error"}, default="friedman_mse"
        Quality measure for splits.
    min_samples_split : int or float, default=2
        Minimum samples to split.
    min_samples_leaf : int or float, default=1
        Minimum samples in leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in leaf.
    max_depth : int, default=3
        Maximum tree depth.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease.
    random_state : int, optional
        Random state.
    max_features : int, float, str, or None
        Features to consider.
    verbose : int, default=0
        Verbosity level.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    warm_start : bool, default=False
        Reuse previous learners.
    validation_fraction : float, default=0.1
        Fraction for early stopping validation.
    n_iter_no_change : int or None
        Iterations without improvement for early stopping.
    tol : float, default=1e-4
        Tolerance for early stopping.
    ccp_alpha : float, default=0.0
        Pruning complexity parameter.

    Attributes
    ----------
    learners_ : list of DecisionTreeRegressor
        The sequence of fitted trees.
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    n_classes_ : int
        Number of classes.
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Mean feature importances.
    train_score_ : ndarray
        Training scores per iteration.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import GradientBoostingClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 0], [0, 2]])
    >>> y = np.array([0, 1, 1, 0])
    >>> clf = GradientBoostingClassifier(n_learners=50, max_depth=2)
    >>> clf.train(X, y)
    GradientBoostingClassifier(max_depth=2, n_learners=50)
    >>> clf.infer([[1, 1]])
    array([1])
    """

    def __init__(
        self,
        *,
        loss: Literal["log_loss", "exponential"] = "log_loss",
        learning_rate: float = 0.1,
        n_learners: int = 100,
        subsample: float = 1.0,
        criterion: Literal["friedman_mse", "squared_error"] = "friedman_mse",
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_depth: int = 3,
        min_impurity_decrease: float = 0.0,
        random_state: Optional[int] = None,
        max_features: Optional[Union[int, float, str]] = None,
        verbose: int = 0,
        max_leaf_nodes: Optional[int] = None,
        warm_start: bool = False,
        validation_fraction: float = 0.1,
        n_iter_no_change: Optional[int] = None,
        tol: float = 1e-4,
        ccp_alpha: float = 0.0,
    ):
        self.loss = loss
        self.learning_rate = learning_rate
        self.n_learners = n_learners
        self.subsample = subsample
        self.criterion = criterion
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.max_depth = max_depth
        self.min_impurity_decrease = min_impurity_decrease
        self.random_state = random_state
        self.max_features = max_features
        self.verbose = verbose
        self.max_leaf_nodes = max_leaf_nodes
        self.warm_start = warm_start
        self.validation_fraction = validation_fraction
        self.n_iter_no_change = n_iter_no_change
        self.tol = tol
        self.ccp_alpha = ccp_alpha

    def _make_tree(self) -> DecisionTreeRegressor:
        """Create a weak learner tree."""
        return DecisionTreeRegressor(
            criterion=self.criterion,
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
    ) -> "GradientBoostingClassifier":
        """
        Fit gradient boosting classifier.

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
        self : GradientBoostingClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]
        n_samples = X.shape[0]

        rng = check_random_state(self.random_state)

        # Encode labels
        label_map = {c: i for i, c in enumerate(self.classes_)}
        y_encoded = np.array([label_map[yi] for yi in y])

        if self.n_classes_ == 2:
            # Binary classification
            return self._train_binary(X, y_encoded, sample_weight, rng)
        else:
            # Multiclass classification (one tree per class per stage)
            return self._train_multiclass(X, y_encoded, sample_weight, rng)

    def _train_binary(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
        rng: np.random.RandomState,
    ) -> "GradientBoostingClassifier":
        """Train for binary classification."""
        n_samples = X.shape[0]

        # Initialize with log-odds
        pos_rate = np.mean(y)
        self.init_score_ = np.log(pos_rate / (1 - pos_rate + 1e-10))

        # Current predictions (log-odds)
        F = np.full(n_samples, self.init_score_)

        self.learners_ = []
        self.train_score_ = []

        for i in range(self.n_learners):
            # Compute probabilities
            p = expit(F)

            # Compute negative gradient (residuals for log-loss)
            residuals = y - p

            # Subsample if needed
            if self.subsample < 1.0:
                n_subsample = max(1, int(self.subsample * n_samples))
                indices = rng.choice(n_samples, n_subsample, replace=False)
                X_sub = X[indices]
                residuals_sub = residuals[indices]
                sw_sub = sample_weight[indices] if sample_weight is not None else None
            else:
                X_sub = X
                residuals_sub = residuals
                sw_sub = sample_weight

            # Fit tree to residuals
            tree = self._make_tree()
            tree.train(X_sub, residuals_sub, sample_weight=sw_sub)

            # Update predictions
            predictions = tree.infer(X)
            F += self.learning_rate * predictions

            self.learners_.append(tree)

            # Compute training score
            train_score = -np.mean(
                y * np.log(expit(F) + 1e-10) +
                (1 - y) * np.log(1 - expit(F) + 1e-10)
            )
            self.train_score_.append(train_score)

            if self.verbose > 0 and (i + 1) % 10 == 0:
                print(f"Iteration {i + 1}, train loss: {train_score:.4f}")

        self.train_score_ = np.array(self.train_score_)
        return self

    def _train_multiclass(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
        rng: np.random.RandomState,
    ) -> "GradientBoostingClassifier":
        """Train for multiclass classification."""
        n_samples = X.shape[0]
        n_classes = self.n_classes_

        # One-hot encode targets
        y_onehot = np.zeros((n_samples, n_classes))
        y_onehot[np.arange(n_samples), y] = 1

        # Initialize scores
        class_priors = np.mean(y_onehot, axis=0)
        self.init_score_ = np.log(class_priors + 1e-10)

        F = np.tile(self.init_score_, (n_samples, 1))

        self.learners_ = []  # List of lists, one per class
        self.train_score_ = []

        for i in range(self.n_learners):
            # Compute probabilities using softmax
            p = softmax(F, axis=1)

            # Trees for this stage
            stage_trees = []

            for k in range(n_classes):
                # Negative gradient for class k
                residuals = y_onehot[:, k] - p[:, k]

                # Subsample
                if self.subsample < 1.0:
                    n_subsample = max(1, int(self.subsample * n_samples))
                    indices = rng.choice(n_samples, n_subsample, replace=False)
                    X_sub = X[indices]
                    residuals_sub = residuals[indices]
                    sw_sub = sample_weight[indices] if sample_weight is not None else None
                else:
                    X_sub = X
                    residuals_sub = residuals
                    sw_sub = sample_weight

                # Fit tree
                tree = self._make_tree()
                tree.train(X_sub, residuals_sub, sample_weight=sw_sub)

                # Update predictions
                predictions = tree.infer(X)
                F[:, k] += self.learning_rate * predictions

                stage_trees.append(tree)

            self.learners_.append(stage_trees)

            # Compute training score (cross-entropy)
            p_clipped = np.clip(softmax(F, axis=1), 1e-10, 1 - 1e-10)
            train_score = -np.mean(np.sum(y_onehot * np.log(p_clipped), axis=1))
            self.train_score_.append(train_score)

            if self.verbose > 0 and (i + 1) % 10 == 0:
                print(f"Iteration {i + 1}, train loss: {train_score:.4f}")

        self.train_score_ = np.array(self.train_score_)
        return self

    def _raw_predict(self, X: np.ndarray) -> np.ndarray:
        """Get raw predictions (log-odds or logits)."""
        check_is_trained(self)
        X = check_array(X)

        n_samples = X.shape[0]

        if self.n_classes_ == 2:
            F = np.full(n_samples, self.init_score_)
            for tree in self.learners_:
                F += self.learning_rate * tree.infer(X)
            return F
        else:
            F = np.tile(self.init_score_, (n_samples, 1))
            for stage_trees in self.learners_:
                for k, tree in enumerate(stage_trees):
                    F[:, k] += self.learning_rate * tree.infer(X)
            return F

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
        proba = self.infer_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

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
        raw = self._raw_predict(X)

        if self.n_classes_ == 2:
            proba_1 = expit(raw)
            return np.column_stack([1 - proba_1, proba_1])
        else:
            return softmax(raw, axis=1)

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute decision function (raw predictions)."""
        return self._raw_predict(X)

    @property
    def feature_importances_(self) -> np.ndarray:
        """Mean feature importances across all trees."""
        check_is_trained(self)

        importances = np.zeros(self.n_features_in_)
        total_trees = 0

        if self.n_classes_ == 2:
            for tree in self.learners_:
                importances += tree.feature_importances_
                total_trees += 1
        else:
            for stage_trees in self.learners_:
                for tree in stage_trees:
                    importances += tree.feature_importances_
                    total_trees += 1

        return importances / total_trees

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                predict_proba=True,
                decision_function=True,
            ),
        )


class GradientBoostingRegressor(RegressorMixin, BaseLearner):
    """
    Gradient Boosting regressor.

    Builds an additive model by sequentially fitting weak learners
    to the negative gradient of the loss.

    Parameters
    ----------
    loss : {"squared_error", "absolute_error", "huber", "quantile"}
        Loss function.
    learning_rate : float, default=0.1
        Shrinkage factor.
    n_learners : int, default=100
        Number of boosting stages.
    subsample : float, default=1.0
        Fraction of samples for fitting trees.
    criterion : {"friedman_mse", "squared_error"}, default="friedman_mse"
        Quality measure for splits.
    min_samples_split : int or float, default=2
        Minimum samples to split.
    min_samples_leaf : int or float, default=1
        Minimum samples in leaf.
    min_weight_fraction_leaf : float, default=0.0
        Minimum weighted fraction in leaf.
    max_depth : int, default=3
        Maximum tree depth.
    min_impurity_decrease : float, default=0.0
        Minimum impurity decrease.
    random_state : int, optional
        Random state.
    max_features : int, float, str, or None
        Features to consider.
    alpha : float, default=0.9
        Quantile for quantile loss.
    verbose : int, default=0
        Verbosity level.
    max_leaf_nodes : int or None
        Maximum leaf nodes.
    warm_start : bool, default=False
        Reuse previous learners.
    validation_fraction : float, default=0.1
        Fraction for early stopping.
    n_iter_no_change : int or None
        Iterations for early stopping.
    tol : float, default=1e-4
        Tolerance for early stopping.
    ccp_alpha : float, default=0.0
        Pruning complexity.

    Attributes
    ----------
    learners_ : list of DecisionTreeRegressor
        Fitted trees.
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Mean feature importances.
    train_score_ : ndarray
        Training scores per iteration.
    """

    def __init__(
        self,
        *,
        loss: Literal["squared_error", "absolute_error", "huber", "quantile"] = "squared_error",
        learning_rate: float = 0.1,
        n_learners: int = 100,
        subsample: float = 1.0,
        criterion: Literal["friedman_mse", "squared_error"] = "friedman_mse",
        min_samples_split: Union[int, float] = 2,
        min_samples_leaf: Union[int, float] = 1,
        min_weight_fraction_leaf: float = 0.0,
        max_depth: int = 3,
        min_impurity_decrease: float = 0.0,
        random_state: Optional[int] = None,
        max_features: Optional[Union[int, float, str]] = None,
        alpha: float = 0.9,
        verbose: int = 0,
        max_leaf_nodes: Optional[int] = None,
        warm_start: bool = False,
        validation_fraction: float = 0.1,
        n_iter_no_change: Optional[int] = None,
        tol: float = 1e-4,
        ccp_alpha: float = 0.0,
    ):
        self.loss = loss
        self.learning_rate = learning_rate
        self.n_learners = n_learners
        self.subsample = subsample
        self.criterion = criterion
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.max_depth = max_depth
        self.min_impurity_decrease = min_impurity_decrease
        self.random_state = random_state
        self.max_features = max_features
        self.alpha = alpha
        self.verbose = verbose
        self.max_leaf_nodes = max_leaf_nodes
        self.warm_start = warm_start
        self.validation_fraction = validation_fraction
        self.n_iter_no_change = n_iter_no_change
        self.tol = tol
        self.ccp_alpha = ccp_alpha

    def _make_tree(self) -> DecisionTreeRegressor:
        """Create a weak learner tree."""
        return DecisionTreeRegressor(
            criterion=self.criterion,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            min_weight_fraction_leaf=self.min_weight_fraction_leaf,
            max_features=self.max_features,
            max_leaf_nodes=self.max_leaf_nodes,
            min_impurity_decrease=self.min_impurity_decrease,
            ccp_alpha=self.ccp_alpha,
        )

    def _compute_residuals(self, y: np.ndarray, F: np.ndarray) -> np.ndarray:
        """Compute negative gradient (residuals)."""
        if self.loss == "squared_error":
            return y - F
        elif self.loss == "absolute_error":
            return np.sign(y - F)
        elif self.loss == "huber":
            diff = y - F
            delta = np.percentile(np.abs(diff), 90)
            mask = np.abs(diff) <= delta
            residuals = np.where(mask, diff, delta * np.sign(diff))
            return residuals
        elif self.loss == "quantile":
            diff = y - F
            return np.where(diff >= 0, self.alpha, self.alpha - 1)
        else:
            return y - F

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "GradientBoostingRegressor":
        """
        Fit gradient boosting regressor.

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
        self : GradientBoostingRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        self.n_features_in_ = X.shape[1]
        n_samples = X.shape[0]

        rng = check_random_state(self.random_state)

        # Initialize with constant
        if self.loss == "absolute_error":
            self.init_score_ = np.median(y)
        elif self.loss == "quantile":
            self.init_score_ = np.percentile(y, 100 * self.alpha)
        else:
            self.init_score_ = np.mean(y)

        F = np.full(n_samples, self.init_score_)

        self.learners_ = []
        self.train_score_ = []

        for i in range(self.n_learners):
            # Compute residuals
            residuals = self._compute_residuals(y, F)

            # Subsample
            if self.subsample < 1.0:
                n_subsample = max(1, int(self.subsample * n_samples))
                indices = rng.choice(n_samples, n_subsample, replace=False)
                X_sub = X[indices]
                residuals_sub = residuals[indices]
                sw_sub = sample_weight[indices] if sample_weight is not None else None
            else:
                X_sub = X
                residuals_sub = residuals
                sw_sub = sample_weight

            # Fit tree
            tree = self._make_tree()
            tree.train(X_sub, residuals_sub, sample_weight=sw_sub)

            # Update predictions
            predictions = tree.infer(X)
            F += self.learning_rate * predictions

            self.learners_.append(tree)

            # Compute training score
            if self.loss == "squared_error":
                train_score = np.mean((y - F) ** 2)
            elif self.loss == "absolute_error":
                train_score = np.mean(np.abs(y - F))
            else:
                train_score = np.mean((y - F) ** 2)

            self.train_score_.append(train_score)

            if self.verbose > 0 and (i + 1) % 10 == 0:
                print(f"Iteration {i + 1}, train loss: {train_score:.4f}")

        self.train_score_ = np.array(self.train_score_)
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

        F = np.full(X.shape[0], self.init_score_)

        for tree in self.learners_:
            F += self.learning_rate * tree.infer(X)

        return F

    @property
    def feature_importances_(self) -> np.ndarray:
        """Mean feature importances across all trees."""
        check_is_trained(self)

        importances = np.zeros(self.n_features_in_)
        for tree in self.learners_:
            importances += tree.feature_importances_

        return importances / len(self.learners_)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )


class AdaBoostClassifier(ClassifierMixin, BaseLearner):
    """
    AdaBoost classifier.

    Adaptive Boosting iteratively trains weak classifiers on
    weighted samples, increasing weights of misclassified samples.

    Parameters
    ----------
    base_learner : object or None
        Base classifier to boost. If None, uses DecisionTreeClassifier
        with max_depth=1 (decision stump).
    n_learners : int, default=50
        Number of boosting iterations.
    learning_rate : float, default=1.0
        Weight update shrinkage factor.
    algorithm : {"SAMME", "SAMME.R"}, default="SAMME.R"
        Boosting algorithm. SAMME.R uses probability estimates.
    random_state : int, optional
        Random state.

    Attributes
    ----------
    learners_ : list
        Fitted weak learners.
    learner_weights_ : ndarray
        Weights of each learner.
    learner_errors_ : ndarray
        Errors of each learner.
    classes_ : ndarray
        Class labels.
    n_classes_ : int
        Number of classes.
    n_features_in_ : int
        Number of features.
    feature_importances_ : ndarray
        Feature importances (if base learner has them).

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import AdaBoostClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 0], [0, 2]])
    >>> y = np.array([0, 1, 1, 0])
    >>> clf = AdaBoostClassifier(n_learners=50)
    >>> clf.train(X, y)
    AdaBoostClassifier(n_learners=50)
    >>> clf.infer([[1, 1]])
    array([1])
    """

    def __init__(
        self,
        *,
        base_learner: Optional[Any] = None,
        n_learners: int = 50,
        learning_rate: float = 1.0,
        algorithm: Literal["SAMME", "SAMME.R"] = "SAMME.R",
        random_state: Optional[int] = None,
    ):
        self.base_learner = base_learner
        self.n_learners = n_learners
        self.learning_rate = learning_rate
        self.algorithm = algorithm
        self.random_state = random_state

    def _make_base_learner(self):
        """Create a base learner."""
        from nalyst.learners.trees import DecisionTreeClassifier
        from nalyst.core.foundation import duplicate

        if self.base_learner is None:
            return DecisionTreeClassifier(max_depth=1)
        else:
            return duplicate(self.base_learner)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "AdaBoostClassifier":
        """
        Fit AdaBoost classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target class labels.
        sample_weight : array-like, optional
            Initial sample weights.

        Returns
        -------
        self : AdaBoostClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]
        n_samples = X.shape[0]

        rng = check_random_state(self.random_state)

        # Initialize sample weights
        if sample_weight is None:
            sample_weight = np.ones(n_samples) / n_samples
        else:
            sample_weight = sample_weight / sample_weight.sum()

        self.learners_ = []
        self.learner_weights_ = []
        self.learner_errors_ = []

        for i in range(self.n_learners):
            # Create and train weak learner
            learner = self._make_base_learner()
            learner.random_state = rng.randint(np.iinfo(np.int32).max)
            learner.train(X, y, sample_weight=sample_weight)

            # Get predictions
            predictions = learner.infer(X)

            # Compute weighted error
            incorrect = predictions != y
            error = np.dot(sample_weight, incorrect)

            # Check for perfect or random classifier
            if error <= 0:
                # Perfect classifier
                self.learners_.append(learner)
                self.learner_weights_.append(1.0)
                self.learner_errors_.append(0.0)
                break
            elif error >= 1 - 1e-10:
                # Random or worse
                break

            # Compute learner weight (alpha)
            if self.n_classes_ == 2:
                alpha = self.learning_rate * np.log((1 - error) / (error + 1e-10))
            else:
                alpha = self.learning_rate * (
                    np.log((1 - error) / (error + 1e-10)) +
                    np.log(self.n_classes_ - 1)
                )

            self.learners_.append(learner)
            self.learner_weights_.append(alpha)
            self.learner_errors_.append(error)

            # Update sample weights
            sample_weight = sample_weight * np.exp(alpha * incorrect)
            sample_weight = sample_weight / sample_weight.sum()

        self.learner_weights_ = np.array(self.learner_weights_)
        self.learner_errors_ = np.array(self.learner_errors_)

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

        n_samples = X.shape[0]

        # Weighted voting
        class_votes = np.zeros((n_samples, self.n_classes_))

        for learner, weight in zip(self.learners_, self.learner_weights_):
            predictions = learner.infer(X)
            for i, pred in enumerate(predictions):
                class_idx = np.searchsorted(self.classes_, pred)
                class_votes[i, class_idx] += weight

        return self.classes_[np.argmax(class_votes, axis=1)]

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

        n_samples = X.shape[0]

        if self.algorithm == "SAMME.R":
            # Use probability estimates
            proba = np.zeros((n_samples, self.n_classes_))

            for learner, weight in zip(self.learners_, self.learner_weights_):
                if hasattr(learner, "infer_proba"):
                    p = learner.infer_proba(X)
                    p = np.clip(p, 1e-10, 1 - 1e-10)
                    log_p = np.log(p)
                    proba += weight * (log_p - log_p.mean(axis=1, keepdims=True))

            proba = softmax(proba, axis=1)
        else:
            # SAMME: use weighted voting
            class_votes = np.zeros((n_samples, self.n_classes_))

            for learner, weight in zip(self.learners_, self.learner_weights_):
                predictions = learner.infer(X)
                for i, pred in enumerate(predictions):
                    class_idx = np.searchsorted(self.classes_, pred)
                    class_votes[i, class_idx] += weight

            proba = class_votes / class_votes.sum(axis=1, keepdims=True)

        return proba

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Compute weighted sum of learner predictions."""
        check_is_trained(self)
        X = check_array(X)

        n_samples = X.shape[0]
        scores = np.zeros((n_samples, self.n_classes_))

        for learner, weight in zip(self.learners_, self.learner_weights_):
            predictions = learner.infer(X)
            for i, pred in enumerate(predictions):
                class_idx = np.searchsorted(self.classes_, pred)
                scores[i, class_idx] += weight

        if self.n_classes_ == 2:
            return scores[:, 1] - scores[:, 0]
        return scores

    @property
    def feature_importances_(self) -> np.ndarray:
        """Weighted mean feature importances."""
        check_is_trained(self)

        if not hasattr(self.learners_[0], "feature_importances_"):
            raise AttributeError(
                "Base learner does not have feature_importances_"
            )

        importances = np.zeros(self.n_features_in_)
        total_weight = 0

        for learner, weight in zip(self.learners_, self.learner_weights_):
            importances += weight * learner.feature_importances_
            total_weight += weight

        return importances / total_weight

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="classifier",
            target_tags=TargetTags(required=True),
            classifier_tags=ClassifierTags(
                binary=True,
                multiclass=True,
                predict_proba=True,
                decision_function=True,
            ),
        )
