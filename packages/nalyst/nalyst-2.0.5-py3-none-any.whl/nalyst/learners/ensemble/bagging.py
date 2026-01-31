"""
Bagging ensemble learners.

Bootstrap Aggregating trains multiple learners on bootstrap samples
and combines predictions through voting or averaging.
"""

from __future__ import annotations

from typing import Any, Optional, Union

import numpy as np
from joblib import Parallel, delayed

from nalyst.core.foundation import (
    BaseLearner,
    ClassifierMixin,
    RegressorMixin,
    duplicate,
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


class BaseBagging(BaseLearner):
    """
    Base class for bagging ensemble learners.

    Parameters
    ----------
    base_learner : object or None
        Base learner to bag. If None, uses a default learner.
    n_learners : int, default=10
        Number of learners in the ensemble.
    max_samples : int or float, default=1.0
        Samples per bootstrap (int or fraction).
    max_features : int or float, default=1.0
        Features per learner (int or fraction).
    bootstrap : bool, default=True
        Whether to use bootstrap sampling.
    bootstrap_features : bool, default=False
        Whether to bootstrap features.
    oob_score : bool, default=False
        Compute out-of-bag score.
    warm_start : bool, default=False
        Reuse previous learners.
    n_jobs : int or None
        Parallel jobs.
    random_state : int, optional
        Random state.
    verbose : int, default=0
        Verbosity level.
    """

    def __init__(
        self,
        base_learner: Optional[Any] = None,
        n_learners: int = 10,
        *,
        max_samples: Union[int, float] = 1.0,
        max_features: Union[int, float] = 1.0,
        bootstrap: bool = True,
        bootstrap_features: bool = False,
        oob_score: bool = False,
        warm_start: bool = False,
        n_jobs: Optional[int] = None,
        random_state: Optional[int] = None,
        verbose: int = 0,
    ):
        self.base_learner = base_learner
        self.n_learners = n_learners
        self.max_samples = max_samples
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.bootstrap_features = bootstrap_features
        self.oob_score = oob_score
        self.warm_start = warm_start
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.verbose = verbose

    def _make_learner(self) -> BaseLearner:
        """Create a base learner."""
        raise NotImplementedError

    def _get_n_samples(self, n_samples: int) -> int:
        """Get number of samples for bootstrap."""
        if isinstance(self.max_samples, int):
            return min(self.max_samples, n_samples)
        return int(self.max_samples * n_samples)

    def _get_n_features(self, n_features: int) -> int:
        """Get number of features to use."""
        if isinstance(self.max_features, int):
            return min(self.max_features, n_features)
        return int(self.max_features * n_features)

    def _train_learner(
        self,
        learner: BaseLearner,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
        seed: int,
        n_samples_bootstrap: int,
        n_features_subset: int,
    ) -> tuple:
        """Train a single learner on a bootstrap sample."""
        rng = check_random_state(seed)
        n_samples, n_features = X.shape

        # Sample selection
        if self.bootstrap:
            sample_indices = rng.randint(0, n_samples, n_samples_bootstrap)
        else:
            sample_indices = rng.choice(
                n_samples, n_samples_bootstrap, replace=False
            )

        # Feature selection
        if self.bootstrap_features:
            feature_indices = rng.randint(0, n_features, n_features_subset)
        else:
            feature_indices = rng.choice(
                n_features, n_features_subset, replace=False
            )

        X_sub = X[sample_indices][:, feature_indices]
        y_sub = y[sample_indices]

        if sample_weight is not None:
            sw_sub = sample_weight[sample_indices]
        else:
            sw_sub = None

        learner.train(X_sub, y_sub, sample_weight=sw_sub)

        return learner, feature_indices, sample_indices


class BaggingClassifier(ClassifierMixin, BaseBagging):
    """
    Bagging classifier.

    Combines multiple classifiers trained on bootstrap samples
    using majority voting.

    Parameters
    ----------
    base_learner : object or None
        Base classifier. If None, uses DecisionTreeClassifier.
    n_learners : int, default=10
        Number of classifiers.
    max_samples : int or float, default=1.0
        Samples per bootstrap.
    max_features : int or float, default=1.0
        Features per classifier.
    bootstrap : bool, default=True
        Use bootstrap sampling.
    bootstrap_features : bool, default=False
        Bootstrap features.
    oob_score : bool, default=False
        Compute out-of-bag score.
    warm_start : bool, default=False
        Reuse previous learners.
    n_jobs : int or None
        Parallel jobs.
    random_state : int, optional
        Random state.
    verbose : int, default=0
        Verbosity level.

    Attributes
    ----------
    learners_ : list
        Fitted classifiers.
    learner_features_ : list of ndarray
        Feature indices for each learner.
    classes_ : ndarray
        Class labels.
    n_classes_ : int
        Number of classes.
    n_features_in_ : int
        Number of features.
    oob_score_ : float
        Out-of-bag score (if oob_score=True).

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import BaggingClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 0], [0, 2]])
    >>> y = np.array([0, 1, 1, 0])
    >>> clf = BaggingClassifier(n_learners=10, random_state=42)
    >>> clf.train(X, y)
    BaggingClassifier(n_learners=10, random_state=42)
    >>> clf.infer([[1, 1]])
    array([1])
    """

    def _make_learner(self) -> BaseLearner:
        """Create base classifier."""
        from nalyst.learners.trees import DecisionTreeClassifier

        if self.base_learner is None:
            return DecisionTreeClassifier()
        return duplicate(self.base_learner)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "BaggingClassifier":
        """
        Fit bagging classifier.

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
        self : BaggingClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]
        n_samples = X.shape[0]

        n_samples_bootstrap = self._get_n_samples(n_samples)
        n_features_subset = self._get_n_features(self.n_features_in_)

        rng = check_random_state(self.random_state)
        seeds = rng.randint(np.iinfo(np.int32).max, size=self.n_learners)

        learners = [self._make_learner() for _ in range(self.n_learners)]

        if self.n_jobs == 1:
            results = [
                self._train_learner(
                    learner, X, y, sample_weight, seed,
                    n_samples_bootstrap, n_features_subset
                )
                for learner, seed in zip(learners, seeds)
            ]
        else:
            results = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                delayed(self._train_learner)(
                    learner, X, y, sample_weight, seed,
                    n_samples_bootstrap, n_features_subset
                )
                for learner, seed in zip(learners, seeds)
            )

        self.learners_ = [r[0] for r in results]
        self.learner_features_ = [r[1] for r in results]

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels by majority voting.

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
        Predict class probabilities by averaging.

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

        all_proba = np.zeros((X.shape[0], self.n_classes_))

        for learner, features in zip(self.learners_, self.learner_features_):
            X_sub = X[:, features]
            if hasattr(learner, "infer_proba"):
                proba = learner.infer_proba(X_sub)
            else:
                predictions = learner.infer(X_sub)
                proba = np.zeros((len(predictions), self.n_classes_))
                for i, pred in enumerate(predictions):
                    class_idx = np.searchsorted(self.classes_, pred)
                    proba[i, class_idx] = 1.0
            all_proba += proba

        return all_proba / len(self.learners_)

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


class BaggingRegressor(RegressorMixin, BaseBagging):
    """
    Bagging regressor.

    Combines multiple regressors trained on bootstrap samples
    by averaging predictions.

    Parameters
    ----------
    base_learner : object or None
        Base regressor. If None, uses DecisionTreeRegressor.
    n_learners : int, default=10
        Number of regressors.
    max_samples : int or float, default=1.0
        Samples per bootstrap.
    max_features : int or float, default=1.0
        Features per regressor.
    bootstrap : bool, default=True
        Use bootstrap sampling.
    bootstrap_features : bool, default=False
        Bootstrap features.
    oob_score : bool, default=False
        Compute out-of-bag score.
    warm_start : bool, default=False
        Reuse previous learners.
    n_jobs : int or None
        Parallel jobs.
    random_state : int, optional
        Random state.
    verbose : int, default=0
        Verbosity level.

    Attributes
    ----------
    learners_ : list
        Fitted regressors.
    learner_features_ : list of ndarray
        Feature indices for each learner.
    n_features_in_ : int
        Number of features.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import BaggingRegressor
    >>> X = np.array([[0], [1], [2], [3]])
    >>> y = np.array([0.0, 1.0, 2.0, 3.0])
    >>> reg = BaggingRegressor(n_learners=10, random_state=42)
    >>> reg.train(X, y)
    BaggingRegressor(n_learners=10, random_state=42)
    >>> reg.infer([[1.5]])
    array([1.5...])
    """

    def _make_learner(self) -> BaseLearner:
        """Create base regressor."""
        from nalyst.learners.trees import DecisionTreeRegressor

        if self.base_learner is None:
            return DecisionTreeRegressor()
        return duplicate(self.base_learner)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "BaggingRegressor":
        """
        Fit bagging regressor.

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
        self : BaggingRegressor
        """
        X, y = check_X_y(X, y, y_numeric=True)

        self.n_features_in_ = X.shape[1]
        n_samples = X.shape[0]

        n_samples_bootstrap = self._get_n_samples(n_samples)
        n_features_subset = self._get_n_features(self.n_features_in_)

        rng = check_random_state(self.random_state)
        seeds = rng.randint(np.iinfo(np.int32).max, size=self.n_learners)

        learners = [self._make_learner() for _ in range(self.n_learners)]

        if self.n_jobs == 1:
            results = [
                self._train_learner(
                    learner, X, y, sample_weight, seed,
                    n_samples_bootstrap, n_features_subset
                )
                for learner, seed in zip(learners, seeds)
            ]
        else:
            results = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                delayed(self._train_learner)(
                    learner, X, y, sample_weight, seed,
                    n_samples_bootstrap, n_features_subset
                )
                for learner, seed in zip(learners, seeds)
            )

        self.learners_ = [r[0] for r in results]
        self.learner_features_ = [r[1] for r in results]

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values by averaging.

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

        for learner, features in zip(self.learners_, self.learner_features_):
            X_sub = X[:, features]
            predictions += learner.infer(X_sub)

        return predictions / len(self.learners_)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )
