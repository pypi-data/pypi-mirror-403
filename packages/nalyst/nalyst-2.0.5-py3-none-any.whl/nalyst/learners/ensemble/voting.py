"""
Voting ensemble learners.

Voting ensembles combine predictions from multiple different learners
using hard voting (majority) or soft voting (probability averaging).
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, Union, Literal

import numpy as np
from joblib import Parallel, delayed

from nalyst.core.foundation import (
    BaseLearner,
    ClassifierMixin,
    RegressorMixin,
    TransformerMixin,
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


class VotingClassifier(ClassifierMixin, TransformerMixin, BaseLearner):
    """
    Soft or hard voting classifier for combining learners.

    Uses majority voting (hard) or probability averaging (soft)
    to combine predictions from multiple classifiers.

    Parameters
    ----------
    learners : list of (str, classifier) tuples
        Named classifiers to combine. Format: [("name1", clf1), ("name2", clf2)].
    voting : {"hard", "soft"}, default="hard"
        If "hard", uses majority class. If "soft", averages probabilities.
    weights : array-like, optional
        Weights for each classifier.
    n_jobs : int or None
        Parallel jobs for fitting.
    flatten_transform : bool, default=True
        Flatten transform output.
    verbose : bool, default=False
        Verbose output during fitting.

    Attributes
    ----------
    learners_ : list
        Fitted classifiers.
    named_learners_ : dict
        Dictionary of name -> classifier.
    classes_ : ndarray
        Class labels.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import VotingClassifier
    >>> from nalyst.learners.linear import LogisticLearner
    >>> from nalyst.learners.trees import DecisionTreeClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 0], [0, 2], [1, 0], [0, 1]])
    >>> y = np.array([0, 1, 1, 0, 1, 0])
    >>> clf1 = LogisticLearner(random_state=42)
    >>> clf2 = DecisionTreeClassifier(random_state=42)
    >>> eclf = VotingClassifier(
    ...     learners=[("log", clf1), ("tree", clf2)],
    ...     voting="soft"
    ... )
    >>> eclf.train(X, y)
    VotingClassifier(learners=[...], voting='soft')
    """

    def __init__(
        self,
        learners: List[Tuple[str, Any]],
        *,
        voting: Literal["hard", "soft"] = "hard",
        weights: Optional[np.ndarray] = None,
        n_jobs: Optional[int] = None,
        flatten_transform: bool = True,
        verbose: bool = False,
    ):
        self.learners = learners
        self.voting = voting
        self.weights = weights
        self.n_jobs = n_jobs
        self.flatten_transform = flatten_transform
        self.verbose = verbose

    def _validate_learners(self):
        """Validate learner names and types."""
        names = []
        for name, learner in self.learners:
            if not isinstance(name, str):
                raise ValueError(f"Learner name must be string, got {type(name)}")
            if name in names:
                raise ValueError(f"Duplicate learner name: {name}")
            names.append(name)

            if learner is None:
                continue
            if not hasattr(learner, "train") or not hasattr(learner, "infer"):
                raise TypeError(
                    f"Learner {name} must have train and infer methods"
                )

            if self.voting == "soft" and not hasattr(learner, "infer_proba"):
                raise ValueError(
                    f"Learner {name} must have infer_proba for soft voting"
                )

    @staticmethod
    def _fit_single(
        learner: BaseLearner,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
    ) -> BaseLearner:
        """Fit a single learner."""
        if learner is None:
            return None

        learner_dup = duplicate(learner)
        if sample_weight is not None:
            learner_dup.train(X, y, sample_weight=sample_weight)
        else:
            learner_dup.train(X, y)
        return learner_dup

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "VotingClassifier":
        """
        Fit all classifiers.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target labels.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : VotingClassifier
        """
        self._validate_learners()
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        # Fit all learners
        base_learners = [learner for name, learner in self.learners]

        if self.n_jobs == 1:
            fitted = [
                self._fit_single(learner, X, y, sample_weight)
                for learner in base_learners
            ]
        else:
            fitted = Parallel(n_jobs=self.n_jobs)(
                delayed(self._fit_single)(learner, X, y, sample_weight)
                for learner in base_learners
            )

        self.learners_ = fitted
        self.named_learners_ = {
            name: learner
            for (name, _), learner in zip(self.learners, fitted)
        }

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

        if self.voting == "soft":
            proba = self.infer_proba(X)
            return self.classes_[np.argmax(proba, axis=1)]
        else:
            # Hard voting
            predictions = self._collect_predictions(X)
            return self._majority_vote(predictions)

    def _collect_predictions(self, X: np.ndarray) -> np.ndarray:
        """Collect predictions from all learners."""
        predictions = []
        for learner in self.learners_:
            if learner is not None:
                predictions.append(learner.infer(X))
        return np.array(predictions)

    def _majority_vote(self, predictions: np.ndarray) -> np.ndarray:
        """Perform weighted majority voting."""
        n_samples = predictions.shape[1]
        n_learners = predictions.shape[0]

        if self.weights is None:
            weights = np.ones(n_learners)
        else:
            weights = np.array(self.weights)

        votes = np.zeros((n_samples, len(self.classes_)))

        for i, pred in enumerate(predictions):
            for j, p in enumerate(pred):
                class_idx = np.searchsorted(self.classes_, p)
                if class_idx < len(self.classes_):
                    votes[j, class_idx] += weights[i]

        return self.classes_[np.argmax(votes, axis=1)]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Compute class probabilities.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Weighted average class probabilities.
        """
        check_is_trained(self)
        X = check_array(X)

        n_learners = len([l for l in self.learners_ if l is not None])

        if self.weights is None:
            weights = np.ones(n_learners) / n_learners
        else:
            weights = np.array(self.weights) / np.sum(self.weights)

        avg_proba = None
        weight_idx = 0

        for learner in self.learners_:
            if learner is None:
                continue

            proba = learner.infer_proba(X)

            if avg_proba is None:
                avg_proba = weights[weight_idx] * proba
            else:
                avg_proba += weights[weight_idx] * proba

            weight_idx += 1

        return avg_proba

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform by returning probability predictions.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        proba : ndarray
            Probability predictions from each learner.
        """
        check_is_trained(self)
        X = check_array(X)

        probas = []
        for learner in self.learners_:
            if learner is None:
                continue
            if hasattr(learner, "infer_proba"):
                probas.append(learner.infer_proba(X))

        result = np.array(probas)

        if self.flatten_transform:
            return result.reshape(X.shape[0], -1)
        return result.transpose(1, 0, 2)

    def get_feature_names_out(self, input_features=None):
        """Get feature names after transform."""
        names = []
        for (name, _), learner in zip(self.learners, self.learners_):
            if learner is None:
                continue
            for cls in self.classes_:
                names.append(f"{name}_{cls}")
        return np.array(names)

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


class VotingRegressor(RegressorMixin, TransformerMixin, BaseLearner):
    """
    Voting regressor for combining multiple regressors.

    Combines predictions by averaging or weighted averaging.

    Parameters
    ----------
    learners : list of (str, regressor) tuples
        Named regressors to combine.
    weights : array-like, optional
        Weights for each regressor.
    n_jobs : int or None
        Parallel jobs for fitting.
    verbose : bool, default=False
        Verbose output during fitting.

    Attributes
    ----------
    learners_ : list
        Fitted regressors.
    named_learners_ : dict
        Dictionary of name -> regressor.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import VotingRegressor
    >>> from nalyst.learners.linear import OrdinaryLinearRegressor
    >>> from nalyst.learners.trees import DecisionTreeRegressor
    >>> X = np.array([[0], [1], [2], [3], [4]])
    >>> y = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    >>> reg1 = OrdinaryLinearRegressor()
    >>> reg2 = DecisionTreeRegressor()
    >>> ereg = VotingRegressor(
    ...     learners=[("lr", reg1), ("tree", reg2)]
    ... )
    >>> ereg.train(X, y)
    VotingRegressor(learners=[...])
    """

    def __init__(
        self,
        learners: List[Tuple[str, Any]],
        *,
        weights: Optional[np.ndarray] = None,
        n_jobs: Optional[int] = None,
        verbose: bool = False,
    ):
        self.learners = learners
        self.weights = weights
        self.n_jobs = n_jobs
        self.verbose = verbose

    def _validate_learners(self):
        """Validate learner names and types."""
        names = []
        for name, learner in self.learners:
            if not isinstance(name, str):
                raise ValueError(f"Learner name must be string, got {type(name)}")
            if name in names:
                raise ValueError(f"Duplicate learner name: {name}")
            names.append(name)

            if learner is None:
                continue
            if not hasattr(learner, "train") or not hasattr(learner, "infer"):
                raise TypeError(
                    f"Learner {name} must have train and infer methods"
                )

    @staticmethod
    def _fit_single(
        learner: BaseLearner,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray],
    ) -> BaseLearner:
        """Fit a single learner."""
        if learner is None:
            return None

        learner_dup = duplicate(learner)
        if sample_weight is not None:
            learner_dup.train(X, y, sample_weight=sample_weight)
        else:
            learner_dup.train(X, y)
        return learner_dup

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "VotingRegressor":
        """
        Fit all regressors.

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
        self : VotingRegressor
        """
        self._validate_learners()
        X, y = check_X_y(X, y, y_numeric=True)

        self.n_features_in_ = X.shape[1]

        # Fit all learners
        base_learners = [learner for name, learner in self.learners]

        if self.n_jobs == 1:
            fitted = [
                self._fit_single(learner, X, y, sample_weight)
                for learner in base_learners
            ]
        else:
            fitted = Parallel(n_jobs=self.n_jobs)(
                delayed(self._fit_single)(learner, X, y, sample_weight)
                for learner in base_learners
            )

        self.learners_ = fitted
        self.named_learners_ = {
            name: learner
            for (name, _), learner in zip(self.learners, fitted)
        }

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict target values by weighted averaging.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Weighted average predictions.
        """
        check_is_trained(self)
        X = check_array(X)

        predictions = self._collect_predictions(X)
        return np.average(predictions, axis=0, weights=self.weights)

    def _collect_predictions(self, X: np.ndarray) -> np.ndarray:
        """Collect predictions from all learners."""
        predictions = []
        for learner in self.learners_:
            if learner is not None:
                predictions.append(learner.infer(X))
        return np.array(predictions)

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform by returning predictions from each regressor.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.

        Returns
        -------
        preds : ndarray of shape (n_samples, n_regressors)
            Predictions from each regressor.
        """
        check_is_trained(self)
        X = check_array(X)

        return self._collect_predictions(X).T

    def get_feature_names_out(self, input_features=None):
        """Get feature names after transform."""
        names = []
        for (name, _), learner in zip(self.learners, self.learners_):
            if learner is not None:
                names.append(name)
        return np.array(names)

    def __nalyst_tags__(self) -> LearnerTags:
        return LearnerTags(
            learner_type="regressor",
            target_tags=TargetTags(required=True),
            regressor_tags=RegressorTags(),
        )


class StackingClassifier(ClassifierMixin, BaseLearner):
    """
    Stacked generalization classifier.

    Uses predictions from base learners as features for a meta-learner.

    Parameters
    ----------
    learners : list of (str, classifier) tuples
        Base classifiers.
    final_learner : classifier
        Meta-classifier to combine predictions.
    cv : int, default=5
        Cross-validation folds for generating training data.
    stack_method : {"auto", "infer_proba", "infer"}, default="auto"
        Method to get predictions from base learners.
    use_probas : bool, default=True
        Use probabilities if available.
    passthrough : bool, default=False
        Include original features with stacked predictions.
    n_jobs : int or None
        Parallel jobs for CV.
    verbose : int, default=0
        Verbosity level.

    Attributes
    ----------
    learners_ : list
        Fitted base classifiers.
    final_learner_ : classifier
        Fitted meta-classifier.
    classes_ : ndarray
        Class labels.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.learners.ensemble import StackingClassifier
    >>> from nalyst.learners.linear import LogisticLearner
    >>> from nalyst.learners.trees import DecisionTreeClassifier
    >>> X = np.array([[0, 0], [1, 1], [2, 0], [0, 2]])
    >>> y = np.array([0, 1, 1, 0])
    >>> clf1 = LogisticLearner()
    >>> clf2 = DecisionTreeClassifier()
    >>> meta = LogisticLearner()
    >>> sclf = StackingClassifier(
    ...     learners=[("log", clf1), ("tree", clf2)],
    ...     final_learner=meta
    ... )
    >>> sclf.train(X, y)
    StackingClassifier(...)
    """

    def __init__(
        self,
        learners: List[Tuple[str, Any]],
        final_learner: Any,
        *,
        cv: int = 5,
        stack_method: Literal["auto", "infer_proba", "infer"] = "auto",
        use_probas: bool = True,
        passthrough: bool = False,
        n_jobs: Optional[int] = None,
        verbose: int = 0,
    ):
        self.learners = learners
        self.final_learner = final_learner
        self.cv = cv
        self.stack_method = stack_method
        self.use_probas = use_probas
        self.passthrough = passthrough
        self.n_jobs = n_jobs
        self.verbose = verbose

    def _get_stack_method(self, learner):
        """Determine method to use for stacking."""
        if self.stack_method != "auto":
            return self.stack_method

        if self.use_probas and hasattr(learner, "infer_proba"):
            return "infer_proba"
        return "infer"

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None,
    ) -> "StackingClassifier":
        """
        Fit stacking classifier.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target labels.
        sample_weight : array-like, optional
            Sample weights.

        Returns
        -------
        self : StackingClassifier
        """
        X, y = check_X_y(X, y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)
        self.n_features_in_ = X.shape[1]

        n_samples = X.shape[0]

        # Generate cross-validated predictions
        stack_predictions = []

        for name, learner in self.learners:
            method = self._get_stack_method(learner)
            cv_preds = self._cross_val_predict(learner, X, y, method)
            stack_predictions.append(cv_preds)

        # Prepare meta features
        meta_X = np.column_stack(stack_predictions)
        if self.passthrough:
            meta_X = np.hstack([meta_X, X])

        # Fit base learners on full data
        self.learners_ = []
        for name, learner in self.learners:
            learner_dup = duplicate(learner)
            learner_dup.train(X, y)
            self.learners_.append(learner_dup)

        # Fit meta-learner
        self.final_learner_ = duplicate(self.final_learner)
        self.final_learner_.train(meta_X, y)

        return self

    def _cross_val_predict(
        self,
        learner: BaseLearner,
        X: np.ndarray,
        y: np.ndarray,
        method: str,
    ) -> np.ndarray:
        """Generate cross-validated predictions."""
        n_samples = X.shape[0]
        indices = np.arange(n_samples)

        rng = check_random_state(None)
        rng.shuffle(indices)

        fold_size = n_samples // self.cv

        if method == "infer_proba":
            predictions = np.zeros((n_samples, self.n_classes_))
        else:
            predictions = np.zeros(n_samples)

        for i in range(self.cv):
            start = i * fold_size
            end = (i + 1) * fold_size if i < self.cv - 1 else n_samples

            test_idx = indices[start:end]
            train_idx = np.concatenate([indices[:start], indices[end:]])

            learner_dup = duplicate(learner)
            learner_dup.train(X[train_idx], y[train_idx])

            if method == "infer_proba":
                predictions[test_idx] = learner_dup.infer_proba(X[test_idx])
            else:
                predictions[test_idx] = learner_dup.infer(X[test_idx])

        return predictions

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

        meta_X = self._transform(X)
        return self.final_learner_.infer(meta_X)

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

        meta_X = self._transform(X)

        if hasattr(self.final_learner_, "infer_proba"):
            return self.final_learner_.infer_proba(meta_X)

        # Fall back to hard predictions
        preds = self.final_learner_.infer(meta_X)
        proba = np.zeros((len(preds), self.n_classes_))
        for i, p in enumerate(preds):
            class_idx = np.searchsorted(self.classes_, p)
            proba[i, class_idx] = 1.0
        return proba

    def _transform(self, X: np.ndarray) -> np.ndarray:
        """Transform input using base learners."""
        predictions = []

        for i, learner in enumerate(self.learners_):
            method = self._get_stack_method(self.learners[i][1])

            if method == "infer_proba":
                preds = learner.infer_proba(X)
            else:
                preds = learner.infer(X).reshape(-1, 1)
            predictions.append(preds)

        meta_X = np.column_stack(predictions)
        if self.passthrough:
            meta_X = np.hstack([meta_X, X])

        return meta_X

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
