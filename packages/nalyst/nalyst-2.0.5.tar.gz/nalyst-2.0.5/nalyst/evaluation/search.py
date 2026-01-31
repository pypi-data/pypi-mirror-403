"""
Hyperparameter search utilities.

Provides grid search and randomized search
for model hyperparameter tuning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Callable, Iterator
from itertools import product
import time

import numpy as np
from joblib import Parallel, delayed

from nalyst.core.foundation import BaseLearner, duplicate, is_classifier
from nalyst.core.validation import check_array, check_random_state
from nalyst.evaluation.splitting import KFold, StratifiedKFold


def _check_param_grid(param_grid: Dict[str, List]) -> List[Dict]:
    """Convert param_grid to list of parameter dictionaries."""
    if not param_grid:
        return [{}]

    keys = list(param_grid.keys())
    values = [param_grid[k] for k in keys]

    param_list = []
    for combo in product(*values):
        param_dict = dict(zip(keys, combo))
        param_list.append(param_dict)

    return param_list


def _fit_and_score_grid(
    learner: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: Any,
    params: Dict,
    scoring: Optional[Callable] = None,
    return_train_score: bool = False,
) -> Dict[str, Any]:
    """Fit with given parameters and score using cross-validation."""
    from nalyst.evaluation.validation import cross_validate

    learner_dup = duplicate(learner)
    learner_dup.set_params(**params)

    results = cross_validate(
        learner_dup, X, y,
        cv=cv,
        scoring=scoring,
        return_train_score=return_train_score,
        n_jobs=1,
    )

    return {
        "params": params,
        "mean_test_score": np.mean(results["test_score"]),
        "std_test_score": np.std(results["test_score"]),
        "mean_fit_time": np.mean(results["fit_time"]),
        "test_scores": results["test_score"],
        "train_scores": results.get("train_score"),
    }


class GridSearchCV(BaseLearner):
    """
    Exhaustive search over specified parameter grid.

    Parameters
    ----------
    learner : object
        Base learner to tune.
    param_grid : dict or list of dicts
        Parameter grid. Keys are parameter names,
        values are lists of values to try.
    scoring : callable, optional
        Scoring function.
    n_jobs : int, optional
        Number of parallel jobs.
    refit : bool, default=True
        Refit best estimator on full data.
    cv : int or cross-validator, optional
        Cross-validation strategy.
    verbose : int, default=0
        Verbosity level.
    return_train_score : bool, default=False
        Whether to compute training scores.
    error_score : "raise" or float, default=np.nan
        Value for failed fits.

    Attributes
    ----------
    cv_results_ : dict
        Cross-validation results.
    best_estimator_ : object
        Best estimator after refit.
    best_score_ : float
        Best cross-validation score.
    best_params_ : dict
        Best parameters.
    best_index_ : int
        Index of best parameter combination.
    n_splits_ : int
        Number of CV splits.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import GridSearchCV
    >>> from nalyst.learners.linear import RidgeRegressor
    >>> X = np.array([[1], [2], [3], [4], [5]])
    >>> y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> param_grid = {"alpha": [0.1, 1.0, 10.0]}
    >>> search = GridSearchCV(RidgeRegressor(), param_grid, cv=3)
    >>> search.train(X, y)
    GridSearchCV(...)
    >>> search.best_params_
    {'alpha': ...}
    """

    def __init__(
        self,
        learner: Any,
        param_grid: Union[Dict[str, List], List[Dict[str, List]]],
        *,
        scoring: Optional[Callable] = None,
        n_jobs: Optional[int] = None,
        refit: bool = True,
        cv: Optional[Union[int, Any]] = None,
        verbose: int = 0,
        return_train_score: bool = False,
        error_score: Union[str, float] = np.nan,
    ):
        self.learner = learner
        self.param_grid = param_grid
        self.scoring = scoring
        self.n_jobs = n_jobs
        self.refit = refit
        self.cv = cv
        self.verbose = verbose
        self.return_train_score = return_train_score
        self.error_score = error_score

    def train(self, X: np.ndarray, y: np.ndarray, **fit_params) -> "GridSearchCV":
        """
        Run grid search with cross-validation.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.
        **fit_params
            Parameters passed to the train method.

        Returns
        -------
        self : GridSearchCV
        """
        X = check_array(X)
        y = np.asarray(y)

        self.n_features_in_ = X.shape[1]

        # Set up cross-validator
        cv = self.cv
        if cv is None:
            cv = 5

        if isinstance(cv, int):
            if is_classifier(self.learner):
                cv = StratifiedKFold(n_splits=cv)
            else:
                cv = KFold(n_splits=cv)

        self.n_splits_ = cv.get_n_splits(X, y)

        # Generate parameter combinations
        if isinstance(self.param_grid, list):
            param_list = []
            for pg in self.param_grid:
                param_list.extend(_check_param_grid(pg))
        else:
            param_list = _check_param_grid(self.param_grid)

        # Run grid search
        if self.n_jobs == 1:
            results = [
                _fit_and_score_grid(
                    self.learner, X, y, cv, params,
                    scoring=self.scoring,
                    return_train_score=self.return_train_score,
                )
                for params in param_list
            ]
        else:
            results = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                delayed(_fit_and_score_grid)(
                    self.learner, X, y, cv, params,
                    scoring=self.scoring,
                    return_train_score=self.return_train_score,
                )
                for params in param_list
            )

        # Aggregate results
        self.cv_results_ = {
            "params": [r["params"] for r in results],
            "mean_test_score": np.array([r["mean_test_score"] for r in results]),
            "std_test_score": np.array([r["std_test_score"] for r in results]),
            "mean_fit_time": np.array([r["mean_fit_time"] for r in results]),
            "rank_test_score": np.zeros(len(results), dtype=int),
        }

        # Add individual split scores
        for i in range(self.n_splits_):
            self.cv_results_[f"split{i}_test_score"] = np.array([
                r["test_scores"][i] for r in results
            ])

        if self.return_train_score:
            self.cv_results_["mean_train_score"] = np.array([
                np.mean(r["train_scores"]) if r["train_scores"] is not None else np.nan
                for r in results
            ])

        # Rank results
        ranks = np.argsort(-self.cv_results_["mean_test_score"])
        for rank, idx in enumerate(ranks):
            self.cv_results_["rank_test_score"][idx] = rank + 1

        # Best results
        self.best_index_ = int(np.argmax(self.cv_results_["mean_test_score"]))
        self.best_score_ = self.cv_results_["mean_test_score"][self.best_index_]
        self.best_params_ = self.cv_results_["params"][self.best_index_]

        # Refit on full data
        if self.refit:
            self.best_estimator_ = duplicate(self.learner)
            self.best_estimator_.set_params(**self.best_params_)
            self.best_estimator_.train(X, y, **fit_params)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict using best estimator."""
        if not self.refit:
            raise ValueError("Must set refit=True to use infer")
        return self.best_estimator_.infer(X)

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities using best estimator."""
        if not self.refit:
            raise ValueError("Must set refit=True to use infer_proba")
        return self.best_estimator_.infer_proba(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using best estimator."""
        if not self.refit:
            raise ValueError("Must set refit=True to use evaluate")
        return self.best_estimator_.evaluate(X, y)


class RandomizedSearchCV(BaseLearner):
    """
    Randomized search over hyperparameters.

    Samples parameters from specified distributions.

    Parameters
    ----------
    learner : object
        Base learner to tune.
    param_distributions : dict
        Parameter distributions. Values can be lists or
        scipy.stats distributions.
    n_iter : int, default=10
        Number of parameter settings to sample.
    scoring : callable, optional
        Scoring function.
    n_jobs : int, optional
        Number of parallel jobs.
    refit : bool, default=True
        Refit best estimator on full data.
    cv : int or cross-validator, optional
        Cross-validation strategy.
    verbose : int, default=0
        Verbosity level.
    random_state : int, optional
        Random seed.
    return_train_score : bool, default=False
        Whether to compute training scores.
    error_score : "raise" or float, default=np.nan
        Value for failed fits.

    Attributes
    ----------
    cv_results_ : dict
        Cross-validation results.
    best_estimator_ : object
        Best estimator after refit.
    best_score_ : float
        Best cross-validation score.
    best_params_ : dict
        Best parameters.
    best_index_ : int
        Index of best parameter combination.
    n_splits_ : int
        Number of CV splits.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import RandomizedSearchCV
    >>> from nalyst.learners.linear import RidgeRegressor
    >>> X = np.array([[1], [2], [3], [4], [5]])
    >>> y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    >>> param_dist = {"alpha": [0.1, 1.0, 10.0]}
    >>> search = RandomizedSearchCV(RidgeRegressor(), param_dist, n_iter=3, cv=2)
    >>> search.train(X, y)
    RandomizedSearchCV(...)
    """

    def __init__(
        self,
        learner: Any,
        param_distributions: Dict[str, Any],
        *,
        n_iter: int = 10,
        scoring: Optional[Callable] = None,
        n_jobs: Optional[int] = None,
        refit: bool = True,
        cv: Optional[Union[int, Any]] = None,
        verbose: int = 0,
        random_state: Optional[int] = None,
        return_train_score: bool = False,
        error_score: Union[str, float] = np.nan,
    ):
        self.learner = learner
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.scoring = scoring
        self.n_jobs = n_jobs
        self.refit = refit
        self.cv = cv
        self.verbose = verbose
        self.random_state = random_state
        self.return_train_score = return_train_score
        self.error_score = error_score

    def _sample_params(self, rng: np.random.RandomState) -> Dict:
        """Sample parameters from distributions."""
        params = {}

        for name, distribution in self.param_distributions.items():
            if hasattr(distribution, "rvs"):
                # scipy distribution
                params[name] = distribution.rvs(random_state=rng)
            elif isinstance(distribution, (list, np.ndarray)):
                # list of values
                params[name] = rng.choice(distribution)
            else:
                # single value
                params[name] = distribution

        return params

    def train(self, X: np.ndarray, y: np.ndarray, **fit_params) -> "RandomizedSearchCV":
        """
        Run randomized search with cross-validation.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.
        **fit_params
            Parameters passed to the train method.

        Returns
        -------
        self : RandomizedSearchCV
        """
        X = check_array(X)
        y = np.asarray(y)

        self.n_features_in_ = X.shape[1]

        # Set up cross-validator
        cv = self.cv
        if cv is None:
            cv = 5

        if isinstance(cv, int):
            if is_classifier(self.learner):
                cv = StratifiedKFold(n_splits=cv)
            else:
                cv = KFold(n_splits=cv)

        self.n_splits_ = cv.get_n_splits(X, y)

        # Sample parameters
        rng = check_random_state(self.random_state)
        param_list = [self._sample_params(rng) for _ in range(self.n_iter)]

        # Run search
        if self.n_jobs == 1:
            results = [
                _fit_and_score_grid(
                    self.learner, X, y, cv, params,
                    scoring=self.scoring,
                    return_train_score=self.return_train_score,
                )
                for params in param_list
            ]
        else:
            results = Parallel(n_jobs=self.n_jobs, verbose=self.verbose)(
                delayed(_fit_and_score_grid)(
                    self.learner, X, y, cv, params,
                    scoring=self.scoring,
                    return_train_score=self.return_train_score,
                )
                for params in param_list
            )

        # Aggregate results
        self.cv_results_ = {
            "params": [r["params"] for r in results],
            "mean_test_score": np.array([r["mean_test_score"] for r in results]),
            "std_test_score": np.array([r["std_test_score"] for r in results]),
            "mean_fit_time": np.array([r["mean_fit_time"] for r in results]),
            "rank_test_score": np.zeros(len(results), dtype=int),
        }

        # Add individual split scores
        for i in range(self.n_splits_):
            self.cv_results_[f"split{i}_test_score"] = np.array([
                r["test_scores"][i] for r in results
            ])

        if self.return_train_score:
            self.cv_results_["mean_train_score"] = np.array([
                np.mean(r["train_scores"]) if r["train_scores"] is not None else np.nan
                for r in results
            ])

        # Rank results
        ranks = np.argsort(-self.cv_results_["mean_test_score"])
        for rank, idx in enumerate(ranks):
            self.cv_results_["rank_test_score"][idx] = rank + 1

        # Best results
        self.best_index_ = int(np.argmax(self.cv_results_["mean_test_score"]))
        self.best_score_ = self.cv_results_["mean_test_score"][self.best_index_]
        self.best_params_ = self.cv_results_["params"][self.best_index_]

        # Refit on full data
        if self.refit:
            self.best_estimator_ = duplicate(self.learner)
            self.best_estimator_.set_params(**self.best_params_)
            self.best_estimator_.train(X, y, **fit_params)

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """Predict using best estimator."""
        if not self.refit:
            raise ValueError("Must set refit=True to use infer")
        return self.best_estimator_.infer(X)

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities using best estimator."""
        if not self.refit:
            raise ValueError("Must set refit=True to use infer_proba")
        return self.best_estimator_.infer_proba(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> float:
        """Score using best estimator."""
        if not self.refit:
            raise ValueError("Must set refit=True to use evaluate")
        return self.best_estimator_.evaluate(X, y)
