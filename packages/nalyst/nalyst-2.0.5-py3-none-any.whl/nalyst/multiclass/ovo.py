"""
One-vs-One multiclass strategy.
"""

from __future__ import annotations

from typing import Optional
from itertools import combinations

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class OneVsOneClassifier(ClassifierMixin, BaseLearner):
    """
    One-vs-one multiclass strategy.

    This strategy consists in fitting one classifier for each pair of classes.
    At prediction time, the class which receives the most votes is selected.

    Parameters
    ----------
    estimator : estimator object
        An estimator that implements train/infer.
    n_jobs : int, default=None
        Number of jobs for parallel execution.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    estimators_ : list of estimators
        Fitted estimators.
    pairwise_indices_ : list of tuples
        Pairs of class indices.

    Examples
    --------
    >>> from nalyst.multiclass import OneVsOneClassifier
    >>> from nalyst.learners.svm import SupportVectorClassifier
    >>> clf = OneVsOneClassifier(SupportVectorClassifier())
    >>> clf.train(X, y)
    >>> predictions = clf.infer(X_test)
    """

    def __init__(self, estimator, n_jobs: Optional[int] = None):
        self.estimator = estimator
        self.n_jobs = n_jobs

    def train(self, X: np.ndarray, y: np.ndarray) -> "OneVsOneClassifier":
        """
        Fit underlying estimators.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : OneVsOneClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)

        self.estimators_ = []
        self.pairwise_indices_ = list(combinations(range(n_classes), 2))

        for i, j in self.pairwise_indices_:
            # Get samples for classes i and j
            mask = (y == self.classes_[i]) | (y == self.classes_[j])
            X_pair = X[mask]
            y_pair = y[mask]

            # Convert to binary
            y_binary = (y_pair == self.classes_[j]).astype(int)

            estimator = duplicate(self.estimator)
            estimator.train(X_pair, y_binary)
            self.estimators_.append(estimator)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels.
        """
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]
        n_classes = len(self.classes_)

        # Vote counting
        votes = np.zeros((n_samples, n_classes))

        for (i, j), estimator in zip(self.pairwise_indices_, self.estimators_):
            pred = estimator.infer(X)

            # Vote for winner
            votes[:, i] += (pred == 0)
            votes[:, j] += (pred == 1)

        return self.classes_[np.argmax(votes, axis=1)]

    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Decision function.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        scores : ndarray of shape (n_samples, n_classes)
            Aggregated decision values.
        """
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]
        n_classes = len(self.classes_)

        # Accumulate decision values
        confidences = np.zeros((n_samples, n_classes))

        for (i, j), estimator in zip(self.pairwise_indices_, self.estimators_):
            if hasattr(estimator, "decision_function"):
                decision = estimator.decision_function(X)
            elif hasattr(estimator, "infer_proba"):
                proba = estimator.infer_proba(X)
                decision = proba[:, 1] - proba[:, 0] if proba.ndim == 2 else proba
            else:
                decision = estimator.infer(X) * 2 - 1

            confidences[:, i] -= decision
            confidences[:, j] += decision

        return confidences
