"""
Self-training classifier.
"""

from __future__ import annotations

from typing import Optional, Callable

import numpy as np

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class SelfTrainingClassifier(ClassifierMixin, BaseLearner):
    """
    Self-training classifier.

    This classifier iteratively adds the most confident predictions
    to the training set.

    Parameters
    ----------
    base_estimator : estimator
        Base classifier with infer_proba method.
    threshold : float, default=0.75
        Confidence threshold for pseudo-labeling.
    criterion : {"threshold", "k_best"}, default="threshold"
        Selection criterion.
    k_best : int, default=10
        Number of samples to add per iteration (if criterion="k_best").
    max_iter : int, default=10
        Maximum iterations.

    Attributes
    ----------
    classes_ : ndarray
        Class labels.
    base_estimator_ : estimator
        Fitted base estimator.
    labeled_iter_ : ndarray
        Iteration in which each sample was labeled.
    transduction_ : ndarray
        Labels for all samples.

    Examples
    --------
    >>> from nalyst.semi_supervised import SelfTrainingClassifier
    >>> from nalyst.learners.linear import LogisticLearner
    >>> self_training = SelfTrainingClassifier(LogisticLearner())
    >>> self_training.train(X, y)  # y contains -1 for unlabeled
    """

    def __init__(
        self,
        base_estimator,
        threshold: float = 0.75,
        criterion: str = "threshold",
        k_best: int = 10,
        max_iter: int = 10,
    ):
        self.base_estimator = base_estimator
        self.threshold = threshold
        self.criterion = criterion
        self.k_best = k_best
        self.max_iter = max_iter

    def train(self, X: np.ndarray, y: np.ndarray) -> "SelfTrainingClassifier":
        """
        Fit the self-training classifier.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Labels with -1 for unlabeled samples.

        Returns
        -------
        self : SelfTrainingClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y).copy()

        n_samples = X.shape[0]

        # Get classes (excluding -1)
        labeled_mask = y != -1
        self.classes_ = np.unique(y[labeled_mask])

        self.labeled_iter_ = np.full(n_samples, -1)
        self.labeled_iter_[labeled_mask] = 0

        for iteration in range(1, self.max_iter + 1):
            # Train on labeled samples
            X_labeled = X[labeled_mask]
            y_labeled = y[labeled_mask]

            if len(np.unique(y_labeled)) < 2:
                break

            self.base_estimator_ = duplicate(self.base_estimator)
            self.base_estimator_.train(X_labeled, y_labeled)

            # Predict unlabeled samples
            unlabeled_mask = ~labeled_mask

            if not unlabeled_mask.any():
                break

            X_unlabeled = X[unlabeled_mask]
            proba = self.base_estimator_.infer_proba(X_unlabeled)

            # Select samples to add
            if self.criterion == "threshold":
                max_proba = proba.max(axis=1)
                selected = max_proba >= self.threshold
            else:  # k_best
                max_proba = proba.max(axis=1)
                k = min(self.k_best, len(max_proba))
                indices = np.argsort(max_proba)[-k:]
                selected = np.zeros(len(max_proba), dtype=bool)
                selected[indices] = True

            if not selected.any():
                break

            # Add pseudo-labels
            unlabeled_indices = np.where(unlabeled_mask)[0]
            selected_indices = unlabeled_indices[selected]

            pseudo_labels = self.classes_[proba[selected].argmax(axis=1)]

            y[selected_indices] = pseudo_labels
            labeled_mask[selected_indices] = True
            self.labeled_iter_[selected_indices] = iteration

        # Final training
        self.base_estimator_ = duplicate(self.base_estimator)
        self.base_estimator_.train(X[labeled_mask], y[labeled_mask])

        self.transduction_ = y

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict labels."""
        check_is_trained(self, "base_estimator_")
        return self.base_estimator_.infer(X)

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities."""
        check_is_trained(self, "base_estimator_")
        return self.base_estimator_.infer_proba(X)
