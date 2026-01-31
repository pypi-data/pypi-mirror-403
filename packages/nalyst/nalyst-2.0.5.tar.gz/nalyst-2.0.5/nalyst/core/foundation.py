"""
Foundation classes for all learners and models in Nalyst.

This module provides the base architecture for all machine learning
components including learners, transformers, and other models.
"""

from __future__ import annotations

import copy
import inspect
import warnings
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union, TypeVar

import numpy as np

from nalyst.core.settings import get_settings, settings_context


T = TypeVar('T', bound='BaseLearner')


def duplicate(learner: T, *, safe: bool = True) -> T:
    """
    Create an unfitted copy of a learner with identical parameters.

    This creates a deep copy of the learner's configuration without
    copying any fitted state or training data.

    Parameters
    ----------
    learner : BaseLearner or collection thereof
        The learner instance(s) to duplicate.
    safe : bool, default=True
        If True, raises an error for non-learner objects.
        If False, falls back to deep copy.

    Returns
    -------
    learner : object
        A new learner instance with the same parameters.

    Examples
    --------
    >>> from nalyst.learners.linear import LogisticLearner
    >>> model = LogisticLearner(strength=0.5)
    >>> model_copy = duplicate(model)
    >>> model_copy.strength
    0.5
    """
    if hasattr(learner, "__nalyst_duplicate__") and not inspect.isclass(learner):
        return learner.__nalyst_duplicate__()
    return _duplicate_parametrized(learner, safe=safe)


def _duplicate_parametrized(learner: Any, *, safe: bool = True) -> Any:
    """Internal implementation of duplicate."""
    learner_type = type(learner)

    if learner_type is dict:
        return {k: duplicate(v, safe=safe) for k, v in learner.items()}
    elif learner_type in (list, tuple, set, frozenset):
        return learner_type([duplicate(e, safe=safe) for e in learner])
    elif not hasattr(learner, "get_params") or isinstance(learner, type):
        if not safe:
            return copy.deepcopy(learner)
        else:
            if isinstance(learner, type):
                raise TypeError(
                    "Cannot duplicate a class. Provide an instance instead."
                )
            else:
                raise TypeError(
                    f"Cannot duplicate '{repr(learner)}' (type {type(learner)}): "
                    "it does not appear to be a Nalyst learner as it lacks "
                    "a 'get_params' method."
                )

    klass = learner.__class__
    params = learner.get_params(deep=False)

    # Recursively duplicate nested learners
    new_params = {}
    for name, param in params.items():
        new_params[name] = duplicate(param, safe=False)

    new_learner = klass(**new_params)

    # Verify parameters were set correctly
    set_params = new_learner.get_params(deep=False)
    for name in new_params:
        if new_params[name] is not set_params[name]:
            raise RuntimeError(
                f"Cannot duplicate {learner}: constructor does not "
                f"properly set parameter '{name}'"
            )

    return new_learner


class BaseLearner(metaclass=ABCMeta):
    """
    Base class for all learners in Nalyst.

    This provides default implementations for:

    - Parameter getting/setting via `get_params()` and `set_params()`
    - String representation
    - Serialization support
    - Parameter validation
    - HTML representation for notebooks

    Notes
    -----
    All learners should specify their parameters as explicit keyword
    arguments in `__init__` (no *args or **kwargs).

    Examples
    --------
    >>> from nalyst.core import BaseLearner
    >>> class MyLearner(BaseLearner):
    ...     def __init__(self, *, alpha=1.0, max_steps=100):
    ...         self.alpha = alpha
    ...         self.max_steps = max_steps
    ...
    ...     def train(self, X, y=None):
    ...         self.is_trained_ = True
    ...         return self
    >>>
    >>> learner = MyLearner(alpha=0.5)
    >>> learner.get_params()
    {'alpha': 0.5, 'max_steps': 100}
    """

    @classmethod
    def _get_param_names(cls) -> List[str]:
        """Get parameter names from the constructor signature."""
        init = getattr(cls.__init__, "deprecated_original", cls.__init__)
        if init is object.__init__:
            return []

        signature = inspect.signature(init)
        parameters = [
            p for p in signature.parameters.values()
            if p.name != "self" and p.kind != p.VAR_KEYWORD
        ]

        for p in parameters:
            if p.kind == p.VAR_POSITIONAL:
                raise RuntimeError(
                    f"Nalyst learners must specify all parameters as keyword "
                    f"arguments in __init__. {cls} with signature {signature} "
                    f"uses *args which is not allowed."
                )

        return sorted([p.name for p in parameters])

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """
        Get parameters for this learner.

        Parameters
        ----------
        deep : bool, default=True
            If True, returns parameters for nested learners as well.

        Returns
        -------
        params : dict
            Parameter names mapped to their values.
        """
        result = {}
        for key in self._get_param_names():
            value = getattr(self, key)
            if deep and hasattr(value, "get_params") and not isinstance(value, type):
                nested = value.get_params()
                result.update({f"{key}__{k}": v for k, v in nested.items()})
            result[key] = value
        return result

    def set_params(self, **params) -> 'BaseLearner':
        """
        Set parameters for this learner.

        Works on simple learners and nested structures. Nested parameters
        use double underscore notation: `<component>__<parameter>`.

        Parameters
        ----------
        **params : dict
            Learner parameters to set.

        Returns
        -------
        self : BaseLearner
            The learner instance.
        """
        if not params:
            return self

        valid_params = self.get_params(deep=True)
        nested = defaultdict(dict)

        for key, value in params.items():
            key_parts = key.split("__", 1)
            if len(key_parts) == 2:
                nested[key_parts[0]][key_parts[1]] = value
            else:
                if key not in valid_params:
                    local_params = self._get_param_names()
                    raise ValueError(
                        f"Invalid parameter '{key}' for {self.__class__.__name__}. "
                        f"Valid parameters: {local_params}"
                    )
                setattr(self, key, value)
                valid_params[key] = value

        for key, sub_params in nested.items():
            valid_params[key].set_params(**sub_params)

        return self

    def __nalyst_duplicate__(self) -> 'BaseLearner':
        """Create an unfitted duplicate of this learner."""
        return _duplicate_parametrized(self)

    def __repr__(self, max_chars: int = 500) -> str:
        """Create a string representation of this learner."""
        from nalyst.utils.formatting import format_learner
        return format_learner(self, max_chars=max_chars)

    def __getstate__(self) -> Dict[str, Any]:
        """Get state for pickling."""
        if hasattr(self, "__slots__"):
            raise TypeError(
                "Learners inheriting from BaseLearner cannot use __slots__."
            )

        try:
            state = super().__getstate__()
            if state is None:
                state = self.__dict__.copy()
        except AttributeError:
            state = self.__dict__.copy()

        from nalyst import __version__
        state["_nalyst_version"] = __version__
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Set state from pickle."""
        from nalyst import __version__

        pickled_version = state.pop("_nalyst_version", "unknown")
        if pickled_version != __version__:
            warnings.warn(
                f"Unpickling {self.__class__.__name__} from version "
                f"{pickled_version} into version {__version__}. "
                "This may cause compatibility issues.",
                UserWarning
            )

        try:
            super().__setstate__(state)
        except AttributeError:
            self.__dict__.update(state)

    def _validate_params(self) -> None:
        """Validate parameter types and values."""
        if hasattr(self, "_param_constraints"):
            from nalyst.core.validation import validate_constraints
            validate_constraints(
                self._param_constraints,
                self.get_params(deep=False),
                caller=self.__class__.__name__
            )

    def __nalyst_tags__(self) -> 'LearnerTags':
        """Return tags describing this learner's capabilities."""
        from nalyst.core.tags import LearnerTags, TargetTags
        return LearnerTags(
            learner_type=None,
            target_tags=TargetTags(required=False),
        )

    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks."""
        from nalyst.utils.formatting import learner_html_repr
        return learner_html_repr(self)


class ClassifierMixin:
    """
    Mixin for classification learners.

    Provides:
    - `score()` method using accuracy
    - Sets learner type tag to 'classifier'

    Examples
    --------
    >>> from nalyst.core import ClassifierMixin, BaseLearner
    >>> class MyClassifier(ClassifierMixin, BaseLearner):
    ...     def train(self, X, y):
    ...         self.classes_ = np.unique(y)
    ...         return self
    ...     def infer(self, X):
    ...         return np.zeros(len(X))
    """

    def score(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute accuracy on given data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Test samples.
        y : array-like of shape (n_samples,)
            True labels.
        sample_weight : array-like of shape (n_samples,), optional
            Sample weights.

        Returns
        -------
        score : float
            Mean accuracy of predictions.
        """
        from nalyst.metrics.classification import accuracy
        return accuracy(y, self.infer(X), sample_weight=sample_weight)

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags, TargetTags, ClassifierTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.learner_type = "classifier"
        tags.classifier_tags = ClassifierTags()
        tags.target_tags = TargetTags(required=True)
        return tags


class RegressorMixin:
    """
    Mixin for regression learners.

    Provides:
    - `score()` method using R coefficient
    - Sets learner type tag to 'regressor'
    """

    def score(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sample_weight: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute R coefficient on given data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Test samples.
        y : array-like of shape (n_samples,)
            True values.
        sample_weight : array-like of shape (n_samples,), optional
            Sample weights.

        Returns
        -------
        score : float
            R coefficient of predictions.
        """
        from nalyst.metrics.regression import r2_coefficient
        return r2_coefficient(y, self.infer(X), sample_weight=sample_weight)

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags, TargetTags, RegressorTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.learner_type = "regressor"
        tags.regressor_tags = RegressorTags()
        tags.target_tags = TargetTags(required=True)
        return tags


class TransformerMixin:
    """
    Mixin for transformer components.

    Provides:
    - `train_transform()` method that chains train and transform
    - `set_output()` for configuring output format
    """

    def train_transform(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        **train_params
    ) -> np.ndarray:
        """
        Train on X and then transform X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Input samples.
        y : array-like of shape (n_samples,), optional
            Target values (required for supervised transformers).
        **train_params : dict
            Additional training parameters.

        Returns
        -------
        X_transformed : ndarray
            Transformed samples.
        """
        if y is None:
            return self.train(X, **train_params).transform(X)
        else:
            return self.train(X, y, **train_params).transform(X)

    def set_output(self, *, transform: Optional[str] = None) -> 'TransformerMixin':
        """
        Configure output format for transform methods.

        Parameters
        ----------
        transform : {"default", "pandas", "polars"}, optional
            Output format. None leaves unchanged.

        Returns
        -------
        self : TransformerMixin
        """
        if transform is not None:
            self._output_format = transform
        return self

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags, TransformerTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.transformer_tags = TransformerTags()
        return tags


class ClusterMixin:
    """
    Mixin for clustering algorithms.

    Provides:
    - `train_infer()` method for one-step clustering
    - Sets learner type tag to 'clusterer'
    """

    def train_infer(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Train on X and return cluster labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Input samples.
        y : ignored
            Not used, present for API consistency.
        **kwargs : dict
            Additional parameters for training.

        Returns
        -------
        labels : ndarray of shape (n_samples,)
            Cluster labels for each sample.
        """
        self.train(X, **kwargs)
        return self.labels_

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.learner_type = "clusterer"
        return tags


class SelectorMixin:
    """
    Mixin for feature selection components.

    Provides:
    - `get_support()` method for selected feature mask
    - `transform()` that applies feature selection
    """

    def get_support(self, indices: bool = False) -> np.ndarray:
        """
        Get mask or indices of selected features.

        Parameters
        ----------
        indices : bool, default=False
            If True, return indices instead of boolean mask.

        Returns
        -------
        support : ndarray
            Boolean mask or integer indices of selected features.
        """
        mask = self._get_support_mask()
        if indices:
            return np.where(mask)[0]
        return mask

    @abstractmethod
    def _get_support_mask(self) -> np.ndarray:
        """Get boolean mask of selected features."""
        pass

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Reduce X to selected features.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Input samples.

        Returns
        -------
        X_selected : ndarray of shape (n_samples, n_selected_features)
            Samples with only selected features.
        """
        from nalyst.core.validation import check_is_trained, check_array
        check_is_trained(self)
        X = check_array(X)
        mask = self.get_support()
        if len(mask) != X.shape[1]:
            raise ValueError(
                f"X has {X.shape[1]} features but selector expects {len(mask)}"
            )
        return X[:, mask]


class MetaLearnerMixin:
    """
    Mixin for meta-learners that wrap other learners.

    Examples include ensemble methods and parameter search utilities.
    """
    pass


class DensityMixin:
    """
    Mixin for density estimation models.

    Sets learner type tag to 'density_estimator'.
    """

    def score(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> float:
        """
        Compute log-likelihood of data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Input samples.
        y : ignored

        Returns
        -------
        log_likelihood : float
            Mean log-likelihood of samples.
        """
        return np.mean(self.score_samples(X))

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.learner_type = "density_estimator"
        return tags


class OutlierMixin:
    """
    Mixin for outlier detection models.

    Provides:
    - `train_infer()` for one-step outlier detection
    - Sets learner type tag to 'outlier_detector'
    """

    def train_infer(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        **kwargs
    ) -> np.ndarray:
        """
        Train on X and return outlier labels.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Input samples.
        y : ignored

        Returns
        -------
        labels : ndarray of shape (n_samples,)
            1 for inliers, -1 for outliers.
        """
        return self.train(X, **kwargs).infer(X)

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.learner_type = "outlier_detector"
        return tags


class MultiOutputMixin:
    """Mixin to mark learners that support multiple outputs."""

    def __nalyst_tags__(self) -> 'LearnerTags':
        from nalyst.core.tags import LearnerTags
        tags = super().__nalyst_tags__() if hasattr(super(), '__nalyst_tags__') else LearnerTags()
        tags.target_tags.multi_output = True
        return tags


# Utility functions for checking learner types
def is_classifier(learner: Any) -> bool:
    """Check if learner is a classifier."""
    from nalyst.core.tags import get_tags
    return get_tags(learner).learner_type == "classifier"


def is_regressor(learner: Any) -> bool:
    """Check if learner is a regressor."""
    from nalyst.core.tags import get_tags
    return get_tags(learner).learner_type == "regressor"


def is_clusterer(learner: Any) -> bool:
    """Check if learner is a clusterer."""
    from nalyst.core.tags import get_tags
    return get_tags(learner).learner_type == "clusterer"


def is_outlier_detector(learner: Any) -> bool:
    """Check if learner is an outlier detector."""
    from nalyst.core.tags import get_tags
    return get_tags(learner).learner_type == "outlier_detector"
