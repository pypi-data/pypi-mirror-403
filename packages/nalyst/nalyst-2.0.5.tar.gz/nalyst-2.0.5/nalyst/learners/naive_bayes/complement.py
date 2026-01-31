"""
Complement Naive Bayes classifier.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained


class ComplementNB(ClassifierMixin, BaseLearner):
    """
    Complement Naive Bayes classifier.

    Particularly suited for imbalanced data sets.

    Parameters
    ----------
    alpha : float, default=1.0
        Additive (Laplace) smoothing parameter.
    fit_prior : bool, default=True
        Whether to learn class prior probabilities.
    class_prior : array-like of shape (n_classes,), optional
        Prior probabilities of the classes.
    norm : bool, default=False
        Whether to weight features by their frequency.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    class_count_ : ndarray of shape (n_classes,)
        Number of samples in each class.
    class_log_prior_ : ndarray of shape (n_classes,)
        Log probability of each class.
    feature_count_ : ndarray of shape (n_classes, n_features)
        Feature counts per class.
    feature_all_ : ndarray of shape (n_features,)
        Sum of feature counts across all classes.
    feature_log_prob_ : ndarray of shape (n_classes, n_features)
        Complement feature log probabilities.

    Examples
    --------
    >>> from nalyst.learners.naive_bayes import ComplementNB
    >>> X = [[1, 2, 0], [2, 1, 0], [0, 1, 2], [0, 0, 3]]
    >>> y = [0, 0, 1, 1]
    >>> clf = ComplementNB()
    >>> clf.train(X, y)
    ComplementNB()
    >>> clf.infer([[1, 1, 1]])
    array([1])
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        fit_prior: bool = True,
        class_prior: Optional[np.ndarray] = None,
        norm: bool = False,
    ):
        self.alpha = alpha
        self.fit_prior = fit_prior
        self.class_prior = class_prior
        self.norm = norm

    def train(self, X: np.ndarray, y: np.ndarray) -> "ComplementNB":
        """
        Fit Complement Naive Bayes classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data (counts).
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : ComplementNB
            Fitted classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        if np.any(X < 0):
            raise ValueError("Negative values in data for ComplementNB")

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        self.class_count_ = np.zeros(n_classes)
        self.feature_count_ = np.zeros((n_classes, n_features))

        for i, cls in enumerate(self.classes_):
            X_cls = X[y == cls]
            self.class_count_[i] = len(X_cls)
            self.feature_count_[i] = np.sum(X_cls, axis=0)

        # Total feature counts
        self.feature_all_ = np.sum(self.feature_count_, axis=0)

        # Compute complement counts and probabilities
        complement_count = self.feature_all_ - self.feature_count_
        smoothed_cc = complement_count + self.alpha
        smoothed_cc_sum = smoothed_cc.sum(axis=1, keepdims=True)

        self.feature_log_prob_ = np.log(smoothed_cc) - np.log(smoothed_cc_sum)

        # Normalize weights if requested
        if self.norm:
            self.feature_log_prob_ = self.feature_log_prob_ / np.abs(self.feature_log_prob_).sum(axis=1, keepdims=True)

        # Negate for CNB
        self.feature_log_prob_ = -self.feature_log_prob_

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
        Perform classification.

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
        """Return probability estimates."""
        log_proba = self._joint_log_likelihood(X)
        log_proba_norm = log_proba - np.max(log_proba, axis=1, keepdims=True)
        proba = np.exp(log_proba_norm)
        proba /= proba.sum(axis=1, keepdims=True)
        return proba

    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """Return log-probability estimates."""
        return np.log(self.predict_proba(X))

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        """Compute unnormalized posterior log probability."""
        check_is_trained(self, "classes_")
        X = check_array(X)

        return np.dot(X, self.feature_log_prob_.T) + self.class_log_prior_
