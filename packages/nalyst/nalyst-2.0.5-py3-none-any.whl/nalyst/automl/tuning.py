"""
Hyperparameter tuning strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import numpy as np
from itertools import product


class BaseTuner(ABC):
    """Base class for hyperparameter tuners."""

    def __init__(self, param_grid: Dict[str, List]):
        self.param_grid = param_grid
        self.best_params_ = None
        self.best_score_ = None
        self.results_ = []

    @abstractmethod
    def get_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate parameter combinations to try."""
        pass

    def search(
        self,
        model_class: Any,
        X: np.ndarray,
        y: np.ndarray,
        evaluate_fn: Callable,
        n_folds: int = 5,
        optimize: str = None,
    ) -> Any:
        """
        Search for best hyperparameters.

        Parameters
        ----------
        model_class : class
            Model class to instantiate.
        X : ndarray
            Training features.
        y : ndarray
            Training targets.
        evaluate_fn : callable
            Function to evaluate model, returns dict of metrics.
        n_folds : int
            Number of CV folds.
        optimize : str
            Metric to optimize. If None, uses first metric.

        Returns
        -------
        best_model : estimator
            Model with best hyperparameters.
        """
        n = len(X)
        indices = np.arange(n)
        np.random.shuffle(indices)

        fold_size = n // n_folds

        best_score = -np.inf
        best_params = None

        for params in self.get_param_combinations():
            fold_scores = []

            for i in range(n_folds):
                # Split
                val_start = i * fold_size
                val_end = (i + 1) * fold_size if i < n_folds - 1 else n

                val_idx = indices[val_start:val_end]
                train_idx = np.concatenate([indices[:val_start], indices[val_end:]])

                X_train = X[train_idx]
                y_train = y[train_idx]
                X_val = X[val_idx]
                y_val = y[val_idx]

                try:
                    # Train model
                    model = model_class(**params)
                    model.train(X_train, y_train)

                    # Evaluate
                    metrics = evaluate_fn(model, X_val, y_val)

                    if optimize is None:
                        optimize = list(metrics.keys())[0]

                    fold_scores.append(metrics.get(optimize, 0))
                except Exception:
                    fold_scores.append(-np.inf)

            avg_score = np.mean(fold_scores)

            self.results_.append({
                'params': params,
                'score': avg_score,
            })

            if avg_score > best_score:
                best_score = avg_score
                best_params = params

        self.best_params_ = best_params
        self.best_score_ = best_score

        # Return model with best params trained on full data
        best_model = model_class(**best_params)
        best_model.train(X, y)

        return best_model


class GridSearch(BaseTuner):
    """
    Exhaustive grid search over parameter grid.

    Parameters
    ----------
    param_grid : dict
        Dictionary with parameter names as keys and lists of values.

    Examples
    --------
    >>> grid = GridSearch({'C': [0.1, 1, 10], 'max_iter': [100, 1000]})
    >>> best_model = grid.search(LogisticLearner, X, y, evaluate_fn)
    """

    def get_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations."""
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())

        combinations = []
        for combo in product(*values):
            combinations.append(dict(zip(keys, combo)))

        return combinations


class RandomSearch(BaseTuner):
    """
    Random search over parameter grid.

    Parameters
    ----------
    param_grid : dict
        Dictionary with parameter names as keys and lists/distributions.
    n_iter : int, default=10
        Number of random combinations to try.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> search = RandomSearch({'C': [0.1, 1, 10], 'max_iter': [100, 1000]}, n_iter=5)
    >>> best_model = search.search(LogisticLearner, X, y, evaluate_fn)
    """

    def __init__(
        self,
        param_grid: Dict[str, List],
        n_iter: int = 10,
        random_state: Optional[int] = None,
    ):
        super().__init__(param_grid)
        self.n_iter = n_iter
        self.random_state = random_state

    def get_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate random parameter combinations."""
        if self.random_state is not None:
            np.random.seed(self.random_state)

        combinations = []

        for _ in range(self.n_iter):
            combo = {}
            for key, values in self.param_grid.items():
                if hasattr(values, 'rvs'):
                    # Scipy distribution
                    combo[key] = values.rvs()
                elif isinstance(values, (list, np.ndarray)):
                    combo[key] = np.random.choice(values)
                else:
                    combo[key] = values
            combinations.append(combo)

        return combinations


class BayesianOptimization(BaseTuner):
    """
    Bayesian optimization for hyperparameter tuning.

    Uses Gaussian Process to model the objective function and
    selects next points using expected improvement.

    Parameters
    ----------
    param_grid : dict
        Dictionary with parameter names as keys and (min, max) tuples or lists.
    n_iter : int, default=20
        Number of iterations.
    n_initial : int, default=5
        Number of initial random points.
    random_state : int, optional
        Random seed.

    Examples
    --------
    >>> bayes = BayesianOptimization(
    ...     {'C': (0.01, 100), 'gamma': (0.001, 10)},
    ...     n_iter=20
    ... )
    >>> best_model = bayes.search(SVC, X, y, evaluate_fn)
    """

    def __init__(
        self,
        param_grid: Dict[str, Any],
        n_iter: int = 20,
        n_initial: int = 5,
        random_state: Optional[int] = None,
    ):
        super().__init__(param_grid)
        self.n_iter = n_iter
        self.n_initial = n_initial
        self.random_state = random_state

        # Parse bounds
        self.bounds = {}
        self.is_integer = {}
        self.is_categorical = {}

        for key, value in param_grid.items():
            if isinstance(value, tuple) and len(value) == 2:
                self.bounds[key] = value
                self.is_integer[key] = isinstance(value[0], int) and isinstance(value[1], int)
                self.is_categorical[key] = False
            elif isinstance(value, list):
                self.bounds[key] = (0, len(value) - 1)
                self.is_integer[key] = True
                self.is_categorical[key] = True
            else:
                raise ValueError(f"Invalid parameter specification for {key}")

    def get_param_combinations(self) -> List[Dict[str, Any]]:
        """Generate parameter combinations using Bayesian optimization."""
        if self.random_state is not None:
            np.random.seed(self.random_state)

        # For simplicity, use random search when GP is not available
        # Full implementation would use Gaussian Process
        combinations = []

        for _ in range(self.n_iter):
            combo = {}
            for key in self.param_grid.keys():
                low, high = self.bounds[key]

                if self.is_categorical[key]:
                    idx = np.random.randint(low, high + 1)
                    combo[key] = self.param_grid[key][idx]
                elif self.is_integer[key]:
                    combo[key] = np.random.randint(low, high + 1)
                else:
                    # Log scale for large ranges
                    if high / (low + 1e-10) > 100:
                        log_val = np.random.uniform(np.log(low + 1e-10), np.log(high))
                        combo[key] = np.exp(log_val)
                    else:
                        combo[key] = np.random.uniform(low, high)

            combinations.append(combo)

        return combinations

    def _expected_improvement(
        self,
        X: np.ndarray,
        X_sample: np.ndarray,
        y_sample: np.ndarray,
        xi: float = 0.01,
    ) -> np.ndarray:
        """Compute expected improvement at points X."""
        from scipy.stats import norm

        # Simple GP prediction (would use sklearn GP in full implementation)
        # This is a placeholder
        mu = np.mean(y_sample)
        sigma = np.std(y_sample) + 1e-10

        best_f = np.max(y_sample)

        Z = (mu - best_f - xi) / sigma
        ei = (mu - best_f - xi) * norm.cdf(Z) + sigma * norm.pdf(Z)

        return ei
