"""
One-vs-Rest multiclass strategy.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class OneVsRestClassifier(ClassifierMixin, BaseLearner):
    """
    One-vs-the-rest (OvR) multiclass strategy.

    Also known as one-vs-all. This strategy consists in fitting one
    classifier per class. For each classifier, the class is fitted
    against all the other classes.

    Parameters
    ----------
    estimator : estimator object
        A regressor or classifier that implements train/infer.
    n_jobs : int, default=None
        Number of jobs for parallel execution.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    estimators_ : list of estimators
        Fitted estimators.
    n_classes_ : int
        Number of classes.

    Examples
    --------
    >>> from nalyst.multiclass import OneVsRestClassifier
    >>> from nalyst.learners.svm import SupportVectorClassifier
    >>> clf = OneVsRestClassifier(SupportVectorClassifier())
    >>> clf.train(X, y)
    >>> predictions = clf.infer(X_test)
    """

    def __init__(self, estimator, n_jobs: Optional[int] = None):
        self.estimator = estimator
        self.n_jobs = n_jobs

    def train(self, X: np.ndarray, y: np.ndarray) -> "OneVsRestClassifier":
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
        self : OneVsRestClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        self.n_classes_ = len(self.classes_)

        self.estimators_ = []

        for c in self.classes_:
            # Binary target: 1 for current class, 0 for rest
            y_binary = (y == c).astype(int)

            estimator = duplicate(self.estimator)
            estimator.train(X, y_binary)
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
        proba = self.infer_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Probability estimates.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Probability of each class.
        """
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]
        scores = np.zeros((n_samples, self.n_classes_))

        for i, estimator in enumerate(self.estimators_):
            if hasattr(estimator, "infer_proba"):
                proba = estimator.infer_proba(X)
                if proba.ndim == 2:
                    scores[:, i] = proba[:, 1]
                else:
                    scores[:, i] = proba
            elif hasattr(estimator, "decision_function"):
                scores[:, i] = estimator.decision_function(X)
            else:
                scores[:, i] = estimator.infer(X)

        # Normalize
        scores /= scores.sum(axis=1, keepdims=True)

        return scores

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
            Raw decision values.
        """
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]
        scores = np.zeros((n_samples, self.n_classes_))

        for i, estimator in enumerate(self.estimators_):
            if hasattr(estimator, "decision_function"):
                scores[:, i] = estimator.decision_function(X)
            elif hasattr(estimator, "infer_proba"):
                proba = estimator.infer_proba(X)
                if proba.ndim == 2:
                    scores[:, i] = proba[:, 1]
                else:
                    scores[:, i] = proba
            else:
                scores[:, i] = estimator.infer(X)

        return scores
