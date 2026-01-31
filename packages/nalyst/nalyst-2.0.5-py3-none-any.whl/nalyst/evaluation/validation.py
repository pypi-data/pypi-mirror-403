"""
Cross-validation utilities.

Provides functions for evaluating model performance
using cross-validation strategies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, Callable
import time

import numpy as np
from joblib import Parallel, delayed

from nalyst.core.foundation import duplicate, is_classifier
from nalyst.core.validation import check_array, check_random_state
from nalyst.evaluation.splitting import KFold, StratifiedKFold


def _score(
    learner: Any,
    X: np.ndarray,
    y: np.ndarray,
    scoring: Optional[Callable] = None,
) -> float:
    """Compute score for a learner."""
    if scoring is not None:
        y_pred = learner.infer(X)
        return scoring(y, y_pred)
    else:
        if hasattr(learner, "evaluate"):
            return learner.evaluate(X, y)
        else:
            y_pred = learner.infer(X)
            if is_classifier(learner):
                return np.mean(y_pred == y)
            else:
                return 1 - np.mean((y - y_pred) ** 2) / np.var(y)


def _fit_and_score(
    learner: Any,
    X: np.ndarray,
    y: np.ndarray,
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    scoring: Optional[Callable] = None,
    fit_params: Optional[Dict] = None,
    return_train_score: bool = False,
    return_estimator: bool = False,
    return_times: bool = False,
) -> Dict[str, Any]:
    """Fit a learner and score on test set."""
    fit_params = fit_params or {}

    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]

    result = {}

    # Fit
    start_fit = time.time()
    learner_dup = duplicate(learner)
    learner_dup.train(X_train, y_train, **fit_params)
    fit_time = time.time() - start_fit

    # Score on test
    start_score = time.time()
    test_score = _score(learner_dup, X_test, y_test, scoring)
    score_time = time.time() - start_score

    result["test_score"] = test_score

    if return_train_score:
        train_score = _score(learner_dup, X_train, y_train, scoring)
        result["train_score"] = train_score

    if return_estimator:
        result["estimator"] = learner_dup

    if return_times:
        result["fit_time"] = fit_time
        result["score_time"] = score_time

    return result


def cross_val_score(
    learner: Any,
    X: np.ndarray,
    y: np.ndarray,
    *,
    groups: Optional[np.ndarray] = None,
    scoring: Optional[Callable] = None,
    cv: Optional[Union[int, Any]] = None,
    n_jobs: Optional[int] = None,
    verbose: int = 0,
    fit_params: Optional[Dict] = None,
    error_score: Union[str, float] = np.nan,
) -> np.ndarray:
    """
    Evaluate a learner by cross-validation.

    Parameters
    ----------
    learner : object
        Learner to evaluate.
    X : array-like of shape (n_samples, n_features)
        Training data.
    y : array-like of shape (n_samples,)
        Target values.
    groups : array-like, optional
        Group labels for grouped cross-validation.
    scoring : callable, optional
        Scoring function. Default uses learner's evaluate method.
    cv : int or cross-validator, optional
        Cross-validation strategy. Default is 5-fold.
    n_jobs : int, optional
        Number of parallel jobs.
    verbose : int, default=0
        Verbosity level.
    fit_params : dict, optional
        Parameters to pass to train method.
    error_score : "raise" or float, default=np.nan
        Value for failed fits.

    Returns
    -------
    scores : ndarray of shape (n_splits,)
        Array of scores for each fold.

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import cross_val_score
    >>> from nalyst.learners.linear import LogisticLearner
    >>> X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]])
    >>> y = np.array([0, 0, 0, 1, 1, 1])
    >>> clf = LogisticLearner()
    >>> scores = cross_val_score(clf, X, y, cv=3)
    >>> scores
    array([...])
    """
    X = check_array(X)
    y = np.asarray(y)

    # Set up cross-validator
    if cv is None:
        cv = 5

    if isinstance(cv, int):
        if is_classifier(learner):
            cv = StratifiedKFold(n_splits=cv)
        else:
            cv = KFold(n_splits=cv)

    # Run cross-validation
    results = []

    if n_jobs == 1:
        for train_idx, test_idx in cv.split(X, y, groups):
            try:
                result = _fit_and_score(
                    learner, X, y, train_idx, test_idx,
                    scoring=scoring, fit_params=fit_params
                )
                results.append(result["test_score"])
            except Exception as e:
                if error_score == "raise":
                    raise
                results.append(error_score)
    else:
        splits = list(cv.split(X, y, groups))

        parallel_results = Parallel(n_jobs=n_jobs, verbose=verbose)(
            delayed(_fit_and_score)(
                learner, X, y, train_idx, test_idx,
                scoring=scoring, fit_params=fit_params
            )
            for train_idx, test_idx in splits
        )

        results = [r["test_score"] for r in parallel_results]

    return np.array(results)


def cross_validate(
    learner: Any,
    X: np.ndarray,
    y: np.ndarray,
    *,
    groups: Optional[np.ndarray] = None,
    scoring: Optional[Union[str, Callable, List, Dict]] = None,
    cv: Optional[Union[int, Any]] = None,
    n_jobs: Optional[int] = None,
    verbose: int = 0,
    fit_params: Optional[Dict] = None,
    return_train_score: bool = False,
    return_estimator: bool = False,
    error_score: Union[str, float] = np.nan,
) -> Dict[str, np.ndarray]:
    """
    Evaluate a learner by cross-validation with detailed results.

    Parameters
    ----------
    learner : object
        Learner to evaluate.
    X : array-like of shape (n_samples, n_features)
        Training data.
    y : array-like of shape (n_samples,)
        Target values.
    groups : array-like, optional
        Group labels for grouped cross-validation.
    scoring : str, callable, list, or dict, optional
        Scoring strategy.
    cv : int or cross-validator, optional
        Cross-validation strategy.
    n_jobs : int, optional
        Number of parallel jobs.
    verbose : int, default=0
        Verbosity level.
    fit_params : dict, optional
        Parameters to pass to train method.
    return_train_score : bool, default=False
        Whether to return training scores.
    return_estimator : bool, default=False
        Whether to return fitted estimators.
    error_score : "raise" or float, default=np.nan
        Value for failed fits.

    Returns
    -------
    results : dict
        Dictionary with keys:
        - 'test_score': array of test scores
        - 'fit_time': array of fit times
        - 'score_time': array of score times
        - 'train_score': (if requested) array of train scores
        - 'estimator': (if requested) list of fitted estimators

    Examples
    --------
    >>> import numpy as np
    >>> from nalyst.evaluation import cross_validate
    >>> from nalyst.learners.linear import LogisticLearner
    >>> X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]])
    >>> y = np.array([0, 0, 0, 1, 1, 1])
    >>> clf = LogisticLearner()
    >>> results = cross_validate(clf, X, y, cv=3, return_train_score=True)
    >>> results['test_score']
    array([...])
    """
    X = check_array(X)
    y = np.asarray(y)

    # Set up cross-validator
    if cv is None:
        cv = 5

    if isinstance(cv, int):
        if is_classifier(learner):
            cv = StratifiedKFold(n_splits=cv)
        else:
            cv = KFold(n_splits=cv)

    # Handle scoring
    scoring_func = None
    if callable(scoring):
        scoring_func = scoring

    # Run cross-validation
    splits = list(cv.split(X, y, groups))

    if n_jobs == 1:
        fold_results = []
        for train_idx, test_idx in splits:
            try:
                result = _fit_and_score(
                    learner, X, y, train_idx, test_idx,
                    scoring=scoring_func,
                    fit_params=fit_params,
                    return_train_score=return_train_score,
                    return_estimator=return_estimator,
                    return_times=True,
                )
                fold_results.append(result)
            except Exception as e:
                if error_score == "raise":
                    raise
                fold_results.append({
                    "test_score": error_score,
                    "fit_time": np.nan,
                    "score_time": np.nan,
                })
    else:
        fold_results = Parallel(n_jobs=n_jobs, verbose=verbose)(
            delayed(_fit_and_score)(
                learner, X, y, train_idx, test_idx,
                scoring=scoring_func,
                fit_params=fit_params,
                return_train_score=return_train_score,
                return_estimator=return_estimator,
                return_times=True,
            )
            for train_idx, test_idx in splits
        )

    # Aggregate results
    results = {
        "test_score": np.array([r["test_score"] for r in fold_results]),
        "fit_time": np.array([r.get("fit_time", np.nan) for r in fold_results]),
        "score_time": np.array([r.get("score_time", np.nan) for r in fold_results]),
    }

    if return_train_score:
        results["train_score"] = np.array([
            r.get("train_score", np.nan) for r in fold_results
        ])

    if return_estimator:
        results["estimator"] = [r.get("estimator") for r in fold_results]

    return results
