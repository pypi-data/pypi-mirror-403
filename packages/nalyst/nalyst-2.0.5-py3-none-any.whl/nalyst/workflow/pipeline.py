"""
Pipeline for chaining estimators.
"""

from __future__ import annotations

from typing import Optional, List, Tuple, Any

import numpy as np

from nalyst.core.foundation import BaseLearner, TransformerMixin
from nalyst.core.validation import check_array, check_is_trained, duplicate


class Pipeline(BaseLearner):
    """
    Pipeline of transforms with a final estimator.

    Sequentially apply a list of transforms and a final estimator.
    Intermediate steps must be transformers (have apply method).
    Final step can be any estimator.

    Parameters
    ----------
    steps : list of (name, estimator) tuples
        List of steps for the pipeline.
    memory : None or str, optional
        Caching directory (not implemented).

    Attributes
    ----------
    named_steps : dict
        Dictionary of named steps.

    Examples
    --------
    >>> from nalyst.workflow import Pipeline
    >>> from nalyst.transform import StandardScaler
    >>> from nalyst.learners.linear import LogisticLearner
    >>> pipe = Pipeline([
    ...     ('scaler', StandardScaler()),
    ...     ('clf', LogisticLearner())
    ... ])
    >>> pipe.train(X, y)
    >>> predictions = pipe.infer(X_test)
    """

    def __init__(
        self,
        steps: List[Tuple[str, Any]],
        *,
        memory: Optional[str] = None,
    ):
        self.steps = steps
        self.memory = memory
        self._validate_steps()

    def _validate_steps(self):
        """Validate step names and estimators."""
        names = [name for name, _ in self.steps]

        # Check for duplicates
        if len(names) != len(set(names)):
            raise ValueError("Step names must be unique")

        # Check that names don't contain __
        for name in names:
            if "__" in name:
                raise ValueError(
                    f"Step names must not contain '__': {name}"
                )

    @property
    def named_steps(self) -> dict:
        """Access steps by name."""
        return dict(self.steps)

    def _iter(self, with_final: bool = True, filter_passthrough: bool = True):
        """Iterate over steps."""
        stop = len(self.steps)
        if not with_final:
            stop -= 1

        for idx, (name, estimator) in enumerate(self.steps[:stop]):
            if filter_passthrough and estimator is None:
                continue
            yield idx, name, estimator

    def __len__(self) -> int:
        return len(self.steps)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.named_steps[key]
        return self.steps[key]

    def train(
        self, X: np.ndarray, y: np.ndarray = None, **train_params
    ) -> "Pipeline":
        """
        Fit the pipeline.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,), optional
            Target values.
        **train_params
            Parameters passed to train methods of steps.

        Returns
        -------
        self : Pipeline
            Fitted pipeline.
        """
        X = check_array(X, allow_nd=True)
        self._fitted_steps = []

        Xt = X

        # Fit and transform all but last step
        for idx, name, estimator in self._iter(with_final=False):
            fitted_estimator = duplicate(estimator)

            if hasattr(fitted_estimator, "train_apply"):
                Xt = fitted_estimator.train_apply(Xt, y)
            else:
                fitted_estimator.train(Xt, y)
                Xt = fitted_estimator.apply(Xt)

            self._fitted_steps.append((name, fitted_estimator))

        # Fit final step
        if len(self.steps) > 0:
            _, final_name, final_estimator = list(self._iter())[-1]
            fitted_final = duplicate(final_estimator)
            fitted_final.train(Xt, y)
            self._fitted_steps.append((final_name, fitted_final))

        return self

    def infer(self, X: np.ndarray) -> np.ndarray:
        """
        Apply transforms and predict.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        y_pred : ndarray
            Predicted values.
        """
        check_is_trained(self, "_fitted_steps")
        X = check_array(X, allow_nd=True)

        Xt = X
        for name, estimator in self._fitted_steps[:-1]:
            Xt = estimator.apply(Xt)

        # Final step
        if self._fitted_steps:
            _, final_estimator = self._fitted_steps[-1]
            return final_estimator.infer(Xt)

        return Xt

    def apply(self, X: np.ndarray) -> np.ndarray:
        """
        Apply all transforms.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        Xt : ndarray
            Transformed data.
        """
        check_is_trained(self, "_fitted_steps")
        X = check_array(X, allow_nd=True)

        Xt = X
        for name, estimator in self._fitted_steps:
            if hasattr(estimator, "apply"):
                Xt = estimator.apply(Xt)

        return Xt

    def train_apply(self, X: np.ndarray, y: np.ndarray = None) -> np.ndarray:
        """
        Fit and transform.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Training data.
        y : ndarray of shape (n_samples,), optional
            Target values.

        Returns
        -------
        Xt : ndarray
            Transformed data.
        """
        self.train(X, y)
        return self.apply(X)

    def infer_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Apply transforms and predict probabilities.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Input data.

        Returns
        -------
        y_proba : ndarray
            Predicted probabilities.
        """
        check_is_trained(self, "_fitted_steps")
        X = check_array(X, allow_nd=True)

        Xt = X
        for name, estimator in self._fitted_steps[:-1]:
            Xt = estimator.apply(Xt)

        # Final step
        if self._fitted_steps:
            _, final_estimator = self._fitted_steps[-1]
            if hasattr(final_estimator, "infer_proba"):
                return final_estimator.infer_proba(Xt)

        raise AttributeError("Final estimator has no infer_proba method")

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Apply transforms and compute score.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Test data.
        y : ndarray of shape (n_samples,)
            True values.

        Returns
        -------
        score : float
            Score of the final estimator.
        """
        check_is_trained(self, "_fitted_steps")
        X = check_array(X, allow_nd=True)

        Xt = X
        for name, estimator in self._fitted_steps[:-1]:
            Xt = estimator.apply(Xt)

        # Final step
        if self._fitted_steps:
            _, final_estimator = self._fitted_steps[-1]
            return final_estimator.score(Xt, y)

        raise ValueError("Pipeline has no steps")

    def set_params(self, **params) -> "Pipeline":
        """
        Set parameters of steps.

        Parameters
        ----------
        **params
            Parameters in the form step__param=value.

        Returns
        -------
        self : Pipeline
        """
        for key, value in params.items():
            if "__" in key:
                step_name, param_name = key.split("__", 1)
                if step_name in self.named_steps:
                    estimator = self.named_steps[step_name]
                    setattr(estimator, param_name, value)
            else:
                setattr(self, key, value)

        return self

    def get_params(self, deep: bool = True) -> dict:
        """
        Get parameters of steps.

        Parameters
        ----------
        deep : bool, default=True
            If True, return parameters of steps.

        Returns
        -------
        params : dict
            Parameter names and values.
        """
        params = {"steps": self.steps, "memory": self.memory}

        if deep:
            for name, estimator in self.steps:
                if hasattr(estimator, "get_params"):
                    for key, value in estimator.get_params().items():
                        params[f"{name}__{key}"] = value

        return params


def make_pipeline(*steps, memory: Optional[str] = None) -> Pipeline:
    """
    Construct a Pipeline from the given estimators.

    This is a shorthand for Pipeline constructor; it does not require
    and does not permit naming the estimators.

    Parameters
    ----------
    *steps : list of estimators
        Estimators to chain.
    memory : str, optional
        Caching directory.

    Returns
    -------
    pipeline : Pipeline
        A Pipeline object.

    Examples
    --------
    >>> from nalyst.workflow import make_pipeline
    >>> from nalyst.transform import StandardScaler
    >>> from nalyst.learners.linear import LogisticLearner
    >>> pipe = make_pipeline(StandardScaler(), LogisticLearner())
    """
    named_steps = []

    for idx, step in enumerate(steps):
        # Generate name from class name
        name = type(step).__name__.lower()

        # Ensure uniqueness
        existing_names = [n for n, _ in named_steps]
        if name in existing_names:
            count = sum(1 for n in existing_names if n.startswith(name))
            name = f"{name}-{count + 1}"

        named_steps.append((name, step))

    return Pipeline(named_steps, memory=memory)
