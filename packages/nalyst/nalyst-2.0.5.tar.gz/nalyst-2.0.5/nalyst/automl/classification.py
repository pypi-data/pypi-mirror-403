"""
Classification experiment for AutoML.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
import numpy as np

from nalyst.automl.experiment import BaseExperiment


class ClassificationExperiment(BaseExperiment):
    """
    AutoML experiment for classification tasks.

    Provides automated model comparison, tuning, and blending for
    classification problems.

    Parameters
    ----------
    session_id : int, optional
        Random seed for reproducibility.
    verbose : bool, default=True
        Whether to print progress messages.

    Examples
    --------
    >>> from nalyst.automl import ClassificationExperiment
    >>> exp = ClassificationExperiment()
    >>> exp.setup(X, y)
    >>> best_models = exp.compare_models()
    >>> tuned = exp.tune_model(best_models[0])
    >>> predictions = exp.predict(tuned, X_new)
    """

    def _get_models(self) -> Dict[str, Any]:
        """Get dictionary of classification models."""
        from nalyst.learners.linear import LogisticLearner
        from nalyst.learners.trees import TreeClassifier
        from nalyst.learners.ensemble import (
            ForestClassifier,
            GradientBoostClassifier,
            AdaBoostClassifier,
        )
        from nalyst.learners.neighbors import KNearestClassifier
        from nalyst.learners.naive_bayes import GaussianNaiveBayes
        from nalyst.learners.svm import SupportVectorClassifier

        return {
            'Logistic Regression': LogisticLearner,
            'Decision Tree': TreeClassifier,
            'Random Forest': ForestClassifier,
            'Gradient Boosting': GradientBoostClassifier,
            'AdaBoost': AdaBoostClassifier,
            'K-Nearest Neighbors': KNearestClassifier,
            'Naive Bayes': GaussianNaiveBayes,
            'SVM': SupportVectorClassifier,
        }

    def _evaluate_model(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Dict[str, float]:
        """Evaluate classification model."""
        y_pred = model.infer(X)

        # Accuracy
        accuracy = np.mean(y_pred == y)

        # For binary classification, compute more metrics
        unique_classes = np.unique(y)

        if len(unique_classes) == 2:
            # Precision, Recall, F1 for positive class
            pos_class = unique_classes[1]

            tp = np.sum((y_pred == pos_class) & (y == pos_class))
            fp = np.sum((y_pred == pos_class) & (y != pos_class))
            fn = np.sum((y_pred != pos_class) & (y == pos_class))

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

            # AUC if model has predict_proba
            if hasattr(model, 'predict_proba'):
                try:
                    proba = model.predict_proba(X)[:, 1]
                    auc = self._compute_auc(y == pos_class, proba)
                except Exception:
                    auc = 0.5
            else:
                auc = 0.5

            return {
                'Accuracy': accuracy,
                'Precision': precision,
                'Recall': recall,
                'F1': f1,
                'AUC': auc,
            }
        else:
            # Multiclass: macro-averaged metrics
            return {
                'Accuracy': accuracy,
                'Precision': self._macro_precision(y, y_pred, unique_classes),
                'Recall': self._macro_recall(y, y_pred, unique_classes),
                'F1': self._macro_f1(y, y_pred, unique_classes),
            }

    def _compute_auc(self, y_true: np.ndarray, y_score: np.ndarray) -> float:
        """Compute AUC-ROC."""
        # Sort by score
        sorted_idx = np.argsort(y_score)[::-1]
        y_true = y_true[sorted_idx]

        n_pos = np.sum(y_true)
        n_neg = len(y_true) - n_pos

        if n_pos == 0 or n_neg == 0:
            return 0.5

        # Compute AUC using trapezoidal rule
        tpr = np.cumsum(y_true) / n_pos
        fpr = np.cumsum(~y_true) / n_neg

        # Add origin
        tpr = np.concatenate([[0], tpr])
        fpr = np.concatenate([[0], fpr])

        auc = np.trapz(tpr, fpr)
        return auc

    def _macro_precision(self, y_true, y_pred, classes) -> float:
        """Macro-averaged precision."""
        precisions = []
        for c in classes:
            tp = np.sum((y_pred == c) & (y_true == c))
            fp = np.sum((y_pred == c) & (y_true != c))
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            precisions.append(p)
        return np.mean(precisions)

    def _macro_recall(self, y_true, y_pred, classes) -> float:
        """Macro-averaged recall."""
        recalls = []
        for c in classes:
            tp = np.sum((y_pred == c) & (y_true == c))
            fn = np.sum((y_pred != c) & (y_true == c))
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            recalls.append(r)
        return np.mean(recalls)

    def _macro_f1(self, y_true, y_pred, classes) -> float:
        """Macro-averaged F1."""
        p = self._macro_precision(y_true, y_pred, classes)
        r = self._macro_recall(y_true, y_pred, classes)
        return 2 * p * r / (p + r) if (p + r) > 0 else 0

    def _get_param_grid(self, model: Any) -> Dict[str, List]:
        """Get parameter grid for classification models."""
        model_name = model.__class__.__name__

        grids = {
            'LogisticLearner': {
                'C': [0.01, 0.1, 1, 10, 100],
                'max_iter': [100, 500, 1000],
            },
            'TreeClassifier': {
                'max_depth': [3, 5, 10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
            },
            'ForestClassifier': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 20, None],
                'min_samples_split': [2, 5, 10],
            },
            'GradientBoostClassifier': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
            },
            'KNearestClassifier': {
                'n_neighbors': [3, 5, 7, 11, 15],
                'weights': ['uniform', 'distance'],
            },
            'SupportVectorClassifier': {
                'C': [0.1, 1, 10],
                'kernel': ['linear', 'rbf', 'poly'],
            },
        }

        return grids.get(model_name, {})

    def create_model(
        self,
        model_name: str,
        **kwargs,
    ) -> Any:
        """
        Create a specific classification model.

        Parameters
        ----------
        model_name : str
            Name of the model to create.
        **kwargs
            Model parameters.

        Returns
        -------
        model : estimator
            Untrained model instance.
        """
        models = self._get_models()

        if model_name not in models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(models.keys())}")

        return models[model_name](**kwargs)

    def calibrate_model(
        self,
        model: Any,
        method: str = 'sigmoid',
    ) -> Any:
        """
        Calibrate model probabilities.

        Parameters
        ----------
        model : estimator
            Trained model to calibrate.
        method : str, default='sigmoid'
            Calibration method: 'sigmoid' (Platt) or 'isotonic'.

        Returns
        -------
        calibrated : CalibratedModel
            Calibrated model.
        """
        from nalyst.calibration import CalibratedClassifier

        calibrated = CalibratedClassifier(model, method=method)
        calibrated.train(self.X_train_, self.y_train_)

        return calibrated

    def interpret_model(self, model: Any) -> Dict[str, Any]:
        """
        Get model interpretation.

        Parameters
        ----------
        model : estimator
            Trained model.

        Returns
        -------
        interpretation : dict
            Feature importances and other interpretation data.
        """
        result = {}

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            result['feature_importances'] = model.feature_importances_
        elif hasattr(model, 'coef_'):
            result['coefficients'] = model.coef_

        # Permutation importance
        try:
            from nalyst.inspection import permutation_importance
            perm_imp = permutation_importance(
                model, self.X_test_, self.y_test_,
                n_repeats=10, random_state=self.session_id
            )
            result['permutation_importance'] = perm_imp
        except Exception:
            pass

        return result
