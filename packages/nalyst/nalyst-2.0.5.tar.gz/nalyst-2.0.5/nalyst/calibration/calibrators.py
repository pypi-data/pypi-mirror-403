"""
Probability calibration estimators.
"""

from __future__ import annotations

from typing import Optional, Literal

import numpy as np
from scipy.special import expit

from nalyst.core.foundation import BaseLearner, ClassifierMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class CalibratedClassifier(ClassifierMixin, BaseLearner):
    """
    Probability calibration with isotonic regression or sigmoid.

    Parameters
    ----------
    estimator : object, optional
        Base classifier. If None, a base classifier must be provided at train.
    method : {"sigmoid", "isotonic"}, default="sigmoid"
        The method to use for calibration.
    cv : int or "prefit", default=None
        Cross-validation strategy.
    n_jobs : int, optional
        Number of parallel jobs.

    Attributes
    ----------
    classes_ : ndarray of shape (n_classes,)
        Class labels.
    calibrated_classifiers_ : list
        List of calibrated classifiers.

    Examples
    --------
    >>> from nalyst.calibration import CalibratedClassifier
    >>> from nalyst.learners.linear import LogisticLearner
    >>> clf = CalibratedClassifier(LogisticLearner(), method='sigmoid')
    >>> clf.train(X, y)
    >>> proba = clf.infer_proba(X_test)
    """

    def __init__(
        self,
        estimator=None,
        *,
        method: Literal["sigmoid", "isotonic"] = "sigmoid",
        cv=None,
        n_jobs: Optional[int] = None,
    ):
        self.estimator = estimator
        self.method = method
        self.cv = cv
        self.n_jobs = n_jobs

    def train(self, X: np.ndarray, y: np.ndarray) -> "CalibratedClassifier":
        """
        Fit the calibrated model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,)
            Target values.

        Returns
        -------
        self : CalibratedClassifier
            Fitted estimator.
        """
        X = check_array(X)
        y = np.asarray(y)

        self.classes_ = np.unique(y)
        n_classes = len(self.classes_)

        if self.cv == "prefit":
            # Estimator is already fitted
            self.base_estimator_ = self.estimator

            # Get uncalibrated probabilities
            if hasattr(self.base_estimator_, "infer_proba"):
                proba = self.base_estimator_.infer_proba(X)
            else:
                # Use decision function
                decision = self.base_estimator_.decision_function(X)
                proba = expit(decision)
                if proba.ndim == 1:
                    proba = np.column_stack([1 - proba, proba])

            # Fit calibration
            self._calibrators = []
            for k in range(n_classes):
                y_k = (y == self.classes_[k]).astype(int)
                calibrator = self._fit_calibrator(proba[:, k], y_k)
                self._calibrators.append(calibrator)
        else:
            # Fit with cross-validation
            from nalyst.evaluation import KFold

            cv = self.cv or 5
            kf = KFold(n_splits=cv, shuffle=True)

            # Collect OOF predictions
            proba_oof = np.zeros((len(X), n_classes))

            for train_idx, val_idx in kf.split(X):
                estimator = duplicate(self.estimator)
                estimator.train(X[train_idx], y[train_idx])

                if hasattr(estimator, "infer_proba"):
                    proba_val = estimator.infer_proba(X[val_idx])
                else:
                    decision = estimator.decision_function(X[val_idx])
                    proba_val = expit(decision)
                    if proba_val.ndim == 1:
                        proba_val = np.column_stack([1 - proba_val, proba_val])

                proba_oof[val_idx] = proba_val

            # Fit calibrators
            self._calibrators = []
            for k in range(n_classes):
                y_k = (y == self.classes_[k]).astype(int)
                calibrator = self._fit_calibrator(proba_oof[:, k], y_k)
                self._calibrators.append(calibrator)

            # Fit final base estimator on all data
            self.base_estimator_ = duplicate(self.estimator)
            self.base_estimator_.train(X, y)

        return self

    def _fit_calibrator(self, proba: np.ndarray, y: np.ndarray):
        """Fit a single calibrator."""
        if self.method == "sigmoid":
            return _SigmoidCalibrator().fit(proba, y)
        elif self.method == "isotonic":
            return _IsotonicCalibrator().fit(proba, y)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict calibrated probabilities.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        proba : ndarray of shape (n_samples, n_classes)
            Calibrated probabilities.
        """
        check_is_trained(self, "_calibrators")
        X = check_array(X)

        # Get uncalibrated probabilities
        if hasattr(self.base_estimator_, "infer_proba"):
            proba = self.base_estimator_.infer_proba(X)
        else:
            decision = self.base_estimator_.decision_function(X)
            proba = expit(decision)
            if proba.ndim == 1:
                proba = np.column_stack([1 - proba, proba])

        # Apply calibration
        calibrated = np.zeros_like(proba)
        for k, calibrator in enumerate(self._calibrators):
            calibrated[:, k] = calibrator.predict(proba[:, k])

        # Normalize
        calibrated /= calibrated.sum(axis=1, keepdims=True)

        return calibrated

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


class _SigmoidCalibrator:
    """Platt's sigmoid calibration."""

    def fit(self, proba: np.ndarray, y: np.ndarray) -> "_SigmoidCalibrator":
        """Fit sigmoid parameters."""
        # Use logistic regression
        from scipy.optimize import minimize

        def loss(params):
            a, b = params
            p = expit(a * proba + b)
            eps = 1e-15
            p = np.clip(p, eps, 1 - eps)
            return -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))

        result = minimize(loss, [1.0, 0.0], method='L-BFGS-B')
        self.a_, self.b_ = result.x

        return self

    def predict(self, proba: np.ndarray) -> np.ndarray:
        """Apply calibration."""
        return expit(self.a_ * proba + self.b_)


class _IsotonicCalibrator:
    """Isotonic regression calibration."""

    def fit(self, proba: np.ndarray, y: np.ndarray) -> "_IsotonicCalibrator":
        """Fit isotonic regression."""
        # Sort by probability
        order = np.argsort(proba)
        self.proba_ = proba[order]
        y_sorted = y[order]

        # Pool Adjacent Violators Algorithm
        n = len(y_sorted)
        self.calibrated_ = y_sorted.astype(float).copy()

        while True:
            changed = False
            i = 0
            while i < n - 1:
                if self.calibrated_[i] > self.calibrated_[i + 1]:
                    # Find block to merge
                    j = i + 1
                    while j < n and self.calibrated_[i] > self.calibrated_[j]:
                        j += 1

                    # Replace with mean
                    self.calibrated_[i:j] = np.mean(self.calibrated_[i:j])
                    changed = True
                    i = j
                else:
                    i += 1

            if not changed:
                break

        return self

    def predict(self, proba: np.ndarray) -> np.ndarray:
        """Apply calibration using interpolation."""
        return np.interp(proba, self.proba_, self.calibrated_)


class CalibrationDisplay:
    """
    Calibration curve visualization.

    Parameters
    ----------
    prob_true : ndarray
        True probabilities.
    prob_pred : ndarray
        Predicted probabilities.
    y_prob : ndarray
        Original probability predictions.
    estimator_name : str, optional
        Name of the estimator.

    Examples
    --------
    >>> from nalyst.calibration import CalibrationDisplay, calibration_curve
    >>> prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)
    >>> disp = CalibrationDisplay(prob_true, prob_pred, y_prob)
    >>> disp.plot()
    """

    def __init__(
        self,
        prob_true: np.ndarray,
        prob_pred: np.ndarray,
        y_prob: np.ndarray,
        *,
        estimator_name: Optional[str] = None,
    ):
        self.prob_true = prob_true
        self.prob_pred = prob_pred
        self.y_prob = y_prob
        self.estimator_name = estimator_name

    def plot(self, ax=None, **kwargs):
        """
        Plot calibration curve.

        Parameters
        ----------
        ax : matplotlib axes, optional
            Axes to plot on.
        **kwargs
            Keyword arguments for matplotlib.

        Returns
        -------
        display : CalibrationDisplay
            Object that stores computed values.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for plotting")

        if ax is None:
            fig, ax = plt.subplots()

        name = self.estimator_name or "Classifier"

        ax.plot([0, 1], [0, 1], 'k--', label='Perfectly calibrated')
        ax.plot(self.prob_pred, self.prob_true, 's-', label=name, **kwargs)

        ax.set_xlabel('Mean predicted probability')
        ax.set_ylabel('Fraction of positives')
        ax.set_title('Calibration curve')
        ax.legend(loc='best')

        self.ax_ = ax
        self.figure_ = ax.figure

        return self
