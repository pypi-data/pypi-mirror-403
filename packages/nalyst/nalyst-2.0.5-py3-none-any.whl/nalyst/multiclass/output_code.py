"""
Error-Correcting Output-Code multiclass strategy.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class OutputCodeClassifier(ClassifierMixin, BaseLearner):
    """
    (Error-Correcting) Output-Code multiclass strategy.

    Output-code based strategies consist in representing each class
    with a binary code.

    Parameters
    ----------
    estimator : estimator object
        An estimator that implements train/infer.
    code_size : float, default=1.5
        Percentage of the number of classes to generate.
    random_state : int, optional
        Random seed.
    n_jobs : int, default=None
        Number of jobs for parallel execution.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    code_book_ : ndarray of shape (n_classes, n_estimators)
        Binary code for each class.
    estimators_ : list of estimators
        Fitted estimators.

    Examples
    --------
    >>> from nalyst.multiclass import OutputCodeClassifier
    >>> from nalyst.learners.svm import SupportVectorClassifier
    >>> clf = OutputCodeClassifier(SupportVectorClassifier(), code_size=2)
    >>> clf.train(X, y)
    >>> predictions = clf.infer(X_test)
    """

    def __init__(
        self,
        estimator,
        code_size: float = 1.5,
        random_state: Optional[int] = None,
        n_jobs: Optional[int] = None,
    ):
        self.estimator = estimator
        self.code_size = code_size
        self.random_state = random_state
        self.n_jobs = n_jobs

    def train(self, X: np.ndarray, y: np.ndarray) -> "OutputCodeClassifier":
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
        self : OutputCodeClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y)

        if self.random_state is not None:
            np.random.seed(self.random_state)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)

        # Generate code book
        n_estimators = int(n_classes * self.code_size)
        self.code_book_ = np.random.choice([-1, 1], size=(n_classes, n_estimators))

        # Ensure each column has both -1 and 1
        for j in range(n_estimators):
            if np.all(self.code_book_[:, j] == 1):
                self.code_book_[0, j] = -1
            elif np.all(self.code_book_[:, j] == -1):
                self.code_book_[0, j] = 1

        self.estimators_ = []

        for j in range(n_estimators):
            # Create binary target
            y_binary = np.zeros(len(y))
            for i, c in enumerate(self.classes_):
                y_binary[y == c] = self.code_book_[i, j]

            # Convert to 0/1
            y_binary = (y_binary > 0).astype(int)

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
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]
        n_estimators = len(self.estimators_)

        # Get predictions from all estimators
        predictions = np.zeros((n_samples, n_estimators))

        for j, estimator in enumerate(self.estimators_):
            pred = estimator.infer(X)
            predictions[:, j] = pred * 2 - 1  # Convert to -1/1

        # Find closest code word using Hamming distance
        distances = np.zeros((n_samples, len(self.classes_)))

        for i in range(len(self.classes_)):
            distances[:, i] = np.sum(predictions != self.code_book_[i], axis=1)

        return self.classes_[np.argmin(distances, axis=1)]

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
            Negative distances to each class code.
        """
        check_is_trained(self, "estimators_")
        X = check_array(X)

        n_samples = X.shape[0]
        n_estimators = len(self.estimators_)

        # Get decision values
        decisions = np.zeros((n_samples, n_estimators))

        for j, estimator in enumerate(self.estimators_):
            if hasattr(estimator, "decision_function"):
                decisions[:, j] = estimator.decision_function(X)
            elif hasattr(estimator, "infer_proba"):
                proba = estimator.infer_proba(X)
                if proba.ndim == 2:
                    decisions[:, j] = proba[:, 1] - proba[:, 0]
                else:
                    decisions[:, j] = proba * 2 - 1
            else:
                decisions[:, j] = estimator.infer(X) * 2 - 1

        # Compute distances (negative for scoring)
        scores = np.zeros((n_samples, len(self.classes_)))

        for i in range(len(self.classes_)):
            scores[:, i] = -np.sum((decisions - self.code_book_[i]) ** 2, axis=1)

        return scores
