"""
Gaussian Naive Bayes classifier.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained


class GaussianNB(ClassifierMixin, BaseLearner):
    """
    Gaussian Naive Bayes classifier.

    Assumes features follow a Gaussian (normal) distribution.

    Parameters
    ----------
    priors : array-like of shape (n_classes,), optional
        Prior probabilities of the classes.
    var_smoothing : float, default=1e-9
        Portion of the largest variance added to variances for stability.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels known to the classifier.
    class_prior_ : ndarray of shape (n_classes,)
        Probability of each class.
    class_count_ : ndarray of shape (n_classes,)
        Number of training samples in each class.
    theta_ : ndarray of shape (n_classes, n_features)
        Mean of each feature per class.
    var_ : ndarray of shape (n_classes, n_features)
        Variance of each feature per class.
    epsilon_ : float
        Absolute additive value to variances.

    Examples
    --------
    >>> from nalyst.learners.naive_bayes import GaussianNB
    >>> X = [[1, 2], [2, 3], [3, 4], [4, 5]]
    >>> y = [0, 0, 1, 1]
    >>> clf = GaussianNB()
    >>> clf.train(X, y)
    GaussianNB()
    >>> clf.infer([[2.5, 3.5]])
    array([0])
    """

    def __init__(
        self,
        *,
        priors: Optional[np.ndarray] = None,
        var_smoothing: float = 1e-9,
    ):
        self.priors = priors
        self.var_smoothing = var_smoothing

    def train(self, X: np.ndarray, y: np.ndarray) -> "GaussianNB":
        """
        Fit Gaussian Naive Bayes classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : GaussianNB
            Fitted classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        # Initialize statistics
        self.theta_ = np.zeros((n_classes, n_features))
        self.var_ = np.zeros((n_classes, n_features))
        self.class_count_ = np.zeros(n_classes)

        for i, cls in enumerate(self.classes_):
            X_cls = X[y == cls]
            self.class_count_[i] = len(X_cls)
            self.theta_[i] = np.mean(X_cls, axis=0)
            self.var_[i] = np.var(X_cls, axis=0)

        # Compute variance smoothing
        self.epsilon_ = self.var_smoothing * np.max(self.var_)
        self.var_ += self.epsilon_

        # Compute class priors
        if self.priors is not None:
            self.class_prior_ = np.asarray(self.priors)
        else:
            self.class_prior_ = self.class_count_ / self.class_count_.sum()

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
        Return probability estimates for test data.

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

        # Normalize using log-sum-exp trick
        log_proba_norm = log_proba - np.max(log_proba, axis=1, keepdims=True)
        proba = np.exp(log_proba_norm)
        proba /= proba.sum(axis=1, keepdims=True)

        return proba

    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Return log-probability estimates.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        log_proba : ndarray of shape (n_samples, n_classes)
            Log-probability of each class.
        """
        return np.log(self.predict_proba(X))

    def _joint_log_likelihood(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the unnormalized posterior log probability.

        P(class) * P(features | class)

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        log_likelihood : ndarray of shape (n_samples, n_classes)
            Log-likelihood for each class.
        """
        check_is_trained(self, "classes_")
        X = check_array(X)

        joint_log_likelihood = []

        for i in range(len(self.classes_)):
            # Log prior
            log_prior = np.log(self.class_prior_[i])

            # Log-likelihood: Gaussian PDF
            # log P(x|class) = -0.5 * sum(log(2*pi*var) + (x - mean)^2 / var)
            n_features = X.shape[1]
            log_likelihood = -0.5 * np.sum(
                np.log(2 * np.pi * self.var_[i]) +
                (X - self.theta_[i]) ** 2 / self.var_[i],
                axis=1
            )

            joint_log_likelihood.append(log_prior + log_likelihood)

        return np.array(joint_log_likelihood).T

    def partial_train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        classes: Optional[np.ndarray] = None,
    ) -> "GaussianNB":
        """
        Incremental fit on a batch of samples.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.
        classes : ndarray of shape (n_classes,), optional
            List of all classes that can appear in y.

        Returns
        -------
        self : GaussianNB
            Updated classifier.
        """
        X = check_array(X)
        y = np.asarray(y)

        # First call - initialize
        if not hasattr(self, "classes_"):
            if classes is None:
                classes = np.unique(y)
            self.classes_ = classes
            n_classes = len(classes)
            n_features = X.shape[1]

            self.theta_ = np.zeros((n_classes, n_features))
            self.var_ = np.zeros((n_classes, n_features))
            self.class_count_ = np.zeros(n_classes)

        n_features = X.shape[1]

        for i, cls in enumerate(self.classes_):
            X_cls = X[y == cls]
            n_new = len(X_cls)

            if n_new == 0:
                continue

            # Welford's online algorithm for variance
            n_old = self.class_count_[i]
            n_total = n_old + n_new

            new_mean = np.mean(X_cls, axis=0)
            new_var = np.var(X_cls, axis=0)

            if n_old == 0:
                self.theta_[i] = new_mean
                self.var_[i] = new_var
            else:
                # Combined mean
                combined_mean = (n_old * self.theta_[i] + n_new * new_mean) / n_total

                # Combined variance
                combined_var = (
                    n_old * (self.var_[i] + (self.theta_[i] - combined_mean) ** 2) +
                    n_new * (new_var + (new_mean - combined_mean) ** 2)
                ) / n_total

                self.theta_[i] = combined_mean
                self.var_[i] = combined_var

            self.class_count_[i] = n_total

        # Update epsilon and priors
        self.epsilon_ = self.var_smoothing * np.max(self.var_) if np.max(self.var_) > 0 else 1e-9
        self.var_ = np.maximum(self.var_, self.epsilon_)

        if self.priors is not None:
            self.class_prior_ = np.asarray(self.priors)
        else:
            self.class_prior_ = self.class_count_ / self.class_count_.sum()

        return self
