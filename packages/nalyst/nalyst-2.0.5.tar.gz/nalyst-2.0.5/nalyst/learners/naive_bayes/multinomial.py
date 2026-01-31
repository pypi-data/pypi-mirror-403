"""
Multinomial Naive Bayes classifier.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained


class MultinomialNB(ClassifierMixin, BaseLearner):
    """
    Multinomial Naive Bayes classifier.

    Suitable for classification with discrete features (e.g., word counts
    for text classification).

    Parameters
    ----------
    alpha : float, default=1.0
        Additive (Laplace/Lidstone) smoothing parameter.
    fit_prior : bool, default=True
        Whether to learn class prior probabilities.
    class_prior : array-like of shape (n_classes,), optional
        Prior probabilities of the classes.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    class_count_ : ndarray of shape (n_classes,)
        Number of samples in each class.
    class_log_prior_ : ndarray of shape (n_classes,)
        Log probability of each class.
    feature_count_ : ndarray of shape (n_classes, n_features)
        Number of samples with each feature value per class.
    feature_log_prob_ : ndarray of shape (n_classes, n_features)
        Log probability of features given a class.

    Examples
    --------
    >>> from nalyst.learners.naive_bayes import MultinomialNB
    >>> X = [[2, 1, 0], [1, 2, 0], [0, 1, 2], [0, 0, 3]]
    >>> y = [0, 0, 1, 1]
    >>> clf = MultinomialNB()
    >>> clf.train(X, y)
    MultinomialNB()
    >>> clf.infer([[1, 1, 1]])
    array([0])
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        fit_prior: bool = True,
        class_prior: Optional[np.ndarray] = None,
    ):
        self.alpha = alpha
        self.fit_prior = fit_prior
        self.class_prior = class_prior

    def train(self, X: np.ndarray, y: np.ndarray) -> "MultinomialNB":
        """
        Fit Multinomial Naive Bayes classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data (counts or frequencies).
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : MultinomialNB
            Fitted classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        if np.any(X < 0):
            raise ValueError("Negative values in data for MultinomialNB")

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        # Initialize counts
        self.class_count_ = np.zeros(n_classes)
        self.feature_count_ = np.zeros((n_classes, n_features))

        for i, cls in enumerate(self.classes_):
            X_cls = X[y == cls]
            self.class_count_[i] = len(X_cls)
            self.feature_count_[i] = np.sum(X_cls, axis=0)

        # Compute log probabilities with smoothing
        smoothed_fc = self.feature_count_ + self.alpha
        smoothed_cc = smoothed_fc.sum(axis=1, keepdims=True)
        self.feature_log_prob_ = np.log(smoothed_fc) - np.log(smoothed_cc)

        # Compute class priors
        if self.fit_prior:
            if self.class_prior is not None:
                self.class_log_prior_ = np.log(np.asarray(self.class_prior))
            else:
                self.class_log_prior_ = np.log(self.class_count_) - np.log(self.class_count_.sum())
        else:
            self.class_log_prior_ = np.zeros(n_classes) - np.log(n_classes)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Perform classification on samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted class labels.
        """
        log_proba = self._joint_log_likelihood(X)
        return self.classes_[np.argmax(log_proba, axis=1)]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Return probability estimates.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Probability of each class.
        """
        log_proba = self._joint_log_likelihood(X)
        log_proba_norm = log_proba - np.max(log_proba, axis=1, keepdims=True)
        proba = np.exp(log_proba_norm)
        proba /= proba.sum(axis=1, keepdims=True)
        return proba

    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """Return log-probability estimates."""
        return np.log(self.predict_proba(X))

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        """Compute the unnormalized posterior log probability."""
        check_is_trained(self, "classes_")
        X = check_array(X)

        return np.dot(X, self.feature_log_prob_.T) + self.class_log_prior_

    def partial_train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[np.ndarray] = None,
    ) -> "MultinomialNB":
        """
        Incremental fit on a batch of samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.
        classes : ndarray, optional
            List of all classes.

        Returns
        -------
        self : MultinomialNB
            Updated classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        # Initialize on first call
        if not hasattr(self, "classes_"):
            if classes is None:
                classes = np.unique(y)
            self.classes_ = classes
            n_classes = len(classes)
            n_features = X.shape[1]

            self.class_count_ = np.zeros(n_classes)
            self.feature_count_ = np.zeros((n_classes, n_features))

        # Update counts
        for i, cls in enumerate(self.classes_):
            X_cls = X[y == cls]
            self.class_count_[i] += len(X_cls)
            self.feature_count_[i] += np.sum(X_cls, axis=0)

        # Recompute probabilities
        smoothed_fc = self.feature_count_ + self.alpha
        smoothed_cc = smoothed_fc.sum(axis=1, keepdims=True)
        self.feature_log_prob_ = np.log(smoothed_fc) - np.log(smoothed_cc)

        if self.fit_prior:
            if self.class_prior is not None:
                self.class_log_prior_ = np.log(np.asarray(self.class_prior))
            else:
                self.class_log_prior_ = np.log(self.class_count_) - np.log(self.class_count_.sum())
        else:
            self.class_log_prior_ = np.zeros(len(self.classes_)) - np.log(len(self.classes_))

        return self
