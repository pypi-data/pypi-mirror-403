"""
Regression experiment for AutoML.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
import numpy as np

from nalyst.automl.experiment import BaseExperiment


class RegressionExperiment(BaseExperiment):
    """
    AutoML experiment for regression tasks.

    Provides automated model comparison, tuning, and blending for
    regression problems.

    Parameters
    ----------
    session_id : int, optional
        Random seed for reproducibility.
    verbose : bool, default=True
        Whether to print progress messages.

    Examples
    --------
    >>> from nalyst.automl import RegressionExperiment
    >>> exp = RegressionExperiment()
    >>> exp.setup(X, y)
    >>> best_models = exp.compare_models()
    >>> tuned = exp.tune_model(best_models[0])
    >>> predictions = exp.predict(tuned, X_new)
    """

    def _get_models(self) -> Dict[str, Any]:
        """Get dictionary of regression models."""
        from nalyst.learners.linear import (
            RidgeLearner,
            LassoLearner,
            ElasticNetLearner,
        )
        from nalyst.learners.trees import TreeRegressor
        from nalyst.learners.ensemble import (
            ForestRegressor,
            GradientBoostRegressor,
        )
        from nalyst.learners.neighbors import KNearestRegressor
        from nalyst.learners.svm import SupportVectorRegressor

        return {
            'Ridge': RidgeLearner,
            'Lasso': LassoLearner,
            'ElasticNet': ElasticNetLearner,
            'Decision Tree': TreeRegressor,
            'Random Forest': ForestRegressor,
            'Gradient Boosting': GradientBoostRegressor,
            'K-Nearest Neighbors': KNearestRegressor,
            'SVR': SupportVectorRegressor,
        }

    def _evaluate_model(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Dict[str, float]:
        """Evaluate regression model."""
        y_pred = model.infer(X)

        # MSE
        mse = np.mean((y - y_pred) ** 2)

        # RMSE
        rmse = np.sqrt(mse)

        # MAE
        mae = np.mean(np.abs(y - y_pred))

        # R-squared
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # MAPE
        mask = y != 0
        if np.any(mask):
            mape = np.mean(np.abs((y[mask] - y_pred[mask]) / y[mask])) * 100
        else:
            mape = np.inf

        return {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'R2': r2,
            'MAPE': mape,
        }

    def _get_param_grid(self, model: Any) -> Dict[str, List]:
        """Get parameter grid for regression models."""
        model_name = model.__class__.__name__

        grids = {
            'RidgeLearner': {
                'alpha': [0.001, 0.01, 0.1, 1, 10, 100],
            },
            'LassoLearner': {
                'alpha': [0.001, 0.01, 0.1, 1, 10],
                'max_iter': [1000, 5000],
            },
            'ElasticNetLearner': {
                'alpha': [0.01, 0.1, 1],
                'l1_ratio': [0.1, 0.5, 0.9],
            },
            'TreeRegressor': {
                'max_depth': [3, 5, 10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
            },
            'ForestRegressor': {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 20, None],
                'min_samples_split': [2, 5, 10],
            },
            'GradientBoostRegressor': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
            },
            'KNearestRegressor': {
                'n_neighbors': [3, 5, 7, 11, 15],
                'weights': ['uniform', 'distance'],
            },
            'SupportVectorRegressor': {
                'C': [0.1, 1, 10],
                'kernel': ['linear', 'rbf', 'poly'],
                'epsilon': [0.01, 0.1, 0.5],
            },
        }

        return grids.get(model_name, {})

    def create_model(
        self,
        model_name: str,
        **kwargs,
    ) -> Any:
        """
        Create a specific regression model.

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

    def plot_residuals(self, model: Any) -> Dict[str, np.ndarray]:
        """
        Get residual plot data.

        Parameters
        ----------
        model : estimator
            Trained model.

        Returns
        -------
        data : dict
            Residual analysis data.
        """
        y_pred = model.infer(self.X_test_)
        residuals = self.y_test_ - y_pred

        return {
            'predictions': y_pred,
            'actual': self.y_test_,
            'residuals': residuals,
            'standardized_residuals': (residuals - np.mean(residuals)) / np.std(residuals),
        }

    def stack_models(
        self,
        models: List[Any],
        meta_learner: Optional[Any] = None,
        use_probas: bool = False,
    ) -> Any:
        """
        Create a stacked ensemble.

        Parameters
        ----------
        models : list
            List of base models.
        meta_learner : estimator, optional
            Meta-learner model. Default is Ridge regression.
        use_probas : bool, default=False
            Whether to use probabilities as meta-features.

        Returns
        -------
        stacked : StackedModel
            Stacked ensemble model.
        """
        if meta_learner is None:
            from nalyst.learners.linear import RidgeLearner
            meta_learner = RidgeLearner()

        return StackedModel(models, meta_learner, use_probas)

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

        return result


class StackedModel:
    """
    Stacked ensemble model.
    """

    def __init__(
        self,
        base_models: List[Any],
        meta_learner: Any,
        use_probas: bool = False,
    ):
        self.base_models = base_models
        self.meta_learner = meta_learner
        self.use_probas = use_probas

    def train(self, X: np.ndarray, y: np.ndarray) -> "StackedModel":
        """Train the stacked model."""
        # Train base models
        for model in self.base_models:
            model.train(X, y)

        # Generate meta-features
        meta_features = self._get_meta_features(X)

        # Train meta-learner
        self.meta_learner.train(meta_features, y)

        return self

    def _get_meta_features(self, X: np.ndarray) -> np.ndarray:
        """Generate meta-features from base model predictions."""
        predictions = []

        for model in self.base_models:
            if self.use_probas and hasattr(model, 'predict_proba'):
                pred = model.predict_proba(X)
            else:
                pred = model.infer(X).reshape(-1, 1)
            predictions.append(pred)

        return np.hstack(predictions)

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        meta_features = self._get_meta_features(X)
        return self.meta_learner.infer(meta_features)
