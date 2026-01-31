"""
Categorical Naive Bayes classifier.
"""

from __future__ import annotations

from typing import Optional, List

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained


class CategoricalNB(ClassifierMixin, BaseLearner):
    """
    Categorical Naive Bayes classifier.

    For categorical features (must be encoded as non-negative integers).

    Parameters
    ----------
    alpha : float, default=1.0
        Additive (Laplace) smoothing parameter.
    fit_prior : bool, default=True
        Whether to learn class prior probabilities.
    class_prior : array-like of shape (n_classes,), optional
        Prior probabilities of the classes.
    min_categories : int or array-like of shape (n_features,), optional
        Minimum number of categories per feature.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    class_count_ : ndarray of shape (n_classes,)
        Number of samples in each class.
    class_log_prior_ : ndarray of shape (n_classes,)
        Log probability of each class.
    category_count_ : list of ndarrays
        Holds arrays of shape (n_classes, n_categories_i) for each feature i.
    n_categories_ : ndarray of shape (n_features,)
        Number of categories for each feature.

    Examples
    --------
    >>> from nalyst.learners.naive_bayes import CategoricalNB
    >>> X = [[0, 0, 1], [0, 1, 0], [1, 0, 1], [1, 1, 0]]
    >>> y = [0, 0, 1, 1]
    >>> clf = CategoricalNB()
    >>> clf.train(X, y)
    CategoricalNB()
    >>> clf.infer([[0, 1, 1]])
    array([0])
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        fit_prior: bool = True,
        class_prior: Optional[np.ndarray] = None,
        min_categories: Optional[int] = None,
    ):
        self.alpha = alpha
        self.fit_prior = fit_prior
        self.class_prior = class_prior
        self.min_categories = min_categories

    def train(self, X: np.ndarray, y: np.ndarray) -> "CategoricalNB":
        """
        Fit Categorical Naive Bayes classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data (categorical, encoded as integers).
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : CategoricalNB
            Fitted classifier.
        """
        X = check_array(X)
        X = X.astype(int)
        y = np.asarray(y)

        if np.any(X < 0):
            raise ValueError("CategoricalNB requires non-negative integer features")

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        # Determine number of categories per feature
        if self.min_categories is not None:
            if np.isscalar(self.min_categories):
                min_cats = np.full(n_features, self.min_categories)
            else:
                min_cats = np.asarray(self.min_categories)
            self.n_categories_ = np.maximum(np.max(X, axis=0) + 1, min_cats)
        else:
            self.n_categories_ = np.max(X, axis=0) + 1

        # Initialize counts
        self.class_count_ = np.zeros(n_classes)
        self.category_count_: List[np.ndarray] = []

        for j in range(n_features):
            self.category_count_.append(np.zeros((n_classes, self.n_categories_[j])))

        # Count occurrences
        for i, cls in enumerate(self.classes_):
            mask = y == cls
            self.class_count_[i] = np.sum(mask)
            X_cls = X[mask]

            for j in range(n_features):
                for cat in range(self.n_categories_[j]):
                    self.category_count_[j][i, cat] = np.sum(X_cls[:, j] == cat)

        # Compute log probabilities with smoothing
        self.feature_log_prob_: List[np.ndarray] = []
        for j in range(n_features):
            smoothed = self.category_count_[j] + self.alpha
            smoothed_sum = smoothed.sum(axis=1, keepdims=True)
            self.feature_log_prob_.append(np.log(smoothed) - np.log(smoothed_sum))

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
        X = X.astype(int)

        n_samples = len(X)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        jll = np.zeros((n_samples, n_classes))

        for j in range(n_features):
            for i in range(n_samples):
                cat = X[i, j]
                if cat < self.n_categories_[j]:
                    jll[i] += self.feature_log_prob_[j][:, cat]
                else:
                    # Unknown category - use uniform probability
                    jll[i] += -np.log(self.n_categories_[j])

        return jll + self.class_log_prior_

    def partial_train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[np.ndarray] = None,
    ) -> "CategoricalNB":
        """Incremental fit on a batch of samples."""
        X = check_array(X)
        X = X.astype(int)
        y = np.asarray(y)

        n_features = X.shape[1]

        if not hasattr(self, "classes_"):
            if classes is None:
                classes = np.unique(y)
            self.classes_ = classes
            n_classes = len(classes)

            if self.min_categories is not None:
                if np.isscalar(self.min_categories):
                    min_cats = np.full(n_features, self.min_categories)
                else:
                    min_cats = np.asarray(self.min_categories)
                self.n_categories_ = np.maximum(np.max(X, axis=0) + 1, min_cats)
            else:
                self.n_categories_ = np.max(X, axis=0) + 1

            self.class_count_ = np.zeros(n_classes)
            self.category_count_ = []
            for j in range(n_features):
                self.category_count_.append(np.zeros((n_classes, self.n_categories_[j])))

        # Expand category arrays if needed
        new_max_cats = np.max(X, axis=0) + 1
        for j in range(n_features):
            if new_max_cats[j] > self.n_categories_[j]:
                old_count = self.category_count_[j]
                new_count = np.zeros((len(self.classes_), new_max_cats[j]))
                new_count[:, :self.n_categories_[j]] = old_count
                self.category_count_[j] = new_count
                self.n_categories_[j] = new_max_cats[j]

        # Update counts
        for i, cls in enumerate(self.classes_):
            mask = y == cls
            self.class_count_[i] += np.sum(mask)
            X_cls = X[mask]

            for j in range(n_features):
                for cat in range(self.n_categories_[j]):
                    self.category_count_[j][i, cat] += np.sum(X_cls[:, j] == cat)

        # Recompute probabilities
        self.feature_log_prob_ = []
        for j in range(n_features):
            smoothed = self.category_count_[j] + self.alpha
            smoothed_sum = smoothed.sum(axis=1, keepdims=True)
            self.feature_log_prob_.append(np.log(smoothed) - np.log(smoothed_sum))

        if self.fit_prior:
            if self.class_prior is not None:
                self.class_log_prior_ = np.log(np.asarray(self.class_prior))
            else:
                self.class_log_prior_ = np.log(self.class_count_) - np.log(self.class_count_.sum())
        else:
            self.class_log_prior_ = np.zeros(len(self.classes_)) - np.log(len(self.classes_))

        return self
