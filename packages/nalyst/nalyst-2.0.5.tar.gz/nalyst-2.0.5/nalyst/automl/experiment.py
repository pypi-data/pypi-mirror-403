"""
Base experiment class for AutoML.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union, Callable
import numpy as np
from datetime import datetime


class BaseExperiment(ABC):
    """
    Base class for AutoML experiments.

    Provides the foundation for automated machine learning workflows
    including data preprocessing, model comparison, tuning, and blending.

    Parameters
    ----------
    session_id : int, optional
        Random seed for reproducibility.
    verbose : bool, default=True
        Whether to print progress messages.

    Attributes
    ----------
    data_ : ndarray
        Training data.
    target_ : ndarray
        Target variable.
    models_ : dict
        Dictionary of available models.
    results_ : DataFrame-like
        Results of model comparisons.
    """

    def __init__(
        self,
        session_id: Optional[int] = None,
        verbose: bool = True,
    ):
        self.session_id = session_id if session_id is not None else np.random.randint(0, 10000)
        self.verbose = verbose

        self._is_setup = False
        self._trained_models = {}
        self._results = []

    def setup(
        self,
        data: np.ndarray,
        target: np.ndarray,
        train_size: float = 0.8,
        preprocess: bool = True,
        normalize: bool = False,
        normalize_method: str = 'zscore',
        handle_missing: str = 'mean',
        remove_outliers: bool = False,
        outlier_threshold: float = 0.05,
    ) -> "BaseExperiment":
        """
        Initialize the experiment with data and preprocessing options.

        Parameters
        ----------
        data : ndarray of shape (n_samples, n_features)
            Feature matrix.
        target : ndarray of shape (n_samples,)
            Target variable.
        train_size : float, default=0.8
            Proportion of data for training.
        preprocess : bool, default=True
            Whether to apply preprocessing.
        normalize : bool, default=False
            Whether to normalize features.
        normalize_method : str, default='zscore'
            Normalization method: 'zscore', 'minmax', 'robust'.
        handle_missing : str, default='mean'
            Missing value strategy: 'mean', 'median', 'drop'.
        remove_outliers : bool, default=False
            Whether to remove outliers.
        outlier_threshold : float, default=0.05
            Outlier detection threshold.

        Returns
        -------
        self : BaseExperiment
        """
        np.random.seed(self.session_id)

        data = np.asarray(data)
        target = np.asarray(target).flatten()

        n_samples = len(target)

        # Handle missing values
        if preprocess and handle_missing != 'drop':
            data = self._handle_missing(data, method=handle_missing)

        # Remove outliers
        if preprocess and remove_outliers:
            mask = self._detect_outliers(data, target, threshold=outlier_threshold)
            data = data[~mask]
            target = target[~mask]

        # Normalize
        if preprocess and normalize:
            data = self._normalize(data, method=normalize_method)

        # Train-test split
        n_train = int(len(target) * train_size)
        indices = np.random.permutation(len(target))

        train_idx = indices[:n_train]
        test_idx = indices[n_train:]

        self.X_train_ = data[train_idx]
        self.X_test_ = data[test_idx]
        self.y_train_ = target[train_idx]
        self.y_test_ = target[test_idx]

        self.data_ = data
        self.target_ = target

        self._is_setup = True

        if self.verbose:
            print(f"Setup completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Training samples: {len(train_idx)}")
            print(f"  Test samples: {len(test_idx)}")
            print(f"  Features: {data.shape[1]}")

        return self

    def _handle_missing(self, data: np.ndarray, method: str = 'mean') -> np.ndarray:
        """Handle missing values in data."""
        result = data.copy()

        for col in range(data.shape[1]):
            mask = np.isnan(data[:, col])
            if np.any(mask):
                if method == 'mean':
                    fill_value = np.nanmean(data[:, col])
                elif method == 'median':
                    fill_value = np.nanmedian(data[:, col])
                else:
                    fill_value = 0

                result[mask, col] = fill_value

        return result

    def _detect_outliers(
        self,
        data: np.ndarray,
        target: np.ndarray,
        threshold: float,
    ) -> np.ndarray:
        """Detect outliers using IQR method."""
        n_outliers = int(len(target) * threshold)

        # Use Mahalanobis-like distance
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0) + 1e-10

        z_scores = np.abs((data - mean) / std)
        max_z = np.max(z_scores, axis=1)

        outlier_mask = max_z > np.percentile(max_z, (1 - threshold) * 100)

        return outlier_mask

    def _normalize(self, data: np.ndarray, method: str = 'zscore') -> np.ndarray:
        """Normalize data."""
        if method == 'zscore':
            mean = np.mean(data, axis=0)
            std = np.std(data, axis=0) + 1e-10
            self._norm_params = {'mean': mean, 'std': std}
            return (data - mean) / std

        elif method == 'minmax':
            min_val = np.min(data, axis=0)
            max_val = np.max(data, axis=0)
            range_val = max_val - min_val + 1e-10
            self._norm_params = {'min': min_val, 'range': range_val}
            return (data - min_val) / range_val

        elif method == 'robust':
            median = np.median(data, axis=0)
            q1 = np.percentile(data, 25, axis=0)
            q3 = np.percentile(data, 75, axis=0)
            iqr = q3 - q1 + 1e-10
            self._norm_params = {'median': median, 'iqr': iqr}
            return (data - median) / iqr

        return data

    @abstractmethod
    def _get_models(self) -> Dict[str, Any]:
        """Get dictionary of available models."""
        pass

    @abstractmethod
    def _evaluate_model(self, model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate a model and return metrics."""
        pass

    def compare_models(
        self,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        fold: int = 5,
        sort: str = None,
        n_select: int = 1,
    ) -> List[Any]:
        """
        Compare multiple models using cross-validation.

        Parameters
        ----------
        include : list of str, optional
            Models to include. If None, uses all.
        exclude : list of str, optional
            Models to exclude.
        fold : int, default=5
            Number of cross-validation folds.
        sort : str, optional
            Metric to sort by.
        n_select : int, default=1
            Number of top models to return.

        Returns
        -------
        models : list
            Top n_select trained models.
        """
        if not self._is_setup:
            raise ValueError("Call setup() before compare_models()")

        models = self._get_models()

        if include is not None:
            models = {k: v for k, v in models.items() if k in include}

        if exclude is not None:
            models = {k: v for k, v in models.items() if k not in exclude}

        results = []

        for name, model_class in models.items():
            if self.verbose:
                print(f"Training {name}...")

            try:
                # Cross-validation
                cv_scores = self._cross_validate(model_class, fold)

                # Train on full training set
                model = model_class()
                model.train(self.X_train_, self.y_train_)

                # Evaluate on test set
                test_metrics = self._evaluate_model(model, self.X_test_, self.y_test_)

                result = {
                    'Model': name,
                    **{f'CV_{k}': v for k, v in cv_scores.items()},
                    **{f'Test_{k}': v for k, v in test_metrics.items()},
                }

                results.append(result)
                self._trained_models[name] = model

            except Exception as e:
                if self.verbose:
                    print(f"  Error training {name}: {e}")

        self._results = results

        # Sort results
        if sort is None:
            sort = list(results[0].keys())[1] if results else None

        if sort:
            results = sorted(results, key=lambda x: x.get(sort, 0), reverse=True)

        if self.verbose:
            print("\nModel Comparison Results:")
            print("-" * 60)
            for r in results[:n_select * 2]:
                print(f"{r['Model']:20s}", end="")
                for k, v in list(r.items())[1:4]:
                    if isinstance(v, float):
                        print(f"{k}: {v:.4f}  ", end="")
                print()

        # Return top models
        top_names = [r['Model'] for r in results[:n_select]]
        return [self._trained_models[name] for name in top_names]

    def _cross_validate(
        self,
        model_class: Any,
        n_folds: int,
    ) -> Dict[str, float]:
        """Perform cross-validation."""
        n = len(self.X_train_)
        indices = np.arange(n)
        np.random.shuffle(indices)

        fold_size = n // n_folds
        all_metrics = []

        for i in range(n_folds):
            # Split
            val_start = i * fold_size
            val_end = (i + 1) * fold_size if i < n_folds - 1 else n

            val_idx = indices[val_start:val_end]
            train_idx = np.concatenate([indices[:val_start], indices[val_end:]])

            X_train_fold = self.X_train_[train_idx]
            y_train_fold = self.y_train_[train_idx]
            X_val_fold = self.X_train_[val_idx]
            y_val_fold = self.y_train_[val_idx]

            # Train and evaluate
            model = model_class()
            model.train(X_train_fold, y_train_fold)

            metrics = self._evaluate_model(model, X_val_fold, y_val_fold)
            all_metrics.append(metrics)

        # Average metrics
        avg_metrics = {}
        for key in all_metrics[0].keys():
            values = [m[key] for m in all_metrics]
            avg_metrics[key] = np.mean(values)

        return avg_metrics

    def tune_model(
        self,
        model: Any,
        optimize: str = None,
        search_algorithm: str = 'random',
        n_iter: int = 10,
        fold: int = 5,
    ) -> Any:
        """
        Tune hyperparameters of a model.

        Parameters
        ----------
        model : estimator
            Model to tune.
        optimize : str, optional
            Metric to optimize.
        search_algorithm : str, default='random'
            Search algorithm: 'random', 'grid', 'bayesian'.
        n_iter : int, default=10
            Number of iterations for random/bayesian search.
        fold : int, default=5
            Number of CV folds.

        Returns
        -------
        tuned_model : estimator
            Tuned model.
        """
        if not self._is_setup:
            raise ValueError("Call setup() first")

        from nalyst.automl.tuning import RandomSearch, GridSearch

        # Get parameter grid for model
        param_grid = self._get_param_grid(model)

        if not param_grid:
            if self.verbose:
                print("No hyperparameters to tune")
            return model

        if self.verbose:
            print(f"Tuning {model.__class__.__name__}...")

        # Perform search
        if search_algorithm == 'grid':
            searcher = GridSearch(param_grid)
        else:
            searcher = RandomSearch(param_grid, n_iter=n_iter)

        best_model = searcher.search(
            model.__class__,
            self.X_train_,
            self.y_train_,
            self._evaluate_model,
            n_folds=fold,
            optimize=optimize,
        )

        if self.verbose:
            print(f"Best parameters: {searcher.best_params_}")

        return best_model

    def _get_param_grid(self, model: Any) -> Dict[str, List]:
        """Get parameter grid for a model."""
        # Override in subclasses with model-specific grids
        return {}

    def blend_models(
        self,
        models: List[Any],
        method: str = 'soft',
        weights: Optional[List[float]] = None,
    ) -> Any:
        """
        Blend multiple models together.

        Parameters
        ----------
        models : list
            List of trained models to blend.
        method : str, default='soft'
            Blending method: 'soft' (probability averaging), 'hard' (voting).
        weights : list of float, optional
            Weights for each model.

        Returns
        -------
        blended : BlendedModel
            Blended model.
        """
        if weights is None:
            weights = [1.0 / len(models)] * len(models)

        return BlendedModel(models, weights, method)

    def predict(self, model: Any, X: np.ndarray) -> np.ndarray:
        """Make predictions using a model."""
        return model.infer(X)

    def save_model(self, model: Any, path: str):
        """Save model to disk."""
        import pickle
        with open(path, 'wb') as f:
            pickle.dump(model, f)

    def load_model(self, path: str) -> Any:
        """Load model from disk."""
        import pickle
        with open(path, 'rb') as f:
            return pickle.load(f)


class BlendedModel:
    """
    Blended ensemble of multiple models.
    """

    def __init__(
        self,
        models: List[Any],
        weights: List[float],
        method: str = 'soft',
    ):
        self.models = models
        self.weights = np.array(weights)
        self.weights /= self.weights.sum()  # Normalize
        self.method = method

    def train(self, X: np.ndarray, y: np.ndarray) -> "BlendedModel":
        """Train all constituent models."""
        for model in self.models:
            model.train(X, y)
        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        predictions = np.array([model.infer(X) for model in self.models])

        if self.method == 'soft' and hasattr(self.models[0], 'predict_proba'):
            # Average probabilities
            probs = np.zeros((len(X), 2))
            for model, weight in zip(self.models, self.weights):
                if hasattr(model, 'predict_proba'):
                    probs += weight * model.predict_proba(X)
            return (probs[:, 1] > 0.5).astype(int)
        else:
            # Weighted average (regression) or voting (classification)
            return np.average(predictions, axis=0, weights=self.weights)
